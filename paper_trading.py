import pandas as pd
from pathlib import Path
import datetime
import data

LEDGER_FILE = Path("paper_trades.csv")

def log_trades(alerts_df):
    """Automatically log any new +EV bets into the paper trading ledger."""
    if alerts_df.empty:
        return
        
    # Initialize ledger if it doesn't exist
    if not LEDGER_FILE.exists():
        df = pd.DataFrame(columns=['Date', 'League', 'Match', 'Pick', 'Odds', 'Edge', 'Status', 'PnL'])
        df.to_csv(LEDGER_FILE, index=False)
        
    ledger = pd.read_csv(LEDGER_FILE)
    
    new_records = []
    for _, row in alerts_df.iterrows():
        # Clean odds string (e.g., "1.35 (Betway)" -> 1.35)
        raw_odds = row['Live Odds'].split()[0]
        if raw_odds == "N/A":
            continue
            
        odds_val = float(raw_odds)
        
        # Check if match is already in ledger
        exists = ledger[(ledger['Match'] == row['Match']) & (ledger['Date'] == row['Date'])]
        
        if exists.empty:
            new_records.append({
                'Date': row['Date'],
                'League': row['League'],
                'Match': row['Match'],
                'Pick': row['Pick'],
                'Odds': odds_val,
                'Edge': row['Edge'],
                'Status': 'Pending',
                'PnL': 0.0
            })
            
    if new_records:
        new_df = pd.DataFrame(new_records)
        ledger = pd.concat([ledger, new_df], ignore_index=True)
        ledger.to_csv(LEDGER_FILE, index=False)

def grade_trades():
    """Check pending trades against historical results to auto-grade them."""
    if not LEDGER_FILE.exists():
        return
        
    ledger = pd.read_csv(LEDGER_FILE)
    pending_mask = ledger['Status'] == 'Pending'
    
    if not pending_mask.any():
        return
        
    # We need historical data to grade. We load all leagues that have pending matches.
    pending_leagues = ledger.loc[pending_mask, 'League'].unique()
    
    for league in pending_leagues:
        try:
            hist_df = data.load_matches(league)
        except:
            continue
            
        league_pending = ledger[(ledger['League'] == league) & (ledger['Status'] == 'Pending')]
        
        for idx, row in league_pending.iterrows():
            match_str = row['Match']
            home_team, away_team = match_str.split(" vs ")
            
            # Find in historical
            match_result = hist_df[(hist_df['HomeTeam'] == home_team) & (hist_df['AwayTeam'] == away_team)]
            
            # If the match has been played and recorded in the downloaded raw CSVs
            if not match_result.empty:
                actual_ftr = match_result.iloc[-1]['FTR'] # Get the latest instance
                
                pick_str = row['Pick']
                pick_outcome = "H" if "Home" in pick_str else ("D" if "Draw" in pick_str else "A")
                
                odds_taken = row['Odds']
                
                if actual_ftr == pick_outcome:
                    ledger.at[idx, 'Status'] = 'Won'
                    ledger.at[idx, 'PnL'] = odds_taken - 1.0
                else:
                    ledger.at[idx, 'Status'] = 'Lost'
                    ledger.at[idx, 'PnL'] = -1.0
                    
    # Save back to CSV
    ledger.to_csv(LEDGER_FILE, index=False)
    
def get_ledger():
    if not LEDGER_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(LEDGER_FILE)
