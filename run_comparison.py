import os
import subprocess

print("Running NEW model...")
subprocess.run(["venv/bin/python", "backtest.py"], stdout=open("new_model_results.txt", "w"))

print("Reverting parameters to OLD model...")
with open("config.py", "r") as f:
    config_content = f.read()
config_content = config_content.replace("ELO_K = 25.0", "ELO_K = 20.0")
config_content = config_content.replace("ELO_SEASON_REGRESSION = 0.40", "ELO_SEASON_REGRESSION = 0.25")
with open("config.py", "w") as f:
    f.write(config_content)

with open("backtest.py", "r") as f:
    bt_content = f.read()
bt_content = bt_content.replace("xi=0.009", "xi=0.0065")
with open("backtest.py", "w") as f:
    f.write(bt_content)

print("Running OLD model...")
subprocess.run(["venv/bin/python", "backtest.py"], stdout=open("old_model_results.txt", "w"))

print("Done!")
