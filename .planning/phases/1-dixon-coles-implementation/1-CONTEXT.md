# Phase 1 Context: Dixon-Coles Implementation

## Domain
Implement the Dixon-Coles model with time-weighting and low-score corrections.

## Canonical Refs
- `PROJECT_OVERVIEW.md`

## Decisions Captured
### Parameter Estimation
- Use `scipy.optimize.minimize` (L-BFGS-B method) for Maximum Likelihood Estimation.

### Time-Weighting Decay
- Apply a time decay half-life of roughly 1.5 years (decay factor ~0.0065) to historical matches.

### Data Persistence
- Store the solved parameters (attack, defense, home advantage, rho) in `dixon_coles_params.json`.

## Code Context
- Will integrate with the existing data pipeline (`data.py`, `evaluate.py`) mentioned in `PROJECT_OVERVIEW.md`.
