#!/usr/bin/env python3
"""Train the XGBoost model and serialize it for daily use.
This script mirrors the training logic from `train_xgb.py` but saves the
trained model to `xgb_model.json`.
"""
import sys
from pathlib import Path
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
import config
import data
import elo
import features
import xg_scraper
import evaluate as ev

def prepare_data():
    matches = data.load_matches()
    xg_df = xg_scraper.load_xg_data()
    matches = features.calculate_xg_form(matches, xg_df)
    matches = features.calculate_situational_factors(matches)
    matches = elo.elo_features(matches)
    feature_cols = [
        "elo_diff",
        "home_xg_roll", "home_xga_roll", "home_xg_ema", "home_xga_ema",
        "away_xg_roll", "away_xga_roll", "away_xg_ema", "away_xga_ema",
        "home_rest_days", "away_rest_days",
        "home_travel_fatigue", "away_travel_fatigue",
    ]
    return matches, feature_cols

def main():
    matches, feature_cols = prepare_data()
    eval_season = config.VALID_SEASON
    train = matches[matches["season"] < eval_season]
    if train.empty:
        print("No training data found for seasons before", eval_season)
        sys.exit(1)
    X_train = train[feature_cols]
    y_train_raw = train["FTR"]
    le = LabelEncoder()
    le.fit(ev.CLASSES)
    y_train = le.transform(y_train_raw)

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        eval_metric="mlogloss",
        learning_rate=0.05,
        max_depth=4,
        n_estimators=100,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=config.SEED,
    )
    model.fit(X_train, y_train)
    model_path = Path(__file__).with_name("xgb_model.json")
    model.save_model(str(model_path))
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()
