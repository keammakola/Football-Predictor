#!/usr/bin/env python3
"""Streamlit dashboard for pre‑match "Strong Tier" alerts.

- Shows upcoming fixtures that meet the Strong‑Tier criteria using the ensemble model.
- Reads configuration from `config.json`.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import xgboost as xgb
import streamlit as st

# ------------------------------------------------------------
# Adjust import path so project modules are discoverable
# ------------------------------------------------------------
sys.path.append(str(Path(__file__).resolve().parents[1]))  # project root

from data import load_matches
from elo import elo_features
from xg_scraper import get_xg_data
from features import calculate_xg_form, calculate_situational_factors
from api_fixtures import fetch_upcoming_fixtures
from dixon_coles import fit_dixon_coles, predict_match, PARAMS_FILE
from odds import fair_odds, margin_free_probs_proportional
from live_odds import get_live_odds

CONFIG_PATH = Path(__file__).with_name('config.json')
MODEL_PATH = Path(__file__).with_name('xgb_model.json')

# ------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------

def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        st.warning('Config file not found – UI will show default settings.')
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

@st.cache_resource
def load_xgb_model(league_name: str) -> xgb.Booster:
    model_path = Path(f"xgb_model_{league_name}.json")
    if not model_path.is_file() and league_name == "EPL" and MODEL_PATH.is_file():
        model_path = MODEL_PATH
        
    if not model_path.is_file():
        return None
        
    model = xgb.Booster()
    model.load_model(str(model_path))
    return model

@st.cache_data(ttl=3600)
def get_strong_tier_alerts(league_name: str) -> pd.DataFrame:
    """Run the end‑to‑end ensemble pipeline and return a DataFrame of alerts."""
    
    historical = load_matches(league_name)
    upcoming = fetch_upcoming_fixtures(league_name)
    
    if upcoming.empty:
        return pd.DataFrame()
        
    upcoming = upcoming.rename(columns={'home_team': 'HomeTeam', 'away_team': 'AwayTeam'})
    
    # FETCH LIVE ODDS
    live_odds_df = get_live_odds(league_name)

    df = pd.concat([historical, upcoming], ignore_index=True)
    df = df.sort_values('date').reset_index(drop=True)

    # Build Features
    df = elo_features(df)
    xg_df = get_xg_data(league_name)
    df = calculate_xg_form(df, xg_df)
    df = calculate_situational_factors(df)

    today = pd.Timestamp.now().normalize()
    max_date = today + pd.Timedelta(days=30)
    upcoming_df = df[(df['date'] >= today) & (df['date'] <= max_date)].copy()

    if upcoming_df.empty:
        return pd.DataFrame()

    # Load Dixon-Coles
    dc_params_path = Path(f"dixon_coles_params_{league_name}.json")
    if not dc_params_path.exists():
        dc_params = fit_dixon_coles(historical, current_date=today)
        with open(dc_params_path, 'w') as f:
            json.dump(dc_params, f)
    else:
        with open(dc_params_path, 'r') as f:
            dc_params = json.load(f)

    # XGBoost predictions
    xgb_model = load_xgb_model(league_name)
    if xgb_model is None:
        st.warning(f"No XGBoost model found for {league_name}. Please train one.")
        return pd.DataFrame()

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

    if xgb_probs.ndim > 1 and xgb_probs.shape[1] == 3:
        xgb_p_home, xgb_p_draw, xgb_p_away = xgb_probs[:, 2], xgb_probs[:, 1], xgb_probs[:, 0]
    else:
        xgb_p_home = xgb_probs[:, 0] if xgb_probs.ndim > 1 else xgb_probs
        xgb_p_draw = np.zeros(len(xgb_probs))
        xgb_p_away = 1.0 - xgb_p_home

    # Assemble rows
    alerts = []
    for idx, (original_idx, row) in enumerate(upcoming_df.iterrows()):
        home = row['HomeTeam']
        away = row['AwayTeam']
        
        # Check Live Odds
        b_odds = "N/A"
        edge_str = "N/A"
        if not live_odds_df.empty:
            match_odds = live_odds_df[(live_odds_df['home_team'] == home) & (live_odds_df['away_team'] == away)]
            if not match_odds.empty:
                odd_h = match_odds.iloc[0]['odds_H']
                odd_d = match_odds.iloc[0]['odds_D']
                odd_a = match_odds.iloc[0]['odds_A']
                # Calculate margin-free implied probs
                margin_free = margin_free_probs_proportional([1/odd_h, 1/odd_d, 1/odd_a])
        
        # Dixon-Coles
        dc_res = predict_match(home, away, dc_params)
        
        # Ensemble Pool (50/50)
        p_home = 0.5 * dc_res['p_home'] + 0.5 * xgb_p_home[idx]
        p_draw = 0.5 * dc_res['p_draw'] + 0.5 * xgb_p_draw[idx]
        p_away = 0.5 * dc_res['p_away'] + 0.5 * xgb_p_away[idx]
        
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home/total, p_draw/total, p_away/total
        
        # Tier logic
        probs_dict = {'Home': p_home, 'Draw': p_draw, 'Away': p_away}
        sorted_probs = sorted(probs_dict.items(), key=lambda x: x[1], reverse=True)
        top_outcome, top_p = sorted_probs[0]
        lead = top_p - sorted_probs[1][1]
        
        if top_p >= 0.60 and lead >= 0.25:
            tier = "Strong"
        elif top_p >= 0.50 and lead >= 0.15:
            tier = "Lean"
        else:
            tier = "No clear edge"
            
        # Add to alerts if Strong or Lean
        if tier in ["Strong", "Lean"]:
            
            # Finalize Live Odds Edge mapping for the pick
            if not live_odds_df.empty and not match_odds.empty:
                idx_map = {'Home': 0, 'Draw': 1, 'Away': 2}
                market_prob = margin_free[idx_map[top_outcome]]
                edge = top_p - market_prob
                b_odds_val = odd_h if top_outcome == 'Home' else (odd_d if top_outcome == 'Draw' else odd_a)
                
                # Format bookmaker name nicely (e.g. 'betway' -> 'Betway')
                bookie_name = str(match_odds.iloc[0]['bookmaker']).capitalize()
                b_odds = f"{b_odds_val:.2f} ({bookie_name})"
                edge_str = f"{edge*100:+.1f}%"
                
            scorelines_str = ", ".join([f"{x}-{y} ({p*100:.1f}%)" for x, y, p in dc_res['top_scorelines'][:2]])
            
            alerts.append({
                'Date': row['date'].strftime('%Y-%m-%d'),
                'Match': f"{home} vs {away}",
                'Pick': f"{top_outcome} ({tier})",
                'Model Prob': f"{top_p*100:.1f}%",
                'Fair Odds': f"{fair_odds(top_p):.2f}",
                'Live Odds': b_odds,
                'Edge': edge_str,
                'Exp Goals': f"{dc_res['lambda_home']:.2f} - {dc_res['lambda_away']:.2f}",
                'Top Scores': scorelines_str,
            })
            
    return pd.DataFrame(alerts)

import paper_trading

# ------------------------------------------------------------
# Streamlit UI definition
# ------------------------------------------------------------

def main():
    st.set_page_config(page_title='Football Betting Predictor', layout='wide')
    
    # Sidebar for League Selection & Filters
    import config
    league_options = ["All Leagues"] + list(config.LEAGUES.keys())
    
    st.sidebar.title("Configuration")
    selected_league = st.sidebar.selectbox("Select League", league_options, index=0)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Betting Filters")
    only_strong = st.sidebar.checkbox("🔥 Strong Tier Only", value=True, help="Hide 'Lean' predictions. Only show matches with high model confidence.")
    only_ev = st.sidebar.checkbox("📈 Positive Edge (+EV) Only", value=True, help="Only show matches where the Bookmaker odds pay out better than the Fair Odds.")
    
    st.title(f'Football Betting Command Center')

    if st.sidebar.button('Refresh alerts & Grade Matches'):
        st.cache_data.clear()
        st.rerun()

    tab1, tab2 = st.tabs(["🔴 Live Market Alerts", "📊 Paper Trading Ledger"])
    
    # GRADE PREVIOUS MATCHES
    paper_trading.grade_trades()

    with tab1:
        st.markdown(f"**Selected:** {selected_league}")
        leagues_to_run = list(config.LEAGUES.keys()) if selected_league == "All Leagues" else [selected_league]
        all_alerts = []
        
        with st.spinner(f"Calculating predictions & fetching live Betway odds..."):
            for l in leagues_to_run:
                try:
                    df = get_strong_tier_alerts(l)
                    if not df.empty:
                        df.insert(0, 'League', l)
                        all_alerts.append(df)
                except FileNotFoundError:
                    st.sidebar.error(f"Missing historical data for {l}.")
                    continue
                
        if not all_alerts:
            st.info('No predictions found right now.')
        else:
            alerts_df = pd.concat(all_alerts, ignore_index=True)
                
            if not alerts_df.empty:
                # Apply Filters
                if only_strong:
                    alerts_df = alerts_df[alerts_df['Pick'].str.contains("Strong")]
                    
                if only_ev:
                    def is_positive_edge(val):
                        if val == "N/A": 
                            return False # Hide if we can't verify positive edge
                        try:
                            return float(val.replace('%', '').replace('+', '')) > 0
                        except:
                            return False
                    alerts_df = alerts_df[alerts_df['Edge'].apply(is_positive_edge)]
                    
            if alerts_df.empty:
                st.info(f'No predictions match your strict filters for {selected_league} right now.')
            else:
                st.subheader(f'Actionable Matches ({len(alerts_df)} Found)')
                st.dataframe(alerts_df, use_container_width=True)
                
                # AUTO-LOG INTO PAPER TRADING
                paper_trading.log_trades(alerts_df)
                st.success("✅ Displayed +EV bets have been automatically locked into the Paper Trading Ledger.")

        st.caption(f'Last refreshed: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}')
        
    with tab2:
        ledger = paper_trading.get_ledger()
        if ledger.empty:
            st.info("Your paper trading ledger is currently empty. Matches will appear here automatically when +EV bets are found.")
        else:
            total_bets = len(ledger)
            completed_bets = ledger[ledger['Status'] != 'Pending']
            wins = len(ledger[ledger['Status'] == 'Won'])
            total_pnl = ledger['PnL'].sum()
            
            roi = (total_pnl / len(completed_bets) * 100) if len(completed_bets) > 0 else 0.0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Bets Logged", total_bets)
            col2.metric("Completed Bets", len(completed_bets))
            col3.metric("Win Rate", f"{(wins/len(completed_bets)*100 if len(completed_bets) > 0 else 0):.1f}%")
            col4.metric("Real ROI", f"{roi:+.1f}%", f"{total_pnl:+.2f} Units")
            
            # Show ledger reversed so newest are at the top
            st.dataframe(ledger.iloc[::-1], use_container_width=True)

if __name__ == '__main__':
    main()
