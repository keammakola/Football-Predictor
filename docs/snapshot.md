# Historical snapshot and reproducibility

## Authoritative evidence

`frontend/public/data/` contains five files that form one bundle:

- `bets.json`: 925 selected bets, 550 wins and −47.63 simulated units.
- `predictions-all.json`: 9,157 eligible match predictions.
- `stats.json`: headline counts and hit rate calculated from those predictions.
- `provenance.json`: original export timestamp, source hashes and xG metadata.
- `run-manifest.json`: snapshot identity, artifact hashes, policy and limitations.

Run the read-only verifier:

```bash
.venv/bin/python publish_snapshot.py --verify
```

It checks counts, hashes, probability ranges, ledger/prediction agreement, and
selected dates, outcomes, scorelines, odds and P&L against cached source files.
These checks do not prove that a provider's observations are correct or that
forecasts were genuinely recorded before kickoff.

## Why the headline changed from 69.3% to 69.2%

The original website reported 69.3% from full-precision predictions but did not
retain that run's exact denominator. Its public predictions are rounded to three
decimals. Applying the published strong rule (top probability at least 60%,
lead at least 25 points) to those probabilities gives **2,169 strong predictions,
1,502 correct, or 69.2485%**, displayed as **69.2%**.

This is a precision-related evidence revision, not a retraining result. The
selected ledger, 59.5% selected-bet hit rate and −5.1% ROI are unchanged. Its
selection membership was decided before rounding and remains frozen; rounded
values cannot reconstruct all original price and confidence decisions exactly.

The published article used the original 69.3% figure. Its overall finding remains,
but an editorial correction or note can explain the revised reproducible figure.
The run manifest preserves the original report and this limitation.

The former root CSVs have 9,158 predictions and 926 bets and differ from the
published snapshot. They now live in `docs/archive/results/legacy-*.csv`, explicitly
labelled as separate research history. They are not the missing full-precision run.

## New research runs

Use Python 3.14.4 and the committed dependency lock. Work from a separate checkout
when refreshing data so you preserve the published evidence.

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
```

Historical results are already cached. If intentionally refreshing them, use
`data.download_raw(league)` for each configured league; this contacts the provider
and may change files. Refresh observed xG only when wanted:

```bash
.venv/bin/python xg_scraper.py --league all
```

Then generate and publish a new experiment:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python backtest.py
.venv/bin/python publish_snapshot.py
.venv/bin/python publish_snapshot.py --verify
```

The backtest writes ignored `matches.csv`, `bets.csv` and `research-run.json`.
The run record captures exact input/output and code hashes, base commit,
configuration, timestamps and package versions. Publication rejects outputs or
inputs changed since the run. It exports all artifacts to a temporary directory,
validates them, then replaces the public bundle. Review and commit all five files
together; deployment happens from that reviewed repository state.

New exports keep full floating-point model probabilities, explicit strong counts
and a model version. The 60% threshold is inclusive throughout. Source validation
rejects inconsistent selections and prices. Code and environment hashes help
identify a run but do not guarantee bit-for-bit equivalence across hardware.

## Model versions

The frozen snapshot is historical model 1.0 with 13 classifier inputs, including
two constant travel-role columns. They did not measure travel. Its original
forecast-generation commit is unknown and recorded as null, rather than invented.

The current research model is **2.0**, with 11 inputs: Elo difference, eight xG
form features and two rest-day features. Travel and injury placeholders are no
longer generated. The shared feature schema and policy are in `model_spec.py`.
This change does not rewrite the historical model’s predictions. A new v2 run
must be evaluated and published as its own experiment.
