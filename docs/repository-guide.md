# Repository guide

## Active website

`frontend/` is the React website. `frontend/public/data/` contains its generated
historical snapshots, including source provenance. These snapshots
are committed so the website can run without Python or private credentials.

## Modelling and data

Python scripts stay at the repository root so their imports and existing CLI
commands keep working:

- `data.py`, `team_names.py`, `xg_scraper.py`, `features.py`: sources and features.
- `elo.py`, `dixon_coles.py`, `train_xgb.py`: models and training.
- `backtest.py`, `evaluate.py`, `audit_backtest.py`, `blend_test.py`: evaluation.
- `model_spec.py`, `research_run.py`: shared schema/policy and hash-linked run records.
- `publish_snapshot.py`: supported staged publication and read-only verification.
- `export_bets.py`, `export_json.py`: implementation helpers for verified exports.
- `api_fixtures.py`, `live_odds.py`, `generate_upcoming.py`: upcoming predictions.
- `config.py`: shared settings; private keys are read from ignored local settings
  or environment variables.

`data/raw/` contains cached input observations and xG manifests. New root-level `matches.csv`, `bets.csv` and `research-run.json` are ignored
generated artifacts. The old conflicting CSVs are labelled under
`docs/archive/results/legacy-*.csv`. Root model JSON files are historical research
artifacts; the current seasonal backtest fits its own models. See
[snapshot notes](snapshot.md) for the distinction between model versions.

## Supporting tools

`run_baseline.py` and `run_comparison.py` support model comparisons.
`paper_trading.py` and `injury_snapshot.py` support ledger and availability work.
The Streamlit scripts and earlier daily automation are supporting interfaces.
The Dockerfiles serve the React website; the React frontend and
the verified historical exports are the current website workflow. Keeping these scripts does not imply they have all been validated as
production entry points.

`tests/` contains isolated fixtures and regression checks. `docs/xg-data.md`
describes collection and chronological xG features. `docs/archive/` contains
historical planning, prototypes, and old outputs, separated from current docs.

## Local-only files

Virtual environments, installed frontend dependencies, build output, caches,
private settings, and credential files are excluded by `.gitignore`.
