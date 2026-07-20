import pandas as pd
from Project_FORESIGHT.utils.helpers import format_rupees

def generate_sku_recommendation_text(row) -> str:
    """Generate professional, action-oriented recommendations for planners."""
    quadrant = row["risk_quadrant"]
    sku_id = row["sku_id"] if "sku_id" in row.index else row.name
    reorder_qty = int(row["reorder_qty"])
    sales_at_risk = format_rupees(row["sales_at_risk_rupees"])
    capital_locked = format_rupees(row["capital_locked_rupees"])
    
    if quadrant == "Reorder Now":
        return (
            f"Replenish {sku_id} immediately. "
            f"Recommended order size: {reorder_qty:,} units (EOQ: {int(row['eoq']):,}). "
            f"Delay puts {sales_at_risk} in sales at risk."
        )
    elif quadrant == "Markdown / Clear":
        return (
            f"Markdown candidate. Excess stock on hand is locking {capital_locked} in capital. "
            f"Recommend a promo or 15-25% markdown to clear excess before holding costs erode margin."
        )
    elif quadrant == "Watch / Volatile":
        return (
            f"Review manually. High demand variance detected. "
            f"On hand covers less than lead time, but safety stock requirements are highly volatile."
        )
    else:
        return (
            f"Healthy inventory levels. No action required. "
            f"On hand covers forward demand and safety stock is within limits."
        )

def attach_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["recommendation_details"] = df.apply(generate_sku_recommendation_text, axis=1)
    return df
