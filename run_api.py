import uvicorn
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("run_api")

if __name__ == "__main__":
    logger.info("Starting REST API service...")
    uvicorn.run("Project_FORESIGHT.api.main:app", host="0.0.0.0", port=8000, reload=True)
