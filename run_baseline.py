"""Baseline pipeline: league frequencies vs Elo -> 3-way probabilities.

  python run_baseline.py --download     # fetch raw CSVs once
  python run_baseline.py                # train on past, evaluate on VALID season
  python run_baseline.py --final        # ONE-TIME check on the TEST season
"""
import argparse
import datetime as dt
import random

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import config
import data
import elo
import evaluate as ev
from team_names import audit

random.seed(config.SEED)
np.random.seed(config.SEED)


def freq_baseline(train, n):
    freqs = train["FTR"].value_counts(normalize=True).reindex(ev.CLASSES).values
    return np.tile(freqs, (n, 1))


def fit_elo_model(train):
    clf = LogisticRegression(max_iter=1000)
    clf.fit(train[["elo_diff"]], train["FTR"])
    return clf


def predict_elo(clf, df):
    p = clf.predict_proba(df[["elo_diff"]])
    order = [list(clf.classes_).index(c) for c in ev.CLASSES]
    return p[:, order]


def log_experiment(rows, split):
    log = pd.DataFrame(rows)
    log.insert(0, "timestamp", dt.datetime.now().isoformat(timespec="seconds"))
    log.insert(1, "split", split)
    log["elo_k"], log["elo_home_adv"], log["seed"] = config.ELO_K, config.ELO_HOME_ADV, config.SEED
    header = not config.EXPERIMENT_LOG.exists()
    log.to_csv(config.EXPERIMENT_LOG, mode="a", header=header, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--final", action="store_true", help="evaluate on the TEST season (do this once)")
    ap.add_argument("--audit", action="store_true", help="print team names for a duplicate check")
    args = ap.parse_args()

    if args.download:
        data.download_raw()
    matches = data.load_matches()
    if args.audit:
        audit(matches)
        
    # Feature Engineering
    import xg_scraper
    import features
    xg_df = xg_scraper.load_xg_data()
    matches = features.calculate_xg_form(matches, xg_df)
    matches = features.calculate_situational_factors(matches)
    matches = elo.elo_features(
        matches,
        elo_k=config.LEAGUES[config.DEFAULT_LEAGUE].get("elo_k", config.ELO_K),
        season_reg=config.LEAGUES[config.DEFAULT_LEAGUE].get("elo_season_regression", config.ELO_SEASON_REGRESSION)
    )

    eval_season = config.TEST_SEASON if args.final else config.VALID_SEASON
    train = matches[matches["season"] < eval_season]
    if args.final:
        print("FINAL hold-out run. Do not tune anything after seeing this.")
    test = matches[matches["season"] == eval_season]
    if test.empty:
        raise SystemExit(f"No matches for season {eval_season}. Check config.SEASONS.")
    print(f"train: {len(train)} matches (before {eval_season}) | evaluate: {len(test)} matches ({eval_season})")

    y = test["FTR"].values
    market = test[["mkt_H", "mkt_D", "mkt_A"]].values
    clf = fit_elo_model(train)
    
    # Fit Dixon-Coles
    import dixon_coles
    dc_xi = config.LEAGUES.get(config.DEFAULT_LEAGUE, {}).get("dc_xi", 0.0065)
    dc_params = dixon_coles.fit_dixon_coles(train, current_date=test["date"].min(), xi=dc_xi)
    
    # Predict Dixon-Coles
    dc_preds = []
    for _, row in test.iterrows():
        p_home, p_draw, p_away = dixon_coles.predict_match(row["HomeTeam"], row["AwayTeam"], dc_params)
        dc_preds.append([p_home, p_draw, p_away])
    dc_preds = np.array(dc_preds)
    
    models = {
        "league_frequencies": freq_baseline(train, len(test)), 
        "elo": predict_elo(clf, test),
        "dixon_coles": dc_preds
    }

    rows = [ev.report(name, y, p, market) for name, p in models.items()]
    if not np.isnan(market).all():
        rows.append({"model": "bookmaker_market", "n": int((~np.isnan(market).any(axis=1)).sum()),
                     "log_loss": ev.log_loss(y[~np.isnan(market).any(axis=1)], market[~np.isnan(market).any(axis=1)])})
    summary = pd.DataFrame(rows).round(4)
    print("\n" + summary.to_string(index=False))

    print("\nCalibration (Elo): predicted probability bucket vs how often it happened")
    print(ev.calibration_table(y, models["elo"]).to_string())
    print("\nTiers (Elo)")
    print(ev.tier_table(y, models["elo"]).to_string())

    log_experiment(rows, "final" if args.final else "valid")
    print(f"\nLogged to {config.EXPERIMENT_LOG.name}")


if __name__ == "__main__":
    main()
