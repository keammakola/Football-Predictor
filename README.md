# The Football Experiment

A football modelling project exploring why winning picks can still lose money.
The website presents historical predictions, simulated returns, the data sources,
and the reasoning behind the implementation.

## What it does

- Predicts home-win, draw, and away-win probabilities across the Premier League,
  La Liga, Bundesliga, Serie A, and Ligue 1.
- Combines a Dixon–Coles goals model with XGBoost using Elo, observed xG form,
  and rest-day features.
- Evaluates models season by season using earlier seasons for training.
- Checks exported bet results and odds against historical source CSVs.
- Generates upcoming predictions from real fixture feeds and bookmaker odds.

The frontend is React and TypeScript, built with Vite and Tailwind CSS. The
modelling pipeline uses Python, pandas, NumPy, SciPy, scikit-learn, and XGBoost.

## Run the website

```bash
cd frontend
npm ci
npm run dev
```

Open the localhost URL printed by Vite. The committed JSON exports allow the
historical website to run without an API key. The upcoming section displays
qualifying matches in the next 24 hours; exports are snapshots, not a live feed.

## Run the modelling pipeline

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python tests/test_xg.py
python tests/test_no_leakage.py
python tests/test_upcoming.py
python tests/test_dc_preparation.py
```

Refresh observed xG and rebuild historical results:

```bash
python xg_scraper.py --league all
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python train_xgb.py --league all
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python backtest.py
python export_bets.py
python export_json.py
```

Historical results and odds are cached in `data/raw/`; `data.download_raw`
refreshes the configured football-data.co.uk season files. The xG collector
fetches completed Understat observations and rejects synthetic or altered caches.
See [the xG collection notes](docs/xg-data.md) for source validation, date
alignment, and feature chronology.

## Private credentials

For current bookmaker odds, set `ODDS_API_KEY` in your environment or create
`config.local.json` in the project root:

```json
{"ODDS_API_KEY": "your-api-key"}
```

The environment variable takes precedence. `config.local.json`, `.env` files,
and private alert settings in `config.json` are ignored by Git. Use
`config.example.json` as a template for alert settings. Never commit credentials.

Refresh upcoming predictions with:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python generate_upcoming.py
```

The generator uses separate histories and models for each league. Missing odds
remain missing, and feed failures are recorded in `upcoming-status.json`.

For deployment, the scheduled GitHub Actions backend refreshes upcoming data
every six hours and requests a Vercel rebuild. Set `ODDS_API_KEY` and
`VERCEL_DEPLOY_HOOK` as repository secrets, then run the workflow once.
See [automated backend setup](docs/deployment.md#automated-backend).

## Read the evidence

`frontend/public/data/bets.json` contains the selected historical bet ledger.
`predictions-all.json` contains model predictions for all exported matches.
`provenance.json` records source links, file hashes, and xG coverage. Historical
P&L uses simulated one-unit stakes; it is not a live trading record. Hit rate,
probability calibration, and profitability are separate measures.

## License

Project code is released under the MIT License; see [LICENSE](LICENSE).
Historical results and odds come from football-data.co.uk, xG from Understat,
fixtures from Fixture Download, and current odds from The Odds API. These
datasets and services retain their providers' terms.

[Portfolio](https://keabetswe.online)

## Repository layout

See [the repository guide](docs/repository-guide.md) for active scripts, generated
artifacts, and supporting tools. Historical design notes and abandoned prototypes
are preserved in `docs/archive/`; `frontend/` is the active website.

## Docker and Vercel

```bash
docker compose up --build -d
```

Open http://localhost:8080. For Vercel, import this repository with Root Directory
`.` and Framework Preset **Other**; `Dockerfile.vercel` builds and serves the
website. See [deployment instructions](docs/deployment.md) for container and
static Vite options, and how to refresh the deployed data.
