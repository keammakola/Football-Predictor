# Phase 2 Context: Feature Engineering & xG Integration

## Domain
Integrate xG-based form features and situational factors into the dataset.

## Canonical Refs
- `PROJECT_OVERVIEW.md`

## Decisions Captured
### xG Data Sourcing
- **Hybrid Approach:** Use a static downloaded CSV dump for historical xG data, but dynamically scrape the current season's data (from Understat/FBref) during updates.

### xG Form Calculation
- **Use Both:** Calculate both simple rolling averages (e.g., last 5 games) and exponentially smoothed averages for xG form. Feed both into the downstream gradient boosting model to let it determine feature importance.

### Situational Factors
- **Rest Days:** Calculate days since the team's last match.
- **Injury/Availability:** Parse the daily snapshots from the existing `snapshots/` folder.
- **Travel Distance/Fatigue:** Factor in domestic vs European travel if the data can be sourced.

## Code Context
- Will integrate with the existing `data.py` pipeline.
- Requires building an xG scraping module and an injury snapshot parser (`injury_snapshot.py` is already in the workspace).
