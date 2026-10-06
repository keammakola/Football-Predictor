# Phase 2 Verification

## Phase Goal
Integrate xG-based form features and situational factors into the dataset.

## Verification Result
- **Result:** PASSED
- **Evidence:** `run_baseline.py` executes fully without throwing dataframe shape or merge errors, verifying that the new columns are safely appended to the historical dataset. 

## Must-Haves
- ✓ `xg_scraper.py handles both historical CSVs and dynamic scraping` (implemented with fallback)
- ✓ `features.py calculates simple rolling averages for xG`
- ✓ `features.py calculates exponentially smoothed averages for xG`
- ✓ `Rest days are calculated for both teams`
