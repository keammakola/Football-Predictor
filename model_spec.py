"""One feature schema and selection policy for new research runs.

The committed historical snapshot predates this schema; see its run manifest.
"""
import math

MODEL_VERSION = '2.0'
FEATURE_COLUMNS = [
    'elo_diff',
    'home_xg_roll', 'home_xga_roll', 'home_xg_ema', 'home_xga_ema',
    'away_xg_roll', 'away_xga_roll', 'away_xg_ema', 'away_xga_ema',
    'home_rest_days', 'away_rest_days',
]
STRONG_MIN_PROB = .60
STRONG_MIN_LEAD = .25


def prediction_tier(probabilities):
    values = list(probabilities)
    if len(values) != 3 or not all(math.isfinite(p) and 0 <= p <= 1 for p in values):
        raise ValueError('Expected three finite probabilities between zero and one')
    if not math.isclose(sum(values), 1, abs_tol=.002):
        raise ValueError('Probabilities must sum to one (within export rounding tolerance)')
    ranked = sorted(values, reverse=True)
    lead = ranked[0] - ranked[1]
    # A small tolerance avoids binary float errors at the stated inclusive boundary.
    if ranked[0] + 1e-12 >= STRONG_MIN_PROB and lead + 1e-12 >= STRONG_MIN_LEAD:
        return 'Strong'
    if ranked[0] + 1e-12 >= .50 and lead + 1e-12 >= .15:
        return 'Lean'
    return 'None'


def favourable_price(probability, odds):
    return math.isfinite(odds) and odds > 1 and odds > 1 / probability if probability > 0 else False
