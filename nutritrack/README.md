# NutriTrack

A full-stack nutrition tracking platform built as a Data Engineering project. NutriTrack collects food product data from Open Food Facts, processes it through an ETL pipeline, stores it in a PostgreSQL data warehouse with star-schema modeling, and provides a REST API + Streamlit frontend for users to track meals and monitor nutritional intake.

## Tech Stack

| Component | Technology | Port | Purpose |
|---|---|---|---|
| Database | PostgreSQL 16 | 5432 | Operational DB (app schema) + Data Warehouse (dw schema) |
| Cache / Broker | Redis 7 | 6379 | API caching + Airflow Celery broker |
| Data Lake | MinIO (S3-compatible) | 9000 / 9001 | Medallion architecture (bronze/silver/gold buckets) |
| ETL Orchestration | Apache Airflow 2.8.1 | 8080 | 6 DAGs for extraction, cleaning, warehouse loading, lake ingestion |
| REST API | FastAPI | 8000 | JWT-authenticated API with RBAC |
| Frontend | Streamlit | 8501 | Nutrition tracking dashboard |

## Architecture Overview

```
                    +------------------+
                    |    Streamlit     |  :8501
                    |   (Frontend)     |
                    +--------+---------+
                             |
                    +--------v---------+
                    |     FastAPI      |  :8000
                    |   (REST API)     |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
    +---------v----------+       +----------v---------+
    |   PostgreSQL 16    |       |      Redis 7       |
    |                    |       |   (Cache/Broker)    |
    |  app schema (OLTP) |       +--------------------+
    |  dw schema  (OLAP) |
    +--------+-----------+
             |
    +--------v-----------+       +--------------------+
    |   Airflow 2.8.1    |------>|   MinIO (S3)       |
    | (Webserver +        |      | bronze/silver/gold |
    |  Scheduler +        |      | backups            |
    |  Celery Worker)     |      +--------------------+
    +---------------------+
```

## Prerequisites

- **Docker** and **Docker Compose** (v2+)
- **Python 3.11+** (for running scripts locally outside Docker)
- **Make** (optional, for shortcut commands)

## Quick Start

### 1. Clone and navigate

```bash
cd nutritrack
```

### 2. Start all services

```bash
# Using Make
make build

# Or directly with Docker Compose
docker compose up -d --build
```

This starts all 10 services: PostgreSQL, Redis, MinIO, MinIO-init, Airflow (init, webserver, scheduler, worker), FastAPI, and Streamlit.

### 3. Wait for initialization (~2-3 minutes)

PostgreSQL automatically runs the SQL init scripts on first boot (mounted from `sql/init/`):
- `00_init_databases.sql` - Creates `nutritrack` and `airflow` databases, roles, permissions
- `01_schema_operational.sql` - Creates the `app` schema (users, products, meals, RGPD registry)
- `02_schema_warehouse.sql` - Creates the `dw` schema (star schema, SCD procedures, datamart views)

Airflow initializes its metadata DB and creates the admin user automatically.

MinIO creates the medallion buckets (bronze, silver, gold, backups) via the `minio-init` container.

### 4. Verify services are running

```bash
docker compose ps
```

Check the web interfaces:
- **Airflow**: http://localhost:8080 (login: `admin` / `admin`)
- **FastAPI Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (login: `minioadmin` / `minioadmin123`)
- **Streamlit App**: http://localhost:8501

## Loading Data - Full ETL Pipeline

The data pipeline runs in 3 phases: **Extract** -> **Clean** -> **Load**. You can run it manually with scripts or through Airflow DAGs.

### Option A: Run scripts manually (recommended for first-time setup)

Install Python dependencies first:

```bash
pip install -r requirements.txt
```

#### Phase 1: Extract data from sources

```bash
# 1. Extract from Open Food Facts REST API (categories, ~3 pages per category)
python scripts/extract_off_api.py --mode category --max-pages 3

# 2. Extract from Open Food Facts Parquet dump via DuckDB (bulk, 50k products)
python scripts/extract_off_parquet.py --countries France --limit 50000

# 3. Scrape nutritional guidelines from ANSES/EFSA
python scripts/extract_scraping.py --sources all

# Or run all three at once:
make extract-all
```

Extracted data lands in `data/raw/`.

#### Phase 2: Aggregate and clean

```bash
python scripts/aggregate_clean.py --sources all

# Or:
make clean-data
```

This merges all sources, removes duplicates, validates Nutri-Score, normalizes units, and outputs cleaned CSVs to `data/cleaned/`.

#### Phase 3: Import to PostgreSQL

```bash
python scripts/import_to_db.py

# Or:
make import-db
```

Bulk-inserts brands, categories, and products into the `app` schema using batch upserts.

#### All-in-one pipeline shortcut

```bash
make pipeline
```

Runs extract-all -> clean-data -> import-db sequentially.

### Option B: Run via Airflow DAGs

Once Airflow is up at http://localhost:8080, you'll see 6 DAGs:

| DAG | Schedule | Description |
|---|---|---|
| `etl_extract_off_api` | Daily | Extracts products from Open Food Facts API |
| `etl_extract_parquet` | Weekly | Bulk extraction from OFF Parquet dump via DuckDB |
| `etl_extract_scraping` | Monthly | Scrapes nutritional guidelines |
| `etl_aggregate_clean` | Daily | Merges, deduplicates, and cleans raw data |
| `etl_load_warehouse` | Daily | Loads star schema dimensions/facts + runs SCD procedures |
| `etl_datalake_ingest` | Daily | Medallion pipeline: bronze -> silver -> gold in MinIO |

To run them:
1. Go to http://localhost:8080
2. Unpause the DAGs you want to run (toggle switch on the left)
3. Trigger them manually with the play button, or let them run on schedule

