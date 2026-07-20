import os
import shutil
import time
import pandas as pd
import numpy as np
from pathlib import Path

# Fix relative import paths
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Project_FORESIGHT.config import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, FORECAST_HORIZON
)
from Project_FORESIGHT.database.database import init_db, save_df_to_table
from Project_FORESIGHT.pipeline.ingest import ingest_raw_files
from Project_FORESIGHT.pipeline.validation import validate_datasets
from Project_FORESIGHT.pipeline.cleaning import clean_all_datasets
from Project_FORESIGHT.pipeline.merge import merge_to_weekly_panel
from Project_FORESIGHT.pipeline.feature_engineering import engineer_features
from Project_FORESIGHT.pipeline.preprocessing import preprocess_for_training
from Project_FORESIGHT.forecasting.trainer import select_and_train_best_model
from Project_FORESIGHT.forecasting.predictor import generate_forecasts
from Project_FORESIGHT.risk.stockout import calculate_safety_stock_and_rop, calculate_stockout_risk
from Project_FORESIGHT.risk.overstock import calculate_eoq, calculate_overstock_risk
from Project_FORESIGHT.risk.decision_engine import compute_decision_matrix
from Project_FORESIGHT.risk.recommendation import attach_recommendations
from Project_FORESIGHT.reports.executive_summary import generate_markdown_summary
from Project_FORESIGHT.reports.generate_pdf import generate_pdf_report
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("run_pipeline")

