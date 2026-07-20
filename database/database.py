import sqlite3
import pandas as pd
from pathlib import Path
from Project_FORESIGHT.config import DB_PATH
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("database")

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))

def init_db():
    """Initialise SQLite tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Logs / Pipeline runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        message TEXT
    )
    """)
    
    # Forecasts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecasts (
        sku_id TEXT,
        week_start TEXT,
        forecast_step INTEGER,
        forecast_units REAL,
        forecast_lo80 REAL,
        forecast_hi80 REAL,
        PRIMARY KEY (sku_id, week_start)
    )
    """)
    
    # Risk scores table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_scores (
        sku_id TEXT PRIMARY KEY,
        stockout_risk REAL,
        overstock_risk REAL,
        on_hand_units REAL,
        on_order_units REAL,
        lead_time_days REAL,
        reorder_point REAL,
        category TEXT,
        subcategory TEXT,
        unit_cost REAL,
        list_price REAL,
        forecast_units_fwd REAL,
        risk_quadrant TEXT,
        recommended_action TEXT,
        sales_at_risk_rupees REAL,
        capital_locked_rupees REAL,
        revenue_at_stake_rupees REAL,
        safety_stock REAL,
        eoq REAL,
        reorder_qty REAL,
        priority_score REAL
    )
    """)

    # Model metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_metrics (
        model_name TEXT PRIMARY KEY,
        wape REAL,
        bias REAL,
        mae REAL,
        rmse REAL,
        mape REAL,
        r2 REAL
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialised.")

def save_df_to_table(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    """Generic helper to save a pandas DataFrame into SQLite table."""
    df = df.copy()
    for col in df.columns:
        # Check if column is Period or has Period objects
        if isinstance(df[col].dtype, pd.PeriodDtype):
            df[col] = df[col].astype(str)
        elif df[col].apply(lambda x: isinstance(x, pd.Period)).any() if len(df) > 0 else False:
            df[col] = df[col].astype(str)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
            
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    conn.close()
    logger.info(f"Saved {len(df)} rows to table '{table_name}'.")

def load_table_as_df(table_name: str) -> pd.DataFrame:
    """Load SQLite table as a pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        logger.error(f"Error loading table {table_name}: {e}")
        df = pd.DataFrame()
    conn.close()
    return df
