import pandas as pd
import numpy as np
from scipy.optimize import minimize

def margin_free(odds):
    inv = 1.0 / odds
    return inv / inv.sum(axis=1, keepdims=True)

def per_match_logloss(probs, y):
    return -np.log(np.clip((probs * y).sum(axis=1), 1e-12, 1))

def main():
    df = pd.read_csv("matches.csv").dropna(subset=["odds_home", "odds_draw", "odds_away"])
    
    y_str = df["result"].values
    classes = ["H", "D", "A"]
    y = np.array([[r == c for c in classes] for r in y_str], dtype=float)
    
    p_mod = df[["p_home", "p_draw", "p_away"]].values
    raw_odds = df[["odds_home", "odds_draw", "odds_away"]].values
    p_mkt = margin_free(raw_odds)
    
    def loss_fn(w):
        w = w[0]
        blend = w * p_mod + (1 - w) * p_mkt
        return per_match_logloss(blend, y).mean()
        
    res = minimize(loss_fn, [0.5], bounds=[(0.0, 1.0)])
    opt_w = res.x[0]
    best_ll = res.fun
    
    mkt_ll = per_match_logloss(p_mkt, y).mean()
    mod_ll = per_match_logloss(p_mod, y).mean()
    
    print(f"Market Log Loss: {mkt_ll:.5f}")
    print(f"Model Log Loss:  {mod_ll:.5f}")
    print(f"Blend Log Loss:  {best_ll:.5f}")
    print(f"Optimal Model Weight (w): {opt_w:.5f}")

if __name__ == "__main__":
    main()
