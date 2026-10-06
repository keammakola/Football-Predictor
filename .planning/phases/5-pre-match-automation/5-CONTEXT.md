# Phase 5 Context: Pre-Match Automation & Alerts

## Domain
Automate the end‑to‑end daily workflow: fetch the latest match schedules and odds, run the XGBoost model, and dispatch alerts for any "Strong Tier" predictions.

## Decisions Captured
- **Data Sources:** Use the existing `data.py` CSV loader for static season fixtures and the `xg_scraper.py` (static dump) for xG. No live‑odds API needed.
- **Scheduling:** A daily cron job (e.g. 02:00 UTC) will execute the automation script.
- **Alert Channels:** Support configurable email (SMTP) and webhook (POST JSON) targets defined in `config.json`.
- **Output:** For each Strong Tier bet, generate a one‑line summary containing date, teams, probability, and a link to the match page.

## Code Context
Will add a new script `run_daily.py` that composes the pipeline, filters Strong Tier bets (re‑using the logic from `train_xgb.py`), and sends alerts.
