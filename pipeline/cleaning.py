import pandas as pd
import numpy as np
from Project_FORESIGHT.utils.constants import CATEGORY_MAP
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("cleaning")

def clean_sku_master(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Deduplicate by sku_id
    before = len(df)
    df = df.drop_duplicates(subset="sku_id")
    logger.info(f"sku_master: Dropped {before - len(df)} duplicate SKU rows.")
    
    # Category mapping
    if "category" in df.columns:
        df["category"] = df["category"].str.strip().map(lambda x: CATEGORY_MAP.get(str(x).lower(), x))
    
    # Enforce numeric types
    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce")
    df["list_price"] = pd.to_numeric(df["list_price"], errors="coerce")
    
    # Fill potential NaNs in cost or price using category medians
    if "unit_cost" in df.columns:
        df["unit_cost"] = df.groupby("category")["unit_cost"].transform(lambda x: x.fillna(x.median()))
    if "list_price" in df.columns:
        df["list_price"] = df.groupby("category")["list_price"].transform(lambda x: x.fillna(x.median()))
        
    return df

def clean_calendar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    df["is_holiday"] = df["is_holiday"].fillna(0).astype(int)
    return df

def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"sales_daily: Dropped {before - len(df)} duplicate rows.")
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    
    # Floor negative units sold to 0
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0)
    df.loc[df["units_sold"] < 0, "units_sold"] = 0
    
    # Impute missing unit prices with SKU's median price, or global median
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["unit_price"] = df.groupby("sku_id")["unit_price"].transform(lambda s: s.fillna(s.median()))
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    
    # Recompute/fix revenue if missing/invalid
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    recomputed = df["units_sold"] * df["unit_price"]
    bad_revenue = df["revenue"].isna() | (df["revenue"] < 0)
    df.loc[bad_revenue, "revenue"] = recomputed[bad_revenue]
    
    df["promo_flag"] = df["promo_flag"].fillna(0).astype(int)
    return df

def clean_inventory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"inventory_snapshots: Dropped {before - len(df)} duplicate rows.")
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    
    df["on_hand_units"] = pd.to_numeric(df["on_hand_units"], errors="coerce").fillna(0).clip(lower=0)
    df["on_order_units"] = pd.to_numeric(df["on_order_units"], errors="coerce").fillna(0).clip(lower=0)
    
    df["lead_time_days"] = pd.to_numeric(df["lead_time_days"], errors="coerce").fillna(14)
    df["reorder_point"] = pd.to_numeric(df["reorder_point"], errors="coerce").fillna(0)
    
    return df

def clean_all_datasets(datasets: dict) -> dict:
    cleaned = {
        "sku_master": clean_sku_master(datasets["sku_master"]),
        "calendar": clean_calendar(datasets["calendar"]),
        "sales_daily": clean_sales(datasets["sales_daily"]),
        "inventory_snapshots": clean_inventory(datasets["inventory_snapshots"])
    }
    return cleaned
