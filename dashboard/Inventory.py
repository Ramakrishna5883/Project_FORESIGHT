import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from Project_FORESIGHT.database.database import load_table_as_df
from Project_FORESIGHT.utils.helpers import format_rupees

st.title("📦 Inventory Management")
st.caption("Safety stock requirements, turnover rates, and holding parameters")

risk_df = load_table_as_df("risk_scores")

if risk_df.empty:
    st.error("No inventory data found in database. Run pipeline.py first.")
    st.stop()

# Overall Inventory KPI Cards
total_stock_value = (risk_df["on_hand_units"] * risk_df["unit_cost"]).sum()
avg_turnover = risk_df["inventory_turnover"].mean()
total_safety_stock = risk_df["safety_stock"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("On Hand Value (Capital)", format_rupees(total_stock_value))
c2.metric("Average Turnover Rate", f"{avg_turnover:.2f}x")
c3.metric("Total Safety Stock Needed", f"{total_safety_stock:,.0f} Units")

st.divider()

# Days of Inventory Chart
st.subheader("Days of Inventory Coverage")
st.caption("Remaining coverage (days of sales) based on current on-hand units and weekly forecast rates.")

fig_days = px.bar(
    risk_df.sort_values("days_of_inventory", ascending=False).head(30),
    x="sku_id",
    y="days_of_inventory",
    color="category",
    labels={"days_of_inventory": "Days of Inventory", "sku_id": "SKU ID"},
    title="Top 30 SKUs by Days of Inventory Coverage"
)
fig_days.update_layout(
    paper_bgcolor="#0f1117",
    plot_bgcolor="#141728",
    font=dict(color="#c5c9e8")
)
st.plotly_chart(fig_days, width='stretch')

st.divider()

# EOQ table analysis
st.subheader("Order Quantity Optimisation (EOQ)")
st.caption("SKU Economic Order Quantities (EOQ) calculated to balance holding costs and order transaction fees.")

st.dataframe(
    risk_df[["sku_id", "category", "unit_cost", "safety_stock", "reorder_point", "eoq"]]
    .rename(columns={"safety_stock": "Safety Stock", "reorder_point": "Reorder Point (ROP)", "eoq": "EOQ (Units)"}),
    width='stretch',
    hide_index=True
)