**Recommended execution order:**
1. `etl_extract_off_api` or `etl_extract_parquet` (data extraction)
2. `etl_aggregate_clean` (cleaning)
3. `etl_load_warehouse` (populate star schema)
4. `etl_datalake_ingest` (populate data lake)

## Setting up the Data Lake

After data is loaded into PostgreSQL, set up MinIO with governance policies:

```bash
python scripts/setup_minio.py --all

# Or:
make setup-lake
```

This creates:
- Medallion buckets with lifecycle rules (bronze: 90d, silver: 1yr, gold: indefinite)
- Group-based access policies (analysts, data-engineers, admins)
- Data catalog metadata in JSON format

## Database Backups

```bash
# Full database backup (uploaded to MinIO backups bucket)
make backup

# Data warehouse schema only
make backup-dw
```

## Project Structure

```
nutritrack/
|-- docker-compose.yml          # 10-service infrastructure
|-- Makefile                     # Shortcut commands
|-- requirements.txt             # Python dependencies (extraction scripts)
|-- .env                         # Environment variables
|
|-- sql/
|   |-- init/
|   |   |-- 00_init_databases.sql       # DB creation, roles, permissions
|   |   |-- 01_schema_operational.sql   # app schema (OLTP)
|   |   +-- 02_schema_warehouse.sql     # dw schema (star schema, SCD, datamarts)
|   |-- queries/
|   |   +-- analytical_queries.sql      # 7 optimized analytical queries
|   +-- scd_procedures.sql              # SCD Type 1/2/3 stored procedures
|
|-- scripts/
|   |-- extract_off_api.py       # C8: REST API extraction
|   |-- extract_off_parquet.py   # C8: Parquet/DuckDB extraction
|   |-- extract_scraping.py      # C8: Web scraping (BeautifulSoup)
|   |-- extract_from_db.py       # C8: Database extraction
|   |-- extract_duckdb.py        # C8: DuckDB big data analytics
|   |-- aggregate_clean.py       # C10: Aggregation and cleaning
|   |-- import_to_db.py          # C11: Database import
|   |-- setup_minio.py           # C19: Data lake setup + governance
|   +-- backup_database.py       # C16: Database backup to MinIO
|
|-- airflow/
|   +-- dags/
|       |-- etl_extract_off_api.py      # DAG: API extraction
|       |-- etl_extract_parquet.py      # DAG: Parquet extraction
|       |-- etl_extract_scraping.py     # DAG: Web scraping
|       |-- etl_aggregate_clean.py      # DAG: Data cleaning
|       |-- etl_load_warehouse.py       # DAG: Star schema ETL + SCD
|       +-- etl_datalake_ingest.py      # DAG: Medallion pipeline
|
|-- api/
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py                  # FastAPI app entry point
|   |-- database.py              # Async SQLAlchemy engine
|   |-- auth/
|   |   +-- jwt.py               # JWT authentication + RBAC
|   |-- models/                  # SQLAlchemy ORM models
|   |-- schemas/                 # Pydantic validation schemas
|   +-- routers/
|       |-- auth.py              # /api/v1/auth (register, login, me)
|       |-- products.py          # /api/v1/products (search, filters)
|       +-- meals.py             # /api/v1/meals (CRUD, daily summary, trends)
|
|-- app/
|   |-- Dockerfile
|   |-- requirements.txt
|   +-- streamlit_app.py         # Streamlit frontend
|
|-- data/                        # Data directory (raw/, cleaned/, exports/)
|-- docs/                        # Report and presentation
|-- models/                      # MERISE data models (MCD, MLD, MPD)
+-- tests/                       # Test suite
```

## API Usage

The FastAPI provides a REST API with JWT authentication. Interactive docs at http://localhost:8000/docs.

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"myuser","password":"mypass123","consent_data_processing":true}'

# Login (get JWT token)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"mypass123"}' | python -m json.tool | grep access_token | cut -d'"' -f4)

# Search products
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/products/?search=nutella&page_size=5"

# Log a meal
curl -X POST http://localhost:8000/api/v1/meals/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"meal_type":"breakfast","items":[{"product_id":1,"quantity_g":30}]}'

# Get daily nutrition summary
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/meals/daily-summary"
```

## Make Commands Reference

```
make help           # Show all available commands
make up             # Start all services
make down           # Stop all services
make build          # Build and start services
make logs           # View all logs
make logs-api       # View FastAPI logs
make logs-airflow   # View Airflow logs
make extract-all    # Run all extraction scripts
make clean-data     # Run aggregation and cleaning
make import-db      # Import cleaned data to PostgreSQL
make pipeline       # Full pipeline: extract -> clean -> import
make setup-lake     # Setup MinIO data lake
make backup         # Full database backup
make backup-dw      # Data warehouse backup only
make test-api       # Test API endpoints with curl
make install        # Install all Python dependencies
```

## Stopping Everything

```bash
# Stop services (keep data volumes)
make down

# Stop and remove all data volumes (full reset)
docker compose down -v
```

## Troubleshooting

**Airflow webserver not starting?**
Wait 2-3 minutes after `docker compose up`. The `airflow-init` container must complete first. Check with:
```bash
docker compose logs airflow-init
```

**PostgreSQL connection refused?**
Ensure postgres is healthy:
```bash
docker compose ps postgres
```

**MinIO buckets not created?**
The `minio-init` container creates them on startup. If it exited, re-run:
```bash
docker compose restart minio-init
```

**Scripts can't connect to database locally?**
When running scripts outside Docker, use `localhost:5432`. Inside Docker, services use `postgres:5432`. The `.env` file is configured for local execution.
