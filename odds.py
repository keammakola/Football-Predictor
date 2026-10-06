import numpy as np

def fair_odds(prob):
    """Convert probability to fair decimal odds."""
    if prob <= 0:
        return np.inf
    return 1.0 / prob

def margin_free_probs_proportional(implied_probs):
    """
    Remove bookmaker margin using the proportional method.
    implied_probs: list or array of implied probabilities [p_home, p_draw, p_away]
    """
    total = sum(implied_probs)
    return [p / total for p in implied_probs]

def margin_free_probs_power(implied_probs):
    """
    Remove bookmaker margin using the power method.
    Finds k such that sum(p^k) = 1.
    """
    from scipy.optimize import root_scalar
    
    def objective(k):
        return sum(p**k for p in implied_probs) - 1.0
        
    # Standard bounds for overround margin power
    try:
        res = root_scalar(objective, bracket=[1.0, 1.2], method='brentq')
        if res.converged:
            k = res.root
            return [p**k for p in implied_probs]
    except ValueError:
        pass
        
    # Fallback if bracket doesn't work or under-round
    return margin_free_probs_proportional(implied_probs)

def expected_value(model_prob, market_decimal_odds):
    """
    Calculate expected value per unit staked.
    EV = (model probability * market decimal odds) - 1
    """
    return (model_prob * market_decimal_odds) - 1.0
