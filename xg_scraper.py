"""Collect observed match xG from Understat. Never substitute synthetic data."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

from team_names import canon
import config

COLUMNS = ['date', 'HomeTeam', 'AwayTeam', 'xG_Home', 'xG_Away', 'understat_id', 'season', 'source_url']


def get_xg_file(league_name):
    return config.RAW_DIR / f'understat_xg_{league_name}.csv'


def validate_xg(df):
    if not set(COLUMNS).issubset(df.columns):
        raise ValueError('Legacy or unverified xG cache. Refresh from Understat.')
    df = df.copy()
    if df[['HomeTeam', 'AwayTeam']].isna().any().any():
        raise ValueError('Missing team names in xG data')
    df['HomeTeam'] = df['HomeTeam'].map(canon)
    df['AwayTeam'] = df['AwayTeam'].map(canon)
    df['date'] = pd.to_datetime(df['date'], errors='raise').dt.normalize()
    if df['date'].isna().any():
        raise ValueError('Missing observed match date')
    if df[['HomeTeam', 'AwayTeam']].isna().any().any() or df['HomeTeam'].str.startswith('Team_').any() or df['AwayTeam'].str.startswith('Team_').any():
        raise ValueError('Synthetic or missing team names in xG data')
    for column in ['xG_Home', 'xG_Away']:
        df[column] = pd.to_numeric(df[column], errors='raise')
        if not df[column].map(lambda n: math.isfinite(n) and n >= 0).all():
            raise ValueError('Invalid observed xG value')
    if df['understat_id'].isna().any() or not df['source_url'].str.startswith('https://understat.com/getLeagueData/').all():
        raise ValueError('Missing Understat provenance')
    if df.duplicated(['date', 'HomeTeam', 'AwayTeam']).any() or df['understat_id'].duplicated().any():
        raise ValueError('Duplicate Understat matches')
    return df.sort_values(['date', 'HomeTeam']).reset_index(drop=True)


def parse_matches(payload, year, league_name):
    if not isinstance(payload, dict) or not isinstance(payload.get('dates'), list):
        raise ValueError('Understat response has no match list')
    url = f"https://understat.com/getLeagueData/{config.LEAGUES[league_name]['understat_code']}/{year}"
    rows = []
    for match in payload['dates']:
        if match.get('isResult') is not True:
            continue
        # Missing or malformed xG is an error, never an invented observation.
        rows.append({'date': match['datetime'][:10], 'HomeTeam': canon(match['h']['title']),
                     'AwayTeam': canon(match['a']['title']), 'xG_Home': float(match['xG']['h']),
                     'xG_Away': float(match['xG']['a']), 'understat_id': str(match['id']),
                     'season': int(year), 'source_url': url})
    return validate_xg(pd.DataFrame(rows, columns=COLUMNS))


def scrape_understat_season(year, league_name):
    url = f"https://understat.com/getLeagueData/{config.LEAGUES[league_name]['understat_code']}/{int(year)}"
    response = requests.get(url, headers={'User-Agent': 'FootballExperiment/1.0', 'X-Requested-With': 'XMLHttpRequest', 'Referer': f"https://understat.com/league/{config.LEAGUES[league_name]['understat_code']}/{int(year)}"}, timeout=45)
    response.raise_for_status()
    return parse_matches(response.json(), int(year), league_name)


def default_seasons(league_name):
    # Request seasons with completed source results, not future fixture-only files.
    years = []
    for path in sorted(config.RAW_DIR.glob(f'{league_name}_*.csv')):
        frame = pd.read_csv(path, encoding='latin-1')
        if 'FTR' in frame and frame['FTR'].isin(['H', 'D', 'A']).any():
            years.append(2000 + int(path.stem.rsplit('_', 1)[1][:2]))
    if not years:
        raise ValueError(f'No historical result seasons for {league_name}')
    return years


def align_source_dates(df, league_name):
    """Use the results-source date for a unique home/away fixture in its season."""
    from data import load_matches
    results = load_matches(league_name).copy()
    results['start_year'] = results['season'].map(lambda code: 2000 + int(code[:2]))
    fixtures = results.groupby(['start_year', 'HomeTeam', 'AwayTeam'])['date'].agg(list).to_dict()
    aligned = df.copy()
    if 'understat_date' not in aligned:
        aligned['understat_date'] = aligned['date'].dt.strftime('%Y-%m-%d')
    aligned['results_date_verified'] = False
    for index, row in aligned.iterrows():
        candidates = fixtures.get((int(row['season']), row['HomeTeam'], row['AwayTeam']), [])
        if len(candidates) == 1:
            aligned.at[index, 'date'] = candidates[0]
            aligned.at[index, 'results_date_verified'] = True
        elif len(candidates) > 1:
            raise ValueError('Ambiguous results fixture; cannot align xG date')
    return validate_xg(aligned)


def save_cache(df, league_name, years):
    output = get_xg_file(league_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    csv_text = df.to_csv(index=False)
    temporary = output.with_suffix('.csv.tmp')
    temporary.write_text(csv_text)
    temporary.replace(output)
    output.with_suffix('.meta.json').write_text(json.dumps({'source': 'Understat', 'fetched_at_utc': datetime.now(timezone.utc).isoformat(), 'seasons': years, 'matches': len(df), 'sha256': hashlib.sha256(csv_text.encode()).hexdigest(), 'urls': sorted(df['source_url'].unique()), 'date_alignment': 'Unique season/home/away fixture uses results-source date; original retained in understat_date'}, indent=2))
    from data import load_matches
    results = load_matches(league_name)
    joined = results.merge(df[['date', 'HomeTeam', 'AwayTeam', 'understat_id']], on=['date', 'HomeTeam', 'AwayTeam'], how='left', validate='one_to_one')
    report_path = config.RAW_DIR.parent / 'xg_coverage.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else []
    report = [row for row in report if row['league'] != league_name]
    unmatched = joined[joined['understat_id'].isna()][['date', 'HomeTeam', 'AwayTeam']].copy()
    unmatched['date'] = unmatched['date'].dt.strftime('%Y-%m-%d')
    report.append({'league': league_name, 'results_matches': len(results), 'matched_xg': int(joined['understat_id'].notna().sum()), 'unmatched': unmatched.to_dict('records')})
    report_path.write_text(json.dumps(sorted(report, key=lambda row: row['league']), indent=2))



def get_xg_data(league_name=None, seasons=None):
    league_name = league_name or config.DEFAULT_LEAGUE
    years = sorted(set(map(int, seasons if seasons is not None else default_seasons(league_name))))
    if not years:
        raise ValueError('No seasons requested')
    with ThreadPoolExecutor(max_workers=3) as executor:
        frames = list(executor.map(lambda year: scrape_understat_season(year, league_name), years))
    empty = [year for year, frame in zip(years, frames) if frame.empty]
    if empty:
        raise ValueError(f'No completed Understat xG matches for seasons {empty}; cache left unchanged')
    df = validate_xg(pd.concat(frames, ignore_index=True))
    df = align_source_dates(df, league_name)
    save_cache(df, league_name, years)
    print(f'{league_name}: collected {len(df):,} observed xG matches ({years[0]}–{years[-1]}).', flush=True)
    return df


def load_xg_data(league_name=None):
    league_name = league_name or config.DEFAULT_LEAGUE
    output = get_xg_file(league_name)
    if output.exists():
        metadata = output.with_suffix('.meta.json')
        if not metadata.exists():
            raise ValueError('Unverified xG cache: refresh from Understat')
        manifest = json.loads(metadata.read_text())
        if manifest.get('source') != 'Understat' or manifest.get('sha256') != hashlib.sha256(output.read_bytes()).hexdigest():
            raise ValueError('xG cache does not match its source manifest')
        return validate_xg(pd.read_csv(output, dtype={'understat_id': str}))
    return get_xg_data(league_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--league', choices=['all', *config.LEAGUES], default='all')
    parser.add_argument('--seasons', nargs='+', type=int)
    args = parser.parse_args()
    for league in config.LEAGUES if args.league == 'all' else [args.league]:
        get_xg_data(league, args.seasons)
