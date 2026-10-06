# How the Prediction Model Calculates Odds

Football Match Predictor · design specification

## 1. Purpose and terminology

This document specifies, step by step, how the model turns historical data into **probabilities** and then into **odds** for a Premier League match. It is the reference for implementation and for checking that the code does what it should.

| Term | Meaning |
| --- | --- |
| Probability | The model's estimate that an outcome happens, between 0 and 1 (for example 0.55) |
| Fair odds | The odds that exactly match a probability, with no bookmaker margin: `fair decimal odds = 1 / probability` |
| Implied probability | The probability hidden inside someone else's odds: `1 / decimal odds` |
| Overround (margin) | The bookmaker's built-in edge. Implied probabilities across all outcomes add up to more than 1 |
| Edge | Model probability minus market probability (after removing the margin) |
| Calibration | Whether a stated 70% really happens about 70% of the time |

**The model's primary output is probabilities.** Odds are a presentation of those probabilities (fair odds) and a way to compare the model with the market. The model does not try to copy bookmaker odds, and it does not add a margin of its own.

## 2. The pipeline at a glance

1. **Inputs:** only information available before kickoff.
2. **Team strength:** Elo ratings, updated match by match.
3. **Goals model:** Dixon-Coles gives an expected-goals pair and a full scoreline distribution, from which win, draw and loss probabilities are summed.
4. **Feature model:** a 3-class gradient-boosted classifier uses Elo, form, rest days, home/away splits and later injury features.
5. **Ensemble:** the models' probabilities are combined.
6. **Calibration:** the combined probabilities are corrected so they match real frequencies.
7. **Odds conversion:** fair odds, plus comparison against the margin-free market.
8. **Confidence tiers:** Strong, Lean or No clear edge.
9. **Output and validation.**

Each stage can be tested on its own, and each later stage must beat or at least match the one before it on out-of-sample log loss, otherwise it is not kept.

## 3. Step 1: Inputs and the leakage rule

**The rule:** every number used to predict a match must have been knowable before kickoff.

Allowed:

- Results of all earlier matches
- Ratings and form computed only from earlier matches
- Rest days, which come from the fixture calendar
- The latest availability snapshot taken before kickoff
- Opening odds, if used as a feature (see section 12)

Not allowed:

- Anything from the match itself (score, shots, cards)
- Season-final tables or season-total statistics for an in-season match
- Injury information published after kickoff
- Closing odds as a feature unless they were genuinely available at prediction time

Implementation: build features by walking through matches in date order, recording each match's features **before** updating any state with its result. The automated leakage test changes later results and checks that earlier features do not move.

## 4. Step 2: Elo team strength

Elo gives each team a rating that rises when it does better than expected and falls when it does worse.

**Pre-match gap**

```
elo_diff = rating_home - rating_away + home_advantage
```

Current settings: every team starts at 1500 (unseen or promoted teams at 1450), home advantage 60 points, K = 20.

**Expected score for the home side**

```
expected_home = 1 / (1 + 10 ^ (-elo_diff / 400))
```

This counts a draw as half a win, so it is **not** a win probability by itself.

**Update after the match**

```
actual_home = 1 (win), 0.5 (draw), 0 (loss)
multiplier  = ln(|goal difference| + 1) + 1   for decisive results, 1.0 for draws
delta       = K * multiplier * (actual_home - expected_home)
rating_home += delta
rating_away -= delta
```

The multiplier makes big wins move ratings more than narrow ones, with diminishing returns.

**Between seasons:** pull every rating 25% of the way toward the league mean, because squads change and early-season ratings should be less certain.

**From Elo gap to three outcomes.** A multinomial logistic regression is fitted on `elo_diff` using training seasons only. It learns how win, draw and loss probabilities change with the gap, so the draw probability comes from data. The draw probability should peak when teams are evenly matched and shrink as the gap grows. If the fitted draw curve does not behave that way, something is wrong.

**Role in the system:** Elo is both a standalone baseline model and a feature for the gradient-boosted model.

## 5. Step 3: The goals model (Dixon-Coles)

This model predicts goals, not results, so one fit gives win, draw and loss probabilities, scorelines, over/under and both-teams-to-score.

### 5.1 Expected goals for each side

Every team has an **attack** rating and a **defence** rating (higher defence rating = concedes more, or use the reverse, as long as it is consistent). Using logs so everything stays positive:

```
lambda_home = exp(base + home_adv + attack[home] - defence[away])
lambda_away = exp(base +            attack[away] - defence[home])
```

