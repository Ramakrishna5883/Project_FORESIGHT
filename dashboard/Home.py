import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import os

# Setup page config
st.set_page_config(
    page_title="FORESIGHT - Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0f1117; color: #e8e8f0; }
    [data-testid="stSidebar"]          { background: #16192a; }
    h1, h2, h3 { color: #c5c9e8 !important; }
    </style>
    """, unsafe_allow_html=True)

# Helper to load navigation programmatically
CURRENT_DIR = Path(__file__).resolve().parent

# Define the pages programmatically to keep the requested flat directory structure
pages = {
    "Overview": [
        st.Page(CURRENT_DIR / "Home.py", title="Home", icon="🏠", default=True),
        st.Page(CURRENT_DIR / "Dashboard.py", title="Dashboard", icon="📊"),
        st.Page(CURRENT_DIR / "Forecast.py", title="Forecast Detail", icon="📈"),
        st.Page(CURRENT_DIR / "Inventory.py", title="Inventory Management", icon="📦"),
        st.Page(CURRENT_DIR / "Analytics.py", title="EDA & Analytics", icon="🔍"),
        st.Page(CURRENT_DIR / "Model.py", title="Model Evaluation", icon="🔬"),
        st.Page(CURRENT_DIR / "Settings.py", title="Settings", icon="⚙️")
    ]
}

# Run navigation if it's the main execution
pg = st.navigation(pages)

# Render main landing content only if we are on the Home page route
if pg.title == "Home":
    st.title("🏠 FORESIGHT Intelligence Platform")
    st.markdown("### NorthBay Living Inventory Planning & Demand Forecasting Hub")
    
    st.divider()
    
    # Quick Summary metrics
    from Project_FORESIGHT.database.database import load_table_as_df
    from Project_FORESIGHT.utils.helpers import format_rupees
    
    risk_df = load_table_as_df("risk_scores")
    
    if not risk_df.empty:
        total_skus = len(risk_df)
        reorders = int((risk_df["risk_quadrant"] == "Reorder Now").sum())
        markdowns = int((risk_df["risk_quadrant"] == "Markdown / Clear").sum())
        val_at_risk = risk_df["revenue_at_stake_rupees"].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Catalog SKUs", f"{total_skus}")
        c2.metric("SKUs to Reorder", f"{reorders}")
        c3.metric("SKUs to Markdown", f"{markdowns}")
        c4.metric("Capital at Stake", format_rupees(val_at_risk))
    else:
        st.warning("No data has been loaded. Please run the pipeline first.")
        
    st.markdown("""
    ### Welcome to Project FORESIGHT
    This platform integrates advanced demand forecasting models and customized inventory risk assessment engines to automate operational inventory planning at NorthBay Living.
    
    #### Key Capabilities
    - **Reproducible Pipeline:** Validates raw CSV snapshots, runs statistical cleaning rules, and prepares features.
    - **ML Forecasting:** Predicts weekly unit sales using Gradient Boosting & LightGBM with statistical fallback baselines.
    - **Inventory Health:** Computes Safety Stock levels, Reorder Points, and Economic Order Quantities (EOQ).
    - **Decision Support:** Classifies each product into operational risk quadrants (Reorder, Markdown, Watch, Healthy).
    - **Orchestrated Exports:** Generates executive Markdown summaries, PDF reports, and CSV planners on demand.
    """)
    
    st.info("💡 Navigation: Use the sidebar menu to explore Operational Planners, Forecast details, and Analytics.")
else:
    # Programmatic execution of the sub-pages
    pg.run()
