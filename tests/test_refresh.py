"""A failed league or odds request must never publish a misleading snapshot."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from refresh_predictions import validate_refresh


class RefreshTests(unittest.TestCase):
    def reports(self):
        return {'leagues': [{'league': league, 'status': 'ready', 'odds_status': 'available'}
                            for league in config.LEAGUES]}

    def test_failed_odds_and_missing_league_block_publication(self):
        status = self.reports()
        status['leagues'][0]['odds_status'] = 'unavailable'
        with self.assertRaises(RuntimeError):
            validate_refresh(status)
        status = self.reports()
        status['leagues'].pop()
        with self.assertRaises(RuntimeError):
            validate_refresh(status)

    def test_empty_schedule_and_no_markets_are_valid(self):
        status = self.reports()
        status['leagues'][0].update(status='no_fixtures', odds_status='not_requested')
        status['leagues'][1]['odds_status'] = 'no_markets'
        validate_refresh(status)

    def test_model_failure_blocks_publication(self):
        status = self.reports()
        status['leagues'][0]['status'] = 'error'
        with self.assertRaises(RuntimeError):
            validate_refresh(status)
