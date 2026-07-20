import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import os

# Setup page config
st.set_page_config(
    page_title="Project FORESIGHT Dashboard",
    page_icon="📦",
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

# Dynamically locate the dashboard directory to survive any folder structures
ROOT_DIR = Path(__file__).resolve().parent
home_path = next(ROOT_DIR.glob("**/Home.py"), None)
if home_path:
    CURRENT_DIR = home_path.parent
else:
    CURRENT_DIR = ROOT_DIR / "dashboard"

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

# Run navigation
pg = st.navigation(pages)
pg.run()
