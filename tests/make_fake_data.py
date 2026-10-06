"""Create fake football-data-style CSVs for a dry run (no internet needed).

  python tests/make_fake_data.py <output_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def make(out_dir, seasons=("2122", "2223", "2324", "2425"), n_teams=20, seed=1):
    rng = np.random.default_rng(seed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    teams = [f"Team {i:02d}" for i in range(n_teams)]
    strength = rng.normal(0, 0.35, n_teams)
    for s in seasons:
        rows, start = [], pd.Timestamp(2000 + int(s[:2]), 8, 10)
        pairs = [(h, a) for h in range(n_teams) for a in range(n_teams) if h != a]
        rng.shuffle(pairs)
        for k, (h, a) in enumerate(pairs):
            lam_h = np.exp(0.25 + 0.3 + strength[h] - strength[a] * 0.5)
            lam_a = np.exp(0.25 + strength[a] - strength[h] * 0.5)
            gh, ga = rng.poisson(lam_h), rng.poisson(lam_a)
            ftr = "H" if gh > ga else "A" if ga > gh else "D"
            p = np.array([np.exp(strength[h] - strength[a] + 0.3), 1.6, np.exp(strength[a] - strength[h])])
            p = p / p.sum()
            odds = 0.95 / p
            date = start + pd.Timedelta(days=int(k * 280 / len(pairs)))
            rows.append({"Date": date.strftime("%d/%m/%Y"), "HomeTeam": teams[h], "AwayTeam": teams[a],
                         "FTHG": gh, "FTAG": ga, "FTR": ftr,
                         "B365H": odds[0], "B365D": odds[1], "B365A": odds[2]})
        pd.DataFrame(rows).to_csv(out_dir / f"E0_{s}.csv", index=False)
        strength += rng.normal(0, 0.05, n_teams)


if __name__ == "__main__":
    make(sys.argv[1] if len(sys.argv) > 1 else "data/raw")
