import sys, os
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb
import warnings
from sklearn.preprocessing import LabelEncoder
import config
import data
from elo import elo_features
from xg_scraper import load_xg_data
from features import calculate_xg_form, calculate_situational_factors
from dixon_coles import fit_dixon_coles, predict_match
from evaluate import CLASSES

warnings.filterwarnings("ignore")

def run_backtest_for_season(league_name, test_season_code, matches):
    # Split data to ensure ZERO data leakage
    train_df = matches[matches["season"] < test_season_code].copy()
    test_df = matches[matches["season"] == test_season_code].copy()
    
    if test_df.empty or len(train_df) < 100:
        return [], []
        
    feature_cols = [
        "elo_diff", "home_xg_roll", "home_xga_roll", "home_xg_ema", "home_xga_ema",
        "away_xg_roll", "away_xga_roll", "away_xg_ema", "away_xga_ema",
        "home_rest_days", "away_rest_days", "home_travel_fatigue", "away_travel_fatigue"
    ]
    
    # 1. Train strict out-of-sample XGBoost model
    le = LabelEncoder()
    le.fit(CLASSES)
    X_train = train_df[feature_cols].astype(float)
    y_train = le.transform(train_df["FTR"])
    
    xgb_model = xgb.XGBClassifier(
        objective="multi:softprob", eval_metric="mlogloss", learning_rate=0.05,
        max_depth=4, n_estimators=100, subsample=0.8, colsample_bytree=0.8,
        random_state=config.SEED
    )
    xgb_model.fit(X_train, y_train)
    
    # Predict XGB
    X_test = test_df[feature_cols].astype(float)
    xgb_probs = xgb_model.predict_proba(X_test)
    xgb_p_home = xgb_probs[:, list(le.classes_).index('H')]
    xgb_p_draw = xgb_probs[:, list(le.classes_).index('D')]
    xgb_p_away = xgb_probs[:, list(le.classes_).index('A')]
    
    # 2. Fit strict out-of-sample Dixon-Coles
    dc_xi = config.LEAGUES.get(league_name, {}).get("dc_xi", 0.0065)
    dc_params = fit_dixon_coles(train_df, current_date=test_df['date'].min(), xi=dc_xi)
    
    # 3. Evaluate Bets
    results = []
    all_match_preds = []
    for idx, (orig_idx, row) in enumerate(test_df.iterrows()):
        home = row['HomeTeam']
        away = row['AwayTeam']
        actual_result = row['FTR']
        
        # Only use recorded source odds. Missing odds cannot support a P&L claim.
        source_odds = [row.get(column, float('nan')) for column in ('B365H', 'B365D', 'B365A')]
        if not all(pd.notna(value) and np.isfinite(float(value)) and float(value) > 1 for value in source_odds):
            continue
        odds_h, odds_d, odds_a = map(float, source_odds)

        # DC predictions
        dc_res = predict_match(home, away, dc_params)
        
        # Ensemble
        p_home = 0.5 * dc_res['p_home'] + 0.5 * xgb_p_home[idx]
        p_draw = 0.5 * dc_res['p_draw'] + 0.5 * xgb_p_draw[idx]
        p_away = 0.5 * dc_res['p_away'] + 0.5 * xgb_p_away[idx]
        
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home/total, p_draw/total, p_away/total
        
        # Tier logic
        probs = {'H': p_home, 'D': p_draw, 'A': p_away}
        sorted_probs = sorted(probs.values(), reverse=True)
        top_p = sorted_probs[0]
        lead = sorted_probs[0] - sorted_probs[1]
        
        pick = [k for k, v in probs.items() if v == top_p][0]
        
        tier = "None"
        if top_p >= 0.60 and lead >= 0.25:
            tier = "Strong"
        elif top_p >= 0.50 and lead >= 0.15:
            tier = "Lean"
            
        if tier in ["Strong"]:
            fair_odds = 1.0 / top_p if top_p > 0 else 0
            odds_taken = odds_h if pick == 'H' else (odds_d if pick == 'D' else odds_a)
            
            # ONLY BET IF IT IS A VALUE BET (Bookmaker Odds > Fair Odds)
            if odds_taken > fair_odds:
                pnl = -1.0
                if pick == actual_result:
                    pnl = odds_taken - 1.0
                    
                results.append({
                'season': test_season_code,
                'league': league_name,
                'match': f"{home} vs {away}",
                'tier': tier,
                'pick': pick,
                'prob': top_p,
                'odds_taken': odds_taken,
                'won': 1 if pnl > 0 else 0,
                'pnl': pnl
            })
            
        all_match_preds.append({
            "date": row['date'],
            "league": league_name,
            "home": home,
            "away": away,
            "p_home": p_home,
            "p_draw": p_draw,
            "p_away": p_away,
            "result": actual_result,
            "fthg": row.get('FTHG', pd.NA),
            "ftag": row.get('FTAG', pd.NA),
            "odds_home": odds_h,
            "odds_draw": odds_d,
            "odds_away": odds_a
        })
            
    return results, all_match_preds

