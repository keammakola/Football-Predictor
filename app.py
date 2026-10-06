import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import subprocess
import os

st.set_page_config(page_title="Football Predictor R&D", layout="wide", page_icon="⚽")

st.title("⚽ Football Predictor R&D Pipeline")
st.markdown("Market Analysis, Paper Trading, and Feature Evaluation Dashboard")

tabs = st.tabs(["📊 Evaluation & Audit", "📝 Paper Trading Log", "⚙️ Configuration"])

with tabs[0]:
    st.header("Pipeline Evaluation Results")
    st.markdown("Analyze the latest run of the evaluation pipeline.")
    
    col_a, col_b = st.columns([1, 4])
    with col_a:
        if st.button("Run Full Evaluation Pipeline"):
            with st.spinner("Running full backtest, audit, and blend... (this takes ~3-4 mins)"):
                try:
                    subprocess.run(["venv/bin/python", "evaluate_pipeline.py"], check=True)
                    st.success("Evaluation complete! Reload to see changes.")
                except Exception as e:
                    st.error(f"Error during evaluation: {e}")
                    
    if os.path.exists("matches.csv") and os.path.exists("bets.csv"):
        matches = pd.read_csv("matches.csv")
        bets = pd.read_csv("bets.csv")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Matches Evaluated", f"{len(matches):,}")
        with col2:
            st.metric("Total Bets (Strong Tier)", f"{len(bets):,}")
        with col3:
            roi = (bets['pnl'].sum() / len(bets)) * 100 if len(bets) > 0 else 0
            st.metric("Bets ROI", f"{roi:+.1f}%")
            
        col_fig, col_stats = st.columns([2, 1])
        
        with col_fig:
            st.subheader("Model Calibration (Home Wins)")
            matches['bucket'] = pd.cut(matches['p_home'], bins=np.arange(0, 1.1, 0.1))
            calib = matches.groupby('bucket', observed=True).apply(
                lambda x: pd.Series({'hit_rate': (x['result'] == 'H').mean(), 'count': len(x)})
            ).reset_index()
            calib['bucket_mid'] = calib['bucket'].apply(lambda x: x.mid).astype(float)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=calib['bucket_mid'], y=calib['hit_rate'], mode='lines+markers', name='Model Calibration', marker=dict(size=8)))
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', line=dict(dash='dash', color='gray'), name='Perfect Calibration'))
            fig.update_layout(xaxis_title="Predicted Probability", yaxis_title="Actual Win Rate", height=400)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_stats:
            st.subheader("Historical Bets by League")
            league_bets = bets.groupby('league').agg(
                Bets=('pnl', 'count'),
                Wins=('won', 'sum'),
                Profit=('pnl', 'sum')
            ).reset_index()
            league_bets['ROI (%)'] = (league_bets['Profit'] / league_bets['Bets'] * 100).round(1)
            st.dataframe(league_bets, use_container_width=True, hide_index=True)

    else:
        st.warning("No evaluation data found. Run the Evaluation Pipeline first.")

with tabs[1]:
    st.header("Paper Trading Log")
    st.markdown("Log of matches where the model strongly disagrees with the market (Edge > 5%).")
    if os.path.exists("matches.csv"):
        matches = pd.read_csv("matches.csv")
        matches = matches.dropna(subset=['odds_home'])
        matches['implied_prob_home'] = 1 / matches['odds_home']
        matches['edge'] = matches['p_home'] - matches['implied_prob_home']
        
        # Latest matches with > 5% edge
        value_bets = matches[matches['edge'] > 0.05].copy()
        value_bets = value_bets.sort_values('date', ascending=False).head(50)
        value_bets = value_bets[['date', 'league', 'home', 'away', 'p_home', 'odds_home', 'implied_prob_home', 'edge', 'result']]
        
        st.dataframe(value_bets.style.format({
            'p_home': '{:.1%}',
            'implied_prob_home': '{:.1%}',
            'edge': '{:+.1%}',
            'odds_home': '{:.2f}'
        }), use_container_width=True, hide_index=True)
    else:
        st.info("Run backtest to generate match data.")

with tabs[2]:
    st.header("Pipeline Configuration")
    st.markdown("Current league memory and decay settings (`config.py`). Edit this file to test new configurations.")
    if os.path.exists("config.py"):
        with open("config.py", "r") as f:
            config_code = f.read()
        st.code(config_code, language="python")

