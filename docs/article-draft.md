# I Built a Football Prediction Bot. Winning Picks Still Lost Money.

I spent weeks building a prediction engine for the top five European football leagues. The goal was familiar: write enough Python to find an edge over the bookmakers.

The result was more interesting than a simple success or failure. The model's strong predictions had a 69.3% hit rate. But the bets selected by my confidence and price rules won only 59.5% of the time—and the historical simulation lost money.

Across 925 selected bets, 550 won. With one unit staked on each bet, the ledger finished down 47.63 units: a −5.1% return on the amount staked.

Those figures describe the published version of the experiment, covering recorded matches from August 2021 to September 2026 across six season labels. The final season is partial. They are simulated results, not money I won or lost in a live betting account.

The useful lesson wasn't that prediction is pointless. It was that a correct pick, a well-calibrated probability and a profitable price are three different things.

## What I actually built

The engine combines Elo ratings, a time-decayed Dixon–Coles goals model and an XGBoost classifier. Its features include observed expected goals, rest days and team strength. Elo updates account for goal difference.

The historical evaluation moves forward season by season. Each season's models are trained on earlier seasons, and match features use earlier observations. That chronology matters: allowing tomorrow's result into today's features would make the experiment look better without making the model more useful.

The selection rule required at least 60% model confidence, a lead of at least 25 percentage points over the next most likely outcome, and recorded bookmaker odds above the model's calculated fair price.

That last requirement sounds reassuring. It wasn't enough.

## Being right isn't the same as being paid enough

Suppose an outcome really has a 62% chance of happening. At decimal odds of 1.50, its expected net return per unit staked is:

`Expected return = probability × decimal odds − 1`

`0.62 × 1.50 − 1 = −0.07`

The bet can win most of the time and still have an expected loss of seven units per hundred staked. Actual results vary; the expectation isn't a promise about a particular sample.

The break-even price is `1 / probability`: approximately 1.613 in this example. Even odds of 1.61 would be slightly below break-even.

This is why a headline win rate tells only part of the story. The losses and the payouts on the wins determine the return.

## The margin raises the hurdle

Consider home, draw and away odds of 1.60, 4.20 and 5.50. Their reciprocal implied probabilities are approximately 62.5%, 23.8% and 18.2%.

Together, they total 104.49%. The 4.49 percentage points above 100% are the overround.

Dividing each implied probability by that total gives roughly 59.8%, 22.8% and 17.4%. This is one way to estimate market probabilities after removing the margin. It doesn't reveal the true chances of the match outcomes: it assumes the margin is distributed proportionally.

Nor does the overround guarantee a loss on every possible wager. An outcome can still be offered at a profitable price if its actual probability is high enough. The problem is identifying that probability reliably—and obtaining the price in practice.

For my experiment, a model claiming an edge was evidence of a disagreement. It wasn't proof that the bookmaker was wrong.

## My apparent value bets needed a separate evaluation

The strong predictions and the selected bets are different groups. The former had a 69.3% hit rate; the latter won 59.5% of the time. Comparing those numbers is useful, but it doesn't prove why the selected group performed worse.

Filtering on disagreement with the market changes the sample. It can concentrate cases where the model's probability estimates are too optimistic. Missing information, model error and ordinary variation are also possible explanations.

My current results don't isolate how much each explanation contributed. I would need to test calibration within the selected bets, compare market and model probability scores, and examine uncertainty in returns before making that claim.

Calling every disagreement a bookmaker mistake was the assumption I needed to stop making.

## Calibration needs more than one matching average

An average predicted probability close to the overall win rate would be encouraging. It would not establish that the model was highly calibrated.

A model can overestimate one group of matches and underestimate another while looking accurate on average. Calibration needs to be checked across probability ranges, on held-out predictions, with enough observations to understand the uncertainty. The subset chosen for betting also needs its own evaluation.

That is why I now keep prediction quality and profitability separate in the evidence page.

## What I take away from the experiment

The backtest supports a specific conclusion: this model and selection rule lost money at the recorded prices in this dataset. It does not establish that every betting strategy must lose, or that the same model will behave identically in the future.

Building it was still valuable. I learned to protect feature chronology, validate data sources and inspect what a selection rule does to a model's results.

I also learned that “the model says this is value” is a hypothesis worth testing, not an edge worth assuming.

The code and historical evidence are public:

- [Explore the experiment](https://betting.keabetswe.online)
- [Read the source code](https://github.com/keammakola/Football-Predictor)

## Sources and publication notes

- [Probability calibration: scikit-learn](https://scikit-learn.org/stable/modules/calibration.html) explains calibration curves and why probability estimates need evaluation across groups.
- [Estimating Expected Loss Rates in Betting Markets: Hegarty and Whelan](https://www.karlwhelan.com/Papers/Overround.pdf) explains the assumptions behind converting overround into expected loss rates.
- Numbers above match the currently published 925-bet export. If publishing the earlier three-season experiment instead, use its versioned artifacts and figures consistently throughout.
- Keep your existing article link and publication disclaimer separate from the empirical claims. This draft revises the article body; it does not assess the legal effect of the disclaimer.
