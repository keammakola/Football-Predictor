# Contributing

The supported product is the React historical website. The supported research
pipeline is the observed-data feature construction, seasonal backtest and
validated snapshot publication. Streamlit interfaces, live-odds helpers and
archived experiments are optional research tools, not production entry points.

## Set up

Use Node 22 for the website and Python 3.14.4 for the tested research environment.

```bash
cd frontend
npm ci
npm run dev
```

From the repository root:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
.venv/bin/python publish_snapshot.py --verify
```

The lock file records the tested Linux Python environment, including optional
Streamlit tools. Other platforms may need compatible wheels. No API key is
needed for the historical website or isolated tests.

## Before opening a pull request

Run `npm run lint` and `npm run build` inside `frontend/`, and run the Python
checks above. CI runs these checks on pushes to main and pull requests; pytest
also collects the function-based chronology tests that unittest discovery misses.

Explain the problem, change and verification in the PR. Include screenshots for
visible UI changes. Keep provider data and model changes separate from styling
changes where practical so results can be reviewed clearly.

## Working with evidence

Do not hand-edit published probabilities, prices, results or headline statistics.
The current historical bundle has a run manifest. Its probabilities were rounded
before publication, and its original full-precision run is unavailable. See
[the snapshot notes](docs/snapshot.md) for the exact limits and headline revision.

For a new run, use a separate checkout, keep the observed cache and manifests
intact, run `backtest.py`, then `publish_snapshot.py`. Publication validates a
staged bundle before replacing public files. Review the entire data diff and
commit all five evidence files together. Rebuilding a model can change results;
do not describe a new run as the same experiment in an existing article.

`matches.csv`, `bets.csv` and `research-run.json` are ignored generated files.
The old conflicting CSVs remain labelled in `docs/archive/results/`. They must
not be reused as current snapshot inputs.

When updating dependencies, deliberately regenerate the relevant lock file and
check installation, tests and builds in a clean environment.

## Credentials and provider data

Use environment variables or ignored `config.local.json` for optional live tools.
Never put secrets in frontend variables, public JSON, source files or issues.
See [SECURITY.md](SECURITY.md) for reporting an exposure privately.

Project code is MIT. Providers retain rights and terms for their data; additions
must identify the source rather than implying the dataset is MIT-licensed.
