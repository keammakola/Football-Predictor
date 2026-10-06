"""Record the exact inputs, code and environment used by a completed backtest."""
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from model_spec import FEATURE_COLUMNS, MODEL_VERSION

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_run(started_at_utc):
    import config
    code = ['config.py', 'model_spec.py', 'research_run.py', 'backtest.py', 'data.py',
            'team_names.py', 'features.py', 'xg_scraper.py', 'elo.py', 'dixon_coles.py',
            'requirements-lock.txt']
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        revision = None
    metadata = {
        'model_version': MODEL_VERSION, 'started_at_utc': started_at_utc,
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'base_commit': revision,
        'code_sha256': {name: sha256(ROOT / name) for name in code},
        'input_sha256': {str(path.relative_to(ROOT)): sha256(path)
                         for path in sorted(config.RAW_DIR.iterdir())
                         if path.suffix in ('.csv', '.json')},
        'output_sha256': {name: sha256(ROOT / name) for name in ('matches.csv', 'bets.csv')},
        'configuration': {'seed': config.SEED, 'leagues': config.LEAGUES,
                          'seasons': config.SEASONS, 'feature_columns': FEATURE_COLUMNS,
                          'ensemble_weights': {'dixon_coles': .5, 'xgboost': .5},
                          'strong_min_probability': .60, 'strong_min_lead': .25},
        'environment': {'python': sys.version, **{name: importlib.metadata.version(name)
                        for name in ('numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost', 'requests')}},
    }
    (ROOT / 'research-run.json').write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n')
