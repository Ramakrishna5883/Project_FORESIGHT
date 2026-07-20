import pandas as pd
import numpy as np
from Project_FORESIGHT.forecasting.metrics import wape, bias, mae, rmse, mape, r2

class ModelEvaluator:
    """Evaluates time series forecasting models and outputs comprehensive diagnostic reports."""
    
    @staticmethod
    def evaluate(y_true, y_pred, y_lo=None, y_hi=None) -> dict:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        
        metrics = {
            "wape": wape(y_true, y_pred),
            "bias": bias(y_true, y_pred),
            "mae": mae(y_true, y_pred),
            "rmse": rmse(y_true, y_pred),
            "mape": mape(y_true, y_pred),
            "r2": r2(y_true, y_pred)
        }
        
        if y_lo is not None and y_hi is not None:
            y_lo = np.asarray(y_lo, dtype=float)
            y_hi = np.asarray(y_hi, dtype=float)
            # Coverage: share of actuals inside the prediction interval
            coverage = np.mean((y_true >= y_lo) & (y_true <= y_hi))
            metrics["interval_coverage"] = float(coverage)
            
        return metrics
