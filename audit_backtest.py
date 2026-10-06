"""Audit a football betting backtest: is the edge real, or noise / a bug?

Two inputs (CSV). Edit COLUMNS below if your column names differ.

1) MATCHES file: one row per match you predicted (ALL matches, not just bets)
   date, league, home, away, p_home, p_draw, p_away, result (H/D/A),
   odds_home, odds_draw, odds_away   <- RAW bookmaker CLOSING odds (margin included)

2) BETS file (optional): one row per bet placed
   date, league, selection (H/D/A), model_prob, odds_taken, won (1/0)
   odds_close (optional, raw closing odds for the same selection, enables CLV)

Usage:
  python audit_backtest.py --matches matches.csv --bets bets.csv
  python audit_backtest.py --demo            # runs on fake data to show the output

What it reports
  1. Model vs margin-free market on EVERY match: log loss, Brier, RPS, paired gap +/- SE
  2. Calibration of all probabilities, and of the Strong tier specifically
  3. Tier hit rates with confidence intervals vs what the market implied
  4. Bets: ROI with standard error / 95% interval, by league, plus closing line value
  5. Red flags (the usual signs of a leak or an odds-joining bug)
"""
import argparse
import sys

import numpy as np
import pandas as pd

# Map the names this script uses (left) to the column names in YOUR files (right).
COLUMNS = {
    "date": "date", "league": "league", "home": "home", "away": "away",
    "p_home": "p_home", "p_draw": "p_draw", "p_away": "p_away", "result": "result",
    "odds_home": "odds_home", "odds_draw": "odds_draw", "odds_away": "odds_away",
    "selection": "pick", "model_prob": "prob", "odds_taken": "odds_taken",
    "odds_close": "odds_close", "won": "won",
}
CLASSES = ["H", "D", "A"]
EPS = 1e-12


# ----------------------------------------------------------------- helpers
def _col(df, name):
    return df[COLUMNS[name]]


