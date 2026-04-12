# Quick Start

## Prerequisites

| Requirement | Minimum Version |
|------------|----------------|
| **Docker** | 24.0+ |
| **Docker Compose** | v2.20+ (included with Docker Desktop) |
| **Git** | 2.30+ |
| **RAM** | 8 GB (6 GB allocated to Docker) |
| **Disk** | 15 GB free space |

!!! warning "Docker Resources"
    Ensure Docker Desktop has at least **6 GB RAM** and **4 CPU cores** allocated. The 15 services require significant resources. Check: Docker Desktop > Settings > Resources.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Reetika12795/NutriTrack.git
cd NutriTrack/nutritrack
```

### 2. Start All Services

```bash
docker compose up -d --build
```

This builds custom images and starts all 15 services. First run takes 5--10 minutes for image builds.

### 3. Wait for Initialization

```bash
# Check that all services are healthy
docker compose ps
```

Wait 2--3 minutes for:

- PostgreSQL to create schemas and seed data
- MinIO to create buckets (bronze, silver, gold, backups)
- Airflow to initialize the database and create the admin user
- Grafana to provision dashboards

### 4. Access Services

| Service | URL | Status Check |
|---------|-----|-------------|
| **Airflow** | [http://localhost:8080](http://localhost:8080) | DAGs list visible |
| **FastAPI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI loads |
| **Streamlit** | [http://localhost:8501](http://localhost:8501) | Login page visible |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | 4 buckets visible |
| **Grafana** | [http://localhost:3000](http://localhost:3000) | 6 dashboards visible |
| **MailHog** | [http://localhost:8025](http://localhost:8025) | Inbox page loads |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | Targets page shows UP |

## Demo Credentials

### Airflow

| Username | Password |
|----------|----------|
| `admin` | `admin` |

### MinIO Console

| Username | Password |
|----------|----------|
| `minioadmin` | `minioadmin123` |

### Grafana

| Username | Password |
|----------|----------|
| `admin` | `admin` |

### Streamlit / FastAPI (demo accounts)

| Email | Password | Role |
|-------|----------|------|
| `user@nutritrack.local` | `demo123` | user |
| `nutritionist@nutritrack.local` | `demo123` | nutritionist |
| `analyst@nutritrack.local` | `demo123` | analyst |
| `admin@nutritrack.local` | `demo123` | admin |

!!! tip "Creating New Users"
    You can also register new accounts via the FastAPI `/api/v1/auth/register` endpoint or the Streamlit registration page. New accounts default to the `user` role.

## Running ETL Pipelines

### Trigger DAGs Manually

1. Open [Airflow UI](http://localhost:8080)
2. Enable the DAGs by toggling the switches
3. Click the play button to trigger a manual run

Recommended order for first run:

1. `etl_extract_off_api` (or `etl_extract_parquet` for bulk data)
2. `etl_aggregate_clean` (waits for extraction to complete)
3. `etl_load_warehouse` (loads star schema)
4. `etl_datalake_ingest` (populates MinIO buckets)

### Verify Data

=== "PostgreSQL"

    ```bash
    docker exec nutritrack-postgres-1 psql -U nutritrack -d nutritrack -c \
      "SELECT COUNT(*) FROM app.products;"
    ```

=== "MinIO"

    Open [MinIO Console](http://localhost:9001) and check:

    - `bronze/` -- raw data files
    - `silver/` -- cleaned Parquet files
    - `gold/` -- analytics-ready aggregates

=== "API"

    ```bash
    # Login
    TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"user@nutritrack.local","password":"demo123"}' \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

    # Search products
    curl -s http://localhost:8000/api/v1/products/?search=nutella \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
    ```

## Stopping Services

```bash
# Stop all services (preserves data)
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v
```

!!! warning "Data Loss"
    Using `docker compose down -v` removes all persistent volumes. This deletes the database, MinIO objects, Grafana dashboards, and Prometheus metrics. Only use this for a complete reset.

## Troubleshooting

### Services not starting

```bash
# Check logs for a specific service
docker compose logs postgres
docker compose logs airflow-webserver
docker compose logs fastapi
```

### Port conflicts

If a port is already in use, either stop the conflicting service or change the port mapping in `docker-compose.yml`.

Common conflicts:

| Port | Service | Common Conflict |
|------|---------|----------------|
| 5432 | PostgreSQL | Local PostgreSQL installation |
| 8080 | Airflow | Other web servers |
| 3000 | Grafana | Other dev tools (e.g., React dev server) |
| 9090 | Prometheus | Other monitoring tools |

### Airflow DAGs not visible

- Wait 1--2 minutes for the scheduler to parse DAG files
- Check scheduler logs: `docker compose logs airflow-scheduler`
- Verify DAG files exist: `ls airflow/dags/`

### Out of memory

- Increase Docker Desktop memory allocation to 8 GB
- Stop unused services: `docker compose stop cadvisor node-exporter`
- The monitoring stack (5 services) can be disabled to save ~1 GB RAM

### Database connection errors

```bash
# Verify PostgreSQL is running and healthy
docker compose ps postgres
docker exec nutritrack-postgres-1 pg_isready -U nutritrack
```
