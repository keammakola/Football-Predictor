import argparse
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import log_loss, accuracy_score

import config
from model_spec import FEATURE_COLUMNS
import data
import elo
import evaluate as ev
import xg_scraper
import features

def prepare_data(league_name):
    matches = data.load_matches(league_name)
    
    # Feature Engineering
    xg_df = xg_scraper.load_xg_data(league_name)
    matches = features.calculate_xg_form(matches, xg_df)
    matches = features.calculate_situational_factors(matches)
    matches = elo.elo_features(matches)
    
    feature_cols = FEATURE_COLUMNS

    return matches, feature_cols

def train_and_evaluate(league_name):
    print(f"\n=============================")
    print(f"=== Training for {league_name} ===")
    print(f"=============================")
    matches, feature_cols = prepare_data(league_name)
    
    eval_season = config.VALID_SEASON
    train = matches[matches["season"] < eval_season]
    test = matches[matches["season"] == eval_season]
    
    if test.empty:
        print(f"No matches found for evaluation season: {eval_season}")
        return
        
    X_train = train[feature_cols]
    y_train_raw = train["FTR"]
    
    X_test = test[feature_cols]
    y_test_raw = test["FTR"]
    
    le = LabelEncoder()
    le.fit(ev.CLASSES)
    y_train = le.transform(y_train_raw)
    y_test = le.transform(y_test_raw)
    
    print(f"Training XGBoost on {len(X_train)} matches... Evaluating on {len(X_test)} matches.")
    
    model = xgb.XGBClassifier(
        objective="multi:softprob",
        eval_metric="mlogloss",
        learning_rate=0.05,
        max_depth=4,
        n_estimators=100,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=config.SEED
    )
    
    model.fit(X_train, y_train)
    
    # Save the model
    model_path = f"xgb_model_{league_name}.json"
    model.get_booster().save_model(model_path)
    print(f"Model saved to {model_path}")
    
    # Predict
    preds = model.predict_proba(X_test)
    loss = log_loss(y_test_raw, preds, labels=le.classes_)
    acc = accuracy_score(y_test_raw, le.inverse_transform(np.argmax(preds, axis=1)))
    
    print(f"Log Loss: {loss:.4f} | Accuracy: {acc:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", type=str, default="all", help="League to train, or 'all'")
    args = parser.parse_args()
    
    if args.league == "all":
        for l in config.LEAGUES.keys():
            train_and_evaluate(l)
    else:
        train_and_evaluate(args.league)