`lambda` is the expected number of goals. `home_adv` is shared across teams at first and can be made team-specific later.

### 5.2 Scoreline probabilities

Goals are modelled as Poisson, with a correction for low scores:

```
P(home goals = x, away goals = y) = tau(x, y) * Poisson(x; lambda_home) * Poisson(y; lambda_away)
```

Plain Poisson treats the two sides as independent and underestimates 0-0 and 1-1 and overestimates 1-0 and 0-1. The Dixon-Coles correction `tau` fixes this using one parameter `rho` (usually small and negative):

| Scoreline | tau |
| --- | --- |
| 0-0 | 1 - lambda\_home \* lambda\_away \* rho |
| 0-1 | 1 + lambda\_home \* rho |
| 1-0 | 1 + lambda\_away \* rho |
| 1-1 | 1 - rho |
| all others | 1 |

`rho` must be bounded so no `tau` goes negative.

### 5.3 Fitting

- Estimate all attack and defence ratings, `base`, `home_adv` and `rho` by **maximum likelihood** over past matches (for example with `scipy.optimize`).
- **Time-weight** each match by `exp(-xi * days_ago)`. A value of about 0.0019 per day gives a half-life near one year: a match from 365 days ago counts about half as much as one from today, and a match from two years ago about a quarter. Choose `xi` by validation log loss, not by feel.
- Add a constraint so ratings are identifiable (for example, average attack rating fixed).
- Promoted teams get ratings shrunk toward the league average until they have played enough matches.
- Refit on a schedule (weekly or monthly), always using only matches before the prediction date.

### 5.4 From the score matrix to outcome probabilities

Build a grid of scorelines from 0-0 up to 10-10, normalise it so it sums to 1, then add:

```
P(home win) = sum of cells where home goals > away goals
P(draw)     = sum of the diagonal
P(away win) = sum of cells where home goals < away goals
```

### 5.5 Worked example

Inputs: expected goals `lambda_home = 1.75`, `lambda_away = 0.95`, `rho = -0.08` (illustrative numbers).

|  | Home win | Draw | Away win |
| --- | --- | --- | --- |
| Plain Poisson | 56.2% | 23.5% | 20.3% |
| Dixon-Coles | 55.3% | 25.3% | 19.4% |

The correction moves about two points of probability into the draw. Fair odds from the Dixon-Coles row: home 1.81, draw 3.96, away 5.15.

Most likely scorelines: 1-1 (12.1%), 1-0 (10.9%), 2-0 (10.3%), 2-1 (9.8%), 0-0 (7.6%), 3-0 (6.0%). Derived markets from the same grid: over 2.5 goals about 50.6%, both teams to score about 51.6%.

## 6. Step 4: The feature-based classifier

A gradient-boosted model (LightGBM or similar) predicts the three outcomes directly from engineered features.

**Target:** home win / draw / away win.

**Candidate features (add one group at a time, keep only what improves validation log loss):**

- Elo gap, and each team's own Elo
- Dixon-Coles attack/defence ratings and expected goals
- Rolling form (goals, xG if available, points) over the last 5 and 10 matches, recency-weighted
- Home-only and away-only form
- Rest days and matches in the last 14 days
- Season stage, and a promoted-team flag
- Match importance (derived from the table and games remaining)
- Availability features from the injury snapshots (section 11)

**Training rules**

- Walk-forward: train on seasons before the validation season, tune on the validation season, test once on the final season.
- Use a multiclass log-loss objective, early stopping on the validation season, and shallow trees with strong regularisation. With about 380 matches per season, complexity overfits quickly.
- Fix random seeds and log every run.

## 7. Step 5: Combining models

Start simple. Linear pooling takes a weighted average of each outcome's probability:

```
p_final = w1 * p_elo + w2 * p_dixon_coles + w3 * p_boosted      (weights >= 0, sum to 1)
```

Example with weights 0.3 / 0.4 / 0.3 and home-win probabilities 0.62, 0.58 and 0.66 gives 0.616. Doing this for all three outcomes (draw 0.226, away 0.158) keeps the result summing to 1.

Choose weights by minimising log loss on the validation season, with a floor so no model is dropped entirely. Equal weights are a good default if the optimised weights are unstable. Stacking with a small logistic regression is a later option.

**Model agreement** is recorded separately for the tiers: the models agree if they pick the same most-likely outcome and their probabilities for that outcome are within 0.10 of each other.

