import os
import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("run_dashboard")

def main():
    dashboard_path = Path(__file__).resolve().parent / "app.py"
    logger.info(f"Launching Streamlit dashboard at {dashboard_path}...")
    
    try:
        # Launch streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path)
        ])
    except KeyboardInterrupt:
        logger.info("Dashboard shutdown by user.")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")

if __name__ == "__main__":
    main()
