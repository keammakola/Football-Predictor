"""Export model predictions with source dates; never fabricate kickoff timestamps."""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    predictions = []
    for row in csv.DictReader((ROOT / 'matches.csv').open()):
        odds = [float(row[f'odds_{name}']) for name in ('home', 'draw', 'away')]
        if not all(math.isfinite(n) and n > 1 for n in odds):
            continue
        implied = [1 / n for n in odds]
        total = sum(implied)
        match_date = row['date'][:10]
        year, month = int(match_date[:4]), int(match_date[5:7])
        start_year = year if month >= 7 else year - 1
        predictions.append({
            'schema_version': 1,
            'id': f"{row['league']}-{match_date}-{row['home']}-{row['away']}".replace(' ', '-'),
            'model_version': '1.0', 'date': match_date,
            'logged_at_utc': None, 'kickoff_utc': None,
            'league': row['league'], 'season': f'{start_year % 100:02d}{(start_year + 1) % 100:02d}',
            'home': row['home'], 'away': row['away'],
            **{f'p_{name}': round(float(row[f'p_{name}']), 3) for name in ('home', 'draw', 'away')},
            **{f'mkt_{name}': round(implied[i] / total, 3) for i, name in enumerate(('home', 'draw', 'away'))},
            **{f'odds_{name}': odds[i] for i, name in enumerate(('home', 'draw', 'away'))},
            'result': row['result'],
        })
    output = ROOT / 'frontend/public/data/predictions-all.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(predictions, allow_nan=False))
    print(f'Exported {len(predictions)} predictions with match dates and no invented timestamps.')


if __name__ == '__main__':
    main()
