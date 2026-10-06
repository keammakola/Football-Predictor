import sys
import pandas as pd
import numpy as np
import subprocess

def run_evaluation():
    print("==============================================================================")
    print("                 FOOTBALL PREDICTOR: EVALUATION PIPELINE")
    print("==============================================================================")
    
    print("\n[1/3] Running Walk-Forward Backtest (Generating matches.csv & bets.csv)...")
    # Call backtest.py
    try:
        subprocess.run([sys.executable, "backtest.py"], check=True)
    except subprocess.CalledProcessError:
        print("Error running backtest.py")
        return

    print("\n[2/3] Running Audit Script...")
    try:
        subprocess.run([
            sys.executable, "audit_backtest.py", 
            "--matches", "matches.csv", 
            "--bets", "bets.csv"
        ], check=True)
    except subprocess.CalledProcessError:
        print("Error running audit_backtest.py")
        return
        
    print("\n[3/3] Running Market Blending Test (w-optimizer)...")
    try:
        subprocess.run([sys.executable, "blend_test.py"], check=True)
    except subprocess.CalledProcessError:
        print("Error running blend_test.py")
        return
        
    print("\n==============================================================================")
    print(" EVALUATION COMPLETE")
    print(" -> If optimal 'w' > 0, the model adds independent information.")
    print(" -> If optimal 'w' = 0, the model is strictly subsumed by the closing line.")
    print("==============================================================================")

if __name__ == "__main__":
    run_evaluation()
