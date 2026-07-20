import pandas as pd
import numpy as np

def format_rupees(val: float) -> str:
    """Format rupee values into human-readable strings."""
    if pd.isna(val) or val is None:
        return "₹0"
    if val >= 10000000:
        return f"₹{val / 10000000:.2f} Cr"
    if val >= 100000:
        return f"₹{val / 100000:.2f} Lakh"
    return f"₹{val:,.2f}"

def safe_divide(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """Safely divide numerator by denominator, returning fallback if denominator is zero or NaN."""
    if pd.isna(denominator) or denominator == 0:
        return fallback
    val = numerator / denominator
    return fallback if pd.isna(val) else val
