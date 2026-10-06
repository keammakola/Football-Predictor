# The Football Experiment

An open-source football modelling experiment exploring why winning picks can
still lose money. The website presents historical predictions, simulated
returns, data sources and the reasoning behind the implementation.

[Explore the website](https://betting.keabetswe.online) ·
[Read the article](https://keammakola.hashnode.dev/house-always-wins) ·
[Author's portfolio](https://keabetswe.online)

## Published experiment

The frozen website snapshot contains 9,157 eligible match predictions and 925
selected one-unit simulated bets. Those bets won 550 times (59.5%) and lost
47.63 units overall (−5.1% ROI). The strong-prediction group has 1,502 correct
outcomes out of 2,169 (69.2%), calculated from the published probabilities.

The original headline was 69.3%. Its original full-precision denominator was not
preserved; the current rounded snapshot supports the reproducible 69.2% figure.
See [snapshot notes](docs/snapshot.md) for precision, model version and limits.
These are historical simulations, not live bets or a future-return guarantee.

## Run the website

Use Node 22:

```bash
cd frontend
npm ci
npm run dev
```

The site uses committed JSON and runs without Python, an API key, a database or
scheduled jobs. It covers the Premier League, La Liga, Bundesliga, Serie A and
Ligue 1. Visitors can filter and expand the historical ledger and inspect the
model's probabilities, returns, source links and evidence downloads.

## Run checks and research

Use the tested Python 3.14.4 environment:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
.venv/bin/python publish_snapshot.py --verify
```

Frontend checks are `npm run lint` and `npm run build` inside `frontend/`.
CI is configured for both frontend checks, all Python tests and snapshot
validation on pushes and pull requests. `requirements-lock.txt` records the tested Linux Python
environment; `frontend/package-lock.json` locks the frontend dependencies.

To create a new research run from cached observed data:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python backtest.py
.venv/bin/python publish_snapshot.py
.venv/bin/python publish_snapshot.py --verify
```

Read [snapshot instructions](docs/snapshot.md) before refreshing or publishing.
The backtest writes a hash-linked run record; the publisher stages and validates
the full bundle before replacing public files. New research uses model 2.0 with
11 observed-history features. The frozen model 1.0 snapshot remains intact apart
from the documented headline revision.

Hosted CI is currently blocked by a GitHub account billing lock: the first
[repository-check run](https://github.com/keammakola/Football-Predictor/actions/runs/37494816196)
could not start either job. On 6 October 2026, a clean local installation passed
all 29 tests and snapshot verification; frontend lint and build also passed.
The account owner must resolve the lock before hosted checks can execute.

## Models and data

The ensemble combines Dixon–Coles goals probabilities and XGBoost at equal
weights. XGBoost uses Elo difference, eight observed xG form features and two
league-history rest-day features. It does not invent injury or travel signals.
Each evaluated season trains on earlier seasons with chronological features.

Results and recorded Bet365 odds come from football-data.co.uk; xG observations
come from Understat. The collector rejects placeholder caches and invalid values.
Source validation and hashes make the published evidence inspectable.

## Documentation

- [Repository guide](docs/repository-guide.md): supported scripts and artifacts.
- [Observed xG notes](docs/xg-data.md): collection, integrity and chronology.
- [Snapshot notes](docs/snapshot.md): figures, provenance and publication.
- [Hosting guide](docs/hosting.md): Docker, Vercel and static serving.
- [Writer handoff](docs/article-writer-handoff.md): methodology, results and claim boundaries.
- [Contributing](CONTRIBUTING.md): setup, checks and pull requests.
- [Security reporting](SECURITY.md): private reports and credential handling.

Earlier experiments and prototypes are retained in `docs/archive/` and are not
current website evidence. Optional live-odds and Streamlit tools are research
helpers; the website does not depend on them. Optional live credentials belong
in environment variables or ignored `config.local.json`, never public exports.

## Docker

```bash
docker compose up --build -d
```

Open http://localhost:8080. For the configured Vercel deployment use repository
root `.` and the Container framework with `Dockerfile.vercel`.

## License and provider data

Code is [MIT licensed](LICENSE). Provider datasets and services retain their own
terms; the code licence does not relicense their data. Contributions should
preserve attribution and source provenance.
