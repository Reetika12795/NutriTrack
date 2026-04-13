# NutriTrack

**Nutritional Data Engineering Platform**

An end-to-end data engineering platform that collects 798K+ French food products from Open Food Facts, cleans them with PySpark, stores them in a star-schema data warehouse and a medallion data lake, and serves them through a role-based Streamlit frontend.

Built as a capstone project for the **RNCP37638 Data Engineer certification** (Level 7).

**[Live Documentation](https://reetika12795.github.io/NutriTrack/)** | **[LinkedIn](https://www.linkedin.com/in/reetika-gautam/)** | **[Portfolio](http://zafire.in/?i=1)**

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (4+ GB RAM allocated)
- [Git](https://git-scm.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/Reetika12795/NutriTrack.git
cd NutriTrack/nutritrack

# Start all 15 services
docker compose up -d

# Wait ~60 seconds for all services to initialize, then verify
docker compose ps
```

### Access the Platform

| Service | URL | Credentials |
|---------|-----|-------------|
| **Streamlit** (Frontend) | http://localhost:8501 | See demo accounts below |
| **FastAPI** (Swagger Docs) | http://localhost:8000/docs | JWT token from login |
| **Airflow** (DAG UI) | http://localhost:8080 | `admin` / `admin` |
| **Grafana** (Monitoring) | http://localhost:3000 | `admin` / `admin` |
| **MinIO** (Data Lake) | http://localhost:9001 | `minioadmin` / `minioadmin123` |
| **MailHog** (Alert Emails) | http://localhost:8025 | None |

### Demo Accounts

| Username | Password | Role | Streamlit Pages |
|----------|----------|------|-----------------|
| `reetika` | `user123demo` | user | 6 pages |
| `dr_martin` | `user123demo` | nutritionist | 7 pages (+ patient dashboard) |
| `analyst_sophie` | `user123demo` | analyst | 7 pages (+ product analytics) |
| `admin_nutritrack` | `user123demo` | admin | 8 pages (all) |

---

## Architecture

```
Sources (3)          Orchestration         Storage              Application
+-----------+       +-------------+      +--------------+     +------------+
| OFF API   |       |             |      | PostgreSQL   |     | FastAPI    |
| OFF Parq. |------>|  Airflow    |----->| 4 schemas:   |---->| JWT + RBAC |
| ANSES     |       |  7 DAGs     |      | app/raw/     |     +-----+------+
+-----------+       |  PySpark    |      | staging/dw   |           |
                    +------+------+      +--------------+     +-----v------+
                           |             | MinIO S3     |     | Streamlit  |
                           +------------>| bronze/      |     | 4 roles    |
                                         | silver/gold  |     +------------+
                                         +--------------+
                    Monitoring: Prometheus + Grafana (6 dashboards) + MailHog
```

### 15 Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 16 | 5432 | Operational DB + Data Warehouse (4 schemas) |
| Redis 7 | 6379 | API cache + Airflow Celery broker |
| MinIO | 9000/9001 | S3-compatible data lake (bronze/silver/gold) |
| Airflow Webserver | 8080 | DAG monitoring UI |
| Airflow Scheduler | - | DAG scheduling |
| Airflow Worker | - | Task execution (Celery + PySpark) |
| FastAPI | 8000 | REST API with JWT auth |
| Streamlit | 8501 | 4-role frontend |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | 6 monitoring dashboards |
| StatsD Exporter | 9102 | Airflow metrics bridge |
| cAdvisor | 8081 | Docker container metrics |
| Node Exporter | 9100 | Host system metrics |
| PG Exporter | 9187 | PostgreSQL metrics |
| MailHog | 8025 | SMTP alert testing |

---

## Data Pipeline

| Step | Time | What happens |
|------|------|-------------|
| **Extraction** | 02:00 | 3 sources: OFF API (JSON), OFF Parquet (DuckDB), ANSES scraping |
| **Cleaning** | 04:00 | PySpark 7-rule pipeline: 798K raw -> 777K clean (97.4% retention) |
| **Loading** | 05:00 | Star schema (7 dims + 2 facts) + Medallion lake (bronze/silver/gold) |
| **Maintenance** | 06:00 | Backups + RGPD cleanup |

### 7 Airflow DAGs

| DAG | Schedule | Description |
|-----|----------|-------------|
| `etl_extract_off_api` | Daily 02:00 | REST API extraction |
| `etl_extract_parquet` | Weekly Sun | DuckDB Parquet extraction |
| `etl_extract_scraping` | Monthly | ANSES/EFSA scraping |
| `etl_aggregate_clean` | Daily 04:00 | PySpark clean + validate + load |
| `etl_datalake_ingest` | Daily 05:00 | Bronze/silver/gold + aggregates |
| `etl_load_warehouse` | Daily 05:00 | Star schema dimensions + facts |
| `etl_backup_maintenance` | Weekly 06:00 | Backups + RGPD cleanup |

---

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| Database | PostgreSQL 16 | OLTP + OLAP (4 schemas) |
| Data Lake | MinIO | S3-compatible medallion architecture |
| Orchestration | Apache Airflow 2.8 | ETL pipeline scheduling (CeleryExecutor) |
| Cleaning | PySpark 3.5 | Distributed data transformation |
| Big Data Query | DuckDB | SQL directly on Parquet files |
| API | FastAPI | Async REST + JWT + RBAC |
| Frontend | Streamlit | 4-role dashboards |
| Monitoring | Prometheus + Grafana | 6 dashboards + SLA tracking |
| Cache | Redis 7 | API cache + Celery broker |

---

## Role-Based Access (RBAC)

Double security: Streamlit hides pages by role **AND** FastAPI's `require_role()` rejects unauthorized API calls with HTTP 403.

| Role | API Access | Streamlit Pages |
|------|-----------|-----------------|
| **user** | /products, /meals | 6 pages (search, meals, dashboard, trends, compare, alternatives) |
| **nutritionist** | + /nutritionist/* | 7 pages (+ patient analytics dashboard) |
| **analyst** | + /analytics/* | 7 pages (+ product analytics, data catalog) |
| **admin** | all endpoints | 8 pages (everything) |

---

## Project Structure

```
nutritrack/
├── airflow/              # DAGs and plugins
│   ├── dags/             # 7 ETL DAGs
│   └── plugins/          # Alerting callbacks
├── api/                  # FastAPI REST API
│   ├── routers/          # auth, products, meals, analytics, nutritionist
│   └── auth/             # JWT authentication
├── app/                  # Streamlit frontend (role-based)
├── sql/                  # Database schemas and migrations
├── scripts/              # Standalone extraction/import scripts
├── monitoring/           # Prometheus, Grafana, StatsD configs
├── mkdocs/               # Documentation site (deployed to GitHub Pages)
├── docs/                 # Report, slides, speaker notes
│   ├── report/           # Final report (EN + FR)
│   ├── slides/           # Defense slides (LaTeX Beamer)
│   └── assets/           # Logos and screenshots
├── tests/                # Pytest test suite
├── docker-compose.yml    # All 15 services
└── Makefile              # Dev commands
```

---

## Useful Commands

```bash
# Start / stop
docker compose up -d
docker compose down

# Trigger ETL pipeline
docker exec nutritrack-airflow-worker-1 airflow dags trigger etl_aggregate_clean

# Check product count
docker exec nutritrack-postgres-1 psql -U nutritrack -d nutritrack \
  -c "SELECT COUNT(*) FROM app.products;"

# View worker logs
docker compose logs -f airflow-worker
```

---

## Author

**Reetika Gautam** - Data Engineer at Publicis Resources

[Portfolio](http://zafire.in/?i=1) | [LinkedIn](https://www.linkedin.com/in/reetika-gautam/) | [GitHub](https://github.com/Reetika12795)

RNCP37638 - Expert en Infrastructures de Donnees Massives | Simplon | April 2026
