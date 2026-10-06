#!/bin/bash
set -e

echo "========================================================="
echo "        FOOTBALL PREDICTOR LIVE AUTOMATION SCRIPT        "
echo "========================================================="

echo "1/4: Downloading latest raw data for the current season..."
venv/bin/python -c "
import config
from data import download_raw
for l in config.LEAGUES.keys():
    download_raw(league_name=l)
"

echo ""
echo "2/4: Running full evaluation pipeline (grading past bets)..."
venv/bin/python evaluate_pipeline.py

echo ""
echo "3/4: Exporting historical bets to frontend JSON..."
venv/bin/python export_bets.py

echo ""
echo "4/4: Generating upcoming fixtures and live odds..."
venv/bin/python generate_upcoming.py

echo ""
echo "========================================================="
echo " Update complete! The frontend is now fully live."
echo "========================================================="
