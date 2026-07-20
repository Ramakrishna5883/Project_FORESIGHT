import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from Project_FORESIGHT.config import MODELS_DIR
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("preprocessing")

# Feature columns we train our model on
FEATURE_COLS = [
    "lag_1", "lag_2", "lag_3", "lag_4", "lag_7", "lag_8", "lag_14", "lag_30", "lag_52",
    "roll_mean_4", "roll_std_4", "roll_mean_8", "roll_std_8", "roll_mean_12", "roll_std_12",
    "woy_sin", "woy_cos", "month", "promo_days_last_wk", "cat_code",
    "average_selling_price", "days_of_inventory", "inventory_turnover"
]

def preprocess_for_training(df: pd.DataFrame, fit_scaler: bool = True) -> tuple:
    """Preprocess features, drop NaNs, and optionally fit and save standard scaler."""
    df_clean = df.dropna(subset=FEATURE_COLS + ["units_sold"]).copy()
    
    X = df_clean[FEATURE_COLS]
    y = df_clean["units_sold"]
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    scaler_path = MODELS_DIR / "scaler.pkl"
    
    if fit_scaler:
        logger.info("Fitting standard scaler on features...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        joblib.dump(scaler, scaler_path)
        logger.info(f"Scaler saved to {scaler_path}")
    else:
        if scaler_path.exists():
            logger.info("Loading existing scaler...")
            scaler = joblib.load(scaler_path)
            X_scaled = scaler.transform(X)
        else:
            logger.warning("No scaler found, returning raw features.")
            X_scaled = X.values
            
    return X_scaled, y, df_clean
