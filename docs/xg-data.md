# Observed xG collection

`xg_scraper.py` reads Understat's `getLeagueData/<league>/<start-year>` JSON endpoint. Only completed matches (`isResult: true`) with finite, nonnegative xG values are retained. No synthetic fallback is used. HTTP, response-format, missing-value, and cache-integrity errors stop collection instead of inventing observations.

Refresh the configured leagues:

```bash
venv/bin/python xg_scraper.py --league all
```

Refresh a specific league and season (2023 means 2023/24):

```bash
venv/bin/python xg_scraper.py --league EPL --seasons 2023
```

An explicit season list replaces that league's complete cache with the requested seasons. The default reads the season files with completed results and fetches their history. Run the default before a full-history model fit.

Each league cache includes Understat match IDs, season, source URL, observed xG, and original Understat date. A sidecar `.meta.json` records collection time, source URLs, and a SHA-256 of the CSV. Training rejects old placeholder caches and altered cache files. A failed league refresh preserves its previous cache.

For a unique home/away fixture within a season, the collector uses the result-source match date, preserving `understat_date`. This resolves source discrepancies and suspended/rescheduled matches. Unmatched observations are explicitly flagged and excluded from form history. `data/xg_coverage.json` reports result-to-xG coverage from the latest verification.

`calculate_xg_form` computes rolling and exponentially weighted history within each team, then looks up observations strictly before each target match date. Current-match and future xG cannot enter that match's features. Missing prior history stays missing; XGBoost handles it rather than filling with a mean computed from future seasons. A fixture without its own observed xG can still use the team's earlier observed form.

After refreshing, rebuild the results:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 venv/bin/python train_xgb.py --league all
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 venv/bin/python backtest.py
python3 export_bets.py
python3 export_json.py
```

Run the collector and chronology checks:

```bash
venv/bin/python tests/test_xg.py
venv/bin/python tests/test_no_leakage.py
```

Tests use isolated fixtures and temporary directories; those records are never exported to the website. Website P&L is a historical simulation, not a live trading record.
