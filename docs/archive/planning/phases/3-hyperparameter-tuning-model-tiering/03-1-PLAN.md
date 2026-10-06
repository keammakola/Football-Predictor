---
wave: 1
depends_on: []
files_modified:
  - train_xgb.py
  - requirements.txt
autonomous: true
---

# Phase 3: Hyperparameter Tuning & Model Tiering

## Goal
Train the XGBoost model using the engineered features and isolate the "Strong Tier" parameters for >75% accuracy.

## Context
- **Model Choice:** XGBoost.
- **Hit-Rate Isolation (Tiering):** Probability + Odds Edge (Match must have a high baseline win probability AND positive expected value against the bookmaker's closing line).
- **Evaluation Metric:** Log Loss strictly during training.

## Tasks

```xml
<task>
  <id>xgb-setup</id>
  <title>Setup XGBoost and Training Pipeline</title>
  <type>tracer</type>
  <read_first>
    - run_baseline.py
    - features.py
  </read_first>
  <instructions>
    1. Add `xgboost` to `requirements.txt`.
    2. Create `train_xgb.py`.
    3. Import the data processing logic from `run_baseline.py` (load matches, engineer xG/situational features, elo features).
    4. Implement an XGBoost classifier (using `XGBClassifier`).
    5. Set the objective to `multi:softprob` and evaluate using `mlogloss` on the validation set.
    6. Select features: Elo diff, xG rolling averages, EMA, rest days, travel fatigue.
  </instructions>
  <acceptance_criteria>
    - `xgboost` is in `requirements.txt`.
    - `train_xgb.py` successfully trains an XGBoost model and outputs the log loss on the test set.
  </acceptance_criteria>
</task>

<task>
  <id>model-tiering</id>
  <title>Implement Strong Tier Isolation</title>
  <depends_on>xgb-setup</depends_on>
  <read_first>
    - train_xgb.py
    - evaluate.py
  </read_first>
  <instructions>
    1. Update `train_xgb.py` to extract the predicted probabilities for the test set.
    2. Implement the "Strong Tier" logic:
       - Condition A: XGBoost predicted probability > `0.60` (or similar high threshold).
       - Condition B: XGBoost predicted probability > Bookmaker implied probability (Positive EV).
    3. Filter the test set predictions to only include matches that pass both conditions.
    4. Calculate and print the Hit Rate (Accuracy) exclusively for the Strong Tier.
  </instructions>
  <acceptance_criteria>
    - `train_xgb.py` prints the number of matches in the Strong Tier and their Hit Rate.
    - Tiering logic explicitly checks the bookmaker market probabilities.
  </acceptance_criteria>
</task>
```

## must_haves
- truths:
  - `requirements.txt contains xgboost`
  - `train_xgb.py uses XGBClassifier`
  - `train_xgb.py optimizes for log loss`
  - `Strong Tier logic checks against bookmaker odds`

## Artifacts this phase produces
- `train_xgb.py`
