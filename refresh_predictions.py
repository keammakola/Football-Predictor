"""Refresh live inputs and fail closed before CI publishes upcoming snapshots."""
import json
import pandas as pd

import config
from data import download_raw, load_matches
from generate_upcoming import main as generate
from xg_scraper import load_xg_data, scrape_understat_season, align_source_dates, save_cache


def validate_refresh(status):
    reports = status['leagues']
    if {row['league'] for row in reports} != set(config.LEAGUES):
        raise RuntimeError('Refresh did not cover every configured league')
    failed = [row['league'] for row in reports if row['status'] not in ('ready', 'no_fixtures')
              or (row['status'] == 'ready' and row['odds_status'] == 'unavailable')]
    if failed:
        raise RuntimeError('Refresh failed; do not publish: ' + ', '.join(failed))


def main():
    if not config.ODDS_API_KEY:
        raise RuntimeError('Set the ODDS_API_KEY GitHub Actions secret before refreshing')
    now = pd.Timestamp.now(tz='UTC')
    year = now.year if now.month >= 7 else now.year - 1
    season = f'{year % 100:02d}{(year + 1) % 100:02d}'
    # Current inputs are refreshed in the runner only. Historical evidence exports
    # and their committed source files stay tied to their original provenance.
    for league in config.LEAGUES:
        download_raw(seasons=[season], league_name=league, refresh=True)
        if not load_matches(league).query('season == @season').empty:
            cached = load_xg_data(league)
            current = scrape_understat_season(year, league)
            if current.empty:
                raise RuntimeError(f'{league}: completed results exist but current xG is empty')
            combined = pd.concat([cached[cached['season'].astype(int) != year], current], ignore_index=True)
            combined = align_source_dates(combined, league)
            save_cache(combined, league, sorted(combined['season'].astype(int).unique().tolist()))
    generate()
    status = json.loads((config.ROOT / 'frontend/public/data/upcoming-status.json').read_text())
    validate_refresh(status)


if __name__ == '__main__':
    main()
