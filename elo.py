"""Walk-forward Elo. The feature for a match is computed BEFORE its result is used."""
import math

import numpy as np
import pandas as pd

import config


def elo_features(matches: pd.DataFrame, elo_k=None, season_reg=None) -> pd.DataFrame:
    """Add pre-match Elo columns: elo_home, elo_away, elo_diff (incl. home advantage).

    Matches must be sorted by date. A match's own result never affects its feature,
    and neither do any later matches (see tests/test_no_leakage.py).
    """
    elo_k = elo_k if elo_k is not None else config.ELO_K
    season_reg = season_reg if season_reg is not None else config.ELO_SEASON_REGRESSION
    
    ratings = {}
    last_season = None
    rows = []
    for m in matches.itertuples(index=False):
        if m.season != last_season:
            if ratings:  # regress toward the mean between seasons
                mean = np.mean(list(ratings.values()))
                for t in ratings:
                    ratings[t] += season_reg * (mean - ratings[t])
            last_season = m.season
        rh = ratings.setdefault(m.HomeTeam, config.ELO_NEW_TEAM)
        ra = ratings.setdefault(m.AwayTeam, config.ELO_NEW_TEAM)

        diff = rh - ra + config.ELO_HOME_ADV
        rows.append((rh, ra, diff))          # recorded BEFORE the update below

        if pd.isna(m.FTR):
            continue

        expected_home = 1 / (1 + 10 ** (-diff / 400))
        actual_home = {"H": 1.0, "D": 0.5, "A": 0.0}[m.FTR]
        gd = abs(m.FTHG - m.FTAG) if not pd.isna(m.FTHG) else 0
        mult = math.log(gd + 1) + 1 if gd > 0 else 1.0
        delta = elo_k * mult * (actual_home - expected_home)
        ratings[m.HomeTeam] = rh + delta
        ratings[m.AwayTeam] = ra - delta

    out = matches.copy()
    out[["elo_home", "elo_away", "elo_diff"]] = pd.DataFrame(rows, index=out.index)
    return out
