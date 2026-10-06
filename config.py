"""All settings in one place. Change them deliberately, and log why."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "raw"          # untouched downloads, never overwritten
SNAPSHOT_DIR = ROOT / "snapshots"        # daily injury snapshots
EXPERIMENT_LOG = ROOT / "experiments.csv"

SEED = 42

# football-data.co.uk season codes: "1415" = 2014/15 ... "2425" = 2024/25
# Add newer seasons as they are published.
SEASONS = ["1516", "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526", "2627"]
URL_TEMPLATE = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"

# Global league configuration mapping
LEAGUES = {
    "EPL": {
        "fd_code": "E0",
        "understat_code": "EPL",
        "fixture_code": "epl",
        "odds_api_sport": "soccer_epl",
        "elo_k": 25.0,
        "elo_season_regression": 0.40,
        "dc_xi": 0.0090
    },
    "LaLiga": {
        "fd_code": "SP1",
        "understat_code": "La_liga",
        "fixture_code": "la-liga",
        "odds_api_sport": "soccer_spain_la_liga",
        "elo_k": 20.0,
        "elo_season_regression": 0.25,
        "dc_xi": 0.0065
    },
    "Bundesliga": {
        "fd_code": "D1",
        "understat_code": "Bundesliga",
        "fixture_code": "bundesliga",
        "odds_api_sport": "soccer_germany_bundesliga",
        "elo_k": 25.0,
        "elo_season_regression": 0.40,
        "dc_xi": 0.0090
    },
    "SerieA": {
        "fd_code": "I1",
        "understat_code": "Serie_A",
        "fixture_code": "serie-a",
        "odds_api_sport": "soccer_italy_serie_a",
        "elo_k": 20.0,
        "elo_season_regression": 0.25,
        "dc_xi": 0.0065
    },
    "Ligue1": {
        "fd_code": "F1",
        "understat_code": "Ligue_1",
        "fixture_code": "ligue-1",
        "odds_api_sport": "soccer_france_ligue_one",
        "elo_k": 20.0,
        "elo_season_regression": 0.25,
        "dc_xi": 0.0065
    }
}

# Local credentials are deliberately excluded from version control.
_LOCAL_CONFIG_PATH = ROOT / "config.local.json"
_LOCAL_CONFIG = json.loads(_LOCAL_CONFIG_PATH.read_text()) if _LOCAL_CONFIG_PATH.exists() else {}
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", _LOCAL_CONFIG.get("ODDS_API_KEY", ""))

# Default league to use if not specified
DEFAULT_LEAGUE = "EPL"

# Time-based split. TEST is the final hold-out: touch it ONCE, at the very end.
VALID_SEASON = "2324"   # used for tuning and choosing tier thresholds
TEST_SEASON = "2425"    # final check only (run_baseline.py --final)

# Elo settings (tune on VALID only)
ELO_START = 1500.0
ELO_NEW_TEAM = 1450.0       # promoted / unseen teams start a little lower
ELO_K = 20.0
ELO_HOME_ADV = 60.0
ELO_SEASON_REGRESSION = 0.25  # pull ratings 40% toward the mean each new season

# Tier rules for "strong" calls (re-check against the backtest, don't trust by feel)
TIERS = {
    "Strong": {"min_prob": 0.60, "min_margin": 0.25},
    "Lean":   {"min_prob": 0.50, "min_margin": 0.15},
}
MIN_TIER_SAMPLE = 30   # warn when a tier has fewer matches than this

# Success criteria, written BEFORE seeing results (see README).
TARGET_LOGLOSS_GAP_TO_MARKET = 0.01   # model log loss within 0.01 of the market's
