import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import subprocess
from Project_FORESIGHT.config import STOCKOUT_HIGH_THRESHOLD, OVERSTOCK_HIGH_THRESHOLD

st.title("⚙️ System Settings")
st.caption("Tune thresholds, adjust parameters, and trigger pipeline runs")

st.subheader("Threshold Tuning")
st.caption("Adjust the split values used to classify SKUs into operational quadrants.")

so_threshold = st.slider(
    "Stockout High Risk Cutoff",
    min_value=0.1, max_value=0.9,
    value=float(STOCKOUT_HIGH_THRESHOLD), step=0.05
)

ov_threshold = st.slider(
    "Overstock High Risk Cutoff",
    min_value=0.1, max_value=0.9,
    value=float(OVERSTOCK_HIGH_THRESHOLD), step=0.05
)

st.divider()

st.subheader("Pipeline Ingestion Trigger")
st.caption("Re-run the cleaning, forecasting, and risk calculations end-to-end using latest raw files.")

if st.button("Run FORESIGHT Pipeline End-to-End"):
    pipeline_path = Path(__file__).resolve().parent.parent / "run_pipeline.py"
    
    with st.spinner("Executing pipeline modules..."):
        try:
            res = subprocess.run(
                [sys.executable, str(pipeline_path)],
                capture_output=True, text=True, check=True
            )
            st.success("Pipeline executed successfully!")
            st.code(res.stdout[-1000:]) # display last 1k chars of output
        except Exception as e:
            st.error(f"Error running pipeline: {e}")
