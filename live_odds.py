import os
import requests
import pandas as pd
import config
from team_names import canon

def get_live_odds(league_name):
    """
    Fetch live odds from The-Odds-API and return a DataFrame.
    Returns: DataFrame with [home_team, away_team, odds_H, odds_D, odds_A]
    """
    sport = config.LEAGUES[league_name].get("odds_api_sport")
    if not sport:
        return pd.DataFrame()
        
    if not os.environ.get("ODDS_API_KEY", config.ODDS_API_KEY):
        raise RuntimeError('Set ODDS_API_KEY in the environment or config.local.json')

    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        "apiKey": os.environ.get("ODDS_API_KEY", config.ODDS_API_KEY),
        "regions": "eu,uk",
        "markets": "h2h",
        "bookmakers": "betway,pinnacle,bet365", # Request Betway first
        "oddsFormat": "decimal"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        if not resp.ok:
            raise RuntimeError(f"Odds feed returned HTTP {resp.status_code}")
        data = resp.json()
    except requests.RequestException:
        raise RuntimeError('Odds feed could not be reached') from None

    records = []
    for match in data:
        home_team = canon(match.get("home_team", ""))
        away_team = canon(match.get("away_team", ""))
        
        bookmakers = match.get("bookmakers", [])
        if not bookmakers:
            continue
            
        # Priority: Betway > Pinnacle > Bet365
        target_bookie = None
        for b_name in ["betway", "pinnacle", "bet365"]:
            target_bookie = next((b for b in bookmakers if b["key"] == b_name), None)
            if target_bookie:
                break
        
        if not target_bookie:
            target_bookie = bookmakers[0]
            
        markets = target_bookie.get("markets", [])
        h2h_market = next((m for m in markets if m["key"] == "h2h"), None)
        
        if not h2h_market:
            continue
            
        outcomes = h2h_market.get("outcomes", [])
        odds_H, odds_D, odds_A = None, None, None
        
        for outcome in outcomes:
            name = outcome.get("name")
            price = outcome.get("price")
            if name == match.get("home_team"):
                odds_H = price
            elif name == match.get("away_team"):
                odds_A = price
            elif name.lower() == "draw":
                odds_D = price
                
        if odds_H and odds_D and odds_A:
            records.append({
                "home_team": home_team,
                "away_team": away_team,
                "kickoff_utc": match["commence_time"],
                "odds_H": odds_H,
                "odds_D": odds_D,
                "odds_A": odds_A,
                "bookmaker": target_bookie["key"]
            })
            
    return pd.DataFrame(records)

if __name__ == "__main__":
    df = get_live_odds("EPL")
    print(df)
