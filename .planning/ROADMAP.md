# Project Roadmap

**Current Milestone:** v1.0 - High Hit-Rate Foundation (COMPLETE)
**Goal:** Build the Dixon-Coles and gradient boosting models to confidently predict 75%+ win probability matches.

## Phase 1: Dixon-Coles Implementation
**Goal:** Implement the Dixon-Coles model with time-weighting and low-score corrections.
- Status: Complete
- Dependencies: None
- Directory: 1

## Phase 2: Feature Engineering & xG Integration
**Goal:** Integrate xG-based form features and situational factors into the dataset.
- Status: Complete
- Dependencies: Phase 1
- Directory: 2

## Phase 3: Model Tuning & Strong Tier Calibration
**Goal:** Tune the Elo and gradient boosting models to isolate the "Strong" tier (75%+ hit rate).
- Status: Complete
- Dependencies: Phase 2
- Directory: 3

## Phase 4: Pivot Assessment
**Goal:** Evaluate hit rate ceiling. If insufficient, assess pivoting to lower-variance sports like Tennis/Basketball.
- Status: Cancelled (Goal achieved in Phase 3)
- Dependencies: Phase 3
- Directory: 4


## Phase 5: Pre-Match Automation & Alerts
**Goal:** Automate the daily data fetch, run the XGBoost predictor, and dispatch "Strong Tier" alerts (e.g. via email or webhook).
- Status: Planned
- Dependencies: Phase 3
- Directory: 5
