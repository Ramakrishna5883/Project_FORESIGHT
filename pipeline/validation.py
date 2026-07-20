import pandas as pd
import re
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("validation")

def validate_datasets(datasets: dict) -> bool:
    """Validate schemas, dates, negative values, duplicates, and SKU format."""
    is_valid = True
    
    # 1. Validation of SKU Master
    sku = datasets["sku_master"]
    logger.info("Validating sku_master...")
    if "sku_id" not in sku.columns:
        logger.error("sku_master missing 'sku_id' column.")
        is_valid = False
    else:
        # Check SKU ID format (NBL-xxxx)
        bad_skus = sku[~sku["sku_id"].astype(str).str.match(r"^NBL-\d+$")]
        if not bad_skus.empty:
            logger.warning(f"sku_master: Found {len(bad_skus)} invalid SKU IDs: {bad_skus['sku_id'].tolist()}")
            
    # Check duplicate SKU IDs
    dupes = sku["sku_id"].duplicated().sum()
    if dupes > 0:
        logger.warning(f"sku_master: Found {dupes} duplicate SKU IDs.")
        
    # Check negative cost/price
    for col in ["unit_cost", "list_price"]:
        if col in sku.columns:
            negatives = (sku[col] < 0).sum()
            if negatives > 0:
                logger.warning(f"sku_master: Found {negatives} negative values in {col}.")
                
    # 2. Validation of Sales Daily
    sales = datasets["sales_daily"]
    logger.info("Validating sales_daily...")
    required_sales = ["date", "sku_id", "units_sold", "unit_price"]
    for col in required_sales:
        if col not in sales.columns:
            logger.error(f"sales_daily missing required column '{col}'")
            is_valid = False
            
    if "units_sold" in sales.columns:
        neg_sales = (sales["units_sold"] < 0).sum()
        if neg_sales > 0:
            logger.warning(f"sales_daily: Found {neg_sales} negative sales units (will be cleaned).")
            
    # 3. Validation of Inventory Snapshots
    inv = datasets["inventory_snapshots"]
    logger.info("Validating inventory_snapshots...")
    required_inv = ["date", "sku_id", "on_hand_units"]
    for col in required_inv:
        if col not in inv.columns:
            logger.error(f"inventory_snapshots missing required column '{col}'")
            is_valid = False
            
    if "on_hand_units" in inv.columns:
        neg_inv = (inv["on_hand_units"] < 0).sum()
        if neg_inv > 0:
            logger.warning(f"inventory_snapshots: Found {neg_inv} negative on-hand values (will be cleaned).")

    # 4. Check Date formats in sales and inventory
    for df_name, df in [("sales_daily", sales), ("inventory_snapshots", inv)]:
        if "date" in df.columns:
            parsed_dates = pd.to_datetime(df["date"], errors="coerce")
            invalid_dates = parsed_dates.isna().sum()
            if invalid_dates > 0:
                logger.warning(f"{df_name}: Found {invalid_dates} invalid date strings.")
                
    return is_valid
