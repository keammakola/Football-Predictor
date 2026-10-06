---
wave: 1
depends_on: []
files_modified:
  - dixon_coles.py
  - run_baseline.py
autonomous: true
---

# Phase 1: Dixon-Coles Implementation

## Goal
Implement the Dixon-Coles maximum likelihood estimation model for Premier League matches, including time-weighting (decay) and the low-score correlation parameter.

## Context
- **Decisions:** Use `scipy.optimize.minimize` (L-BFGS-B method) for MLE estimation.
- **Time decay:** Half-life of 1.5 years (decay factor ~0.0065).
- **Persistence:** Save solved parameters in `dixon_coles_params.json`.

## Tasks

```xml
<task>
  <id>dc-model</id>
  <title>Implement Dixon-Coles Core</title>
  <type>tracer</type>
  <read_first>
    - data.py
    - evaluate.py
  </read_first>
  <instructions>
    1. Create `dixon_coles.py`.
    2. Implement the log-likelihood function for Dixon-Coles, incorporating the rho parameter (low-scoring match correction) and a time decay factor `xi = 0.0065`.
    3. Use `scipy.optimize.minimize(method='L-BFGS-B')` to fit the parameters (attack arrays, defense arrays, home advantage, rho) on historical matches.
    4. Implement a function to calculate probabilities for Home, Draw, Away for two teams given their fitted parameters.
    5. Save/load the parameters to/from `dixon_coles_params.json`.
  </instructions>
  <acceptance_criteria>
    - `dixon_coles.py` contains `fit_dixon_coles` and `predict_match` functions.
    - `fit_dixon_coles` successfully optimizes using `scipy.optimize.minimize`.
    - Probability predictions sum to 1.0.
  </acceptance_criteria>
</task>

<task>
  <id>dc-eval</id>
  <title>Evaluate Dixon-Coles</title>
  <depends_on>dc-model</depends_on>
  <read_first>
    - run_baseline.py
    - evaluate.py
  </read_first>
  <instructions>
    1. Update `run_baseline.py` to evaluate the Dixon-Coles model in a walk-forward manner.
    2. Compare Brier score and log loss of Dixon-Coles vs market odds vs existing Elo.
  </instructions>
  <acceptance_criteria>
    - `run_baseline.py` runs Dixon-Coles evaluation and prints the Brier score.
    - Evaluation successfully completes without crashing.
  </acceptance_criteria>
</task>
```

## must_haves
truths:
  - `dixon_coles.py contains scipy.optimize.minimize`
  - `dixon_coles.py handles the rho correction for 0-0, 1-0, 0-1, 1-1`
  - `Time decay factor is applied to historical matches`

## Artifacts this phase produces
- `dixon_coles.py`
- `dixon_coles_params.json`
