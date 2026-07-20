import pandas as pd
import numpy as np
from Project_FORESIGHT.pipeline.preprocessing import FEATURE_COLS
from Project_FORESIGHT.forecasting.metrics import wape, bias
from Project_FORESIGHT.config import N_BACKTEST_FOLDS, FORECAST_HORIZON
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("cross_validation")

def rolling_origin_cv(df: pd.DataFrame, model_class, model_kwargs: dict, 
                      horizon: int = FORECAST_HORIZON, n_folds: int = N_BACKTEST_FOLDS) -> pd.DataFrame:
    """Perform rolling-origin cross validation and return fold-level results for each step."""
    logger.info(f"Starting rolling-origin CV with {n_folds} folds and horizon {horizon}...")
    periods = sorted(df["period"].unique())
    
    # We need enough history for lag_52 (which is min 52 weeks)
    if len(periods) < 52 + horizon + n_folds:
        logger.warning("Not enough periods for a full rolling-origin CV. Adjusting splits.")
        usable = periods[min(len(periods)-1, 53):]
    else:
        usable = periods[52 + horizon:]
        
    if len(usable) < n_folds + 1:
        n_folds = max(1, len(usable) - 2)
        
    fold_cuts = usable[-(n_folds + horizon):-horizon]
    results = []
    
    for fold, cut in enumerate(fold_cuts):
        logger.info(f"CV Fold {fold+1}/{n_folds} (cut: {cut})...")
        
        train = df[df["period"] <= cut].dropna(subset=FEATURE_COLS + ["units_sold"])
        if len(train) < 50:
            logger.warning(f"Fold {fold+1}: Training size too small ({len(train)}). Skipping.")
            continue
            
        model = model_class(**model_kwargs)
        model.fit(train[FEATURE_COLS], train["units_sold"])
        
        for step in range(1, horizon + 1):
            test_period = cut + step
            test = df[df["period"] == test_period].dropna(subset=["seasonal_naive"])
            if len(test) == 0:
                continue
                
            test_feat = test.dropna(subset=FEATURE_COLS)
            if len(test_feat) == 0:
                continue
                
            preds = np.clip(model.predict(test_feat[FEATURE_COLS]), 0, None)
            
            results.append({
                "fold": fold + 1,
                "cut_period": str(cut),
                "horizon_step": step,
                "n_test": len(test_feat),
                "wape_baseline": wape(test_feat["units_sold"], test_feat["seasonal_naive"]),
                "wape_model": wape(test_feat["units_sold"], preds),
                "bias_model": bias(test_feat["units_sold"], preds),
            })
            
    return pd.DataFrame(results)
