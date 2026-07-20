import sys
import types
from pathlib import Path

# Resolve ROOT_DIR (repository root containing app.py)
ROOT_DIR = Path(__file__).resolve().parent

# Runtime Package Aliasing:
# Redirect imports of "Project_FORESIGHT.*" to folders in the current root directory
# to survive case-sensitive deployments (like Streamlit Community Cloud on Linux)
if "Project_FORESIGHT" not in sys.modules:
    project_foresight_module = types.ModuleType("Project_FORESIGHT")
    project_foresight_module.__path__ = [str(ROOT_DIR)]
    sys.modules["Project_FORESIGHT"] = project_foresight_module

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
home_path = next(ROOT_DIR.glob("**/Home.py"), None)
if home_path:
    CURRENT_DIR = home_path.parent
else:
    CURRENT_DIR = ROOT_DIR / "dashboard"

# Define page files
page_files = ["Home.py", "Dashboard.py", "Forecast.py", "Inventory.py", "Analytics.py", "Model.py", "Settings.py"]
pages_dict = {}
missing_files = []

# Case-insensitive file search helper
def find_file_case_insensitive(directory: Path, filename: str) -> Path:
    if not directory.exists():
        return None
    for item in directory.iterdir():
        if item.is_file() and item.name.lower() == filename.lower():
            return item
    return None

for pf in page_files:
    resolved_path = find_file_case_insensitive(CURRENT_DIR, pf)
    if resolved_path:
        pages_dict[pf] = resolved_path
    else:
        missing_files.append(pf)

if missing_files:
    st.error("⚠️ FORESIGHT Deployment Diagnostics")
    st.markdown(f"**Missing files under `{CURRENT_DIR}`:** {missing_files}")
    st.markdown("**Files found in Root directory:**")
    st.write(os.listdir(ROOT_DIR))
    if CURRENT_DIR.exists():
        st.markdown(f"**Files found in `{CURRENT_DIR.name}`:**")
        st.write(os.listdir(CURRENT_DIR))
    st.stop()

pages = {
    "Overview": [
        st.Page(pages_dict["Home.py"], title="Home", icon="🏠", default=True),
        st.Page(pages_dict["Dashboard.py"], title="Dashboard", icon="📊"),
        st.Page(pages_dict["Forecast.py"], title="Forecast Detail", icon="📈"),
        st.Page(pages_dict["Inventory.py"], title="Inventory Management", icon="📦"),
        st.Page(pages_dict["Analytics.py"], title="EDA & Analytics", icon="🔍"),
        st.Page(pages_dict["Model.py"], title="Model Evaluation", icon="🔬"),
        st.Page(pages_dict["Settings.py"], title="Settings", icon="⚙️")
    ]
}

# Run navigation
pg = st.navigation(pages)
pg.run()
