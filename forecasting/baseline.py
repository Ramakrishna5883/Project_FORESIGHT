import pandas as pd
import numpy as np

class SeasonalNaiveBaseline:
    """Seasonal Naive baseline forecaster.
    Predicts demand using the same week last year (52 weeks lag).
    Falls back to lag 1 for newer SKUs with less than a year of history.
    """
    def __init__(self):
        pass
        
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Return the seasonal naive predictions from the dataframe column."""
        if "seasonal_naive" in df.columns:
            return df["seasonal_naive"].fillna(0)
            
        # fallback calculation in case it wasn't engineered
        df_sorted = df.sort_values(["sku_id", "week_start"])
        preds = df_sorted.groupby("sku_id")["units_sold"].shift(52)
        preds = preds.fillna(df_sorted.groupby("sku_id")["units_sold"].shift(1))
        return preds.fillna(0)
