import pandas as pd
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("merge")

def merge_to_weekly_panel(sales: pd.DataFrame, sku: pd.DataFrame, 
                           cal: pd.DataFrame, inv: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily sales to weekly, join metadata, and merge inventory as-of week start."""
    logger.info("Merging datasets to weekly SKU-level panel...")
    
    # Merge daily sales with calendar
    sales = sales.merge(
        cal[["date", "week", "month", "season", "is_holiday", "promo_event"]],
        on="date", how="left"
    )
    sales["iso_year"] = sales["date"].dt.isocalendar().year
    sales["iso_week"] = sales["date"].dt.isocalendar().week
    
    # Aggregate to weekly level
    weekly = (
        sales.groupby(["sku_id", "iso_year", "iso_week"])
        .agg(
            units_sold=("units_sold", "sum"),
            revenue=("revenue", "sum"),
            avg_price=("unit_price", "mean"),
            promo_days=("promo_flag", "sum"),
            week_start=("date", "min"),
        )
        .reset_index()
    )
    
    # Merge SKU Master metadata
    weekly = weekly.merge(sku, on="sku_id", how="left")
    
    # Merge inventory snapshots as of the week start (using pd.merge_asof)
    inv_sorted = inv.sort_values("date")
    weekly = weekly.sort_values("week_start")
    
    merged = pd.merge_asof(
        weekly, inv_sorted,
        left_on="week_start", right_on="date",
        by="sku_id", direction="backward",
        suffixes=("", "_inv")
    )
    
    # Cleanup unnecessary date column from inventory
    if "date" in merged.columns:
        merged = merged.drop(columns=["date"])
        
    logger.info(f"Weekly panel built successfully with {len(merged)} rows.")
    return merged
