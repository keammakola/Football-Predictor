# Phase 1 Verification

## Phase Goal
Implement the Dixon-Coles model with time-weighting and low-score corrections.

## Verification Result
- **Result:** PASSED
- **Evidence:** `run_baseline.py` outputs predictions from `dixon_coles.py` alongside Elo, properly applying the rho correction and exponential time decay. Log loss was evaluated (0.9644).

## Must-Haves
- ✓ `dixon_coles.py contains scipy.optimize.minimize` (using SLSQP)
- ✓ `dixon_coles.py handles the rho correction for 0-0, 1-0, 0-1, 1-1`
- ✓ `Time decay factor is applied to historical matches`
