import pandas as pd
import numpy as np
from Project_FORESIGHT.config import DEFAULT_SERVICE_LEVEL

def calculate_safety_stock_and_rop(fc: pd.DataFrame, inv_latest: pd.DataFrame, 
                                   hist_demand_std: pd.Series) -> tuple:
    """Compute Safety Stock and Reorder Point (ROP) for all SKUs.
    Safety Stock = Z-score * std_dev * sqrt(lead_time_weeks)
    ROP = Lead Time Demand + Safety Stock
    """
    safety_stocks = {}
    rops = {}
    
    # Calculate Lead time in weeks
    lead_weeks = (inv_latest["lead_time_days"] / 7.0).clip(lower=1.0)
    
    for sku_id, row in inv_latest.iterrows():
        l_weeks = lead_weeks.get(sku_id, 2.0)
        std_val = hist_demand_std.get(sku_id, 5.0)
        
        # Safety Stock formula
        sf = DEFAULT_SERVICE_LEVEL * std_val * np.sqrt(l_weeks)
        safety_stocks[sku_id] = float(sf)
        
        # Lead Time Demand sum from forecast
        sku_fc = fc[fc["sku_id"] == sku_id].sort_values("forecast_step")
        if not sku_fc.empty:
            lead_steps = int(np.ceil(l_weeks))
            lt_demand = sku_fc.iloc[:lead_steps]["forecast_units"].sum()
        else:
            lt_demand = 0.0
            
        rop = lt_demand + sf
        rops[sku_id] = float(rop)
        
    return pd.Series(safety_stocks), pd.Series(rops)

def calculate_stockout_risk(fc: pd.DataFrame, inv_latest: pd.DataFrame, rops: pd.Series) -> pd.Series:
    """Stockout Risk = (ROP - Covering Stock) / ROP, bounded [0, 1]
    Where Covering Stock = on_hand + on_order.
    """
    covering_stock = inv_latest["on_hand_units"] + inv_latest["on_order_units"]
    shortfall = rops - covering_stock
    risk = shortfall / rops.replace(0, np.nan)
    return risk.clip(0.0, 1.0).fillna(0.0)
