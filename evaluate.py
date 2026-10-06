"""Metrics that matter: log loss, Brier, calibration, tier hit rates, market comparison."""
import numpy as np
import pandas as pd

import config

CLASSES = ["H", "D", "A"]


def _onehot(y):
    return np.array([[c == k for k in CLASSES] for c in y], dtype=float)


def log_loss(y, probs, eps=1e-12):
    p = np.clip(np.asarray(probs), eps, 1)
    return float(-np.mean(np.log((p * _onehot(y)).sum(axis=1))))


def brier(y, probs):
    return float(np.mean(((np.asarray(probs) - _onehot(y)) ** 2).sum(axis=1)))


def accuracy(y, probs):
    pred = np.array(CLASSES)[np.asarray(probs).argmax(axis=1)]
    return float(np.mean(pred == np.asarray(y)))


def calibration_table(y, probs, bins=(0, .2, .3, .4, .5, .6, .7, .8, 1.0)):
    """For every (match, outcome) pair: predicted prob bucket vs how often it happened."""
    p = np.asarray(probs).ravel()
    hit = _onehot(y).ravel()
    df = pd.DataFrame({"p": p, "hit": hit})
    df["bucket"] = pd.cut(df["p"], bins=list(bins), include_lowest=True)
    t = df.groupby("bucket", observed=True).agg(n=("hit", "size"), avg_pred=("p", "mean"), actual=("hit", "mean"))
    return t.round(3)


def tier_table(y, probs):
    """Label each match Strong / Lean / No clear edge, then check real hit rates."""
    probs = np.asarray(probs)
    order = np.sort(probs, axis=1)
    top, margin = order[:, -1], order[:, -1] - order[:, -2]
    pick = np.array(CLASSES)[probs.argmax(axis=1)]
    tier = np.full(len(probs), "No clear edge", dtype=object)
    for name in reversed(list(config.TIERS)):         # Lean first, then Strong overrides
        r = config.TIERS[name]
        tier[(top >= r["min_prob"]) & (margin >= r["min_margin"])] = name
    df = pd.DataFrame({"tier": tier, "top": top, "hit": pick == np.asarray(y)})
    t = df.groupby("tier").agg(n=("hit", "size"), avg_confidence=("top", "mean"), hit_rate=("hit", "mean"))
    t = t.reindex([k for k in [*config.TIERS, "No clear edge"] if k in t.index]).round(3)
    small = t[t["n"] < config.MIN_TIER_SAMPLE].index.tolist()
    if small:
        print(f"  WARNING: tiers with < {config.MIN_TIER_SAMPLE} matches (too noisy to trust): {small}")
    return t


def report(name, y, probs, market=None):
    out = {"model": name, "n": len(y), "log_loss": log_loss(y, probs),
           "brier": brier(y, probs), "accuracy": accuracy(y, probs)}
    if market is not None:
        ok = ~np.isnan(market).any(axis=1)
        out["market_log_loss"] = log_loss(np.asarray(y)[ok], market[ok])
        out["gap_to_market"] = log_loss(np.asarray(y)[ok], np.asarray(probs)[ok]) - out["market_log_loss"]
    return out

# ---------------------------------------------------------------------------
# Odds conversion helper
# ---------------------------------------------------------------------------
def map_odds_to_prob(odds):
    """Convert decimal betting odds to implied probabilities.

    Parameters
    ----------
    odds : array‑like or scalar
        Decimal odds (e.g., 2.50). Can be a NumPy array, pandas Series, or list.

    Returns
    -------
    numpy.ndarray or pandas.Series
        Implied probability = 1 / odds. Invalid/zero odds become ``nan``.
    """
    import numpy as np
    # Preserve pandas Series type if input is a Series
    is_series = hasattr(odds, "__class__") and hasattr(odds, "dtype") and "pandas" in str(type(odds))
    arr = np.asarray(odds, dtype=float)
    # Avoid division by zero or negative odds
    arr = np.where(arr > 0, arr, np.nan)
    probs = 1.0 / arr
    if is_series:
        import pandas as pd
        return pd.Series(probs, index=odds.index)
    return probs
