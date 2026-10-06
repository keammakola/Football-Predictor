# Phase 3 Context: Hyperparameter Tuning & Model Tiering

## Domain
Train the XGBoost model using the engineered features and isolate the "Strong Tier" parameters for >75% accuracy.

## Canonical Refs
- `PROJECT_OVERVIEW.md`

## Decisions Captured
### Model Choice
- **XGBoost:** Selected for its speed, robust handling of missing data, and industry-standard performance on tabular data.

### Hit-Rate Isolation (Tiering)
- **Probability + Odds Edge:** The "Strong Tier" will not rely solely on our model's probability cutoff. A match must exhibit *both* a high baseline win probability AND positive expected value (an edge) against the bookmaker's closing line to qualify for the Strong Tier.

### Evaluation Metric
- **Log Loss:** The model will be strictly optimized for Log Loss (multiclass `mlogloss` for H/D/A) during training. This ensures perfectly calibrated probabilities. The tiering and thresholding logic will be applied *after* training, rather than using a custom training objective that could skew calibration.

## Code Context
- Requires adding `xgboost` to requirements.
- Will create a new `train_xgb.py` script or integrate into the evaluation pipeline.
