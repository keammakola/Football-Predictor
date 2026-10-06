"""Download (never overwrite) raw files, then load them into one clean table."""
import pandas as pd
import numpy as np
import requests

import config
from team_names import canon

# (home, draw, away) odds column triples, best first. Closing odds preferred.
ODDS_TRIPLES = [
    ("PSCH", "PSCD", "PSCA"),
    ("B365CH", "B365CD", "B365CA"),
    ("PSH", "PSD", "PSA"),
    ("B365H", "B365D", "B365A"),
]


def download_raw(seasons=None, league_name=None):
    """Save each season CSV once. Existing files are left alone (raw stays raw)."""
    seasons = seasons or config.SEASONS
    league_name = league_name or config.DEFAULT_LEAGUE
    league_code = config.LEAGUES[league_name]["fd_code"]
    
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    for s in seasons:
        path = config.RAW_DIR / f"{league_name}_{s}.csv"
        # Always overwrite the current season to get latest results.
        # Skip downloading if it's an old season and the file already exists.
        if path.exists() and s != "2627":
            continue
        url = config.URL_TEMPLATE.format(season=s, league=league_code)
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        path.write_bytes(r.content)
        print(f"downloaded {path.name}")


def _market_probs(df):
    """Market probabilities with the bookmaker margin removed."""
    h = pd.Series(float("nan"), index=df.index)
    d, a = h.copy(), h.copy()
    for ch, cd, ca in ODDS_TRIPLES:
        if ch in df.columns:
            m = h.isna() & df[ch].notna() & df[cd].notna() & df[ca].notna()
            h[m], d[m], a[m] = df.loc[m, ch], df.loc[m, cd], df.loc[m, ca]
    inv = pd.DataFrame({"H": 1 / h, "D": 1 / d, "A": 1 / a})
    inv = inv.div(inv.sum(axis=1), axis=0)
    return inv.rename(columns=lambda c: f"mkt_{c}")


def load_matches(league_name=None):
    """Load all historical matches from raw CSV files."""
    league_name = league_name or config.DEFAULT_LEAGUE
    frames = []
    for path in sorted(config.RAW_DIR.glob(f"{league_name}_*.csv")):
        season = path.stem.split("_")[1]
        df = pd.read_csv(path, encoding="latin-1")
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTR"]).copy()
        df["season"] = season
        df["date"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed")
        df["HomeTeam"] = df["HomeTeam"].map(canon)
        df["AwayTeam"] = df["AwayTeam"].map(canon)
        out = df[["season", "date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]].copy()
        
        # Try to include B365 odds if they exist
        for col in ["B365H", "B365D", "B365A"]:
            if col in df.columns:
                out[col] = df[col]
            else:
                out[col] = np.nan
                
        out = pd.concat([out, _market_probs(df)], axis=1)
        frames.append(out)
    if not frames:
        raise FileNotFoundError(f"No raw files in {config.RAW_DIR}. Run: python run_baseline.py --download")
    matches = pd.concat(frames, ignore_index=True)
    matches = matches.sort_values(["date", "HomeTeam"], kind="mergesort").reset_index(drop=True)
    return matches


def load_fixtures(league_name=None, upcoming=False):
    """Return fixtures DataFrame.
    If upcoming=True, filters to dates >= today.
    """
    matches = load_matches(league_name)
    if upcoming:
        today = pd.Timestamp.now()
        matches = matches[matches['date'] >= today].reset_index(drop=True)
    return matches
