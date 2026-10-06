---
wave: 1
depends_on: []
files_modified:
  - xg_scraper.py
  - data.py
  - features.py
autonomous: true
---

# Phase 2: Feature Engineering & xG Integration

## Goal
Integrate xG-based form features and situational factors into the dataset.

## Context
- **xG Data Sourcing:** Hybrid Approach (static CSV for history + dynamic scrape for current season).
- **xG Form Calculation:** Use Both (simple rolling average + exponential smoothing).
- **Situational Factors:** Rest Days, Injury/Availability snapshots, Travel Distance/Fatigue.

## Tasks

```xml
<task>
  <id>xg-scraper</id>
  <title>Build xG Scraper (Hybrid Mode)</title>
  <type>tracer</type>
  <read_first>
    - data.py
  </read_first>
  <instructions>
    1. Create `xg_scraper.py`.
    2. Implement a function to download/load a static CSV dump for historical xG data.
    3. Implement a dynamic scraper (using `requests`/`BeautifulSoup` or `pandas.read_html`) to fetch the current season's xG data from FBref or Understat.
    4. Merge the historical and dynamic data into a single DataFrame.
  </instructions>
  <acceptance_criteria>
    - `xg_scraper.py` contains a `get_xg_data()` function.
    - The function successfully returns a DataFrame containing historical and current season xG.
  </acceptance_criteria>
</task>

<task>
  <id>xg-features</id>
  <title>Calculate xG Form Features</title>
  <depends_on>xg-scraper</depends_on>
  <read_first>
    - data.py
    - features.py
  </read_first>
  <instructions>
    1. Create/update `features.py`.
    2. Implement simple rolling averages (e.g., last 5 games) for xG and xGA (xG Against) per team.
    3. Implement exponentially smoothed averages (EMA) for xG and xGA per team.
    4. Merge these features into the main matches DataFrame.
  </instructions>
  <acceptance_criteria>
    - `features.py` calculates both rolling and EMA xG features.
    - Output DataFrame contains columns like `xg_roll_5`, `xg_ema`.
  </acceptance_criteria>
</task>

<task>
  <id>situational-factors</id>
  <title>Integrate Situational Factors</title>
  <depends_on>xg-features</depends_on>
  <read_first>
    - injury_snapshot.py
    - features.py
  </read_first>
  <instructions>
    1. Update `features.py` to calculate "Rest Days" (days since last match) for both home and away teams.
    2. Parse the daily snapshots from the `snapshots/` folder (using `injury_snapshot.py` if applicable) to create availability metrics (e.g., key players missing).
    3. Add a basic "Travel Distance" or fatigue metric (e.g., played away in Europe mid-week).
    4. Merge all situational factors into the main matches DataFrame.
  </instructions>
  <acceptance_criteria>
    - Output DataFrame contains columns for rest days, injury availability score, and travel fatigue.
  </acceptance_criteria>
</task>
```

## must_haves
- truths:
  - `xg_scraper.py handles both historical CSVs and dynamic scraping`
  - `features.py calculates simple rolling averages for xG`
  - `features.py calculates exponentially smoothed averages for xG`
  - `Rest days are calculated for both teams`

## Artifacts this phase produces
- `xg_scraper.py`
- `features.py`
