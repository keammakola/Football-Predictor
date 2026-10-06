#!/usr/bin/env python3
"""Daily automation script for pre‑match predictions.

- Loads fixture schedule (CSV) via `data.py` utilities.
- Loads static xG data (synthetic fallback) via `xg_scraper.py`.
- Constructs feature matrix using the same pipeline as `run_baseline.py`.
- Loads the trained XGBoost model (`xgb_model.json`).
- Applies the **Strong Tier** filter (probability > 0.77 and > bookmaker implied).
- Sends alerts (email or webhook) defined in `config.json`.
- Appends a daily log to `experiments_daily.csv`.
"""
import json
import smtplib
import sys
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText

import pandas as pd
import xgboost as xgb

# Project‑relative imports – adjust if package layout changes
sys.path.append(str(Path(__file__).resolve().parents[1]))  # add project root to PYTHONPATH

from data import load_fixtures  # assumed function to load upcoming fixtures
from xg_scraper import get_xg_data  # returns DataFrame with xG info
from features import calculate_xg_form, calculate_situational_factors
from evaluate import map_odds_to_prob  # helper to get bookmaker implied probabilities

CONFIG_PATH = Path(__file__).with_name('config.json')
MODEL_PATH = Path(__file__).with_name('xgb_model.json')
DAILY_LOG = Path(__file__).with_name('experiments_daily.csv')

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def load_model() -> xgb.Booster:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    model = xgb.Booster()
    model.load_model(str(MODEL_PATH))
    return model

def build_features(fixtures: pd.DataFrame) -> pd.DataFrame:
    # Re‑use the same feature engineering pipeline as the training code.
    xg_df = get_xg_data()
    df = fixtures.merge(xg_df, on=['home_team', 'away_team', 'date'], how='left')
    df['xg_form'] = calculate_xg_form(df)
    df = calculate_situational_factors(df)
    # Drop columns not used by the model (keep same order as training)
    feature_cols = [c for c in df.columns if c not in ['date', 'home_team', 'away_team', 'result']]
    return df[feature_cols]

def strong_tier_filter(df: pd.DataFrame, probs: pd.Series, bookmaker_probs: pd.Series) -> pd.DataFrame:
    # Apply the same thresholds used in Phase 3.
    mask = (probs > 0.77) & (probs > bookmaker_probs)
    return df[mask]

def send_email(alerts: list, cfg: dict):
    if not alerts:
        return
    body = "\n".join(alerts)
    msg = MIMEText(body)
    msg["Subject"] = cfg.get("email_subject", "Strong Tier Match Alerts")
    msg["From"] = cfg["alert_email"]
    msg["To"] = cfg["alert_recipient"]

    with smtplib.SMTP_SSL(cfg["smtp_server"], cfg.get("smtp_port", 465)) as server:
        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.send_message(msg)

def send_webhook(alerts: list, cfg: dict):
    import requests
    if not alerts:
        return
    payload = {"alerts": alerts, "timestamp": datetime.utcnow().isoformat() + "Z"}
    requests.post(cfg["webhook_url"], json=payload)

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main():
    cfg = load_config()
    model = load_model()

    # Load upcoming fixtures – we assume `load_fixtures` returns a DataFrame with at least
    # ['date', 'home_team', 'away_team', 'mkt_H', 'mkt_A'] columns.
    fixtures = load_fixtures(upcoming=True)
    if fixtures.empty:
        print("No upcoming fixtures found.")
        return

    X = build_features(fixtures)
    dmatrix = xgb.DMatrix(X)
    preds = model.predict(dmatrix)
    # Assuming binary classifier where index 0 = Home win probability.
    prob_home = preds[:, 0] if preds.ndim > 1 else preds
    bookmaker_probs = map_odds_to_prob(fixtures['mkt_H'].values)

    # Filter Strong Tier bets
    filtered = strong_tier_filter(fixtures, prob_home, bookmaker_probs)
    if filtered.empty:
        print("No Strong Tier predictions today.")
        return

    alerts = []
    for _, row in filtered.iterrows():
        prob = prob_home[row.name]
        alerts.append(
            f"{row['date'].date()} – {row['home_team']} vs {row['away_team']} – "
            f"ProbWin={prob:.3f} – Bookie={bookmaker_probs[row.name]:.3f}"
        )

    # Dispatch alerts
    if cfg.get("email_enabled", True):
        send_email(alerts, cfg)
    if cfg.get("webhook_enabled", False) and cfg.get("webhook_url"):
        send_webhook(alerts, cfg)

    # Append to daily log
    log_path = DAILY_LOG
    today = datetime.utcnow().date()
    log_df = pd.DataFrame({
        "date": [today] * len(alerts),
        "summary": alerts,
    })
    if not log_path.is_file():
        log_df.to_csv(log_path, index=False)
    else:
        log_df.to_csv(log_path, mode="a", header=False, index=False)

    print(f"Sent {len(alerts)} alerts and logged to {log_path}")

if __name__ == "__main__":
    main()
