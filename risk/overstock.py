import pandas as pd
import numpy as np

def calculate_eoq(avg_weekly_demand: pd.Series, unit_costs: pd.Series, 
                  order_cost: float = 1000.0, holding_rate: float = 0.20) -> pd.Series:
    """Calculate Economic Order Quantity (EOQ) for all SKUs.
    EOQ = sqrt( (2 * D * S) / H )
    D = Annual Demand (weekly demand * 52)
    S = Order/Setup Cost (default: 1000 INR)
    H = Annual Holding Cost per unit (holding_rate * unit_cost)
    """
    annual_demand = avg_weekly_demand * 52.0
    holding_cost = (unit_costs * holding_rate).clip(lower=1.0) # avoid division by zero
    
    eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost)
    return eoq.fillna(10.0).round(0)

def calculate_overstock_risk(fc: pd.DataFrame, inv_latest: pd.DataFrame, 
                             forward_weeks: int = 8) -> pd.Series:
    """Overstock Risk: Compare on-hand stock against forecast demand over the forward window.
    Risk rises as on-hand stock cover exceeds the forward demand.
    """
    demand_fwd = fc[fc["forecast_step"] <= forward_weeks].groupby("sku_id")["forecast_units"].sum()
    on_hand = inv_latest["on_hand_units"]
    
    merged = pd.concat([demand_fwd.rename("demand_fwd"), on_hand], axis=1).dropna()
    excess = merged["on_hand_units"] - merged["demand_fwd"]
    
    risk = excess / merged["on_hand_units"].replace(0, np.nan)
    return risk.clip(0.0, 1.0).fillna(0.0)
