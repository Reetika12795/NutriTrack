# System Architecture

## Overview

NutriTrack is a containerized data engineering platform with **15 Docker services** spanning 5 layers: data sources, orchestration, storage, analytics, and monitoring.

## Full Architecture Diagram

```mermaid
graph TB
    subgraph External["External Data Sources"]
        OFF["Open Food Facts<br/>REST API"]
        PQD["OFF Parquet Dump<br/>3M+ products"]
        ANSES["ANSES / EFSA<br/>Web Scraping"]
    end

    subgraph Orchestration["Orchestration Layer"]
        AW["Airflow Webserver<br/>:8080"]
        AS["Airflow Scheduler"]
        AWK["Airflow Worker<br/>(Celery)"]
        SD["StatsD Exporter<br/>:9102"]
    end

    subgraph Storage["Storage Layer"]
        PG[("PostgreSQL 16<br/>:5432<br/>─────────<br/>app schema (OLTP)<br/>dw schema (OLAP)")]
        MN[("MinIO S3<br/>:9000 / :9001<br/>─────────<br/>bronze / silver<br/>gold / backups")]
        RD[("Redis 7<br/>:6379<br/>─────────<br/>Cache + Broker")]
    end

    subgraph Analytics["Analytics & API Layer"]
        API["FastAPI<br/>:8000<br/>JWT + RBAC"]
        ST["Streamlit<br/>:8501"]
        SS["Superset 6.0.1<br/>:8088<br/>RBAC"]
        MH["MailHog<br/>:8025<br/>SMTP Test"]
    end

    subgraph Monitoring["Monitoring Layer"]
        PR["Prometheus<br/>:9090"]
        GF["Grafana<br/>:3000<br/>6 dashboards"]
        CA["cAdvisor<br/>:8081"]
        NE["Node Exporter<br/>:9100"]
        PE["Postgres Exporter<br/>:9187"]
    end

    OFF --> AWK
    PQD --> AWK
    ANSES --> AWK

    AW --- AS
    AS --> AWK
    AWK --> SD

    AWK -->|ETL Load| PG
    AWK -->|Medallion Pipeline| MN
    AWK -->|Email Alerts| MH
    RD -.->|Celery Broker| AWK

    PG --> API
    PG --> SS
    PG --> ST
    RD -->|Cache| API

    PE -->|Scrape| PR
    SD -->|Metrics| PR
    CA -->|Containers| PR
    NE -->|Host| PR
    PR --> GF

    style External fill:#e8f5e9,stroke:#2e7d32
    style Storage fill:#e3f2fd,stroke:#1565c0
    style Analytics fill:#fff3e0,stroke:#e65100
    style Monitoring fill:#fce4ec,stroke:#c62828
    style Orchestration fill:#f3e5f5,stroke:#6a1b9a
```

## Service Matrix

| Service | Image | Port(s) | Layer | Purpose |
|---------|-------|---------|-------|---------|
| `postgres` | postgres:16-alpine | 5432 | Storage | Operational DB + Data Warehouse |
| `redis` | redis:7-alpine | 6379 | Storage | API cache + Airflow Celery broker |
| `minio` | minio/minio:latest | 9000, 9001 | Storage | S3-compatible data lake |
| `airflow-webserver` | custom | 8080 | Orchestration | Airflow UI |
| `airflow-scheduler` | custom | — | Orchestration | DAG scheduling |
| `airflow-worker` | custom | — | Orchestration | Celery task execution |
| `fastapi` | custom | 8000 | Analytics | REST API (JWT + RBAC) |
| `streamlit` | custom | 8501 | Analytics | Web frontend |
| `superset` | custom | 8088 | Analytics | BI dashboards |
| `mailhog` | mailhog/mailhog | 1025, 8025 | Analytics | SMTP test server |
| `prometheus` | prom/prometheus | 9090 | Monitoring | Metrics collection |
| `grafana` | grafana/grafana | 3000 | Monitoring | Dashboards |
| `statsd-exporter` | prom/statsd-exporter | 9102, 9125 | Monitoring | Airflow metrics bridge |
| `cadvisor` | gcr.io/cadvisor | 8081 | Monitoring | Container metrics |
| `node-exporter` | prom/node-exporter | 9100 | Monitoring | Host metrics |
| `postgres-exporter` | prometheuscommunity/postgres-exporter | 9187 | Monitoring | DB metrics |

## Network Topology

All services communicate over a shared Docker bridge network. Key connections:

```mermaid
graph LR
    subgraph Internal
        PG[(PostgreSQL)]
        RD[(Redis)]
        MN[(MinIO)]
    end

    subgraph Consumers
        API[FastAPI]
        AF[Airflow Worker]
        SS[Superset]
        ST[Streamlit]
    end

    PG --- API
    PG --- AF
    PG --- SS
    PG --- ST
    RD --- API
    RD --- AF
    MN --- AF
```

## Deployment

Single-command deployment via Docker Compose:

```bash
docker compose up -d --build
```

All services include health checks, restart policies (`unless-stopped`), and persistent volumes for data durability.

### Persistent Volumes

| Volume | Service | Purpose |
|--------|---------|---------|
| `postgres_data` | PostgreSQL | Database files |
| `redis_data` | Redis | Cache persistence |
| `minio_data` | MinIO | Object store |
| `prometheus_data` | Prometheus | Metric time series |
| `grafana_data` | Grafana | Dashboard state |