## 8. Step 6: Calibration

A model can rank outcomes well and still be over- or under-confident. Calibration fixes the numbers.

- **Check first:** group all predictions by stated probability (0-20%, 20-30% and so on) and compare to how often the outcome really happened.
- **If miscalibrated:** use temperature scaling (one parameter that sharpens or softens all probabilities), or isotonic or Platt calibration per outcome followed by renormalising so the three probabilities sum to 1. Temperature scaling is the safest with limited data.
- **Data rule:** fit the calibrator on predictions the model did not train on (out-of-fold or the validation season), never on the final test season.
- **Re-check after calibrating,** and report the calibration table with the number of matches in each bucket.

Probabilities should also be clipped to a sensible range (for example 0.01 to 0.97) so a single overconfident error cannot dominate log loss, then renormalised.

## 9. Step 7: Converting probabilities to odds

### 9.1 Fair odds

```
fair decimal odds = 1 / probability
```

| Probability | Decimal | Fractional (approx.) | American (approx.) |
| --- | --- | --- | --- |
| 0.553 | 1.81 | 4/5 | -123 |
| 0.253 | 3.96 | 3/1 | +296 |
| 0.194 | 5.15 | 4/1 | +415 |

American odds: for decimal odds of 2.00 or more, `(decimal - 1) * 100`; below 2.00, `-100 / (decimal - 1)`.

The three probabilities sum to 1, so fair odds contain **no margin**. A bookmaker's odds for the same match will be shorter because of their margin.

### 9.2 Removing the margin from market odds

To compare with the market, first strip out the bookmaker margin.

Example bookmaker odds: home 1.60, draw 4.20, away 5.50.

```
implied: 0.625, 0.238, 0.182     (sum = 1.045, so overround = 4.5%)
```

- **Proportional (default):** divide each implied probability by the sum: 59.8%, 22.8%, 17.4%.
- **Power method (alternative):** raise each implied probability to a power `k` so they sum to 1 (here about k = 1.049): 61.1%, 22.2%, 16.7%. It takes slightly more margin off longshots, which is closer to how margins are often applied.

Pick one method, use it everywhere, and use the same method when benchmarking log loss.

### 9.3 Edge and expected value

```
edge = model probability - margin-free market probability
expected value per unit staked at the market odds = model probability * market decimal odds - 1
```

Using the Dixon-Coles example against the market above:

|  | Home | Draw | Away |
| --- | --- | --- | --- |
| Model | 55.3% | 25.3% | 19.4% |
| Market (margin removed) | 59.8% | 22.8% | 17.4% |
| Edge | -4.5 pts | +2.5 pts | +2.0 pts |
| Expected value at market odds | -11.5% | +6.2% | +6.7% |

**How to read this:** a positive number does not mean a good bet. It means the model disagrees with the market, and the market is usually the more accurate of the two. A model that likes draws and longshots more than the market is a common pattern when the model is simply miscalibrated at the extremes (the favourite-longshot bias). Edges only count after the backtest shows that large model-versus-market disagreements historically paid off, with enough matches to trust the result. If money is ever involved, only risk what you can afford to lose. I'm not a financial advisor, and this document describes an analysis tool, not a betting system.

## 10. Step 8: Confidence tiers and uncertainty

Tiers use the final calibrated probabilities (thresholds in `config.py`, to be re-chosen from the backtest):

| Tier | Top probability | Lead over second-best | Extra conditions to add |
| --- | --- | --- | --- |
| Strong | at least 0.60 | at least 0.25 | Models agree; no downgrade flag |
| Lean | at least 0.50 | at least 0.15 | Models agree or only mildly disagree |
| No clear edge | everything else |  |  |

**Downgrade flags** (drop one tier when any apply): early season (a team has played fewer than about 8 matches), a newly promoted team, a high injury load on either side, or the model and the margin-free market disagreeing by more than about 10 points on the top outcome.

**Uncertainty to report alongside the tier:** the spread across the ensemble's models, and optionally a bootstrap interval from refitting on resampled history.

**Honesty checks for each tier:** report the number of matches in it and its real hit rate on unseen seasons. A tier with fewer than about 30 matches is shown but not trusted. Draws almost never reach Strong or Lean, and that is correct.

## 11. Injury and availability adjustments

**Preferred route (feature-based):** from the daily snapshot, build features per team: total market value or minutes share of unavailable players, and counts of unavailable regulars by position (goalkeeper, defence, midfield, attack). Join the **latest snapshot before kickoff** and let the boosted model learn the effect from history. This only works once enough snapshots exist.

