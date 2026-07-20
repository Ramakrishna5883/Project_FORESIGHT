# Project FORESIGHT — Operational Inventory Intelligence

FORESIGHT is a production-grade weekly SKU-level demand forecasting and inventory replenishment platform developed for **NorthBay Living** (Zidio Development).

---

## 🏗 System Architecture

```
                 +-----------------------+
                 |    Raw Extracts CSV   |
                 +-----------+-----------+
                             |
                             ▼
                 +-----------------------+
                 |  Modular Ingestion &  |
                 |  Data Validation      |
                 +-----------+-----------+
                             |
                             ▼
                 +-----------------------+
                 |  Feature Engineering  |
                 |  (Lags, Rollings, KPI) |
                 +-----------+-----------+
                             |
                             ▼
                 +-----------+-----------+
                 |    Trainer Engine     | <---+ CV Metrics Comparison
                 | (RF / GB / LightGBM)   |
                 +-----------+-----------+
                             |
                             ▼
                 +-----------+-----------+
                 |   Predictor & Risk    | ---> SQLite Database (foresight.db)
                 | (Safety Stock / EOQ)  |
                 +-----------+-----------+
                             |
            +----------------+----------------+
            |                                 |
            ▼                                 ▼
+-----------------------+         +-----------------------+
|  Multi-Page Dashboard  |         |     FastAPI Service   |
| (Streamlit: 7 pages)  |         |      (REST API)       |
+-----------------------+         +-----------------------+
```

---

## 📂 Project Directory Structure

```
Project_FORESIGHT/
├── app.py                      # Main entrypoint wrapper for the Streamlit dashboard
├── requirements.txt            # Package dependencies
├── README.md                   # System documentation
├── LICENSE                     # License terms
├── .gitignore                  # Git ignore rules
├── config.py                   # Central settings & default thresholds
├── run_pipeline.py             # Orchestrates the ETL, training, and risk calculations
├── run_dashboard.py            # Streamlit launcher script
├── run_api.py                  # API service launcher script
│
├── data/
│   ├── raw/                    # Input snapshots (sales, master, inventory, calendar)
│   ├── processed/              # Merged and feature engineered datasets
│   └── reports/                # PDF, markdown audits and execution logs
│
├── database/
│   ├── database.py             # SQLite helper and schema definitions
│   └── foresight.db            # Persisted forecasts and metrics
│
├── pipeline/
│   ├── ingest.py               # Raw file loader
│   ├── validation.py           # Schema checks, duplicate and negative counts
│   ├── cleaning.py             # Normalization, category mapping, imputation
│   ├── merge.py                # Weekly aggregation and pd.merge_asof join
│   ├── feature_engineering.py  # Lags, rolling metrics, pricing, inventory KPIs
│   └── preprocessing.py        # Scalers, encoder encoding, training subset splits
│
├── forecasting/
│   ├── baseline.py             # Seasonal Naive benchmark model
│   ├── trainer.py              # Models comparison and selected champion trainer
│   ├── predictor.py            # Iterative multi-step recursive forecaster
│   ├── evaluator.py            # Forecast error metrics (WAPE, Bias, MAE, R2)
│   ├── cross_validation.py     # Rolling-origin validation folds
│   └── metrics.py              # Custom error calculations
│
├── risk/
│   ├── stockout.py             # Safety stock and ROP calculations
│   ├── overstock.py            # EOQ and inventory cover estimations
│   ├── decision_engine.py      # Classification matrix and prioritization
│   └── recommendation.py       # Action recommendation details generator
│
├── dashboard/                  # Multi-page views
│   ├── Home.py                 # Welcome hub
│   ├── Dashboard.py            # Operational scatter grid and planners
│   ├── Forecast.py             # SKU demand projections
│   ├── Inventory.py            # Safety stocks, turnovers, and EOQ charts
│   ├── Analytics.py            # Seasonality and ABC value classifications
│   ├── Model.py                # Diagnostic backtests and error ratios
│   └── Settings.py             # Threshold parameters tuning
│
├── api/
│   ├── main.py                 # REST application server
│   ├── routes.py               # REST endpoints
│   └── schemas.py              # Pydantic validation schemas
│
├── utils/
│   ├── charts.py               # Plotly theme formatting
│   ├── logger.py               # Central structured logs handler
│   ├── constants.py            # Global lookups
│   └── helpers.py              # Rupees string parser
│
├── reports/
│   ├── executive_summary.py    # Markdown audit generator
│   └── generate_pdf.py         # PDF report compilation
│
├── notebooks/
│   └── exploration.ipynb       # Sandbox notebook
│
└── tests/
    ├── test_pipeline.py        # Ingestion test suite
    ├── test_model.py           # Evaluation tests
    └── test_api.py             # Routing test suite
```

---

## ⚡ Setup & Installation

1. **Clone the repository** and navigate to the project directory.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Running the Platform

### 1. Execute the Pipeline
Run the end-to-end data pipeline to ingest, clean, train the models, forecast demand, calculate risk priority metrics, and generate executive summaries:
```bash
python run_pipeline.py
```
*Or use Make:*
```bash
make run-pipeline
```

### 2. Launch the Operational Dashboard
Start the multi-page Streamlit planning dashboard:
```bash
python run_dashboard.py
```
*Or use Make:*
```bash
make run-dashboard
```

### 3. Launch the API Service
Start the FastAPI endpoint microservice:
```bash
python run_api.py
```
*Or use Make:*
```bash
make run-api
```
The interactive Swagger API documentation will be available at: **http://localhost:8000/docs**.
