import pandas as pd
import numpy as np
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("feature_engineering")

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer time-series lags, rolling windows, calendar, and inventory features."""
    logger.info("Engineering features for the weekly panel...")
    df = df.sort_values(["sku_id", "week_start"]).copy()
    
    # Add period column for continuous time tracking
    df["period"] = pd.to_datetime(df["week_start"]).dt.to_period("W-MON")
    
    # Calendar features
    df["year"] = df["week_start"].dt.year
    df["quarter"] = df["week_start"].dt.quarter
    df["month"] = df["week_start"].dt.month
    df["week"] = df["week_start"].dt.isocalendar().week.astype(int)
    df["day"] = df["week_start"].dt.day
    
    # Cosine/sine week of year for cyclic time encoding
    df["woy_sin"] = np.sin(2 * np.pi * df["week"] / 52.0)
    df["woy_cos"] = np.cos(2 * np.pi * df["week"] / 52.0)
    
    # Promos and Holidays (retaining aggregated metrics)
    df["promo_days_last_wk"] = df.groupby("sku_id")["promo_days"].shift(1).fillna(0)
    
    # Lags (shifted to prevent leakage)
    # Lags requested: Lag 1, Lag 7, Lag 14, Lag 30 (we interpret these as steps in the sorted series)
    # To be extremely robust and match the request exactly, we create lag_1, lag_2, lag_4, lag_8, lag_12, lag_52
    # but we also explicitly add lag_7, lag_14, lag_30. If weekly, lag_7 is 7 weeks.
    g = df.groupby("sku_id")["units_sold"]
    
    # Lags
    lags_to_create = [1, 2, 3, 4, 7, 8, 14, 30, 52]
    for lag in lags_to_create:
        df[f"lag_{lag}"] = g.shift(lag)
        
    # Rolling features (shifted by 1 to prevent data leakage)
    for w in [4, 7, 8, 12, 30]:
        df[f"roll_mean_{w}"] = g.shift(1).rolling(w).mean().reset_index(level=0, drop=True)
        df[f"roll_std_{w}"] = g.shift(1).rolling(w).std().reset_index(level=0, drop=True)
        
    # Pricing metrics
    df["average_selling_price"] = df["avg_price"].fillna(df["list_price"])
    
    # Inventory KPI Metrics
    # Days of Inventory = On Hand Units / (Average Weekly Units Sold / 7)
    # Inventory Turnover = (Weekly Units Sold * Unit Cost) / (On Hand Units * Unit Cost) = Weekly Units Sold / On Hand
    df["inventory_turnover"] = (df["units_sold"] / df["on_hand_units"].replace(0, np.nan)).fillna(0)
    
    # Average weekly sales over 8 weeks to estimate daily rate for Days of Inventory
    avg_sales_8w = g.shift(1).rolling(8).mean().reset_index(level=0, drop=True).fillna(1.0)
    daily_sales_est = (avg_sales_8w / 7.0).clip(lower=0.1)
    df["days_of_inventory"] = (df["on_hand_units"] / daily_sales_est).fillna(0)
    
    # Category Code encoding
    df["cat_code"] = df["category"].astype("category").cat.codes
    
    # Seasonal Naive baseline prediction (52-week lag or fallback to lag_1)
    df["seasonal_naive"] = df.groupby("sku_id")["units_sold"].shift(52)
    df["seasonal_naive"] = df["seasonal_naive"].fillna(df.groupby("sku_id")["units_sold"].shift(1))
    
    logger.info("Feature engineering complete.")
    return df
