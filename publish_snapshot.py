"""Publish one validated evidence bundle, or verify the committed frozen snapshot.

This command never trains models, downloads observations or contacts an API.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from model_spec import MODEL_VERSION, FEATURE_COLUMNS, prediction_tier
from team_names import canon

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'frontend/public/data'
ARTIFACTS = ('bets.json', 'predictions-all.json', 'stats.json', 'provenance.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def strong_stats(predictions, precision):
    strong = []
    for row in predictions:
        probabilities = [row[f'p_{name}'] for name in ('home', 'draw', 'away')]
        if prediction_tier(probabilities) == 'Strong':
            pick = ('H', 'D', 'A')[max(range(3), key=lambda i: probabilities[i])]
            strong.append(pick == row['result'])
    return {
        'strong_hit_rate': round(sum(strong) / len(strong) * 100, 1) if strong else None,
        'strong_predictions': len(strong), 'strong_correct': sum(strong),
        'probability_precision': precision,
    }


def validate_evidence(directory):
    bets = read(directory / 'bets.json')
    predictions = read(directory / 'predictions-all.json')
    stats = read(directory / 'stats.json')
    provenance = read(directory / 'provenance.json')
    if not bets or not predictions:
        raise ValueError('Empty historical evidence cannot be published')
    if len(bets) != provenance['verified_records']:
        raise ValueError('Ledger/provenance count mismatch')
    ledger_hash = hashlib.sha256(json.dumps(bets, allow_nan=False).encode()).hexdigest()
    if ledger_hash != provenance['ledger_sha256']:
        raise ValueError('Ledger/provenance hash mismatch')
    expected = strong_stats(predictions, stats['probability_precision'])
    if stats != expected:
        raise ValueError('Strong prediction counts or hit rate do not match predictions')
    models = {}
    for row in predictions:
        key = (row['league'], row['date'], f"{row['home']} vs {row['away']}")
        if key in models or row['result'] not in ('H', 'D', 'A'):
            raise ValueError('Duplicate match or invalid result in predictions')
        probabilities = [row[f'p_{name}'] for name in ('home', 'draw', 'away')]
        prediction_tier(probabilities)  # Includes finite/range/sum validation.
        if any(not math.isfinite(row[f'odds_{name}']) or row[f'odds_{name}'] <= 1
               for name in ('home', 'draw', 'away')):
            raise ValueError('Invalid recorded prediction odds')
        models[key] = row
    sources = {}
    for source in provenance['sources']:
        path = ROOT / 'data/raw' / source['file']
        if digest(path) != source['sha256']:
            raise ValueError(f"Source integrity failure: {source['file']}")
        rows = {}
        with path.open(encoding='latin-1') as handle:
            for row in csv.DictReader(handle):
                if row.get('FTR') not in ('H', 'D', 'A'):
                    continue
                identity = f"{canon(row['HomeTeam'])} vs {canon(row['AwayTeam'])}"
                if identity in rows:
                    raise ValueError('Ambiguous result-source fixture')
                rows[identity] = row
        sources[(source['league'], source['season'])] = rows
    for prediction in predictions:
        source = sources[(prediction['league'], prediction['season'])][f"{prediction['home']} vs {prediction['away']}"]
        source_date = None
        for fmt in ('%d/%m/%Y', '%d/%m/%y'):
            try:
                source_date = datetime.strptime(source['Date'], fmt).date().isoformat()
                break
            except ValueError:
                pass
        if source_date != prediction['date'] or source['FTR'] != prediction['result']:
            raise ValueError('Prediction/source date or result mismatch')
        for name, column in (('home', 'B365H'), ('draw', 'B365D'), ('away', 'B365A')):
            if not math.isclose(prediction[f'odds_{name}'], float(source[column]), abs_tol=1e-8):
                raise ValueError('Prediction/source recorded odds mismatch')
    for source in provenance.get('xg_sources', []):
        path = ROOT / 'data/raw' / f"understat_xg_{source['league']}.csv"
        if source.get('source') != 'Understat' or digest(path) != source['sha256']:
            raise ValueError('xG source integrity failure')
    seen = set()
    for bet in bets:
        if bet['id'] in seen:
            raise ValueError('Duplicate ledger ID')
        seen.add(bet['id'])
        prediction = models.get((bet['league'], bet['date'], bet['match']))
        if prediction is None or bet['result'] != prediction['result']:
            raise ValueError('Ledger/prediction identity or result mismatch')
        for key in ('p_home', 'p_draw', 'p_away'):
            if bet[key] != prediction[key]:
                raise ValueError('Ledger/prediction probability mismatch')
        source = sources[(bet['league'], bet['season'])][bet['match']]
        source_date = None
        for fmt in ('%d/%m/%Y', '%d/%m/%y'):
            try:
                source_date = datetime.strptime(source['Date'], fmt).date().isoformat()
                break
            except ValueError:
                pass
        odds = float(source[{'H': 'B365H', 'D': 'B365D', 'A': 'B365A'}[bet['pick']]])
        won = int(bet['pick'] == source['FTR'])
        pnl = odds - 1 if won else -1
        score = f"{int(float(source['FTHG']))}-{int(float(source['FTAG']))}"
        if (source_date != bet['date'] or bet['result'] != source['FTR']
                or bet['scoreline'] != score or bet['won'] != won
                or not math.isclose(bet['odds_taken'], odds, abs_tol=1e-8)
                or not math.isclose(bet['pnl'], pnl, abs_tol=1e-8)):
            raise ValueError('Ledger/source date, result, price or P&L mismatch')
        chosen_name = {'H': 'home', 'D': 'draw', 'A': 'away'}[bet['pick']]
        if bet['prob'] != prediction[f'p_{chosen_name}']:
            raise ValueError('Selected probability mismatch')
    return bets, predictions, stats, provenance


def create_manifest(directory, historical=False):
    bets, predictions, stats, provenance = validate_evidence(directory)
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        revision = None
    code_paths = ['model_spec.py', 'backtest.py', 'features.py', 'elo.py',
                  'dixon_coles.py', 'export_bets.py', 'export_json.py',
                  'publish_snapshot.py', 'research_run.py', 'data.py', 'team_names.py', 'xg_scraper.py', 'config.py', 'requirements-lock.txt']
    manifest = {
        'schema_version': 1,
        'snapshot_id': ('historical-2026-10-06-rounded-v1' if historical else
                        f"research-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-v2"),
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'data_exported_at_utc': provenance['exported_at_utc'],
        'evidence_tool_base_commit': revision,
        'evidence_tool_sha256': {name: digest(ROOT / name) for name in code_paths},
        'forecast_generation_commit': None,
        'forecast_generation_note': 'Generation commit was not recorded; code hashes describe the evidence tools, not a reconstructed training run.',
        'model_version': '1.0' if historical else MODEL_VERSION,
        'feature_columns': FEATURE_COLUMNS + (['home_travel_fatigue', 'away_travel_fatigue'] if historical else []),
        'selection_policy': {'min_probability': .60, 'min_lead': .25, 'favourable_price': 'odds > 1 / probability', 'stake_units': 1},
        'counts': {'predictions': len(predictions), 'selected_bets': len(bets),
                   'selected_wins': sum(b['won'] for b in bets),
                   'strong_predictions': stats['strong_predictions'],
                   'strong_correct': stats['strong_correct']},
        'strong_hit_rate': stats['strong_hit_rate'],
        'net_units': round(sum(b['pnl'] for b in bets), 8),
        'probability_precision': stats['probability_precision'],
        'artifacts_sha256': {name: digest(directory / name) for name in ARTIFACTS},
    }
    if historical:
        manifest['historical_limitations'] = [
            'Predictions were rounded to three decimals before publication.',
            'Strong-group membership is now computed from the published rounded probabilities.',
            'Original reported strong hit rate was 69.3%; its full-precision denominator was not preserved.',
            'Historical selected-bet membership was decided before rounding and is preserved, not reselected.',
            'This snapshot predates the removal of constant travel features.',
        ]
    else:
        run = read(ROOT / 'research-run.json')
        if run['model_version'] != MODEL_VERSION:
            raise ValueError('Research run/model version mismatch')
        for name, expected in run['output_sha256'].items():
            if digest(ROOT / name) != expected:
                raise ValueError('Research outputs changed after backtesting')
        for name, expected in run['input_sha256'].items():
            if digest(ROOT / name) != expected:
                raise ValueError('Research inputs changed after backtesting')
        manifest['forecast_generation_commit'] = run['base_commit']
        manifest['forecast_generation_note'] = 'Base commit plus exact code hashes in research_run identifies the training code.'
        manifest['research_run'] = run
        manifest['research_inputs_sha256'] = run['output_sha256']
    (directory / 'run-manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    return manifest


def verify(directory=PUBLIC):
    bets, predictions, stats, _ = validate_evidence(directory)
    manifest = read(directory / 'run-manifest.json')
    for name in ARTIFACTS:
        if digest(directory / name) != manifest['artifacts_sha256'][name]:
            raise ValueError(f'Artifact integrity failure: {name}')
    expected_counts = {'predictions': len(predictions), 'selected_bets': len(bets),
                       'selected_wins': sum(b['won'] for b in bets),
                       'strong_predictions': stats['strong_predictions'], 'strong_correct': stats['strong_correct']}
    if manifest['counts'] != expected_counts or manifest['strong_hit_rate'] != stats['strong_hit_rate']:
        raise ValueError('Run-manifest count or headline mismatch')
    if not math.isclose(manifest['net_units'], sum(b['pnl'] for b in bets), abs_tol=1e-8):
        raise ValueError('Run-manifest P&L mismatch')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Read-only validation of the published snapshot')
    args = parser.parse_args()
    if args.verify:
        manifest = verify()
    else:
        # Stage and validate every artifact before modifying the public directory.
        import export_bets
        import export_json
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            export_bets.main(directory)
            export_json.main(directory)
            manifest = create_manifest(directory)
            verify(directory)
            for name in (*ARTIFACTS, 'run-manifest.json'):
                target = PUBLIC / name
                staging = target.with_suffix('.json.tmp')
                staging.write_bytes((directory / name).read_bytes())
                staging.replace(target)
    print(f"Verified {manifest['snapshot_id']}: {manifest['counts']['predictions']} predictions, "
          f"{manifest['counts']['selected_bets']} selections, {manifest['net_units']:+.2f} units")


if __name__ == '__main__':
    main()