def run_multi_season_backtest():
    leagues = ["EPL", "LaLiga", "Bundesliga", "SerieA", "Ligue1"]
    test_seasons = ["2122", "2223", "2324", "2425", "2526", "2627"]
    
    all_results = []
    all_matches = []
    print(f"Running Strict Walk-Forward Backtest for seasons: {', '.join(test_seasons)}")
    print("This will train a separate, isolated model for EVERY season to prevent data leakage...")
    print("-" * 75)
    
    for league_name in leagues:
        print(f"Processing {league_name}...")
        matches = data.load_matches(league_name)
        xg_df = load_xg_data(league_name)
        
        # Prep base features
        matches = calculate_xg_form(matches, xg_df)
        matches = calculate_situational_factors(matches)
        matches = elo_features(
            matches, 
            elo_k=config.LEAGUES[league_name].get("elo_k", config.ELO_K), 
            season_reg=config.LEAGUES[league_name].get("elo_season_regression", config.ELO_SEASON_REGRESSION)
        )
        
        feature_cols = [
            "elo_diff", "home_xg_roll", "home_xga_roll", "home_xg_ema", "home_xga_ema",
            "away_xg_roll", "away_xga_roll", "away_xg_ema", "away_xga_ema",
            "home_rest_days", "away_rest_days", "home_travel_fatigue", "away_travel_fatigue"
        ]
        
        for season in test_seasons:
            season_results, season_matches = run_backtest_for_season(league_name, season, matches)
            all_results.extend(season_results)
            all_matches.extend(season_matches)
    if not all_results:
        print("No results found.")
        return
        
    df_res = pd.DataFrame(all_results)
    df_res.to_csv("bets.csv", index=False)
    
    df_matches = pd.DataFrame(all_matches)
    df_matches.to_csv("matches.csv", index=False)
    
    # Summarize by League
    summary = []
    for l in leagues:
        l_df = df_res[df_res['league'] == l]
        if l_df.empty:
            continue
            
        strong = l_df[l_df['tier'] == 'Strong']
        
        s_bets, s_pnl = len(strong), strong['pnl'].sum()
        s_wins = strong['won'].sum()
        s_roi = (s_pnl / s_bets * 100) if s_bets > 0 else 0
        s_win_rate = (s_wins / s_bets * 100) if s_bets > 0 else 0
        
        summary.append({
            'League': l,
            'Strong Bets': s_bets,
            'Wins': s_wins,
            'Win Rate': f"{s_win_rate:.1f}%",
            'Strong P/L': round(s_pnl, 2),
            'Strong ROI': f"{s_roi:.1f}%"
        })
        
    sum_df = pd.DataFrame(summary)
    print("\n" + sum_df.to_string(index=False))
    
    # Overall summary
    total_bets = len(df_res)
    total_wins = df_res['won'].sum()
    total_pnl = df_res['pnl'].sum()
    total_roi = (total_pnl / total_bets) * 100 if total_bets > 0 else 0
    total_win_rate = (total_wins / total_bets) * 100 if total_bets > 0 else 0
    print("-" * 75)
    print(f"STRONG TIER (+EV FILTER) - OVERALL RESULTS ({len(test_seasons)} seasons, {len(leagues)} leagues):")
    print(f"Total Bets Placed: {total_bets}")
    print(f"Total Wins:        {total_wins} ({total_win_rate:.1f}% Win Rate)")
    print(f"Total Profit/Loss: {total_pnl:+.2f} units")
    print(f"Overall ROI:       {total_roi:+.1f}%")

if __name__ == "__main__":
    run_multi_season_backtest()
