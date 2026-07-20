import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from Project_FORESIGHT.database.database import load_table_as_df
from Project_FORESIGHT.utils.helpers import format_rupees
from Project_FORESIGHT.utils.constants import QUADRANT_COLORS

# Header
st.title("📊 Operational Dashboard")
st.caption("Plan actions, replenish critical SKUs, and clear overstocks")

risk_df = load_table_as_df("risk_scores")

if risk_df.empty:
    st.error("No database risk scores found. Run pipeline.py first.")
    st.stop()

# Filters in sidebar
st.sidebar.markdown("### Filters")
categories = sorted(risk_df["category"].dropna().unique().tolist())
sel_categories = st.sidebar.multiselect("Select Categories", categories, default=categories)

quadrants = sorted(risk_df["risk_quadrant"].dropna().unique().tolist())
sel_quadrants = st.sidebar.multiselect("Select Status", quadrants, default=quadrants)

filtered = risk_df[
    risk_df["category"].isin(sel_categories) & risk_df["risk_quadrant"].isin(sel_quadrants)
]

if filtered.empty:
    st.warning("No SKUs match the selected filters.")
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("SKUs in View", len(filtered))
col2.metric("Critical Reorders", int((filtered["risk_quadrant"] == "Reorder Now").sum()))
col3.metric("Capital Locked", format_rupees(filtered["capital_locked_rupees"].sum()))
col4.metric("Sales at Risk", format_rupees(filtered["sales_at_risk_rupees"].sum()))

st.divider()

# Decisioning scatter plot
st.subheader("Inventory Risk Profile")
st.caption("Scatter chart mapping Stockout risk vs. Overstock risk. Bubble size represents capital value at stake.")

fig = px.scatter(
    filtered,
    x="overstock_risk",
    y="stockout_risk",
    color="risk_quadrant",
    size="revenue_at_stake_rupees",
    size_max=35,
    hover_name="sku_id",
    hover_data=["category", "subcategory", "recommended_action"],
    color_discrete_map=QUADRANT_COLORS,
    labels={"overstock_risk": "Overstock Risk →", "stockout_risk": "Stockout Risk ↑"}
)
fig.add_vline(x=0.5, line_dash="dash", line_color="#3a3e5a")
fig.add_hline(y=0.5, line_dash="dash", line_color="#3a3e5a")
fig.update_layout(
    paper_bgcolor="#0f1117",
    plot_bgcolor="#141728",
    font=dict(color="#c5c9e8"),
    margin=dict(l=0, r=0, t=10, b=0),
    height=400
)
st.plotly_chart(fig, width='stretch')

st.divider()

# Reorders and Markdowns tabs
tab_reorder, tab_markdown = st.tabs(["🔴 Recommended Reorders", "🔵 Markdown Tasks"])

with tab_reorder:
    reorders_df = filtered[filtered["risk_quadrant"] == "Reorder Now"].sort_values("sales_at_risk_rupees", ascending=False)
    if reorders_df.empty:
        st.success("No critical reorders in view.")
    else:
        st.dataframe(
            reorders_df[["sku_id", "category", "subcategory", "on_hand_units", "on_order_units", "reorder_point", "reorder_qty", "sales_at_risk_rupees"]]
            .rename(columns={"reorder_qty": "Order Qty", "sales_at_risk_rupees": "Sales Risk (₹)"}),
            width='stretch',
            hide_index=True
        )
        
        # Download CSV button
        csv = reorders_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Reorder List (CSV)", csv, "reorder_plan.csv", "text/csv")

with tab_markdown:
    markdowns_df = filtered[filtered["risk_quadrant"] == "Markdown / Clear"].sort_values("capital_locked_rupees", ascending=False)
    if markdowns_df.empty:
        st.success("No overstocks requiring markdown in view.")
    else:
        st.dataframe(
            markdowns_df[["sku_id", "category", "subcategory", "on_hand_units", "forecast_units_fwd", "capital_locked_rupees"]]
            .rename(columns={"forecast_units_fwd": "8W Demand", "capital_locked_rupees": "Capital Locked (₹)"}),
            width='stretch',
            hide_index=True
        )
        
        # Download CSV
        csv_md = markdowns_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Markdown List (CSV)", csv_md, "markdown_plan.csv", "text/csv")
