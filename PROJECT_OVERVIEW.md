# Football Match Predictor: Full Project Document

A free, locally run model that predicts **home win / draw / away win** probabilities for Premier League matches and flags the matches it feels strongly about.

---

## 1. Decisions made so far

| Decision | Choice |
|---|---|
| Prediction target | Three-way: P(home), P(draw), P(away). Draws are predicted, not removed |
| Extra output | A "strong call" layer that labels matches the model is confident about (win or loss) |
| Cost | Completely free: free data, free tools, own machine (Colab as backup) |
| Scope | Premier League only, one model family at a time |
| Injury/availability data | Free API route: daily snapshots of the Fantasy Premier League feed |
| Purpose | **Still to fill in:** learning, portfolio, or something you'd act on |

---

## 2. What the model outputs

For each match:

- **P(home win) / P(draw) / P(away win)**
- **Tier label:** Strong, Lean, or No clear edge
- Later additions: expected goals, likely scorelines, how many models agree, and the market's probability alongside the model's

### Why probabilities, not picks
A calibrated 55 / 25 / 20 carries far more information than "home win". It also lets you test honesty: when the model says 70%, the outcome should happen about 70% of the time.

### How "strong" is defined
Tiers combine two rules (thresholds live in `config.py`):

| Tier | Top probability | Lead over second-best outcome |
|---|---|---|
| Strong | at least 0.60 | at least 0.25 |
| Lean | at least 0.50 | at least 0.15 |
| No clear edge | everything else | |

These starting values are guesses. They should be re-chosen from the backtest so each tier's real hit rate is something you can state. Planned additions to the definition: models agree on the side, and early-season / promoted-team / key-player-doubt matches get downgraded.

Draws almost never reach high probability, so Strong and Lean calls will nearly always be home or away. That is correct behaviour, so don't force draws into the tiers.

---

## 3. Realistic expectations

These figures are approximate, from general knowledge, and should be checked against your own backtest.

- **Base rates with no team information:** roughly 45% home / 26% draw / 29% away in most leagues. A uniform 33/33/33 is the "know nothing about football" guess and is a weaker baseline.
- **Three-way accuracy:** about 50-55% for a good model. Bookmaker closing odds sit around 52-56%. Consistently above about 57% should make you suspect leakage or a bug.
- **Win-vs-lose only (draws removed):** about 68-72% is plausible, but that's an easier question, not a better model.
- **Strong tier:** if calibrated, picks rated 70%+ should win about 70-75% of the time, but only about 10-15% of fixtures reach that level, and roughly one in four still loses.
- **72% is not an overall target.** Chasing an accuracy number pushes you towards overfitting. Targets should be verifiable: log loss near the market, calibration, and tier hit rates.
- **The market is very efficient.** Matching bookmaker log loss is already a strong result. Beating it consistently is unlikely. If money is ever involved, only risk what you can afford to lose. This project is an analysis tool, not financial advice.

---

## 4. Success criteria (written before results)

1. Log loss on unseen seasons within 0.01 of the bookmaker closing odds (margin removed). *This is a documented target: the script prints the gap, but doesn't enforce it automatically.*
2. Calibrated: matches rated about 70% happen about 70% of the time.
3. "Strong" hits more often than "Lean", and each tier matches its stated confidence.
4. Overall three-way accuracy around 50-55%.
5. Every tier reported with its sample size. Tiers under 30 matches aren't trusted.

Don't edit these after seeing results.

---

## 5. Data sources (all free)

| Need | Source | Notes |
|---|---|---|
| Historical results + bookmaker odds | football-data.co.uk CSVs | Bulk download, decades of Premier League data. Backbone of the build |
| Team strength | Computed Elo (ClubElo is an alternative) | Built from the results |
| Upcoming fixtures (later) | football-data.org free tier | Reported as 12 competitions, delayed scores, 10 calls/minute. One source said 30/minute, so assume 10 |
| Injuries / availability | Fantasy Premier League feed (unofficial) | Premier League only. Status, news note, chance of playing |
| Lineups (optional, later) | API-Football free tier | Reported 100 requests/day cap |
| xG / advanced stats (optional) | StatsBomb open data, FBref, Understat | Check scraping terms first |
| Weather (optional) | Open-Meteo | Free, no key. Small effect |

Free tiers and terms change. Verify each source's terms yourself before depending on it, and keep each source behind its own swappable function.

---

## 6. Method

