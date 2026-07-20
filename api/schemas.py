from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    data_loaded: bool
    skus_count: int

class ForecastPoint(BaseModel):
    week_start: str
    forecast_step: int
    forecast_units: float
    forecast_lo80: float
    forecast_hi80: float

class SkuForecastResponse(BaseModel):
    sku_id: str
    forecast: List[ForecastPoint]

class SkuRiskResponse(BaseModel):
    sku_id: str
    stockout_risk: float
    overstock_risk: float
    risk_quadrant: str
    recommended_action: str
    sales_at_risk_rupees: float
    capital_locked_rupees: float
    revenue_at_stake_rupees: float
    safety_stock: float
    eoq: float
    reorder_qty: float

class PredictRequest(BaseModel):
    sku_ids: List[str]

class PredictResponse(BaseModel):
    results: List[Dict[str, Any]]

class ModelMetricResponse(BaseModel):
    model_name: str
    wape: float
    bias: float
    mae: float
    rmse: float
    mape: float
    r2: float

class DashboardDataResponse(BaseModel):
    total_skus: int
    reorder_now_count: int
    markdown_clear_count: int
    total_sales_at_risk: float
    total_capital_locked: float
