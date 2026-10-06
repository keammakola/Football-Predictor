#!/usr/bin/env python3
"""Generate a table of all predictions using the overhauled Ensemble model (Dixon-Coles + XGBoost).
Outputs a detailed summary meeting the Markdown specification.
"""
import sys, os
sys.path.append(os.getcwd())
import pandas as pd
import numpy as np
import xgboost as xgb
import json

from data import load_matches
from elo import elo_features
from xg_scraper import get_xg_data
from features import calculate_xg_form, calculate_situational_factors
from api_fixtures import fetch_upcoming_fixtures
from dixon_coles import fit_dixon_coles, predict_match, PARAMS_FILE
from odds import fair_odds, margin_free_probs_proportional

# 1. Load historical and upcoming matches
try:
    historical = load_matches()
except Exception as e:
    print(f"Error loading historical matches: {e}")
    sys.exit(1)

upcoming = fetch_upcoming_fixtures()
if upcoming.empty:
    print('No upcoming fixtures found from the API.')
    sys.exit(0)
upcoming = upcoming.rename(columns={'home_team': 'HomeTeam', 'away_team': 'AwayTeam'})

df = pd.concat([historical, upcoming], ignore_index=True)
df = df.sort_values('date').reset_index(drop=True)

# 2. Build Features
df = elo_features(df)
xg_df = get_xg_data()
df = calculate_xg_form(df, xg_df)
df = calculate_situational_factors(df)

today = pd.Timestamp.now().normalize()
max_date = today + pd.Timedelta(days=30)
upcoming_df = df[(df['date'] >= today) & (df['date'] <= max_date)].copy()

if upcoming_df.empty:
    print('No upcoming fixtures in the next 30 days.')
    sys.exit(0)

# 3. Fit or Load Dixon-Coles
if not PARAMS_FILE.exists():
    print("Fitting Dixon-Coles model (this may take a moment)...")
    # Fit only on historical matches before today
    dc_params = fit_dixon_coles(historical, current_date=today)
else:
    with open(PARAMS_FILE, 'r') as f:
        dc_params = json.load(f)

# 4. Load XGBoost
model_path = 'xgb_model.json'
if not os.path.exists(model_path):
    print('XGBoost Model file not found:', model_path)
    sys.exit(1)
xgb_model = xgb.Booster()
xgb_model.load_model(model_path)

expected_features = [
    'elo_diff', 'home_xg_roll', 'home_xga_roll', 'home_xg_ema', 'home_xga_ema',
    'away_xg_roll', 'away_xga_roll', 'away_xg_ema', 'away_xga_ema',
    'home_rest_days', 'away_rest_days', 'home_travel_fatigue', 'away_travel_fatigue'
]
for col in expected_features:
    if col not in upcoming_df.columns:
        upcoming_df[col] = 0.0

X = upcoming_df[expected_features].astype(float)
xgb_probs = xgb_model.predict(xgb.DMatrix(X))

# XGBoost output depends on objective; assuming multi:softprob for ['A', 'D', 'H'] (indices 0, 1, 2)
# We map: 2 -> Home, 1 -> Draw, 0 -> Away
# If it's a binary model for some reason, we handle that safely.
if xgb_probs.ndim > 1 and xgb_probs.shape[1] == 3:
    xgb_p_home = xgb_probs[:, 2]
    xgb_p_draw = xgb_probs[:, 1]
    xgb_p_away = xgb_probs[:, 0]
else:
    # Fallback to evenly distributing if unexpected shape
    xgb_p_home = xgb_probs[:, 0] if xgb_probs.ndim > 1 else xgb_probs
    xgb_p_draw = np.zeros(len(xgb_probs))
    xgb_p_away = 1.0 - xgb_p_home

# 5. Ensemble and Output Generation
output_rows = []
for idx, (original_idx, row) in enumerate(upcoming_df.iterrows()):
    home = row['HomeTeam']
    away = row['AwayTeam']
    
    # Dixon-Coles prediction
    dc_res = predict_match(home, away, dc_params)
    dc_p_home, dc_p_draw, dc_p_away = dc_res['p_home'], dc_res['p_draw'], dc_res['p_away']
    
    # XGBoost prediction
    x_home, x_draw, x_away = xgb_p_home[idx], xgb_p_draw[idx], xgb_p_away[idx]
    
    # Linear Pooling (50/50 weighting as default starting point)
    p_home = 0.5 * dc_p_home + 0.5 * x_home
    p_draw = 0.5 * dc_p_draw + 0.5 * x_draw
    p_away = 0.5 * dc_p_away + 0.5 * x_away
    
    # Normalize just in case
    total = p_home + p_draw + p_away
    p_home, p_draw, p_away = p_home/total, p_draw/total, p_away/total
    
    # Determine Tier
    probs = [p_home, p_draw, p_away]
    sorted_probs = sorted(probs, reverse=True)
    top_p = sorted_probs[0]
    lead = sorted_probs[0] - sorted_probs[1]
    
    if top_p >= 0.60 and lead >= 0.25:
        tier = "Strong"
    elif top_p >= 0.50 and lead >= 0.15:
        tier = "Lean"
    else:
        tier = "No clear edge"
        
    top_outcome = "Home" if top_p == p_home else ("Draw" if top_p == p_draw else "Away")
    
    # Format Scorelines
    scorelines_str = ", ".join([f"{x}-{y} ({p*100:.1f}%)" for x, y, p in dc_res['top_scorelines'][:3]])
    
    output_rows.append({
        'Date': row['date'].strftime('%Y-%m-%d'),
        'Match': f"{home} vs {away}",
        'P(H)': f"{p_home:.3f}",
        'P(D)': f"{p_draw:.3f}",
        'P(A)': f"{p_away:.3f}",
        'Fair Odds (H/D/A)': f"{fair_odds(p_home):.2f} / {fair_odds(p_draw):.2f} / {fair_odds(p_away):.2f}",
        'Exp Goals': f"{dc_res['lambda_home']:.2f} - {dc_res['lambda_away']:.2f}",
        'Top Scores': scorelines_str,
        'Tier': f"{tier} ({top_outcome})"
    })

res_df = pd.DataFrame(output_rows)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
print(res_df.to_string(index=False))
