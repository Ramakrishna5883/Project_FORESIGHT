import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"

# Database
DB_PATH = DATABASE_DIR / "foresight.db"

# Forecasting Configuration
FORECAST_HORIZON = 6  # weeks
N_BACKTEST_FOLDS = 4
LAGS = [1, 2, 3, 4, 8, 52]
ROLLING_WINDOWS = [4, 8, 12]

# Risk Engine Thresholds
STOCKOUT_HIGH_THRESHOLD = 0.5
OVERSTOCK_HIGH_THRESHOLD = 0.5
OVERSTOCK_FORWARD_WEEKS = 8

# Model selection options
AVAILABLE_MODELS = ["RandomForest", "GradientBoosting", "LightGBM"]

# Reorder settings
DEFAULT_SERVICE_LEVEL = 1.64  # 95% service level factor (Z-score)
