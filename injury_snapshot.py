"""Daily snapshot of Premier League player availability (free, no API key).

Source: the unofficial Fantasy Premier League endpoint. It is undocumented and
can change, so check the field names if the script breaks.

Run once a day (cron, Task Scheduler, or a free GitHub Actions schedule).
Each run saves a dated CSV, so you build a clean "who was missing before
each match" history from today onward.
"""
import datetime as dt
import pathlib

import pandas as pd
import requests

URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
OUT_DIR = pathlib.Path("snapshots")

# status codes: a = available, d = doubtful, i = injured, s = suspended,
# u = unavailable (e.g. left club), n = not in squad
def take_snapshot() -> pathlib.Path:
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    teams = {t["id"]: t["name"] for t in data["teams"]}
    players = pd.DataFrame(data["elements"])
    players["team_name"] = players["team"].map(teams)

    cols = [
        "id", "web_name", "team_name", "element_type", "status", "news",
        "news_added", "chance_of_playing_next_round", "now_cost", "minutes",
        "total_points",
    ]
    # Keep ALL players (not just injured) so you can weight absences by
    # importance (cost, minutes) later.
    snap = players[cols].copy()
    snap["snapshot_date"] = dt.date.today().isoformat()

    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"availability_{snap['snapshot_date'].iloc[0]}.csv"
    snap.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    p = take_snapshot()
    df = pd.read_csv(p)
    out = df[df["status"] != "a"]
    print(f"Saved {len(df)} players to {p}; {len(out)} not fully available.")
    print(out[["web_name", "team_name", "status", "news"]].head(15).to_string(index=False))
