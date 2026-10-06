"""Generate league-specific upcoming predictions from real schedules and observed xG."""
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder

import config
from model_spec import FEATURE_COLUMNS, prediction_tier, favourable_price
from data import load_matches
from elo import elo_features
from xg_scraper import load_xg_data
from features import calculate_xg_form, calculate_situational_factors
from api_fixtures import fetch_upcoming_fixtures
from live_odds import get_live_odds
from dixon_coles import fit_dixon_coles, predict_match

FEATURES = FEATURE_COLUMNS


def predict_league(league, fixtures, odds, now):
    history = load_matches(league)
    cutoff = now.tz_localize(None)
    history = history[history['date'] < cutoff.normalize()].copy()
    if history.empty:
        raise ValueError('No completed history for training')
    future = fixtures.rename(columns={'home_team': 'HomeTeam', 'away_team': 'AwayTeam'}).copy()
    future['_fixture_kickoff'] = future['date']
    future['_upcoming'] = True
    history['_upcoming'] = False
    combined = pd.concat([history, future], ignore_index=True).sort_values('date').reset_index(drop=True)
    settings = config.LEAGUES[league]
    combined = elo_features(combined, elo_k=settings.get('elo_k', config.ELO_K), season_reg=settings.get('elo_season_regression', config.ELO_SEASON_REGRESSION))
    observed = load_xg_data(league)
    observed = observed[observed['date'] < cutoff.normalize()]
    combined = calculate_situational_factors(calculate_xg_form(combined, observed))
    train = combined[~combined['_upcoming']]
    future = combined[combined['_upcoming']]
    encoder = LabelEncoder().fit(['H', 'D', 'A'])
    model = xgb.XGBClassifier(objective='multi:softprob', eval_metric='mlogloss', learning_rate=.05, max_depth=4, n_estimators=100, subsample=.8, colsample_bytree=.8, random_state=config.SEED, n_jobs=1)
    model.fit(train[FEATURES].astype(float), encoder.transform(train['FTR']))
    predictions = model.predict_proba(future[FEATURES].astype(float))
    dc = fit_dixon_coles(history, current_date=cutoff.normalize(), xi=settings.get('dc_xi', .0065))
    output = []
    for index, (_, row) in enumerate(future.iterrows()):
        goals = predict_match(row['HomeTeam'], row['AwayTeam'], dc)
        probabilities = {label: .5 * predictions[index, list(encoder.classes_).index(label)] + .5 * goals[f'p_{name}'] for label, name in [('H', 'home'), ('D', 'draw'), ('A', 'away')]}
        total = sum(probabilities.values())
        probabilities = {key: value / total for key, value in probabilities.items()}
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        pick, probability = ranked[0]
        available = odds[(odds.home_team == row.HomeTeam) & (odds.away_team == row.AwayTeam)] if not odds.empty else odds
        if not available.empty:
            available = available.copy()
            times = pd.to_datetime(available['kickoff_utc'], utc=True).dt.tz_localize(None)
            available = available[(times - row['_fixture_kickoff']).abs() < pd.Timedelta(hours=36)]
        market = available.iloc[0] if len(available) == 1 else None
        price = float(market[f'odds_{pick}']) if market is not None else None
        if price is not None and (not np.isfinite(price) or price <= 1):
            price = None
        edge = probability - 1 / price if price else None
        strong = prediction_tier(probabilities.values()) == "Strong"
        kickoff_utc = market['kickoff_utc'] if market is not None else row['_fixture_kickoff'].isoformat()+'Z'
        output.append({'date': kickoff_utc[:10], 'kickoff_utc': kickoff_utc, 'league': league, 'match': f'{row.HomeTeam} vs {row.AwayTeam}', 'pick': {'H': 'Home', 'D': 'Draw', 'A': 'Away'}[pick], 'prob': round(float(probability), 3), 'odds_advantage': round(float(edge), 3) if edge is not None else None, 'odds': price, 'qualifies': bool(strong and price is not None and favourable_price(probability, price)), 'status': 'awaiting_odds' if edge is None else 'qualifying' if strong and edge > 0 else 'outside_criteria', 'bookmaker': market['bookmaker'] if market is not None else None, 'fixture_source': row['source_url'], 'trained_through': history['date'].max().strftime('%Y-%m-%d')})
    return output


def main():
    now = pd.Timestamp(datetime.now(timezone.utc))
    reports, rows = [], []
    for league in config.LEAGUES:
        report = {'league': league, 'fixtures': 0, 'predictions': 0, 'odds_status': 'not_requested'}
        try:
            fixtures = fetch_upcoming_fixtures(league, now=now)
            fixtures = fixtures[fixtures['date'] <= now.tz_localize(None) + pd.Timedelta(days=30)]
            report['fixtures'] = len(fixtures)
            if fixtures.empty:
                report['status'] = 'no_fixtures'
            else:
                try:
                    odds = get_live_odds(league)
                    report['odds_status'] = 'available' if not odds.empty else 'no_markets'
                except (RuntimeError, requests.RequestException) as error:
                    odds = pd.DataFrame()
                    report['odds_status'] = 'unavailable'
                    report['odds_error'] = str(error)
                predictions = predict_league(league, fixtures, odds, now)
                rows.extend(predictions)
                report.update(status='ready', predictions=len(predictions))
        except Exception as error:
            report.update(status='error', error=f'{type(error).__name__}: {error}' if not isinstance(error, requests.RequestException) else 'Fixture feed could not be reached')
        reports.append(report)
        print(f"{league}: {report['status']}, {report['fixtures']} fixtures, {report['predictions']} predictions, odds {report['odds_status']}", flush=True)
    rows.sort(key=lambda row: row['kickoff_utc'])
    output = config.ROOT / 'frontend/public/data'
    (output/'upcoming.json').write_text(json.dumps(rows, allow_nan=False))
    (output/'upcoming-status.json').write_text(json.dumps({'generated_at_utc': now.isoformat(), 'window_days': 30, 'predictions': len(rows), 'qualifying_bets': sum(row['qualifies'] for row in rows), 'leagues': reports}, indent=2))
    print(f'Exported {len(rows)} real fixture predictions; {sum(row["qualifies"] for row in rows)} qualify.', flush=True)


if __name__ == '__main__':
    main()
