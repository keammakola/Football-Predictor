"""Guard against the #1 failure: features that peek at results at or after kickoff.

Run: python -m pytest tests -q     (or: python tests/test_no_leakage.py)
"""
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
import data  # noqa: E402
import elo  # noqa: E402
from make_fake_data import make  # noqa: E402


def _matches():
    tmp = Path(tempfile.mkdtemp())
    make(tmp)
    for path in tmp.glob('E0_*.csv'):
        path.rename(path.with_name(path.name.replace('E0_', 'EPL_', 1)))
    original = config.RAW_DIR
    try:
        config.RAW_DIR = tmp
        return data.load_matches('EPL')
    finally:
        config.RAW_DIR = original


def test_features_ignore_own_and_future_results():
    m = _matches()
    base = elo.elo_features(m)
    k = len(m) - 300                       # change results from here onward
    altered = m.copy()
    altered.loc[k:, "FTHG"], altered.loc[k:, "FTAG"] = 9, 0
    altered.loc[k:, "FTR"] = "H"
    new = elo.elo_features(altered)
    # Every feature up to AND including match k must be unchanged.
    assert np.allclose(base.loc[:k, "elo_diff"], new.loc[:k, "elo_diff"])
    # ...and later ones should change (proves the test can detect an effect).
    assert not np.allclose(base.loc[k + 1:, "elo_diff"], new.loc[k + 1:, "elo_diff"])


def test_sorted_by_date():
    assert _matches()["date"].is_monotonic_increasing


def test_split_is_by_time():
    m = _matches()
    train, test = m[m["season"] < "2324"], m[m["season"] == "2324"]
    assert train["date"].max() < test["date"].min()


if __name__ == "__main__":
    test_features_ignore_own_and_future_results()
    test_sorted_by_date()
    test_split_is_by_time()
    print("all leakage checks passed")
