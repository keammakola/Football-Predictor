# Repository guide

## Active website

`frontend/` is the React website. `frontend/public/data/` contains its generated
historical and upcoming snapshots, including source provenance. These snapshots
are committed so the website can run without Python or private credentials.

## Modelling and data

Python scripts stay at the repository root so their imports and existing CLI
commands keep working:

- `data.py`, `team_names.py`, `xg_scraper.py`, `features.py`: sources and features.
- `elo.py`, `dixon_coles.py`, `train_xgb.py`: models and training.
- `backtest.py`, `evaluate.py`, `audit_backtest.py`, `blend_test.py`: evaluation.
- `export_bets.py`, `export_json.py`: verified historical website exports.
- `api_fixtures.py`, `live_odds.py`, `generate_upcoming.py`: upcoming predictions.
- `config.py`: shared settings; private keys are read from ignored local settings
  or environment variables.

`data/raw/` contains cached input observations and xG manifests. Root-level
`matches.csv`, `bets.csv`, and model JSON files are generated artifacts kept for
reproducibility and compatibility with the existing scripts.

## Supporting tools

`run_baseline.py` and `run_comparison.py` support model comparisons.
`paper_trading.py` and `injury_snapshot.py` support ledger and availability work.
The Streamlit scripts and earlier daily automation are supporting interfaces.
The Dockerfiles serve the React website; the React frontend and
`generate_upcoming.py` are the current website workflow. Keeping these scripts does not imply they have all been validated as
production entry points.

`tests/` contains isolated fixtures and regression checks. `docs/xg-data.md`
describes collection and chronological xG features. `docs/archive/` contains
historical planning, prototypes, and old outputs, separated from current docs.

## Local-only files

Virtual environments, installed frontend dependencies, build output, caches,
private settings, and credential files are excluded by `.gitignore`.
