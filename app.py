import sys
from pathlib import Path
import streamlit as st
import os

# Setup page config
st.set_page_config(
    page_title="Project FORESIGHT Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup path resolver
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR.parent))
sys.path.append(str(ROOT_DIR))

# Case-insensitive file search helper
def find_file_case_insensitive(directory: Path, filename: str) -> Path:
    if not directory.exists():
        return None
    for item in directory.iterdir():
        if item.is_file() and item.name.lower() == filename.lower():
            return item
    return None

# Find the dashboard directory dynamically
home_file = None
# Search recursively
for root, dirs, files in os.walk(str(ROOT_DIR)):
    # skip venv and dotfiles
    if ".venv" in root or "venv" in root or ".git" in root:
        continue
    for f in files:
        if f.lower() == "home.py":
            home_file = Path(root) / f
            break
    if home_file:
        break

if home_file:
    CURRENT_DIR = home_file.parent
else:
    CURRENT_DIR = ROOT_DIR / "dashboard"

# Define page files
page_files = ["Home.py", "Dashboard.py", "Forecast.py", "Inventory.py", "Analytics.py", "Model.py", "Settings.py"]
pages_dict = {}
missing_files = []

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
