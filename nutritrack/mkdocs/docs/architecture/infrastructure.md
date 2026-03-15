# Infrastructure

## Docker Compose Architecture

All services are defined in a single `docker-compose.yml` with health checks, restart policies, and persistent volumes.

```mermaid
graph TB
    subgraph volumes["Persistent Volumes"]
        v1[("postgres_data")]
        v2[("redis_data")]
        v3[("minio_data")]
        v4[("prometheus_data")]
        v5[("grafana_data")]
    end

    subgraph init["Init Containers (run once)"]
        MI["minio-init<br/>Create buckets"]
        AI["airflow-init<br/>DB migrate + admin user"]
    end

    subgraph core["Core Services"]
        PG["postgres:16-alpine"] --> v1
        RD["redis:7-alpine"] --> v2
        MN["minio/minio"] --> v3
    end

    subgraph airflow["Airflow Cluster"]
        AW["airflow-webserver"]
        AS["airflow-scheduler"]
        AWK["airflow-worker"]
    end

    subgraph apps["Application Services"]
        API["fastapi"]
        ST["streamlit"]
        SS["superset"]
        MH["mailhog"]
    end

    subgraph mon["Monitoring Stack"]
        PR["prometheus"] --> v4
        GF["grafana"] --> v5
        SD["statsd-exporter"]
        CA["cadvisor"]
        NE["node-exporter"]
        PE["postgres-exporter"]
    end

    AI -.->|depends_on| PG
    AI -.->|depends_on| RD
    MI -.->|depends_on| MN
    AW -.->|depends_on| AI
    AS -.->|depends_on| AI
    AWK -.->|depends_on| AI

    style init fill:#f5f5f5,stroke:#9e9e9e
    style core fill:#e3f2fd,stroke:#1565c0
    style airflow fill:#f3e5f5,stroke:#6a1b9a
    style apps fill:#fff3e0,stroke:#e65100
    style mon fill:#fce4ec,stroke:#c62828
```

## Resource Requirements

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| PostgreSQL | 1 core | 512MB | 2GB+ |
| MinIO | 0.5 core | 256MB | 5GB+ |
| Airflow (3 services) | 2 cores | 2GB | 500MB |
| Superset | 1 core | 1GB | 200MB |
| Monitoring (5 services) | 1 core | 512MB | 1GB |
| **Total** | **~6 cores** | **~5GB** | **~10GB** |

## CI/CD Pipelines

```mermaid
graph LR
    subgraph trigger["Trigger"]
        PR["Push / PR to main"]
    end

    subgraph jobs["GitHub Actions"]
        L["Lint<br/>─────<br/>Ruff (Python)<br/>sqlfluff (SQL)"]
        T["Test<br/>─────<br/>pytest<br/>56 tests"]
        D["Docker Build<br/>─────<br/>API, App<br/>Airflow, Superset"]
    end

    subgraph deploy["Deploy"]
        DOCS["MkDocs<br/>GitHub Pages"]
    end

    PR --> L
    PR --> T
    PR --> D
    PR -->|main only| DOCS

    style trigger fill:#e8f5e9,stroke:#2e7d32
    style jobs fill:#e3f2fd,stroke:#1565c0
    style deploy fill:#fff3e0,stroke:#e65100
```

### Workflow Details

| Workflow | File | Trigger | What it does |
|----------|------|---------|-------------|
| **Lint** | `lint.yml` | Push/PR to main | Ruff on `*.py`, sqlfluff on `*.sql` |
| **Test** | `test.yml` | Push/PR to main | pytest with Python 3.11 (56 tests) |
| **Docker** | `docker.yml` | Push/PR to main | Build-validates all 4 Dockerfiles |
| **Docs** | `deploy-docs.yml` | Push to main | Build & deploy MkDocs to GitHub Pages |
