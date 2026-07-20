import pandas as pd
import numpy as np
from Project_FORESIGHT.config import STOCKOUT_HIGH_THRESHOLD, OVERSTOCK_HIGH_THRESHOLD
from Project_FORESIGHT.utils.constants import QUADRANT_ACTIONS

def get_risk_quadrant(so_risk: float, ov_risk: float) -> str:
    if so_risk >= STOCKOUT_HIGH_THRESHOLD and ov_risk >= OVERSTOCK_HIGH_THRESHOLD:
        return "Watch / Volatile"
    if so_risk >= STOCKOUT_HIGH_THRESHOLD:
        return "Reorder Now"
    if ov_risk >= OVERSTOCK_HIGH_THRESHOLD:
        return "Markdown / Clear"
    return "Healthy"

def compute_decision_matrix(risk_df: pd.DataFrame) -> pd.DataFrame:
    """Classify SKUs into risk quadrants and compute priority scores and recommended action quantities."""
    df = risk_df.copy()
    
    # Risk quadrant classification
    df["risk_quadrant"] = df.apply(
        lambda r: get_risk_quadrant(r["stockout_risk"], r["overstock_risk"]), 
        axis=1
    )
    df["recommended_action"] = df["risk_quadrant"].map(QUADRANT_ACTIONS)
    
    # Priority Score = max(stockout_risk, overstock_risk) * log10(revenue_at_stake + 1)
    df["priority_score"] = np.maximum(df["stockout_risk"], df["overstock_risk"]) * np.log10(df["revenue_at_stake_rupees"] + 1)
    
    # Recommended Reorder Quantity (if Reorder Now, recommend EOQ or shortfalls to safety stock)
    # Recommended Qty = max(0, ROP - (on_hand + on_order))
    df["reorder_qty"] = np.where(
        df["risk_quadrant"] == "Reorder Now",
        (df["reorder_point"] - (df["on_hand_units"] + df["on_order_units"])).clip(lower=0),
        0.0
    ).round(0)
    
    # If recommended quantity is zero but it's a reorder SKU, default to EOQ
    df.loc[(df["risk_quadrant"] == "Reorder Now") & (df["reorder_qty"] == 0), "reorder_qty"] = df["eoq"]
    
    return df
