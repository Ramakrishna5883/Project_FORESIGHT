import pandas as pd
import numpy as np
import joblib
from Project_FORESIGHT.pipeline.preprocessing import FEATURE_COLS
from Project_FORESIGHT.pipeline.feature_engineering import engineer_features
from Project_FORESIGHT.config import MODELS_DIR, FORECAST_HORIZON
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("predictor")

def load_best_model():
    model_path = MODELS_DIR / "best_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not trained. File not found: {model_path}")
    return joblib.load(model_path)

def compute_sku_residuals(df: pd.DataFrame, model) -> pd.Series:
    """Calculate the standard deviation of residuals for each SKU, falling back to a global average."""
    hist = df.dropna(subset=FEATURE_COLS + ["units_sold"]).copy()
    if hist.empty:
        return pd.Series(dtype=float)
        
    hist["pred"] = np.clip(model.predict(hist[FEATURE_COLS]), 0, None)
    hist["resid"] = hist["units_sold"] - hist["pred"]
    
    # Standard deviation of residuals per SKU
    sku_stds = hist.groupby("sku_id")["resid"].std()
    global_std = hist["resid"].std()
    
    # Fill missing or zero SKU std dev with global
    sku_stds = sku_stds.fillna(global_std)
    sku_stds.loc[sku_stds == 0] = global_std
    
    return sku_stds

def generate_forecasts(df: pd.DataFrame, horizon: int = FORECAST_HORIZON, 
                       model_wins_vs_baseline: bool = True) -> pd.DataFrame:
    """Generate recursive multi-step forecasts for the next N weeks for all SKUs."""
    logger.info(f"Generating forecasts for the next {horizon} weeks...")
    model = load_best_model()
    sku_stds = compute_sku_residuals(df, model)
    
    work = df.copy()
    last_period = work["period"].max()
    out_rows = []
    
    for step in range(1, horizon + 1):
        target_period = last_period + step
        new_rows = []
        
        # Build dummy rows for the next week
        for sku_id, g in work.groupby("sku_id"):
            g = g.sort_values("week_start")
            last_row = g.iloc[-1]
            new_row = {
                "sku_id": sku_id,
                "period": target_period,
                "week_start": last_row["week_start"] + pd.Timedelta(weeks=1),
                "category": last_row["category"],
                "subcategory": last_row.get("subcategory"),
                "unit_cost": last_row.get("unit_cost"),
                "list_price": last_row.get("list_price"),
                "lead_time_days": last_row.get("lead_time_days"),
                "reorder_point": last_row.get("reorder_point"),
                "promo_days": 0,
                "revenue": np.nan,
                "units_sold": np.nan,
                "on_hand_units": last_row.get("on_hand_units"), # keep latest inventory static for lag features
                "on_order_units": last_row.get("on_order_units")
            }
            new_rows.append(new_row)
            
        new_df = pd.DataFrame(new_rows)
        work = pd.concat([work, new_df], ignore_index=True)
        
        # Re-engineer features to populate the lags of predictions
        work = engineer_features(work)
        
        pred_mask = work["period"] == target_period
        
        if model_wins_vs_baseline:
            feat_ready = work.loc[pred_mask, FEATURE_COLS].notna().all(axis=1)
            idx = work.loc[pred_mask].index
            valid_idx = idx[feat_ready.values]
            fallback_idx = idx[~feat_ready.values]
            
            if len(valid_idx) > 0:
                preds_valid = np.clip(model.predict(work.loc[valid_idx, FEATURE_COLS]), 0, None)
                work.loc[valid_idx, "units_sold"] = preds_valid
                
            if len(fallback_idx) > 0:
                work.loc[fallback_idx, "units_sold"] = work.loc[fallback_idx, "seasonal_naive"].fillna(0)
        else:
            work.loc[pred_mask, "units_sold"] = work.loc[pred_mask, "seasonal_naive"].fillna(0)
            
        # Add prediction intervals (80% confidence interval: z-score = 1.28)
        for idx in work.loc[pred_mask].index:
            sku_id = work.at[idx, "sku_id"]
            fc_val = work.at[idx, "units_sold"]
            sigma = sku_stds.get(sku_id, fc_val * 0.3)
            
            work.at[idx, "forecast_lo80"] = max(0.0, fc_val - 1.28 * sigma)
            work.at[idx, "forecast_hi80"] = fc_val + 1.28 * sigma
            
        work.loc[pred_mask, "forecast_step"] = step
        out_rows.append(work.loc[pred_mask].copy())
        
    forecast_df = pd.concat(out_rows, ignore_index=True)
    forecast_df = forecast_df.rename(columns={"units_sold": "forecast_units"})
    
    logger.info("Forecast generation complete.")
    return forecast_df[["sku_id", "period", "week_start", "forecast_step",
                         "forecast_units", "forecast_lo80", "forecast_hi80"]]