### 6.1 Build order
1. Start the daily availability snapshot (can't be backfilled)
2. Download about 10 seasons of Premier League CSVs
3. League-frequency baseline: the number every model must beat
4. Elo model (built)
5. Dixon-Coles with time-weighting (planned): proper draw probabilities and scorelines
6. Gradient boosting on engineered features, added one at a time (planned)
7. Calibration and market benchmark
8. Streamlit UI
9. Injury features, once a few months of snapshots exist

### 6.2 Elo model (as implemented)

- Every team starts at 1500, except unseen/promoted teams at 1450.
- Pre-match difference: `elo_diff = rating_home − rating_away + home_advantage (60)`
- Expected home score: `1 / (1 + 10^(−elo_diff / 400))`. This counts a draw as half a win, so it is not a win probability by itself.
- After the match: `delta = K × multiplier × (actual − expected)`, with K = 20 and actual = 1 / 0.5 / 0 for win / draw / loss.
- Goal-difference multiplier: `ln(|goal difference| + 1) + 1` for decisive results, 1.0 for draws.
- Between seasons, ratings regress 25% toward the mean.

### 6.3 From rating gap to three-way probabilities
A multinomial logistic regression is fitted on `elo_diff`, using training seasons only. It learns how draw probability changes with the rating gap, so the draw model comes from data instead of guesswork.

### 6.4 Illustration (made-up numbers)
Home 1800, away 1650, home advantage 60 → gap 210 → expected score about 0.77. With a draw probability near 20%, that gives roughly 67% / 20% / 13%. Real values come from the fitted model.

### 6.5 Planned improvements
- **Dixon-Coles:** attack/defence ratings per team plus a low-score correction (plain Poisson underestimates 0-0, 1-0, 0-1, 1-1). Draw probability falls out of the scoreline distribution. Time-weighting handles model drift.
- **Gradient boosting (3-class):** add features one at a time, keeping only those that improve out-of-sample log loss.
- **Ordinal alternative:** treat outcomes as ordered (away < draw < home).
- **Ensemble:** combine models, and use agreement between them as part of the Strong tier.

---

## 7. Features and factors that can shift the weighting

**Derivable from results data (start here)**
- Home advantage per team (varies, and dipped in the empty-stadium 2020/21 season)
- Rest days and fixture congestion
- Goal difference and xG-based form, not just points
- Season stage and early-season uncertainty
- Promoted teams (weaker, more uncertain starting ratings)

**Needs some work**
- Manager changes (evidence mixed, so test it)
- Match importance (title, relegation, nothing to play for)
- Derbies and rivalries
- Travel distance
- Weather
- Referee tendencies (mostly cards and penalties)
- Transfer-window squad value changes

**Market information**
- Opening vs closing odds movement. Late moves often reflect injury and lineup news. The CSVs include both for many leagues.

**Suggested priority:** team strength → home advantage → rest days → xG-based form → match importance → injuries → odds movement → the rest, tested one at a time.

**Weak signals people overrate:** head-to-head history, "momentum", big-name players. Test them before trusting them. Recency weighting often helps more than adding new inputs.

### Turning injuries into weightings
Don't count injuries. Weight by importance: sum the lost value (market value or share of team minutes) of unavailable players, separately for goalkeeper, defence, midfield and attack. Goalkeepers and top scorers matter far more than the average squad player.

---

## 8. Injury / availability pipeline

**`injury_snapshot.py`** calls the unofficial Fantasy Premier League endpoint (no key) and saves a dated CSV in `snapshots/`.

- Columns kept: id, name, team, position type, status, news, news added, chance of playing next round, cost, minutes, total points, snapshot date
- Status codes: `a` available, `d` doubtful, `i` injured, `s` suspended, `u` unavailable, `n` not in squad
- All players are kept (not just injured), so absences can be weighted by importance later
- Unofficial and undocumented: field names can change without notice
- Not tested against the live endpoint in my sandbox (no internet), so run it once yourself

**`.github/workflows/snapshot.yml`** runs it daily at 06:00 UTC on GitHub Actions and commits new CSVs. Trigger it once manually. If the feed rejects GitHub's servers, run the script locally with cron or Task Scheduler instead. Check GitHub's current free-minutes limits for private repos.

**The key limitation:** current feeds only give today's snapshot. History starts the day you start running it, so train the base model without injury features and add them after a few months. Alternatives or supplements: proxies from historical data (regulars' minutes in recent matches, squad market value, fixture congestion) and odds as an injury-aware signal.

Join rule: for each match, use the latest snapshot taken **before** kickoff.

---

## 9. Pitfalls and how the project guards against them

