# Plan Summary: 01-1-PLAN

## Outcome
Successfully implemented the Dixon-Coles model and integrated it into the evaluation pipeline.

## Work Completed
- **`dixon_coles.py`:** Created with `fit_dixon_coles` (using SLSQP with alpha mean constraint) and `predict_match` (handling rho corrections). Time decay factor applied.
- **`run_baseline.py`:** Updated to fit Dixon-Coles on the training set and predict the evaluation season.
- **`dixon_coles_params.json`:** Successfully wrote fitted parameters to disk.

## Verification
- Dixon-Coles successfully executes the `SLSQP` optimization.
- Probabilities cleanly sum to 1.0.
- Log Loss: 0.9644 (Worse than Elo's 0.9395, likely due to static time-decay vs Elo's dynamic match-by-match updating).
