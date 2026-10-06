import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

PARAMS_FILE = Path("dixon_coles_params.json")

def rho_correction(x, y, lambda_, mu, rho):
    if x == 0 and y == 0:
        return np.maximum(0, 1 - lambda_ * mu * rho)
    elif x == 0 and y == 1:
        return np.maximum(0, 1 + lambda_ * rho)
    elif x == 1 and y == 0:
        return np.maximum(0, 1 + mu * rho)
    elif x == 1 and y == 1:
        return np.maximum(0, 1 - rho)
    else:
        return 1.0

def _prepare_likelihood(df, teams, xi, current_date):
    # These inputs are constant during an optimiser fit; prepare them once.
    indices = {team: index for index, team in enumerate(teams)}
    days_ago = (current_date - df['date']).dt.days.clip(lower=0).values if current_date is not None else np.zeros(len(df))
    return (df['HomeTeam'].map(indices).values, df['AwayTeam'].map(indices).values,
            df['FTHG'].values, df['FTAG'].values, np.exp(-xi * days_ago))


def dc_log_likelihood(params, df, teams, xi=0.0065, current_date=None, prepared=None):
    n_teams = len(teams)
    # params: alpha (0..n-1), beta (n..2n-1), gamma (2n), rho (2n+1)
    alphas = params[:n_teams]
    betas = params[n_teams:2*n_teams]
    gamma = params[2*n_teams]
    rho = params[2*n_teams + 1]

    home_idx, away_idx, x, y, weights = prepared if prepared is not None else _prepare_likelihood(df, teams, xi, current_date)
    lambda_ = alphas[home_idx] * betas[away_idx] * gamma
    mu = alphas[away_idx] * betas[home_idx]

    # Poisson probabilities
    # We clip lambda and mu to avoid log(0)
    lambda_ = np.clip(lambda_, 1e-10, None)
    mu = np.clip(mu, 1e-10, None)
    
    log_pois_x = poisson.logpmf(x, lambda_)
    log_pois_y = poisson.logpmf(y, mu)

    # Rho correction
    # Vectorized rho correction
    tau = np.ones(len(df))
    mask_00 = (x == 0) & (y == 0)
    mask_01 = (x == 0) & (y == 1)
    mask_10 = (x == 1) & (y == 0)
    mask_11 = (x == 1) & (y == 1)

    tau[mask_00] = 1 - lambda_[mask_00] * mu[mask_00] * rho
    tau[mask_01] = 1 + lambda_[mask_01] * rho
    tau[mask_10] = 1 + mu[mask_10] * rho
    tau[mask_11] = 1 - rho
    
    # Clip tau to avoid log(<=0)
    tau = np.clip(tau, 1e-10, None)

    log_likelihood = np.sum(weights * (np.log(tau) + log_pois_x + log_pois_y))
    return -log_likelihood # Negative for minimization

def fit_dixon_coles(df, current_date=None, xi=0.0065):
    teams = sorted(list(set(df["HomeTeam"].unique()) | set(df["AwayTeam"].unique())))
    n_teams = len(teams)
    
    # Initial guess: alpha=1, beta=1, gamma=1, rho=0
    init_params = np.concatenate([np.ones(n_teams), np.ones(n_teams), [1.0, 0.0]])
    
    # Bounds: alpha > 0, beta > 0, gamma > 0, -1 <= rho <= 1
    # Actually, rho's valid range depends on lambda and mu. Let's just constrain rho to [-0.5, 0.5] to be safe, 
    # but the paper suggests max(-1/(lambda*mu), ...) which varies. [-0.2, 0.2] is typical.
    bounds = [(0.01, 5.0)] * (2 * n_teams) + [(0.1, 5.0), (-0.2, 0.2)]
    
    # Constraint: average of alphas = 1
    def constraint_alpha(params):
        return np.mean(params[:n_teams]) - 1.0

    constraints = [{'type': 'eq', 'fun': constraint_alpha}]
    
    prepared = _prepare_likelihood(df, teams, xi, current_date)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        opt = minimize(
            dc_log_likelihood, 
            init_params, 
            args=(df, teams, xi, current_date, prepared), 
            method='SLSQP', # SLSQP supports constraints, L-BFGS-B does not natively support eq constraints without penalty
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 200, 'disp': False}
        )
    
    if not opt.success:
        print(f"Warning: Dixon-Coles optimization failed: {opt.message}")
        
    alphas = opt.x[:n_teams]
    betas = opt.x[n_teams:2*n_teams]
    gamma = opt.x[2*n_teams]
    rho = opt.x[2*n_teams + 1]
    
    params_dict = {
        "teams": teams,
        "alpha": dict(zip(teams, alphas)),
        "beta": dict(zip(teams, betas)),
        "gamma": gamma,
        "rho": rho,
        "xi": xi
    }
    
    with open(PARAMS_FILE, 'w') as f:
        json.dump(params_dict, f, indent=2)
        
    return params_dict

def predict_match(home_team, away_team, params_dict, max_goals=10):
    alpha = params_dict["alpha"]
    beta = params_dict["beta"]
    gamma = params_dict["gamma"]
    rho = params_dict["rho"]
    
    if home_team not in alpha or away_team not in alpha:
        # Fallback for unknown teams
        lambda_ = gamma
        mu = 1.0
    else:
        lambda_ = alpha[home_team] * beta[away_team] * gamma
        mu = alpha[away_team] * beta[home_team]
        
    prob_matrix = np.zeros((max_goals, max_goals))
    for x in range(max_goals):
        for y in range(max_goals):
            p = poisson.pmf(x, lambda_) * poisson.pmf(y, mu)
            p *= rho_correction(x, y, lambda_, mu, rho)
            prob_matrix[x, y] = np.maximum(0, p)
            
    # Normalize just in case
    prob_matrix = prob_matrix / prob_matrix.sum()
    
    p_home = np.sum(np.tril(prob_matrix, -1))
    p_draw = np.sum(np.diag(prob_matrix))
    p_away = np.sum(np.triu(prob_matrix, 1))
    
    # Get top scorelines
    flat_indices = np.argsort(prob_matrix, axis=None)[::-1]
    top_scorelines = []
    for idx in flat_indices[:5]:
        x, y = np.unravel_index(idx, prob_matrix.shape)
        if prob_matrix[x, y] > 0.001:
            top_scorelines.append((int(x), int(y), float(prob_matrix[x, y])))
            
    # Derived markets
    goals_grid = np.arange(max_goals)[:, None] + np.arange(max_goals)[None, :]
    p_over_2_5 = np.sum(prob_matrix[goals_grid > 2.5])
    
    # BTTS
    p_btts = np.sum(prob_matrix[1:, 1:])
    
    return {
        "p_home": p_home, "p_draw": p_draw, "p_away": p_away,
        "lambda_home": lambda_, "lambda_away": mu,
        "top_scorelines": top_scorelines,
        "p_over_2_5": p_over_2_5,
        "p_btts": p_btts
    }
