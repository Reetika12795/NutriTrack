# Tech Stack

## Technology Choices

Every technology was selected based on project requirements, resource constraints (~48K EUR engineering budget, zero licensing cost), and certification competency coverage.

## Full Stack

| Technology | Version | Purpose | Why Chosen | Alternatives Considered |
|-----------|---------|---------|------------|------------------------|
| **PostgreSQL** | 16 | Relational DB (OLTP + OLAP) | Mature, extensible, supports multiple schemas in one instance | MySQL (fewer features), MongoDB (not relational) |
| **MinIO** | latest | S3-compatible object store | Self-hosted, S3 API compatible, lightweight | AWS S3 (cost), HDFS (overkill for project scale) |
| **Apache Airflow** | 2.8.1 | Workflow orchestration | Industry standard, DAG-based, rich operator library | Prefect (less mature), Luigi (less features) |
| **PySpark** | 3.5 | Data cleaning at scale | Distributed processing, DataFrame API, handles 800K rows | Pandas (memory limits), Polars (less ecosystem) |
| **DuckDB** | latest | Analytical queries on Parquet | In-process OLAP, zero-config, reads Parquet natively | Spark SQL (heavier), raw Parquet readers |
| **FastAPI** | latest | REST API | Async, auto OpenAPI docs, Pydantic validation | Flask (no async), Django REST (heavier) |
| **Streamlit** | latest | Web frontend | Rapid prototyping, Python-native, multi-page apps | Dash (more verbose), React (separate stack) |
| **Redis** | 7 | Caching + message broker | In-memory speed, Celery support, simple setup | Memcached (no persistence), RabbitMQ (more complex) |
| **Prometheus** | latest | Metrics collection | Pull-based, PromQL, Grafana integration | InfluxDB (push-based), Datadog (paid) |
| **Grafana** | latest | Dashboards and alerting | Multi-source, alerting rules, provisioning as code | Kibana (ELK-only), Metabase (less flexible) |
| **Docker Compose** | v2 | Container orchestration | Single-file deployment, reproducible, no cloud dependency | Kubernetes (overkill), Podman (less adoption) |
| **GitHub Actions** | -- | CI/CD | Native to GitHub, free for public repos | GitLab CI (separate platform), Jenkins (self-hosted overhead) |
| **MailHog** | latest | SMTP testing | Captures all emails, web UI, zero config | Mailtrap (cloud), real SMTP (risky in dev) |
| **BeautifulSoup** | 4 | Web scraping | Simple HTML parsing, well-documented | Scrapy (overkill), Selenium (heavy) |
| **SQLAlchemy** | 2.x | ORM / DB toolkit | Async support, both ORM and Core, migration support | raw psycopg2 (no ORM), Peewee (less features) |
| **Pydantic** | 2.x | Data validation | FastAPI integration, type safety, serialization | Marshmallow (slower), Cerberus (less typed) |
| **bcrypt** | -- | Password hashing | Industry standard, salt built-in | Argon2 (newer, less adoption), SHA256 (not suitable) |
| **JWT (HS256)** | -- | API authentication | Stateless, widely supported, 60-min expiry | Session-based (stateful), OAuth2 (complexity) |

## Architecture Principles

| Principle | Implementation |
|-----------|---------------|
| **Single-command deploy** | `docker compose up -d` starts all 15 services |
| **~48K EUR engineering (one-time)** | 3-month team: Data Engineer + Architect + DevOps |
| **Zero licensing** | All tools are open-source; no cloud subscriptions |
| **OPEX < 100 EUR/year** | Domain + electricity; saves ~8K/yr vs AWS |
| **Reproducibility** | Docker images pin versions; `requirements.txt` freezes Python deps |
| **Separation of concerns** | 4 PostgreSQL schemas, 4 MinIO buckets, layered architecture |
| **Observability** | Prometheus + Grafana + StatsD + activity logging |

## Resource Footprint

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| Storage (PostgreSQL + Redis + MinIO) | 2 cores | 1 GB | 7 GB+ |
| Orchestration (Airflow x3) | 2 cores | 2 GB | 500 MB |
| Analytics (FastAPI + Streamlit + MailHog) | 1 core | 512 MB | 200 MB |
| Monitoring (Prometheus + Grafana + exporters) | 1 core | 512 MB | 1 GB |
| **Total** | **~6 cores** | **~4 GB** | **~9 GB** |

!!! info "Development Machine"
    The platform runs on a standard laptop (8+ GB RAM, 4+ cores). No cloud infrastructure required.