**Interim route (adjustment to expected goals):** if there is no history yet, scale each side's expected goals by a factor that depends on the importance of the missing players, for example reduce attack `lambda` for a missing top scorer and raise the opponent's `lambda` for a missing goalkeeper or defenders. The factors must be estimated from data or kept very small, because invented factors are just opinions. Label outputs that use this route as lower confidence.

**Weighting rule:** never count injuries; weight by importance. A first-choice goalkeeper or leading scorer matters far more than a rotation player.

## 12. Market odds as an input

Two separate uses, kept apart:

1. **As a benchmark (always):** compare model log loss with the margin-free market's on the same matches.
2. **As a feature (optional, decide deliberately):** opening odds or odds movement carries news the model cannot see (lineups, injuries). The drawback is that the model then leans on the market, so beating the market stops being a meaningful test. If used, use **opening** odds only, and report results with and without them.

## 13. Output specification

For each match, the model returns:

| Field | Description |
| --- | --- |
| P(home), P(draw), P(away) | Calibrated probabilities, summing to 1 |
| Fair odds | `1 / probability` for each outcome |
| Expected goals | `lambda_home`, `lambda_away` from the goals model |
| Top scorelines | Highest-probability scorelines with their probabilities |
| Derived markets | Over/under 2.5, both teams to score |
| Tier | Strong, Lean or No clear edge, with downgrade flags |
| Model agreement | Number of models agreeing, and the spread |
| Market comparison | Margin-free market probabilities and the edge, when odds are available |
| Data quality notes | Early season, promoted team, high injury load, stale snapshot |

The interface should show probabilities and tiers, never a bare "X will win".

## 14. Validation

**Metrics (computed on seasons the model never trained on)**

```
log loss = -average( ln(probability given to the outcome that happened) )
Brier    = average( sum over outcomes of (probability - actual)^2 ),  actual = 1 or 0
```

Ranked probability score is a useful extra, because the outcomes are ordered (away, draw, home). Accuracy is reported but treated as secondary, since draws cap it.

**Splits:** train on earlier seasons, tune on one validation season, test once on the final season. Never split randomly.

**Pass conditions (set before seeing results)**

- Log loss within about 0.01 of the margin-free market
- Calibration table close to the diagonal
- Strong hits more than Lean, and both match their stated confidence
- Three-way accuracy around 50-55%; far higher means look for a leak

**Automatic sanity checks**

- The three probabilities sum to 1 (within a tiny tolerance) and each lies in the clipped range
- Swapping the teams and removing home advantage mirrors the probabilities
- Raising the home team's rating raises P(home) and lowers P(away)
- The same inputs always give the same outputs (fixed seeds)
- The leakage test passes

## 15. Failure modes and guardrails

| Problem | Guard |
| --- | --- |
| Leakage | Date-ordered feature building and the leakage test |
| Overconfidence | Calibration, clipping, and shallow regularised models |
| Too few matches for tiers | Report sample sizes; do not trust tiers under about 30 matches |
| Overfitting to the test season | Test season used once, at the very end |
| Market-chasing | Edges are only trusted after a backtest of model-versus-market disagreements |
| Stale data | Snapshot date shown; flag outputs when the latest snapshot is old |
| Drift | Time-weighting, scheduled refits, season regression |
| Silent bugs in name joins | Canonical team names and a name audit |

## 16. Implementation map

| Component | File | Status |
| --- | --- | --- |
| Data loading, market probabilities with margin removed | `data.py` | Built |
| Elo features | `elo.py` | Built |
| Elo-to-probabilities (logistic regression), baseline | `run_baseline.py` | Built |
| Metrics, calibration table, tiers, market gap | `evaluate.py` | Built |
| Injury snapshot | `injury_snapshot.py` | Built, untested against the live feed |
| Dixon-Coles fit and score matrix | `dixon_coles.py` | To build |
| Feature builder and boosted model | `features.py`, `boosted.py` | To build |
| Ensemble and calibration | `ensemble.py`, `calibrate.py` | To build |
| Odds conversion and market comparison | `odds.py` | To build |
| Prediction output and UI | `predict.py`, Streamlit app | To build |

**Suggested next step:** build `dixon_coles.py` and `odds.py` first. Together they give proper draw probabilities, scorelines and fair odds, and they reproduce the worked example in section 5.5, which makes a good first test.
