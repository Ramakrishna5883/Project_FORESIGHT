import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from Project_FORESIGHT.database.database import load_table_as_df, get_connection

st.title("📈 Forecast Explorer")
st.caption("Deep-dive into 6-week forward predictions for individual SKUs")

forecasts_df = load_table_as_df("forecasts")
risk_df = load_table_as_df("risk_scores")

if forecasts_df.empty or risk_df.empty:
    st.error("Forecast data missing from database. Run pipeline.py first.")
    st.stop()

# SKU selection
sku_list = sorted(forecasts_df["sku_id"].unique().tolist())
sel_sku = st.selectbox("Select SKU ID to Analyze", sku_list)

# Load selected SKU details
sku_risk = risk_df[risk_df["sku_id"] == sel_sku]
sku_fc = forecasts_df[forecasts_df["sku_id"] == sel_sku].sort_values("week_start")

if sku_risk.empty or sku_fc.empty:
    st.warning("Data not found for the selected SKU.")
    st.stop()

r = sku_risk.iloc[0]

# Display SKU metadata cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Category", str(r["category"]))
c2.metric("Subcategory", str(r["subcategory"]))
c3.metric("On Hand Units", f"{int(r['on_hand_units']):,}")
c4.metric("Risk Quadrant", str(r["risk_quadrant"]))

# Plotly line graph of predictions with uncertainty intervals
st.subheader("6-Week Demand Projection")

fig = go.Figure()

# 80% prediction interval band
fig.add_trace(go.Scatter(
    x=pd.concat([sku_fc["week_start"], sku_fc["week_start"][::-1]]),
    y=pd.concat([sku_fc["forecast_hi80"], sku_fc["forecast_lo80"][::-1]]),
    fill="toself",
    fillcolor="rgba(139,128,249,0.15)",
    line=dict(width=0),
    name="80% Interval"
))

# Mean forecast line
fig.add_trace(go.Scatter(
    x=sku_fc["week_start"],
    y=sku_fc["forecast_units"],
    mode="lines+markers",
    name="Mean Forecast",
    line=dict(color="#8b80f9", width=3.0),
    marker=dict(size=7)
))

# Safety Stock & ROP horizontal lines
fig.add_shape(
    type="line",
    x0=sku_fc["week_start"].min(), x1=sku_fc["week_start"].max(),
    y0=r["reorder_point"], y1=r["reorder_point"],
    line=dict(color="#e05252", width=1.5, dash="dash"),
    name="Reorder Point"
)

fig.update_layout(
    xaxis_title="Week Start Date",
    yaxis_title="Demand (Units)",
    paper_bgcolor="#0f1117",
    plot_bgcolor="#141728",
    font=dict(color="#c5c9e8"),
    margin=dict(l=0, r=0, t=30, b=0),
    height=380
)
st.plotly_chart(fig, width='stretch')

# Recommendations
st.subheader("Planning Recommendation")
st.info(f"💡 **Recommendation:** {r.get('recommendation_details', r['recommended_action'])}")
