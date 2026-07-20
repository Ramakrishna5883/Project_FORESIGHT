from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Project_FORESIGHT.api.routes import router
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("api_main")

app = FastAPI(
    title="Project FORESIGHT API",
    description="REST API service for inventory intelligence, forecasting, and risk prioritization.",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Project FORESIGHT API version 2.0.0",
        "documentation": "/docs"
    }
