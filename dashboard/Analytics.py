import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from Project_FORESIGHT.database.database import load_table_as_df

st.title("🔍 EDA & Analytics")
st.caption("Investigate demand behaviors, seasonality, ABC classifications, and promotional effects")

# Load analysis_ready data from CSV (more history than risk scores)
from Project_FORESIGHT.config import PROCESSED_DATA_DIR
csv_path = PROCESSED_DATA_DIR / "analysis_ready.csv"

if not csv_path.exists():
    st.error("No clean analysis-ready dataset found. Run run_pipeline.py first.")
    st.stop()
    
df = pd.read_csv(csv_path, parse_dates=["week_start"])

# ABC Analysis calculation
st.subheader("ABC Analysis (Product Value Contribution)")
st.caption("Classifying inventory based on sales volume contribution (80/15/5% rule).")

sku_sales = df.groupby("sku_id")["revenue"].sum().sort_values(ascending=False).reset_index()
total_rev = sku_sales["revenue"].sum()
sku_sales["cum_pct"] = sku_sales["revenue"].cumsum() / total_rev

sku_sales["class"] = np.where(sku_sales["cum_pct"] <= 0.80, "A",
                       np.where(sku_sales["cum_pct"] <= 0.95, "B", "C"))

abc_counts = sku_sales["class"].value_counts().reset_index()
abc_counts.columns = ["Class", "SKUs"]

fig_abc = px.pie(abc_counts, values="SKUs", names="Class", title="Distribution of Inventory Value Classes (A/B/C)")
fig_abc.update_layout(
    paper_bgcolor="#0f1117",
    font=dict(color="#c5c9e8")
)
st.plotly_chart(fig_abc, width='stretch')

st.divider()

# Month seasonality
st.subheader("Seasonality: Average Weekly Units by Month")
df["month_name"] = df["week_start"].dt.strftime("%b")
monthly_avg = df.groupby("month_name")["units_sold"].mean().reindex(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]).reset_index()

fig_season = px.line(
    monthly_avg,
    x="month_name",
    y="units_sold",
    markers=True,
    labels={"units_sold": "Avg Weekly Units Sold", "month_name": "Month"},
    title="Demand Distribution by Month"
)
fig_season.update_layout(
    paper_bgcolor="#0f1117",
    plot_bgcolor="#141728",
    font=dict(color="#c5c9e8")
)
st.plotly_chart(fig_season, width='stretch')

st.divider()

# Promo impact
st.subheader("Promotional Impact Analysis")
st.caption("Comparing sales volume in weeks with promotions vs regular weeks.")

# Calculate promo weeks vs non-promo
df["is_promo_week"] = df["promo_days"] > 0
promo_comp = df.groupby("is_promo_week")["units_sold"].mean().reset_index()
promo_comp["is_promo_week"] = promo_comp["is_promo_week"].map({True: "Promo Weeks", False: "Regular Weeks"})

fig_promo = px.bar(
    promo_comp,
    x="is_promo_week",
    y="units_sold",
    color="is_promo_week",
    labels={"units_sold": "Average Weekly Sales (Units)", "is_promo_week": "Week Type"},
    title="Average Sales Volume by Promotional Activity"
)
fig_promo.update_layout(
    paper_bgcolor="#0f1117",
    plot_bgcolor="#141728",
    font=dict(color="#c5c9e8")
)
st.plotly_chart(fig_promo, width='stretch')