| Risk | Guard |
|---|---|
| **Leakage** (features using post-kickoff information) | Features recorded before the Elo update; `tests/test_no_leakage.py` alters later results and checks earlier features don't move |
| Random splits | Train on seasons before the validation season; validate on one season; test season touched once |
| Tuning on the test set | Test season only via `--final`, with an on-screen warning |
| Small samples (about 380 matches/season) | `MIN_TIER_SAMPLE` warning; report n per tier; don't over-read one season |
| Overfitting with many features | Add one at a time; keep only if out-of-sample log loss improves |
| Silent join failures from team names | `team_names.py` aliases and `--audit` listing |
| Raw data being modified | Downloads never overwrite; cleaning happens in code |
| Model drift (tactics, rules, empty stadiums) | Season regression now; time-weighting with Dixon-Coles later |
| Fooling yourself after the fact | Success criteria written first; every run logged to `experiments.csv` |
| Overconfidence | Output probabilities and tiers, never "X will win" |
| Source terms changing | README terms checklist; one swappable function per source |

---

## 10. Code reference

```
football_predictor/
├── README.md                  purpose, success criteria, checklist, run steps
├── config.py                  all settings in one place
├── data.py                    download (never overwrite) + load/clean + market probabilities
├── team_names.py              canonical names, aliases, audit helper
├── elo.py                     walk-forward Elo features
├── evaluate.py                log loss, Brier, accuracy, calibration, tiers, market gap
├── run_baseline.py            end-to-end baseline run
├── injury_snapshot.py         daily availability snapshot
├── requirements.txt           pandas, numpy, scikit-learn, requests, pytest
├── data/raw/                  untouched downloads
├── snapshots/                 dated availability CSVs
├── tests/
│   ├── test_no_leakage.py     leakage, date-order and time-split checks
│   └── make_fake_data.py      fake data for an offline dry run
└── .github/workflows/snapshot.yml   free daily snapshot job
```

### Key behaviours
- **`data.py`:** reads football-data.co.uk CSVs, canonicalises team names, sorts by date, and builds market probabilities from the best available odds columns (Pinnacle closing, Bet365 closing, then pre-match versions), normalised to remove the bookmaker margin.
- **`elo.py`:** returns the matches with `elo_home`, `elo_away` and `elo_diff` columns computed before each match's result is used.
- **`evaluate.py`:** multiclass log loss and Brier score, accuracy, calibration table (predicted-probability bucket vs actual frequency), tier table with hit rates and sample sizes, and gap to the market.
- **`run_baseline.py`:** compares league frequencies vs Elo; prints metrics, calibration and tiers; appends to `experiments.csv`.

### Settings in `config.py`
Seasons list, validation season (2023/24) and test season (2024/25), Elo parameters (start 1500, new team 1450, K 20, home advantage 60, season regression 0.25), tier thresholds, minimum tier sample (30), seed (42).

### Running it
```
pip install -r requirements.txt
python tests/test_no_leakage.py          # must pass
python run_baseline.py --download        # once
python run_baseline.py --audit           # check team names
python run_baseline.py                   # evaluate on the validation season
python run_baseline.py --final           # one time only, at the very end
```

### Testing status
The leakage tests pass and the full pipeline ran end to end on **fake** data. It has not been run on real downloads, because my sandbox had no internet. If the real CSVs differ (column names, date formats), expect to adjust `data.py`. The fake-data scores are meaningless, so ignore them.

---

## 11. Known limitations of the current scaffold

- One model (Elo plus a one-feature logistic regression). No Dixon-Coles, boosting or ensemble yet.
- "Models agree" is not part of the tiers yet.
- No upcoming-fixture ingestion or UI yet.
- Time-weighting for drift only exists as Elo season regression.
- Team alias list is partial. Run `--audit` and extend it.
- Injury feed is Premier League only, unofficial, and has no history before you start collecting.
- The log-loss-gap success criterion is documented but not enforced by code.
- Tier thresholds are starting guesses until you backtest them.

---

## 12. Next actions

1. Fill in the purpose line in the README.
2. Read the terms for each data source and tick the checklist.
3. Start the daily snapshot job today.
4. Install requirements, pass the leakage test, download data, run `--audit`, then run the baseline.
5. Tune Elo settings on the validation season only.
6. Add Dixon-Coles, then boosted features one at a time.
7. Re-choose the tier thresholds from backtest calibration.
8. Build the Streamlit UI.
9. Add injury features after a few months of snapshots.

---

## 13. Glossary

- **Log loss:** a score for probabilities that punishes confident wrong answers heavily. Lower is better.
- **Brier score:** mean squared error of the probabilities. Lower is better.
- **Calibration:** whether predicted probabilities match real frequencies.
- **Elo:** a rating system that updates after each match based on the surprise of the result.
- **Dixon-Coles:** a goals model with per-team attack/defence ratings and a correction for low scores.
- **Leakage:** using information that wouldn't have been available before kickoff.
- **Closing odds:** bookmaker odds just before kickoff, the best public benchmark.
- **Margin (overround):** the bookmaker's built-in edge, removed by normalising implied probabilities to sum to 1.
- **xG:** expected goals, a measure of chance quality.
