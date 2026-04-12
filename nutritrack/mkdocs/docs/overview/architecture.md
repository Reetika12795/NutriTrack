# System Architecture

## Overview

NutriTrack is a containerized data engineering platform with **15 Docker services** spanning 5 layers: data sources, orchestration, storage, analytics, and monitoring. All services deploy with a single `docker compose up -d` command.

## Full Architecture Diagram

```mermaid
graph TB
    subgraph External["External Data Sources"]
        OFF["Open Food Facts<br/>REST API"]
        PQD["OFF Parquet Dump<br/>via DuckDB"]
        ANSES["ANSES / EFSA<br/>Web Scraping"]
    end

    subgraph Orchestration["Orchestration Layer"]
        AW["Airflow Webserver<br/>:8080"]
        AS["Airflow Scheduler"]
        AWK["Airflow Worker<br/>(Celery)"]
        SD["StatsD Exporter<br/>:9102"]
    end

    subgraph Storage["Storage Layer"]
        PG[("PostgreSQL 16<br/>:5432<br/>4 schemas:<br/>app / raw / staging / dw")]
        MN[("MinIO S3<br/>:9000 / :9001<br/>bronze / silver<br/>gold / backups")]
        RD[("Redis 7<br/>:6379<br/>Cache + Broker")]
    end

    subgraph Analytics["Analytics & API Layer"]
        API["FastAPI<br/>:8000<br/>JWT + RBAC"]
        ST["Streamlit<br/>:8501<br/>4-role frontend"]
        MH["MailHog<br/>:8025<br/>SMTP alerts"]
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

| # | Service | Image | Port(s) | Layer | Purpose |
|---|---------|-------|---------|-------|---------|
| 1 | `postgres` | postgres:16-alpine | 5432 | Storage | OLTP (app) + Data Warehouse (dw) + Raw + Staging |
| 2 | `redis` | redis:7-alpine | 6379 | Storage | API response cache + Airflow Celery broker |
| 3 | `minio` | minio/minio:latest | 9000, 9001 | Storage | S3-compatible data lake (4 buckets) |
| 4 | `airflow-webserver` | custom | 8080 | Orchestration | Airflow UI and API |
| 5 | `airflow-scheduler` | custom | -- | Orchestration | DAG scheduling and task triggering |
| 6 | `airflow-worker` | custom | -- | Orchestration | Celery task execution (PySpark available) |
| 7 | `fastapi` | custom | 8000 | Analytics | REST API with JWT auth and RBAC (8 endpoints) |
| 8 | `streamlit` | custom | 8501 | Analytics | 4-role web frontend (28 pages total) |
| 9 | `mailhog` | mailhog/mailhog | 1025, 8025 | Analytics | SMTP test server for alert emails |
| 10 | `prometheus` | prom/prometheus | 9090 | Monitoring | Metrics collection and storage |
| 11 | `grafana` | grafana/grafana | 3000 | Monitoring | 6 dashboards for SLA and operations |
| 12 | `statsd-exporter` | prom/statsd-exporter | 9102, 9125 | Monitoring | Airflow metrics bridge to Prometheus |
| 13 | `cadvisor` | gcr.io/cadvisor | 8081 | Monitoring | Container resource metrics |
| 14 | `node-exporter` | prom/node-exporter | 9100 | Monitoring | Host OS metrics |
| 15 | `postgres-exporter` | prometheuscommunity/postgres-exporter | 9187 | Monitoring | PostgreSQL metrics |

## PostgreSQL Schema Layout

NutriTrack uses a single PostgreSQL instance with 4 schemas for logical separation:

| Schema | Purpose | Tables |
|--------|---------|--------|
| `app` | Operational OLTP data | users, products, meals, meal_items, etl_activity_log, rgpd_data_registry |
| `raw` | Raw extracted data before cleaning | raw_products_api, raw_products_parquet, raw_guidelines |
| `staging` | Intermediate processing | staging_products, data_quality_checks |
| `dw` | Star schema data warehouse | 7 dimensions + 2 facts + 6 datamart views |

## Persistent Volumes

| Volume | Service | Purpose |
|--------|---------|---------|
| `postgres_data` | PostgreSQL | Database files |
| `redis_data` | Redis | Cache persistence |
| `minio_data` | MinIO | Object store data |
| `prometheus_data` | Prometheus | Metric time series |
| `grafana_data` | Grafana | Dashboard state |

## Network

All services communicate over a shared Docker bridge network (`nutritrack_default`). External access is through mapped ports only. Internal service names resolve via Docker DNS.
