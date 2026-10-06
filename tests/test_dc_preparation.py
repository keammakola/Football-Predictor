"""Check the cached optimiser inputs against a scalar likelihood calculation."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from dixon_coles import _prepare_likelihood, dc_log_likelihood


class LikelihoodTests(unittest.TestCase):
    def test_low_score_corrections_and_time_decay(self):
        frame = pd.DataFrame({'HomeTeam': ['A', 'B', 'A', 'B', 'A'], 'AwayTeam': ['B', 'A', 'B', 'A', 'B'], 'FTHG': [0, 0, 1, 1, 3], 'FTAG': [0, 1, 0, 1, 2], 'date': pd.date_range('2023-01-01', periods=5)})
        params = np.array([1.2, .8, .9, 1.1, 1.3, .05])
        current = pd.Timestamp('2023-01-10')
        expected = 0.
        for row in frame.itertuples():
            h, a = ['A', 'B'].index(row.HomeTeam), ['A', 'B'].index(row.AwayTeam)
            lam, mu = params[h] * params[2 + a] * params[4], params[a] * params[2 + h]
            x, y = row.FTHG, row.FTAG
            tau = {(0, 0): 1-lam*mu*params[5], (0, 1): 1+lam*params[5], (1, 0): 1+mu*params[5], (1, 1): 1-params[5]}.get((x, y), 1)
            logp = math.log(tau) + x*math.log(lam)-lam-math.lgamma(x+1) + y*math.log(mu)-mu-math.lgamma(y+1)
            expected -= math.exp(-.0065*(current-row.date).days)*logp
        prepared = _prepare_likelihood(frame, ['A', 'B'], .0065, current)
        self.assertAlmostEqual(expected, dc_log_likelihood(params, frame, ['A', 'B'], .0065, current, prepared), places=10)
        self.assertAlmostEqual(expected, dc_log_likelihood(params, frame, ['A', 'B'], .0065, current), places=10)


if __name__ == '__main__':
    unittest.main()