def ensure_raw_data():
    """Copy raw data from old foresight dir if available, or generate it."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    required = ["sku_master.csv", "calendar.csv", "sales_daily.csv", "inventory_snapshots.csv"]
    
    missing = [f for f in required if not (RAW_DATA_DIR / f).exists()]
    if not missing:
        return
        
    logger.info(f"Raw data files missing from {RAW_DATA_DIR}. Attempting to copy from existing extracts...")
    
    old_raw_dir = Path(__file__).resolve().parent.parent / "foresight_project" / "foresight" / "data" / "raw"
    alt_raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    
    copied = 0
    for f in required:
        for source_dir in [old_raw_dir, alt_raw_dir]:
            source_file = source_dir / f
            if source_file.exists():
                shutil.copy(source_file, RAW_DATA_DIR / f)
                logger.info(f"Copied {f} from {source_dir.parent.name}")
                copied += 1
                break
                
    if copied < len(required):
        logger.info("Some raw files still missing. Running generate_data fallback...")
        from Project_FORESIGHT.src.generate_data import main as generate_fallback
        generate_fallback()

def run_pipeline_end_to_end():
    logger.info("Initializing FORESIGHT Inventory Intelligence Pipeline...")
    t0 = time.time()
    
    # 1. Initialize SQLite Database
    init_db()
    
    # 2. Ensure raw data exists
    ensure_raw_data()
    
    # 3. Ingestion
    logger.info("Stage 1: Ingesting raw datasets...")
    raw_datasets = ingest_raw_files()
    
    # 4. Validation
    logger.info("Stage 2: Validating schemas and constraints...")
    if not validate_datasets(raw_datasets):
        logger.warning("Pipeline encountered validation issues (review logs). Continuing...")
        
    # 5. Cleaning
    logger.info("Stage 3: Cleaning datasets...")
    cleaned_datasets = clean_all_datasets(raw_datasets)
    
    # 6. Merge
    logger.info("Stage 4: Merging to weekly SKU-level panel...")
    weekly_panel = merge_to_weekly_panel(
        cleaned_datasets["sales_daily"],
        cleaned_datasets["sku_master"],
        cleaned_datasets["calendar"],
        cleaned_datasets["inventory_snapshots"]
    )
    
    # 7. Feature Engineering
    logger.info("Stage 5: Engineering features...")
    featured_panel = engineer_features(weekly_panel)
    
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    featured_panel.to_csv(PROCESSED_DATA_DIR / "analysis_ready.csv", index=False)
    
    # 8. Preprocessing
    logger.info("Stage 6: Preprocessing features...")
    X_scaled, y, train_ready_df = preprocess_for_training(featured_panel, fit_scaler=True)
    
    # 9. Train and select model
    logger.info("Stage 7: Selecting and training best forecasting model...")
    fit_metrics = select_and_train_best_model(featured_panel)
    
    # 10. Generate Forecasts
    logger.info("Stage 8: Generating 6-week recursive forecasts...")
    forecast_df = generate_forecasts(featured_panel, horizon=FORECAST_HORIZON, 
                                     model_wins_vs_baseline=fit_metrics["model_wins_vs_baseline"])
    forecast_df.to_csv(PROCESSED_DATA_DIR / "forecast.csv", index=False)
    
    # Save forecasts to SQLite
    save_df_to_table(forecast_df, "forecasts", if_exists="replace")
    
    # 11. Risk Engine calculations
    logger.info("Stage 9: Executing Risk Engine and Decision logic...")
    inv = cleaned_datasets["inventory_snapshots"]
    inv_latest = (
        inv.sort_values("date").groupby("sku_id").tail(1).set_index("sku_id")
    )
    
    # std deviation of historical demand per SKU
    hist_std = train_ready_df.groupby("sku_id")["units_sold"].std().fillna(5.0)
    avg_weekly_demand = train_ready_df.groupby("sku_id")["units_sold"].mean().fillna(5.0)
    
    safety_stock, rops = calculate_safety_stock_and_rop(forecast_df, inv_latest, hist_std)
    
    sku_master_clean = cleaned_datasets["sku_master"].set_index("sku_id")
    
    # Risk Dataframe construction
    risk_df = pd.DataFrame(index=inv_latest.index)
    risk_df["on_hand_units"] = inv_latest["on_hand_units"]
    risk_df["on_order_units"] = inv_latest["on_order_units"]
    risk_df["lead_time_days"] = inv_latest["lead_time_days"]
    risk_df["reorder_point"] = inv_latest["reorder_point"]
    
    risk_df = risk_df.join(sku_master_clean[["category", "subcategory", "unit_cost", "list_price"]], how="left")
    
    # Demand forecast sums
    fwd_demand = forecast_df.groupby("sku_id")["forecast_units"].sum()
    risk_df["forecast_units_fwd"] = fwd_demand
    
    # safety stock & ROP
    risk_df["safety_stock"] = safety_stock
    risk_df["reorder_point_calc"] = rops
    
    # Calculate risks
    risk_df["stockout_risk"] = calculate_stockout_risk(forecast_df, inv_latest, rops)
    risk_df["overstock_risk"] = calculate_overstock_risk(forecast_df, inv_latest)
    
    # Economic Order Quantity
    risk_df["eoq"] = calculate_eoq(avg_weekly_demand, risk_df["unit_cost"])
    
    # Latest historical metrics
    latest_turnover = train_ready_df.sort_values("week_start").groupby("sku_id")["inventory_turnover"].last()
    latest_days_of_inv = train_ready_df.sort_values("week_start").groupby("sku_id")["days_of_inventory"].last()
    
    risk_df["inventory_turnover"] = latest_turnover
    risk_df["days_of_inventory"] = latest_days_of_inv
    
    # Financial metrics
    lead_weeks = np.ceil(risk_df["lead_time_days"] / 7.0).clip(lower=1.0)
    demand_over_lead = forecast_df.groupby("sku_id").apply(
        lambda g: g.sort_values("forecast_step").iloc[:int(np.ceil(lead_weeks.get(g.name, 2.0)))]["forecast_units"].sum(),
        include_groups=False
    )
    
    covering_stock = risk_df["on_hand_units"] + risk_df["on_order_units"]
    shortfall = (demand_over_lead - covering_stock).clip(lower=0)
    
    # sales_at_risk_rupees
    risk_df["sales_at_risk_rupees"] = np.where(
        risk_df["stockout_risk"] >= 0.5,
        shortfall * risk_df["list_price"],
        0.0
    )
    
    # capital_locked_rupees
    excess_units = (risk_df["on_hand_units"] - risk_df["forecast_units_fwd"]).clip(lower=0)
    risk_df["capital_locked_rupees"] = np.where(
        risk_df["overstock_risk"] >= 0.5,
        excess_units * risk_df["unit_cost"],
        0.0
    )
    risk_df["revenue_at_stake_rupees"] = risk_df["sales_at_risk_rupees"] + risk_df["capital_locked_rupees"]
    
    # Quadrant and priorities
    risk_df = compute_decision_matrix(risk_df)
    
    # Formatting planner text recommendations
    risk_df = attach_recommendations(risk_df)
    
    # Save risk scores to CSV
    risk_scores_path = PROCESSED_DATA_DIR / "risk_scores.csv"
    risk_df.to_csv(risk_scores_path, index=True)
    
    # Save risk scores to SQLite
    save_df_to_table(risk_df.reset_index(), "risk_scores", if_exists="replace")
    
    # 12. Reporting
    logger.info("Stage 10: Generating reports...")
    generate_markdown_summary(risk_df.reset_index(), fit_metrics)
    generate_pdf_report(risk_df.reset_index(), fit_metrics)
    
    elapsed = time.time() - t0
    logger.info(f"Pipeline executed successfully in {elapsed:.2f} seconds.")
    
    # Log run details to pipeline_runs table
    try:
        from Project_FORESIGHT.database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pipeline_runs (status, message) VALUES (?, ?)", 
                       ("SUCCESS", f"Run complete in {elapsed:.2f}s. Model: {fit_metrics['model_name']}"))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging run details to DB: {e}")

if __name__ == "__main__":
    run_pipeline_end_to_end()
