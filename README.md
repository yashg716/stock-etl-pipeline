# Stock ETL Optimization Pipeline

A fully automated, end-to-end data engineering pipeline that ingests S&P 500 stock price data, optimizes storage format, transforms and validates the data using dbt, and loads it into a cloud Postgres warehouse (Supabase).

---

## Project Overview

This project demonstrates a production-style ETL workflow built with Python, dbt, and PostgreSQL. It is designed to run incrementally — only pulling new data when the warehouse is out of date — and validates the final output with automated dbt tests.

## Tech Stack

| Layer | Tool |
|-------|------|
| Data Source | yfinance (Python) |
| Data Processing | Python (pandas, SQLAlchemy, psycopg2, dotenv) |
| Cloud Warehouse | PostgreSQL via Supabase |
| Transformation | dbt (data build tool) |
| Orchestration | PowerShell / Batch runner |

---

## Architecture

```
Raw API / CSV Data
        ↓
  phase1_naive.py        ← Initial data load (naive, unoptimized)
        ↓
  phase2_naive.py        ← Optimization: deduplication, type casting, Parquet output
        ↓
  auto_refresh.py        ← Incremental refresh: only loads new rows not yet in DB
        ↓
  Supabase PostgreSQL    ← Cloud warehouse (stocks_optimized table)
        ↓
  dbt run                ← Staging → Intermediate → Mart models
        ↓
  dbt test               ← Data quality validation
        ↓
  mart_stock_summary     ← Final analytics-ready table
```

---

## Project Structure

```
ETL_optimization-project/
├── phase1_naive.py              # Initial raw data load
├── phase2_naive.py              # Data optimization and enriched load
├── auto_refresh.py              # Incremental refresh logic
├── full_pipeline.py             # Orchestrator: full rebuild
├── refresh_pipeline.py          # Orchestrator: incremental refresh only
├── run_refresh.bat              # One-click batch launcher with menu
├── run.sql                      # Raw SQL exploration queries
├── .env.example                 # Environment variable template
├── .gitignore
└── stock_transforms/            # dbt project
    ├── dbt_project.yml
    ├── models/
    │   ├── staging/
    │   │   ├── stg_stocks.sql       # Cleans and casts raw data
    │   │   └── sources.yml          # Source definitions + tests
    │   ├── intermediate/
    │   │   └── int_stock_metrics.sql  # Yearly aggregations
    │   └── marts/
    │       └── mart_stock_summary.sql # Final analytics-ready table
    └── models/schema.yml            # Model-level dbt tests
```

---

## dbt Models

| Model | Type | Description |
|-------|------|-------------|
| `stg_stocks` | View | Cleans nulls, casts types from raw source |
| `int_stock_metrics` | View | Adds yearly high, low, avg close per ticker |
| `mart_stock_summary` | Table | Final mart: joins staging + metrics for analytics |

---

## dbt Tests

| Test | Column | Result |
|------|--------|--------|
| `not_null` | `close` | ✅ PASS |
| `not_null` | `date` | ✅ PASS |
| `not_null` | `ticker` | ✅ PASS |
| `source not_null` | `date` (source) | ✅ PASS |
| `source not_null` | `ticker` (source) | ✅ PASS |

---

## How to Run

### 1. Clone the repo

```bash
git clone https://github.com/yashg716/stock-etl-pipeline.git
cd stock-etl-pipeline
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```env
DB_CONN_STRING=postgresql://postgres:<your-password>@<your-supabase-host>:5432/postgres
```

### 4. Run the pipeline

**Option A — batch launcher (Windows):**

Double-click `run_refresh.bat` and choose:
- `1` for daily refresh (incremental)
- `2` for full rebuild from scratch

**Option B — terminal:**

```bash
# Incremental refresh
python refresh_pipeline.py

# Full rebuild
python full_pipeline.py
```

---

## Pipeline Logic

### Full Pipeline (`full_pipeline.py`)
1. Runs `phase1_naive.py` — downloads raw stock data
2. Runs `phase2_naive.py` — optimizes and loads to Supabase
3. Runs `dbt run` — builds all models
4. Runs `dbt test` — validates all models

### Refresh Pipeline (`refresh_pipeline.py`)
1. Runs `auto_refresh.py` — checks latest date in DB, skips if already current
2. Runs `dbt run` — rebuilds models with any new data
3. Runs `dbt test` — re-validates

---

## Environment Variables

Copy `.env.example` and populate it:

```env
DB_CONN_STRING=postgresql://postgres:<password>@<host>:5432/postgres
```

> ⚠️ Never commit `.env` to version control. It is excluded via `.gitignore`.

---

## Key Design Decisions

- **Incremental refresh logic:** `auto_refresh.py` queries the latest date in the warehouse and skips ingestion if data is current, avoiding redundant loads.
- **Parquet optimization:** Raw CSV data is converted to Parquet format during the optimization phase, reducing storage footprint and improving read performance.
- **dbt layered modeling:** Staging → Intermediate → Mart follows standard dbt best practices for separation of concerns.
- **Automated tests:** dbt `not_null` tests run on every pipeline execution to catch data quality issues early.

---


## Author

**Yash** 
GitHub: [yashg716](https://github.com/yashg716)
