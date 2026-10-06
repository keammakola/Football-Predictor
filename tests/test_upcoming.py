"""Verify actual fixture filtering, provider aliases, and error handling."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from api_fixtures import fetch_upcoming_fixtures
from live_odds import get_live_odds
from team_names import canon


class UpcomingTests(unittest.TestCase):
    def test_future_only_source_times_and_season(self):
        future = {'DateUtc': '2026-10-10 14:00:00Z', 'HomeTeam': 'Manchester City', 'AwayTeam': 'Spurs', 'HomeTeamScore': None, 'AwayTeamScore': None}
        completed = {**future, 'HomeTeamScore': 1, 'AwayTeamScore': 0}
        past = {**future, 'DateUtc': '2026-10-01 14:00:00Z'}
        response = Mock(ok=True)
        response.json.return_value = [future, completed, past]
        with patch('api_fixtures.requests.get', return_value=response):
            rows = fetch_upcoming_fixtures('EPL', pd.Timestamp('2026-10-06T00:00:00Z'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.iloc[0]['date'], pd.Timestamp('2026-10-10T14:00:00'))
        self.assertEqual(rows.iloc[0]['season'], '2627')
        self.assertEqual(rows.iloc[0]['home_team'], 'Man City')
        self.assertEqual(rows.iloc[0]['away_team'], 'Tottenham')

    def test_empty_feed_and_failed_feed_are_distinct(self):
        response = Mock(ok=True)
        response.json.return_value = []
        with patch('api_fixtures.requests.get', return_value=response):
            self.assertTrue(fetch_upcoming_fixtures('EPL').empty)
        response.ok = False
        response.status_code = 503
        with patch('api_fixtures.requests.get', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'HTTP 503'):
                fetch_upcoming_fixtures('EPL')

    def test_odds_errors_do_not_include_secret_urls(self):
        response = Mock(ok=False, status_code=401)
        with patch('live_odds.requests.get', return_value=response):
            with self.assertRaisesRegex(RuntimeError, '^Odds feed returned HTTP 401$'):
                get_live_odds('EPL')

    def test_provider_names_map_to_training_teams(self):
        for provider, canonical in [('FC Bayern München', 'Bayern Munich'), ('Atlético de Madrid', 'Ath Madrid'), ('Paris Saint-Germain', 'Paris SG'), ('Internazionale', 'Inter')]:
            self.assertEqual(canon(provider), canonical)


if __name__ == '__main__':
    unittest.main()
