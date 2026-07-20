import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from Project_FORESIGHT.pipeline.preprocessing import FEATURE_COLS
from Project_FORESIGHT.forecasting.cross_validation import rolling_origin_cv
from Project_FORESIGHT.forecasting.metrics import wape, bias, mae, rmse, mape, r2
from Project_FORESIGHT.config import MODELS_DIR, REPORTS_DIR, DB_PATH
from Project_FORESIGHT.utils.logger import get_logger
import json

# Try to import LightGBM, fallback to HistGradientBoosting if unavailable
try:
    from lightgbm import LGBMRegressor
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

logger = get_logger("trainer")

def get_model_options() -> dict:
    options = {
        "RandomForest": (RandomForestRegressor, {"n_estimators": 100, "max_depth": 8, "random_state": 42}),
        "GradientBoosting": (GradientBoostingRegressor, {"n_estimators": 100, "max_depth": 5, "random_state": 42})
    }
    if HAS_LGBM:
        options["LightGBM"] = (LGBMRegressor, {"n_estimators": 150, "max_depth": 6, "learning_rate": 0.08, "random_state": 42, "verbose": -1})
    else:
        options["LightGBM"] = (HistGradientBoostingRegressor, {"max_iter": 150, "max_depth": 6, "learning_rate": 0.08, "random_state": 42})
        
    return options

def select_and_train_best_model(df: pd.DataFrame) -> dict:
    """Evaluate models, select the one with the lowest overall WAPE, and train it on the full dataset."""
    logger.info("Starting model selection and training process...")
    
    options = get_model_options()
    cv_scores = {}
    
    for name, (model_cls, kwargs) in options.items():
        logger.info(f"Cross-validating {name}...")
        try:
            cv_results = rolling_origin_cv(df, model_cls, kwargs)
            if not cv_results.empty:
                avg_wape = cv_results["wape_model"].mean()
                avg_bias = cv_results["bias_model"].mean()
                cv_scores[name] = {
                    "wape": avg_wape,
                    "bias": avg_bias,
                    "results_df": cv_results
                }
                logger.info(f"Model {name} CV WAPE: {avg_wape:.4f}, Bias: {avg_bias:.4f}")
            else:
                logger.warning(f"CV results empty for {name}.")
        except Exception as e:
            logger.error(f"Error cross-validating {name}: {e}")
            
    # Baseline comparison (Seasonal Naive)
    baseline_wapes = []
    if len(cv_scores) > 0:
        # get baseline scores from one of the results
        first_model_res = list(cv_scores.values())[0]["results_df"]
        baseline_wape = first_model_res["wape_baseline"].mean()
        logger.info(f"Seasonal Naive Baseline WAPE: {baseline_wape:.4f}")
    else:
        baseline_wape = 999.0
        
    # Choose best model
    best_name = None
    best_wape = 999.0
    
    for name, score in cv_scores.items():
        if score["wape"] < best_wape:
            best_wape = score["wape"]
            best_name = name
            
    if best_name and best_wape < baseline_wape:
        logger.info(f"Winner: {best_name} beats Baseline ({best_wape:.4f} < {baseline_wape:.4f})")
        model_cls, kwargs = options[best_name]
        model_wins = True
    else:
        logger.info(f"Baseline wins or no models trained. Using Seasonal Naive baseline logic.")
        # We fall back to LightGBM (or GB) as the ML model to save anyway, but flag model_wins=False
        best_name = "LightGBM"
        model_cls, kwargs = options[best_name]
        model_wins = False
        
    # Train selected model on all history
    logger.info(f"Training final {best_name} model on all available history...")
    train_data = df.dropna(subset=FEATURE_COLS + ["units_sold"])
    
    final_model = model_cls(**kwargs)
    final_model.fit(train_data[FEATURE_COLS], train_data["units_sold"])
    
    # Save the trained model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "best_model.pkl"
    joblib.dump(final_model, model_path)
    logger.info(f"Saved best model to {model_path}")
    
    # Calculate fit metrics on all history
    preds = np.clip(final_model.predict(train_data[FEATURE_COLS]), 0, None)
    y_true = train_data["units_sold"].values
    
    fit_metrics = {
        "model_name": best_name,
        "wape": float(wape(y_true, preds)),
        "bias": float(bias(y_true, preds)),
        "mae": float(mae(y_true, preds)),
        "rmse": float(rmse(y_true, preds)),
        "mape": float(mape(y_true, preds)),
        "r2": float(r2(y_true, preds)),
        "model_wins_vs_baseline": model_wins,
        "baseline_wape": float(baseline_wape)
    }
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / "backtest_summary.json", "w") as f:
        json.dump(fit_metrics, f, indent=2)
        
    # Also save to DB
    try:
        from Project_FORESIGHT.database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO model_metrics VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (fit_metrics["model_name"], fit_metrics["wape"], fit_metrics["bias"], 
                        fit_metrics["mae"], fit_metrics["rmse"], fit_metrics["mape"], fit_metrics["r2"]))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving model metrics to DB: {e}")
        
    return fit_metrics
