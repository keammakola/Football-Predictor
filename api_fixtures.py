"""Read real upcoming fixture schedules from Fixture Download's UTC JSON feed."""
import datetime
import pandas as pd
import requests
from team_names import canon
import config


def fetch_upcoming_fixtures(league_name=None, now=None):
    league_name = league_name or config.DEFAULT_LEAGUE
    now = pd.Timestamp(now or datetime.datetime.now(datetime.timezone.utc))
    now = now.tz_localize('UTC') if now.tzinfo is None else now.tz_convert('UTC')
    year = now.year if now.month >= 7 else now.year - 1
    code = config.LEAGUES[league_name]['fixture_code']
    url = f'https://fixturedownload.com/feed/json/{code}-{year}'
    response = requests.get(url, headers={'User-Agent': 'FootballExperiment/1.0'}, timeout=30)
    if not response.ok:
        raise RuntimeError(f'Fixture feed returned HTTP {response.status_code} for {league_name}')
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError('Fixture feed did not return a match list')
    rows = []
    for match in payload:
        if match.get('HomeTeamScore') is not None or match.get('AwayTeamScore') is not None:
            continue
        kickoff = pd.to_datetime(match['DateUtc'], utc=True, errors='raise')
        if kickoff <= now:
            continue
        rows.append({'season': f'{year % 100:02d}{(year+1) % 100:02d}', 'date': kickoff.tz_localize(None),
                     'home_team': canon(match['HomeTeam']), 'away_team': canon(match['AwayTeam']),
                     'FTHG': float('nan'), 'FTAG': float('nan'), 'FTR': None, 'source_url': url})
    return pd.DataFrame(rows, columns=['season', 'date', 'home_team', 'away_team', 'FTHG', 'FTAG', 'FTR', 'source_url'])
