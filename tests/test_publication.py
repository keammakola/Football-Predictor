"""Evidence corruption and exact policy boundaries must fail predictably."""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model_spec import FEATURE_COLUMNS, favourable_price, prediction_tier
from publish_snapshot import PUBLIC, verify


class SelectionPolicyTests(unittest.TestCase):
    def test_inclusive_confidence_and_lead_boundaries(self):
        self.assertEqual(prediction_tier([.60, .35, .05]), 'Strong')
        self.assertNotEqual(prediction_tier([.5999, .35, .0501]), 'Strong')
        self.assertNotEqual(prediction_tier([.60, .3501, .0499]), 'Strong')

    def test_price_must_exceed_break_even(self):
        self.assertFalse(favourable_price(.60, 1 / .60))
        self.assertTrue(favourable_price(.60, 1.67))
        self.assertFalse(favourable_price(.60, float('nan')))
        self.assertFalse(favourable_price(0, 2))

    def test_no_unobserved_injury_or_travel_inputs(self):
        self.assertEqual(len(FEATURE_COLUMNS), 11)
        self.assertFalse(any('travel' in key or 'injury' in key for key in FEATURE_COLUMNS))

    def test_invalid_probabilities_are_rejected(self):
        for probabilities in ([.8, .5, .1], [float('nan'), .5, .5], [1.1, -.1, 0]):
            with self.assertRaises(ValueError):
                prediction_tier(probabilities)


class PublishedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        for name in ('bets.json', 'predictions-all.json', 'stats.json', 'provenance.json', 'run-manifest.json'):
            shutil.copy(PUBLIC / name, self.directory / name)

    def change(self, filename, mutation):
        path = self.directory / filename
        value = json.loads(path.read_text())
        mutation(value)
        path.write_text(json.dumps(value))

    def test_committed_snapshot_verifies(self):
        verify(self.directory)

    def test_headline_count_corruption_is_rejected(self):
        self.change('stats.json', lambda stats: stats.update(strong_correct=0))
        with self.assertRaisesRegex(ValueError, 'Strong prediction'):
            verify(self.directory)

    def test_probability_corruption_is_rejected(self):
        self.change('predictions-all.json', lambda rows: rows[0].update(p_home=.99))
        with self.assertRaises(ValueError):
            verify(self.directory)

    def test_ledger_corruption_is_rejected(self):
        self.change('bets.json', lambda rows: rows[0].update(pnl=100))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            verify(self.directory)

    def test_invalid_staged_bundle_leaves_public_files_untouched(self):
        import export_bets
        import export_json
        import publish_snapshot
        before = {path.name: path.read_bytes() for path in self.directory.iterdir()}

        def invalid_export(output):
            for name in ('bets.json', 'predictions-all.json', 'stats.json', 'provenance.json'):
                shutil.copy(PUBLIC / name, output / name)
            path = output / 'stats.json'
            stats = json.loads(path.read_text())
            stats['strong_correct'] = 0
            path.write_text(json.dumps(stats))

        with patch.object(export_bets, 'main', side_effect=invalid_export), patch.object(export_json, 'main'), patch.object(publish_snapshot, 'PUBLIC', self.directory), patch.object(sys, 'argv', ['publish_snapshot.py']):
            with self.assertRaisesRegex(ValueError, 'Strong prediction'):
                publish_snapshot.main()
        after = {path.name: path.read_bytes() for path in self.directory.iterdir()}
        self.assertEqual(before, after)

    def test_manifest_count_corruption_is_rejected(self):
        self.change('run-manifest.json', lambda manifest: manifest['counts'].update(selected_bets=0))
        with self.assertRaisesRegex(ValueError, 'Run-manifest'):
            verify(self.directory)


class ExportBoundaryTests(unittest.TestCase):
    def test_exact_sixty_percent_selection_exports_with_matching_counts(self):
        import export_bets
        import export_json
        import publish_snapshot
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / 'data/raw'
            raw.mkdir(parents=True)
            source = {'Date': '01/08/2023', 'HomeTeam': 'Arsenal', 'AwayTeam': 'Chelsea',
                      'FTR': 'H', 'FTHG': 1, 'FTAG': 0, 'B365H': 2, 'B365D': 3, 'B365A': 6}
            prediction = {'date': '2023-08-01', 'league': 'EPL', 'home': 'Arsenal', 'away': 'Chelsea',
                          'p_home': .60, 'p_draw': .35, 'p_away': .05, 'result': 'H',
                          'odds_home': 2, 'odds_draw': 3, 'odds_away': 6}
            bet = {'league': 'EPL', 'season': '2324', 'match': 'Arsenal vs Chelsea',
                   'tier': 'Strong', 'pick': 'H', 'prob': .60, 'odds_taken': 2, 'won': 1, 'pnl': 1}
            for path, row in ((raw / 'EPL_2324.csv', source), (root / 'matches.csv', prediction),
                              (root / 'bets.csv', bet)):
                with path.open('w') as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(row))
                    writer.writeheader()
                    writer.writerow(row)
            output = root / 'output'
            with patch.object(export_bets, 'ROOT', root), patch.object(export_json, 'ROOT', root), patch.object(publish_snapshot, 'ROOT', root):
                export_bets.main(output)
                export_json.main(output)
                bets, predictions, stats, _ = publish_snapshot.validate_evidence(output)
            self.assertEqual(len(bets), 1)
            self.assertEqual(stats['strong_predictions'], 1)
            self.assertEqual(stats['strong_correct'], 1)
            self.assertEqual(predictions[0]['p_home'], .60)
            self.assertEqual(predictions[0]['model_version'], '2.0')


if __name__ == '__main__':
    unittest.main()
