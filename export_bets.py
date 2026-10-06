"""Export only ledger rows verified against historical source results and odds."""
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from team_names import canon
from model_spec import prediction_tier, favourable_price

ROOT = Path(__file__).resolve().parent
CODES = {"EPL": "E0", "LaLiga": "SP1", "Bundesliga": "D1", "SerieA": "I1", "Ligue1": "F1"}


def main(output_dir=None):
    raw = {}
    files = {}
    for path in sorted((ROOT / "data/raw").glob("*.csv")):
        league, season = path.stem.rsplit("_", 1)
        if league not in CODES:
            continue
        files[(league, season)] = path
        for row in csv.DictReader(path.open(encoding="latin-1")):
            if row.get("FTR") not in {"H", "D", "A"}:
                continue
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    match_date = datetime.strptime(row["Date"], fmt).date().isoformat()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid source date in {path.name}: {row['Date']}")
            match = f"{canon(row['HomeTeam'])} vs {canon(row['AwayTeam'])}"
            key = (league, season, match)
            if key in raw:
                raise ValueError(f"Ambiguous match identity: {key}")
            raw[key] = (match_date, row)

    predictions = list(csv.DictReader((ROOT / "matches.csv").open()))
    model_rows = {(r["league"], r["date"], f"{r['home']} vs {r['away']}"): r for r in predictions}
    bets = []
    used_sources = set()
    for bet in csv.DictReader((ROOT / "bets.csv").open()):
        if bet["tier"] != "Strong":
            continue
        identity = (bet["league"], bet["season"], bet["match"])
        if identity not in raw:
            raise ValueError(f"No source match for {identity}")
        match_date, source = raw[identity]
        recorded_odds = float(source[{"H": "B365H", "D": "B365D", "A": "B365A"}[bet["pick"]]])
        if not math.isfinite(recorded_odds) or recorded_odds <= 1 or not math.isclose(recorded_odds, float(bet["odds_taken"]), abs_tol=1e-8):
            raise ValueError(f"Missing or non-source odds for {identity}")
        won = int(bet["pick"] == source["FTR"])
        pnl = recorded_odds - 1 if won else -1.
        if int(bet["won"]) != won or not math.isclose(pnl, float(bet["pnl"]), abs_tol=1e-8):
            raise ValueError(f"Result/P&L mismatch for {identity}")
        model = model_rows.get((bet["league"], match_date, bet["match"]))
        if model is None or model["result"] != source["FTR"]:
            raise ValueError(f"No matching model row for {identity}")
        probabilities = [float(model[f'p_{name}']) for name in ('home', 'draw', 'away')]
        labels = ('H', 'D', 'A')
        top = max(range(3), key=lambda index: probabilities[index])
        if (prediction_tier(probabilities) != 'Strong' or labels[top] != bet['pick']
                or not math.isclose(probabilities[top], float(bet['prob']), abs_tol=1e-10)
                or not favourable_price(probabilities[top], recorded_odds)):
            raise ValueError(f'Selection/model mismatch for {identity}')
        used_sources.add((bet["league"], bet["season"]))
        bets.append({
            "id": f"{bet['league']}-{match_date}-{bet['match']}", "date": match_date,
            "season": bet["season"], "league": bet["league"], "match": bet["match"],
            "pick": bet["pick"], "prob": float(bet["prob"]),
            "odds_taken": recorded_odds, "won": won, "pnl": pnl, "result": source["FTR"],
            "scoreline": f"{int(float(source['FTHG']))}-{int(float(source['FTAG']))}",
            **{key: float(model[key]) for key in ("p_home", "p_draw", "p_away")},
        })
    bets.sort(key=lambda r: (r["date"], r["id"]), reverse=True)
    if len({r["id"] for r in bets}) != len(bets):
        raise ValueError("Duplicate ledger records")
    # Include sources for the whole eligible prediction universe, not only selected bets.
    for model in predictions:
        year, month = int(model['date'][:4]), int(model['date'][5:7])
        start_year = year if month >= 7 else year - 1
        season = f'{start_year % 100:02d}{(start_year + 1) % 100:02d}'
        used_sources.add((model['league'], season))
    sources = [{"league": league, "season": season, "file": files[(league, season)].name,
                "url": f"https://www.football-data.co.uk/mmz4281/{season}/{CODES[league]}.csv",
                "sha256": hashlib.sha256(files[(league, season)].read_bytes()).hexdigest()}
               for league, season in sorted(used_sources)]
    xg_sources = []
    for league in sorted({r['league'] for r in bets}):
        cache = ROOT / f'data/raw/understat_xg_{league}.csv'
        manifest_file = cache.with_suffix('.meta.json')
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text())
            if manifest.get('source') != 'Understat' or manifest.get('sha256') != hashlib.sha256(cache.read_bytes()).hexdigest():
                raise ValueError(f'Invalid xG manifest for {league}')
            xg_sources.append({'league': league, **manifest})
    coverage_path = ROOT / 'data/xg_coverage.json'
    provenance = {"exported_at_utc": datetime.now(timezone.utc).isoformat(), "verified_records": len(bets),
                  "first_match": min(r["date"] for r in bets), "last_match": max(r["date"] for r in bets),
                  "results_source": "football-data.co.uk historical CSVs", "odds_source": "Recorded Bet365 1X2 odds (B365H/B365D/B365A)",
                  "ledger_sha256": hashlib.sha256(json.dumps(bets, allow_nan=False).encode()).hexdigest(), "sources": sources, "xg_sources": xg_sources, "xg_coverage": json.loads(coverage_path.read_text()) if coverage_path.exists() else []}
    out = Path(output_dir) if output_dir else ROOT / "frontend/public/data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "bets.json").write_text(json.dumps(bets, allow_nan=False))
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2))
    strong = []
    for row in predictions:
        ranked = sorted(((float(row[f"p_{name}"]), label) for name, label in (("home", "H"), ("draw", "D"), ("away", "A"))), reverse=True)
        if prediction_tier([float(row[f"p_{name}"]) for name in ("home", "draw", "away")]) == "Strong":
            strong.append(ranked[0][1] == row["result"])
    (out / "stats.json").write_text(json.dumps({"strong_hit_rate": round(sum(strong) / len(strong) * 100, 1) if strong else None, "strong_predictions": len(strong), "strong_correct": sum(strong), "probability_precision": "full_precision"}, allow_nan=False))
    print(f"Exported {len(bets)} source-verified bets from {len(sources)} historical CSVs.")


if __name__ == '__main__':
    # Direct CLI use must publish a complete validated bundle too.
    from publish_snapshot import main as publish
    publish()