def wilson(k, n, z=1.96):
    """95% interval for a hit rate."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (centre - half, centre + half)


def margin_free(odds, method="proportional"):
    """odds: (n,3) raw decimal odds -> (n,3) probabilities summing to 1."""
    inv = 1.0 / np.asarray(odds, dtype=float)
    if method == "proportional":
        return inv / inv.sum(axis=1, keepdims=True)
    lo, hi = np.full(len(inv), 0.3), np.full(len(inv), 3.0)   # power method, row-wise bisection
    for _ in range(60):
        k = (lo + hi) / 2
        s = (inv ** k[:, None]).sum(axis=1)
        lo, hi = np.where(s > 1, k, lo), np.where(s > 1, hi, k)
    return inv ** ((lo + hi) / 2)[:, None]


def onehot(result):
    return np.array([[r == c for c in CLASSES] for r in result], dtype=float)


def per_match_logloss(probs, y):
    return -np.log(np.clip((probs * y).sum(axis=1), EPS, 1))


def per_match_brier(probs, y):
    return ((probs - y) ** 2).sum(axis=1)


def per_match_rps(probs, y):
    """Ranked probability score; outcomes ordered H, D, A."""
    cp, cy = np.cumsum(probs, axis=1)[:, :2], np.cumsum(y, axis=1)[:, :2]
    return 0.5 * ((cp - cy) ** 2).sum(axis=1)


def paired(a, b):
    d = a - b
    se = d.std(ddof=1) / np.sqrt(len(d))
    return d.mean(), se


def section(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


# ----------------------------------------------------------------- matches
def audit_matches(m, strong_prob, strong_margin):
    flags = []
    probs = m[[COLUMNS["p_home"], COLUMNS["p_draw"], COLUMNS["p_away"]]].to_numpy(float)
    res = _col(m, "result").to_numpy()
    y = onehot(res)

    bad_sum = np.abs(probs.sum(axis=1) - 1) > 1e-3
    if bad_sum.any():
        flags.append(f"{bad_sum.sum()} matches have probabilities that don't sum to 1.")

    ll_m, br_m, rps_m = per_match_logloss(probs, y), per_match_brier(probs, y), per_match_rps(probs, y)
    n = len(m)
    section(f"1. MODEL vs MARKET on every match (n = {n})")
    pred = np.array(CLASSES)[probs.argmax(axis=1)]
    print(f"model   log loss {ll_m.mean():.4f} | Brier {br_m.mean():.4f} | RPS {rps_m.mean():.4f} | accuracy {np.mean(pred == res):.3f}")

    have_odds = all(COLUMNS[c] in m.columns for c in ("odds_home", "odds_draw", "odds_away"))
    mkt_probs = None
    if have_odds:
        raw = m[[COLUMNS["odds_home"], COLUMNS["odds_draw"], COLUMNS["odds_away"]]].to_numpy(float)
        ok = np.isfinite(raw).all(axis=1) & (raw > 1).all(axis=1)
        print(f"rows with usable closing odds: {ok.sum()} of {n}")
        for method in ("proportional", "power"):
            mp = np.full_like(probs, np.nan)
            mp[ok] = margin_free(raw[ok], method)
            ll_k, br_k, rps_k = (f(mp[ok], y[ok]) for f in (per_match_logloss, per_match_brier, per_match_rps))
            gap, se = paired(ll_m[ok], ll_k)
            print(f"market ({method:12s}) log loss {ll_k.mean():.4f} | Brier {br_k.mean():.4f} | RPS {rps_k.mean():.4f}")
            print(f"  model minus market log loss: {gap:+.4f} +/- {se:.4f} (1 SE)   [negative = model better]")
            if method == "proportional":
                mkt_probs, headline_gap = mp, gap
                overround = (1 / raw[ok]).sum(axis=1).mean() - 1
                print(f"  average bookmaker overround in your closing odds: {overround * 100:.1f}%")
        if headline_gap < -0.02:
            flags.append(f"Model beats the closing line by {-headline_gap:.3f} log loss. That is far more than "
                         "anyone realistically achieves: look for leakage (features that include the match itself, "
                         "models fitted on future data).")
        if "league" in COLUMNS and COLUMNS["league"] in m.columns:
            rows = []
            for lg, idx in m.groupby(COLUMNS["league"]).groups.items():
                pos = m.index.get_indexer(idx)
                k = pos[ok[pos]]
                if len(k) > 1:
                    g, s = paired(ll_m[k], per_match_logloss(mkt_probs[k], y[k]))
                    rows.append({"league": lg, "n": len(k), "model_ll": ll_m[k].mean(), "gap_vs_market": g, "se": s})
            if rows:
                print("\nBy league (log loss gap, negative = model better):")
                print(pd.DataFrame(rows).round(4).to_string(index=False))
    else:
        print("No closing odds columns found, so the market comparison was skipped.")

    # ---- calibration
    section("2. CALIBRATION (every match x outcome pair)")
    p, hit = probs.ravel(), y.ravel()
    df = pd.DataFrame({"p": p, "hit": hit})
    df["bucket"] = pd.cut(df["p"], [0, .1, .2, .3, .4, .5, .6, .7, .8, 1.0], include_lowest=True)
    cal = df.groupby("bucket", observed=True).agg(n=("hit", "size"), avg_predicted=("p", "mean"), actual=("hit", "mean"))
    print(cal.round(3).to_string())

    # ---- tiers
    section(f"3. STRONG TIER (prob >= {strong_prob}, lead >= {strong_margin})")
    srt = np.sort(probs, axis=1)
    top, lead = srt[:, -1], srt[:, -1] - srt[:, -2]
    strong = (top >= strong_prob) & (lead >= strong_margin)
    pick_idx = probs.argmax(axis=1)
    won = pick_idx == y.argmax(axis=1)
    k, ns = int(won[strong].sum()), int(strong.sum())
    if ns:
        lo, hi = wilson(k, ns)
        print(f"matches in tier: {ns} of {n} ({ns / n * 100:.1f}%)")
        print(f"average model probability on the pick : {top[strong].mean():.3f}")
        print(f"actual hit rate                        : {k / ns:.3f}  (95% interval {lo:.3f} to {hi:.3f})")
        if mkt_probs is not None:
            mk_on_pick = mkt_probs[np.arange(n), pick_idx]
            sel = strong & np.isfinite(mk_on_pick)
            print(f"average market probability on the pick: {mk_on_pick[sel].mean():.3f}")
        if top[strong].mean() - k / ns > 0.04:
            flags.append("Strong tier is overconfident: the model's average stated probability is more than "
                         "4 points above the real hit rate. Calibrate before trusting the tier.")
        if ns < 100:
            flags.append(f"Only {ns} matches in the Strong tier: too few to judge it.")
    else:
        print("No matches reach the Strong tier with these thresholds.")
    return flags


# -------------------------------------------------------------------- bets
def audit_bets(b):
    flags = []
    odds = _col(b, "odds_taken").to_numpy(float)
    won = _col(b, "won").to_numpy(float)
    mp = _col(b, "model_prob").to_numpy(float)
    ret = won * odds - 1.0                      # profit per 1 unit staked
    n = len(b)
    section(f"4. BETS (n = {n})")
    roi, se = ret.mean(), ret.std(ddof=1) / np.sqrt(n)
    lo_hi = (roi - 1.96 * se, roi + 1.96 * se)
    k = int(won.sum())
    print(f"wins {k} | hit rate {k / n:.3f} | average odds taken {odds.mean():.2f} | profit {ret.sum():+.2f} units")
    print(f"ROI {roi * 100:+.1f}%  +/- {se * 100:.1f} pts (1 SE)   95% interval {lo_hi[0] * 100:+.1f}% to {lo_hi[1] * 100:+.1f}%")
    if lo_hi[0] <= 0 <= lo_hi[1]:
        print("-> The interval includes 0%: this sample cannot tell a small edge from none or from a small loss.")
    print(f"average model probability on bets {mp.mean():.3f} vs actual hit rate {k / n:.3f}")

    if COLUMNS["league"] in b.columns:
        rows = []
        for lg, g in b.groupby(COLUMNS["league"]):
            r = _col(g, "won").to_numpy(float) * _col(g, "odds_taken").to_numpy(float) - 1
            s = r.std(ddof=1) / np.sqrt(len(r)) if len(r) > 1 else np.nan
            rows.append({"league": lg, "bets": len(r), "ROI %": r.mean() * 100, "SE pts": s * 100,
                         "enough data": "yes" if len(r) >= 150 else "NO (noise)"})
        print("\nBy league (differences between leagues are usually just noise):")
        print(pd.DataFrame(rows).round(1).to_string(index=False))

    if COLUMNS["odds_close"] in b.columns:
        oc = _col(b, "odds_close").to_numpy(float)
        ok = np.isfinite(oc) & (oc > 1)
        clv = odds[ok] / oc[ok] - 1
        beat = np.mean(odds[ok] > oc[ok])
        print(f"\nClosing line value: average {clv.mean() * 100:+.2f}% +/- {clv.std(ddof=1) / np.sqrt(ok.sum()) * 100:.2f} pts; "
              f"beat the closing odds on {beat * 100:.0f}% of bets (n={ok.sum()})")
        print("Consistently positive CLV over several hundred bets is stronger evidence than ROI.")
    else:
        print("\n(No odds_close column, so closing line value was skipped.)")

    # red flags
    implied = 1 / odds
    claimed_edge = (mp - implied).mean()
    win_odds = odds[won == 1].mean() if k else np.nan
    print(f"\naverage claimed edge (model prob minus odds-implied prob): {claimed_edge * 100:+.1f} pts")
    print(f"average odds on WINNING bets: {win_odds:.2f}   (model fair odds on those bets: {np.mean(1 / mp[won == 1]):.2f})")
    if claimed_edge > 0.10:
        flags.append(f"Average claimed edge is {claimed_edge * 100:.0f} points. Real markets are rarely wrong by that "
                     "much. Check that odds are joined to the right match and the right outcome (H/D/A).")
    if np.nanmean(odds) > 1 / mp.mean() * 1.4:
        flags.append("Average odds taken are much longer than the model's own fair odds on the same bets. "
                     "That pattern appears when odds are attached to the wrong outcome or fixture.")
    if (odds < 1.01).any() or (odds > 30).any():
        flags.append("Some odds are below 1.01 or above 30: check for bad rows.")
    dup_cols = [COLUMNS[c] for c in ("date", "league", "selection") if COLUMNS[c] in b.columns]
    if len(dup_cols) == 3 and b.duplicated(dup_cols + [COLUMNS["odds_taken"]]).any():
        flags.append("Duplicate bet rows found.")
    return flags


# -------------------------------------------------------------------- demo
def make_demo(seed=3, n=3000, leak=False):
    """Efficient market + a model that is the market plus noise. Optionally leak the result."""
    rng = np.random.default_rng(seed)
    true = rng.dirichlet([4.5, 2.6, 3.2], size=n)
    true = 0.4 * true + 0.6 * np.array([0.45, 0.26, 0.29])        # football-like spread
    true /= true.sum(axis=1, keepdims=True)
    res = np.array([rng.choice(CLASSES, p=p) for p in true])
    mkt = true * np.exp(rng.normal(0, 0.03, true.shape)); mkt /= mkt.sum(axis=1, keepdims=True)
    odds = 1 / (mkt * 1.045)
    model = true * np.exp(rng.normal(0, 0.18, true.shape))
    if leak:
        model = model * (1 + 1.2 * onehot(res))
    model /= model.sum(axis=1, keepdims=True)
    m = pd.DataFrame({"date": pd.date_range("2021-08-01", periods=n, freq="3h").astype(str),
                      "league": rng.choice(["EPL", "La Liga", "Serie A", "Bundesliga", "Ligue 1"], n),
                      "home": "A", "away": "B", "p_home": model[:, 0], "p_draw": model[:, 1], "p_away": model[:, 2],
                      "result": res, "odds_home": odds[:, 0], "odds_draw": odds[:, 1], "odds_away": odds[:, 2]})
    # bets: Strong tier where raw closing odds exceed model fair odds
    srt = np.sort(model, axis=1)
    pick = model.argmax(axis=1)
    strong = (srt[:, -1] >= 0.60) & (srt[:, -1] - srt[:, -2] >= 0.25)
    taken = odds[np.arange(n), pick]
    sel = strong & (taken > 1 / srt[:, -1])
    b = pd.DataFrame({"date": m["date"][sel], "league": m["league"][sel],
                      "selection": np.array(CLASSES)[pick][sel], "model_prob": srt[sel, -1],
                      "odds_taken": taken[sel], "odds_close": taken[sel] * np.exp(rng.normal(0, 0.01, sel.sum())),
                      "won": (np.array(CLASSES)[pick] == res)[sel].astype(int)})
    return m, b.reset_index(drop=True)


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matches")
    ap.add_argument("--bets")
    ap.add_argument("--strong-prob", type=float, default=0.60)
    ap.add_argument("--strong-margin", type=float, default=0.25)
    ap.add_argument("--demo", action="store_true", help="run on fake data (efficient market)")
    ap.add_argument("--demo-leak", action="store_true", help="fake data where the model secretly sees results")
    a = ap.parse_args()

    if a.demo or a.demo_leak:
        m, b = make_demo(leak=a.demo_leak)
        print("DEMO MODE: fake data, so ignore the numbers and look at the report format.")
    elif a.matches:
        m = pd.read_csv(a.matches)
        b = pd.read_csv(a.bets) if a.bets else None
    else:
        sys.exit("Give --matches (and optionally --bets), or use --demo.")

    flags = audit_matches(m, a.strong_prob, a.strong_margin)
    if b is not None and len(b) > 1:
        flags += audit_bets(b)

    section("5. RED FLAGS")
    if flags:
        for f in flags:
            print(f"- {f}")
    else:
        print("None triggered. That is not proof the backtest is clean: also confirm features are shifted "
              "by one match and models are refit using only earlier data.")
    print("\nNote: this is an analysis aid, not financial advice.")


if __name__ == "__main__":
    main()
