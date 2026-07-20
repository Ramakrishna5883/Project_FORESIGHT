import pandas as pd
from pathlib import Path
from Project_FORESIGHT.config import RAW_DATA_DIR
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("ingest")

def ingest_raw_files(raw_dir: Path = RAW_DATA_DIR) -> dict:
    """Load the four raw CSV datasets."""
    files = {
        "sku_master": raw_dir / "sku_master.csv",
        "calendar": raw_dir / "calendar.csv",
        "sales_daily": raw_dir / "sales_daily.csv",
        "inventory_snapshots": raw_dir / "inventory_snapshots.csv"
    }
    
    datasets = {}
    for name, path in files.items():
        if not path.exists():
            raise FileNotFoundError(f"Required raw file not found: {path}")
        logger.info(f"Ingesting {path.name}...")
        datasets[name] = pd.read_csv(path)
        
    return datasets
