from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import pandas as pd
from Project_FORESIGHT.api.schemas import (
    HealthResponse, SkuForecastResponse, SkuRiskResponse, 
    PredictRequest, PredictResponse, ModelMetricResponse, DashboardDataResponse
)
from Project_FORESIGHT.database.database import load_table_as_df, get_connection
from Project_FORESIGHT.utils.logger import get_logger

router = APIRouter()
logger = get_logger("routes")

@router.get("/health", response_model=HealthResponse)
def health():
    try:
        conn = get_connection()
        conn.close()
        db_connected = True
    except Exception as e:
        logger.error(f"DB Connection failed in health check: {e}")
        db_connected = False
        
    risk_df = load_table_as_df("risk_scores")
    skus_count = len(risk_df)
    
    return HealthResponse(
        status="ok",
        database_connected=db_connected,
        data_loaded=not risk_df.empty,
        skus_count=skus_count
    )

@router.get("/skus", response_model=List[str])
def list_skus():
    risk_df = load_table_as_df("risk_scores")
    if risk_df.empty:
        raise HTTPException(status_code=404, detail="No SKU data loaded in database.")
    return sorted(risk_df["sku_id"].unique().tolist())

@router.get("/forecast", response_model=SkuForecastResponse)
def get_sku_forecast(sku_id: str):
    conn = get_connection()
    query = "SELECT * FROM forecasts WHERE sku_id = ? ORDER BY forecast_step"
    fc_df = pd.read_sql(query, conn, params=[sku_id])
    conn.close()
    
    if fc_df.empty:
        raise HTTPException(status_code=404, detail=f"No forecast found for SKU {sku_id}")
        
    points = [
        {
            "week_start": row["week_start"],
            "forecast_step": int(row["forecast_step"]),
            "forecast_units": float(row["forecast_units"]),
            "forecast_lo80": float(row["forecast_lo80"]),
            "forecast_hi80": float(row["forecast_hi80"])
        } for _, row in fc_df.iterrows()
    ]
    return SkuForecastResponse(sku_id=sku_id, forecast=points)

@router.get("/risk", response_model=SkuRiskResponse)
def get_sku_risk(sku_id: str):
    conn = get_connection()
    query = "SELECT * FROM risk_scores WHERE sku_id = ?"
    risk_df = pd.read_sql(query, conn, params=[sku_id])
    conn.close()
    
    if risk_df.empty:
        raise HTTPException(status_code=404, detail=f"No risk score found for SKU {sku_id}")
        
    r = risk_df.iloc[0]
    return SkuRiskResponse(
        sku_id=sku_id,
        stockout_risk=float(r["stockout_risk"]),
        overstock_risk=float(r["overstock_risk"]),
        risk_quadrant=str(r["risk_quadrant"]),
        recommended_action=str(r["recommended_action"]),
        sales_at_risk_rupees=float(r["sales_at_risk_rupees"]),
        capital_locked_rupees=float(r["capital_locked_rupees"]),
        revenue_at_stake_rupees=float(r["revenue_at_stake_rupees"]),
        safety_stock=float(r["safety_stock"]),
        eoq=float(r["eoq"]),
        reorder_qty=float(r["reorder_qty"])
    )

@router.post("/predict", response_model=PredictResponse)
def predict_batch(req: PredictRequest):
    if not req.sku_ids:
        raise HTTPException(status_code=400, detail="sku_ids batch list cannot be empty.")
        
    conn = get_connection()
    placeholders = ",".join(["?"] * len(req.sku_ids))
    
    # fetch forecasts
    fc_query = f"SELECT * FROM forecasts WHERE sku_id IN ({placeholders}) ORDER BY sku_id, forecast_step"
    fc_df = pd.read_sql(fc_query, conn, params=req.sku_ids)
    
    # fetch risk
    risk_query = f"SELECT * FROM risk_scores WHERE sku_id IN ({placeholders})"
    risk_df = pd.read_sql(risk_query, conn, params=req.sku_ids)
    conn.close()
    
    results = []
    for sku_id in req.sku_ids:
        sku_fc = fc_df[fc_df["sku_id"] == sku_id]
        sku_risk = risk_df[risk_df["sku_id"] == sku_id]
        
        if sku_fc.empty:
            results.append({"sku_id": sku_id, "error": "No forecast found"})
            continue
            
        fc_points = [
            {
                "week_start": r["week_start"],
                "forecast_step": int(r["forecast_step"]),
                "forecast_units": float(r["forecast_units"])
            } for _, r in sku_fc.iterrows()
        ]
        
        risk_payload = {}
        if not sku_risk.empty:
            r = sku_risk.iloc[0]
            risk_payload = {
                "stockout_risk": float(r["stockout_risk"]),
                "overstock_risk": float(r["overstock_risk"]),
                "risk_quadrant": str(r["risk_quadrant"]),
                "revenue_at_stake": float(r["revenue_at_stake_rupees"])
            }
            
        results.append({
            "sku_id": sku_id,
            "forecast": fc_points,
            "risk": risk_payload
        })
        
    return PredictResponse(results=results)

@router.get("/dashboard-data", response_model=DashboardDataResponse)
def get_dashboard_data():
    risk_df = load_table_as_df("risk_scores")
    if risk_df.empty:
        return DashboardDataResponse(
            total_skus=0, reorder_now_count=0, markdown_clear_count=0,
            total_sales_at_risk=0.0, total_capital_locked=0.0
        )
        
    total_skus = len(risk_df)
    reorder_count = int((risk_df["risk_quadrant"] == "Reorder Now").sum())
    markdown_count = int((risk_df["risk_quadrant"] == "Markdown / Clear").sum())
    
    return DashboardDataResponse(
        total_skus=total_skus,
        reorder_now_count=reorder_count,
        markdown_clear_count=markdown_count,
        total_sales_at_risk=float(risk_df["sales_at_risk_rupees"].sum()),
        total_capital_locked=float(risk_df["capital_locked_rupees"].sum())
    )

@router.get("/model-metrics", response_model=List[ModelMetricResponse])
def get_model_metrics():
    metrics_df = load_table_as_df("model_metrics")
    if metrics_df.empty:
        return []
    return [
        ModelMetricResponse(
            model_name=str(r["model_name"]),
            wape=float(r["wape"]),
            bias=float(r["bias"]),
            mae=float(r["mae"]),
            rmse=float(r["rmse"]),
            mape=float(r["mape"]),
            r2=float(r["r2"])
        ) for _, r in metrics_df.iterrows()
    ]
