---
wave: 1
depends_on: []
files_modified:
  - run_daily.py
  - config.json
  - .planning/phases/5-pre-match-automation/5-CONTEXT.md
autonomous: true
---

# Phase 5 Plan – Pre‑Match Automation & Alerts

## Objective
Create an end‑to‑end daily pipeline that:
1. Pulls the latest fixture schedule and static xG data.
2. Runs the XGBoost model trained in Phase 3.
3. Filters predictions to the **Strong Tier** (P > 0.77 & P > bookmaker implied).
4. Sends a concise alert (email or webhook) for each qualifying match.
5. Logs the run for auditability.

## High‑Level Steps
| Step | Description |
|------|-------------|
| 1️⃣  | Add `run_daily.py` – compose the existing data pipeline (`run_baseline.py` feature extraction) and model inference. |
| 2️⃣  | Serialize the trained XGBoost model (`model.save_model('xgb_model.json')`) and load it in the script. |
| 3️⃣  | Implement **Strong Tier** filter (reuse logic from `train_xgb.py`). |
| 4️⃣  | Build an alert formatter – one‑line summary with date, teams, probability, and match URL. |
| 5️⃣  | Add configurable alert back‑ends in `config.json` (SMTP email, optional webhook). |
| 6️⃣  | Write daily results to `experiments_daily.csv` (append‑only). |
| 7️⃣  | Create a cron entry (`0 2 * * * /usr/bin/python3 /path/to/run_daily.py >> logs/daily.log 2>&1`). |

## Decisions & Assumptions
- **Data source**: We continue using the static CSV fixtures (`data.py`) and the synthetic xG dump from `xg_scraper.py`. No live odds API is required.
- **Model**: The XGBoost model trained in Phase 3 will be saved once (`xgb_model.json`) and re‑used daily to avoid retraining.
- **Alert Channels**: Email is the default; a webhook URL can be added later without code changes.
- **Scheduling**: UTC 02:00 is chosen to run before most European leagues’ weekend matches kick‑off.
- **Idempotency**: The script will check for existing `experiments_daily.csv` header and create it if missing.

## Acceptance Criteria
- `run_daily.py` executes without error on a fresh clone of the repo.
- At least one Strong Tier prediction is detected and an email is sent (or webhook POST) when such bets exist.
- `experiments_daily.csv` contains a row for each processed match with columns: date, home, away, prob_win, bookmaker_implied, tier.
- Cron job is installed and verified (`crontab -l` shows the entry).

## Risks & Mitigations
- **Rate‑limit on fixture source** – Use the existing CSV; no external API calls.
- **Email credentials leakage** – Store in `config.json` and add `.gitignore` entry to prevent committing secrets.
- **Model drift** – Schedule a quarterly retraining step (outside this phase).

## Next Actions
- Implement `run_daily.py` (see task file in DISCUSSION‑LOG).
- Add `config.json` entries for alerts.
- Add cron entry via `crontab -e`.
- Run a dry‑run locally for the upcoming weekend fixtures.
