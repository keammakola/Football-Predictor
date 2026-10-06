"""Collector validation and chronological, team-isolated xG features."""
import unittest
from unittest.mock import patch
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import requests
from features import calculate_xg_form
from xg_scraper import parse_matches, scrape_understat_season, validate_xg, get_xg_data, load_xg_data, align_source_dates


def match(id_, date, home, away, h, a, completed=True):
    return {'id': str(id_), 'datetime': date + ' 15:00:00', 'h': {'title': home}, 'a': {'title': away}, 'xG': {'h': str(h), 'a': str(a)}, 'isResult': completed}


class XgTests(unittest.TestCase):
    def test_observed_only_and_aliases(self):
        frame = parse_matches({'dates': [match(1, '2023-08-11', 'Manchester City', 'Manchester United', 2.4, .3), match(2, '2023-08-12', 'Chelsea', 'Arsenal', 0, 0, False)]}, 2023, 'EPL')
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]['HomeTeam'], 'Man City')
        self.assertEqual(frame.iloc[0]['AwayTeam'], 'Man United')
        self.assertEqual(frame.iloc[0]['xG_Home'], 2.4)

    def test_rejects_placeholders_and_malformed_data(self):
        with self.assertRaises(ValueError):
            validate_xg(pd.DataFrame({'date': ['2023-01-01']}))
        for h in ('nan', '-1'):
            with self.assertRaises(ValueError):
                parse_matches({'dates': [match(1, '2023-01-01', 'Arsenal', 'Chelsea', h, 1)]}, 2023, 'EPL')
        with self.assertRaises(ValueError):
            parse_matches({'dates': [match(1, '2023-01-01', 'Team_0', 'Team_1', 1.5, 1)]}, 2023, 'EPL')
        with self.assertRaises(ValueError):
            parse_matches({'error': 'unavailable'}, 2023, 'EPL')

    def test_network_error_does_not_generate_data(self):
        with patch('xg_scraper.requests.get', side_effect=requests.Timeout):
            with self.assertRaises(requests.Timeout):
                scrape_understat_season(2023, 'EPL')

    def test_failed_refresh_preserves_existing_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'understat_xg_EPL.csv'
            cache.write_text('existing cache')
            with patch('xg_scraper.config.RAW_DIR', Path(directory)), patch('xg_scraper.scrape_understat_season', side_effect=requests.Timeout):
                with self.assertRaises(requests.Timeout):
                    get_xg_data('EPL', [2023])
            self.assertEqual(cache.read_text(), 'existing cache')

    def test_legacy_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'understat_xg_EPL.csv').write_text('date,HomeTeam,AwayTeam,xG_Home,xG_Away\n2023-01-01,Team_0,Team_1,1.5,1.0\n')
            with patch('xg_scraper.config.RAW_DIR', Path(directory)):
                with self.assertRaises(ValueError):
                    load_xg_data('EPL')

    def test_postponed_match_date_is_aligned_with_original_preserved(self):
        observed = parse_matches({'dates': [match(1, '2024-04-14', 'Udinese', 'Roma', 1, 2)]}, 2023, 'SerieA')
        results = pd.DataFrame({'date': pd.to_datetime(['2024-04-25']), 'HomeTeam': ['Udinese'], 'AwayTeam': ['Roma'], 'season': ['2324']})
        with patch('data.load_matches', return_value=results):
            aligned = align_source_dates(observed, 'SerieA')
        self.assertEqual(aligned.iloc[0]['date'], pd.Timestamp('2024-04-25'))
        self.assertEqual(aligned.iloc[0]['understat_date'], '2024-04-14')
        self.assertTrue(aligned.iloc[0]['results_date_verified'])

    def test_features_exclude_current_future_and_other_teams(self):
        observed = parse_matches({'dates': [match(1, '2023-01-01', 'Arsenal', 'Chelsea', 2, 1), match(2, '2023-01-02', 'Liverpool', 'Everton', 100, 200), match(3, '2023-01-08', 'Arsenal', 'Chelsea', 4, 3)]}, 2023, 'EPL')
        targets = pd.DataFrame({'date': pd.to_datetime(['2023-01-01', '2023-01-08', '2023-01-15']), 'HomeTeam': ['Arsenal'] * 3, 'AwayTeam': ['Chelsea'] * 3})
        form = calculate_xg_form(targets, observed)
        self.assertTrue(pd.isna(form.iloc[0]['home_xg_roll']))
        self.assertEqual(form.iloc[1]['home_xg_roll'], 2)
        self.assertEqual(form.iloc[1]['away_xg_roll'], 1)
        self.assertEqual(form.iloc[2]['home_xg_roll'], 3)
        altered = observed.copy()
        altered.loc[altered['date'] == pd.Timestamp('2023-01-08'), 'xG_Home'] = 900
        new = calculate_xg_form(targets, altered)
        self.assertEqual(new.iloc[1]['home_xg_ema'], form.iloc[1]['home_xg_ema'])
        self.assertNotEqual(new.iloc[2]['home_xg_roll'], form.iloc[2]['home_xg_roll'])


if __name__ == '__main__':
    unittest.main()
