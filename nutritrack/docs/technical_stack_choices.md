# NutriTrack — Technical Stack Choices and Architecture Decisions

**Project**: NutriTrack — Fitness Nutrition Tracker
**Certification**: Expert en Infrastructures de Donnees Massives (RNCP37638)
**Document Purpose**: Justify every technology choice in the NutriTrack platform, explain alternatives considered, and map each decision to certification competencies.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Docker Compose — Containerized Infrastructure](#2-docker-compose--containerized-infrastructure)
3. [PostgreSQL 16 — Relational Database](#3-postgresql-16--relational-database)
4. [Apache Airflow 2.8.1 — ETL Orchestration](#4-apache-airflow-281--etl-orchestration)
5. [MinIO — S3-Compatible Data Lake](#5-minio--s3-compatible-data-lake)
6. [Redis 7 — Caching and Message Broker](#6-redis-7--caching-and-message-broker)
7. [FastAPI — REST API Framework](#7-fastapi--rest-api-framework)
8. [Streamlit — Frontend Dashboard](#8-streamlit--frontend-dashboard)
9. [Python Data Libraries — Extraction and Processing](#9-python-data-libraries--extraction-and-processing)
10. [Security, RGPD, and Governance Choices](#10-security-rgpd-and-governance-choices)
11. [Eco-Responsibility and Resource Optimization](#11-eco-responsibility-and-resource-optimization)
12. [Summary — Technology-to-Competency Mapping](#12-summary--technology-to-competency-mapping)

---

## 1. Architecture Overview

NutriTrack is built as a 10-service Docker Compose stack that covers the full data engineering lifecycle: ingestion, storage, transformation, warehousing, data lake archival, API exposure, and visualization.

```
    External Sources                    User-Facing Layer
   (Open Food Facts,                  (Streamlit :8501)
    ANSES, EFSA)                            │
         │                                  │
         ▼                           FastAPI :8000
  ┌──────────────┐                   (REST API + JWT)
  │   Airflow    │                          │
  │  :8080       │                          │
  │  Scheduler   │──────────► PostgreSQL 16 :5432
  │  Worker      │            ┌─────────────────────┐
  │  Webserver   │            │  app schema (OLTP)  │
  └──────┬───────┘            │  dw schema  (OLAP)  │
         │                    └─────────────────────┘
         │                              │
         ▼                              │
    MinIO :9000/9001           Redis 7 :6379
    (Data Lake)                (Cache + Broker)
```

**Design principle**: Every component is independently replaceable. PostgreSQL could be swapped for MySQL, MinIO for AWS S3, Airflow for Prefect — without rewriting the entire system. This modularity is intentional and reflects production-grade architecture practices.

---

## 2. Docker Compose — Containerized Infrastructure

**Choice**: Docker Compose with 10 services
**Competencies**: C3 (Technical framework), C14 (DW creation), C19 (Infrastructure components)

### Why Docker Compose?

| Criterion | Docker Compose | Manual installation | Kubernetes |
|---|---|---|---|
| **Setup time** | `docker compose up` — 3 minutes | Hours of manual config | Complex YAML + cluster setup |
| **Reproducibility** | Identical on any machine | "Works on my machine" problem | Reproducible but over-engineered |
| **Appropriate scale** | Single-node, dev/small prod | Single-node | Multi-node, large-scale prod |
| **Learning curve** | Moderate | Low per tool, high overall | Steep |

### Why not Kubernetes?

Kubernetes is designed for orchestrating hundreds of containers across multiple nodes. NutriTrack is a single-project platform with 10 services running on one machine. Docker Compose provides the same containerization benefits (isolation, reproducibility, declarative config) without the operational overhead of a cluster orchestrator. In a production scenario with horizontal scaling requirements, migrating to Kubernetes would be a natural evolution — the Docker images are already built and portable.

### Key architectural decisions in docker-compose.yml

- **Health checks on all critical services** — PostgreSQL, Redis, MinIO, and Airflow webserver all define health checks. Dependent services use `condition: service_healthy` to ensure correct startup order. This prevents race conditions where the API starts before the database is ready.
- **Named volumes for persistence** — `postgres_data`, `redis_data`, `minio_data` survive container restarts. Data is not lost when running `docker compose down`.
- **Volume mounts for development** — `./api:/app/api`, `./airflow/dags:/opt/airflow/dags` enable live code reloading without rebuilding images.
- **Init containers** — `airflow-init` creates the admin user and database connections, then exits. `minio-init` creates the medallion buckets, then exits. This pattern separates one-time setup from runtime services.

---

## 3. PostgreSQL 16 — Relational Database

**Choice**: PostgreSQL 16 Alpine
**Competencies**: C9 (SQL queries), C11 (RGPD-compliant database), C13 (Star schema), C14 (DW creation), C16 (DW maintenance)

### Why PostgreSQL?

| Criterion | PostgreSQL | MySQL | MongoDB | ClickHouse |
|---|---|---|---|---|
| **Dual schema support** | Native schemas (app + dw) | Separate databases only | Not applicable | OLAP only, no OLTP |
| **Star schema + SCD** | Full support with procedures | Limited stored procedures | No relational modeling | Good for OLAP, no SCD |
| **RGPD compliance** | Row-level security, pgcrypto | Basic encryption | Document-level | Limited |
| **JSON support** | JSONB for semi-structured data | JSON type (limited) | Native | Limited |
| **Ecosystem** | Largest open-source RDBMS | Popular but less advanced | Different paradigm | Niche |
| **AsyncIO drivers** | asyncpg (fastest Python driver) | aiomysql (less mature) | motor | Not relevant |

### Why not separate databases for OLTP and OLAP?

A common architecture uses one database for operations and another (e.g., ClickHouse, Redshift) for analytics. We chose a **dual-schema approach within a single PostgreSQL instance**:

- `app` schema — operational/OLTP (products, users, meals, RGPD registry)
- `dw` schema — analytical/OLAP (star schema dimensions, fact tables, datamart views)

**Justification**: For a project of this scale (hundreds of thousands of products, not billions), PostgreSQL handles both workloads efficiently. The schemas provide logical separation with different access roles, while avoiding the operational complexity of synchronizing two separate database systems. The ETL from `app` to `dw` uses SQL `INSERT ... SELECT` statements that execute entirely within PostgreSQL, eliminating network latency between systems.

**Trade-off acknowledged**: In a production environment with millions of daily analytical queries, a dedicated columnar store (ClickHouse, BigQuery) would outperform PostgreSQL for OLAP. The current design prioritizes simplicity and demonstrates the architectural pattern — migrating the `dw` schema to a dedicated OLAP engine would require changing only the ETL target connection, not the schema design itself.

### PostgreSQL-specific features used

- **pgcrypto extension** — SHA-256 hashing for user pseudonymization in the warehouse (`encode(digest(user_id::text, 'sha256'), 'hex')`), ensuring RGPD compliance (C11, C21)
- **Stored procedures** — SCD Type 1/2/3 implementations as PostgreSQL functions (C17)
- **Schema-level role isolation** — `app_readonly`, `nutritionist_role`, `admin_role`, `etl_service` roles with granular GRANT permissions per schema (C21)
- **Auto-initialization** — SQL scripts in `sql/init/` are mounted to `/docker-entrypoint-initdb.d/` for automatic schema creation on first boot (C14)

---

## 4. Apache Airflow 2.8.1 — ETL Orchestration

**Choice**: Apache Airflow 2.8.1 with CeleryExecutor
**Competencies**: C8 (Data extraction), C10 (Aggregation), C15 (ETL pipelines), C16 (DW maintenance)

### Why Airflow?

| Criterion | Airflow | Prefect | Luigi | Cron + scripts |
|---|---|---|---|---|
| **DAG visualization** | Web UI with task graphs | Cloud-based UI | Minimal UI | None |
| **Retry/failure handling** | Built-in retries, alerts, SLAs | Built-in | Basic | Manual |
| **Scheduling** | Cron syntax, sensors, triggers | Cron + event-based | Cron-based | Cron only |
| **Industry adoption** | De facto standard for data engineering | Growing | Declining | Universal but primitive |
| **Monitoring** | Task logs, duration tracking, Gantt charts | Observability dashboard | Limited | Log files only |
| **Scalability** | CeleryExecutor, KubernetesExecutor | Workers with Dask/Ray | Local only | N/A |

### Why Airflow over Prefect?

Prefect is a modern alternative with a cleaner Python API. However, Airflow was chosen because:

1. **Industry standard** — Airflow is used by Airbnb, Spotify, Twitter, and most data engineering teams in France. A jury evaluating a Data Engineer candidate expects familiarity with Airflow.
2. **CeleryExecutor** — demonstrates distributed task execution with Redis as the message broker, which is a realistic production pattern. Prefect's execution model is different (agent-based) and less representative of traditional ETL orchestration.
3. **Connection management** — Airflow's UI allows configuring database and S3 connections visually, which is useful for demonstrating infrastructure configuration (C19).

### Why CeleryExecutor instead of LocalExecutor?

The CeleryExecutor distributes tasks across worker processes via Redis, demonstrating a production-ready architecture:

```
Scheduler → Redis (broker) → Worker(s) → Task execution
```

LocalExecutor runs tasks in the scheduler process itself, which is simpler but doesn't demonstrate distributed processing. The CeleryExecutor choice also justifies the Redis service in the stack — it serves as both the Celery broker and the API cache.

### Airflow DAG design

Six DAGs with clear separation of concerns:

| DAG | Schedule (UTC) | Purpose | Competency | Upstream Dependency |
|---|---|---|---|---|
| `etl_extract_parquet` | `0 1 * * 0` | Bulk Parquet/DuckDB extraction (Sundays) | C8 | — |
| `etl_extract_off_api` | `0 2 * * *` | REST API extraction (daily) | C8 | — |
| `etl_extract_scraping` | `0 3 * * 1` | Web scraping — BeautifulSoup (Mondays) | C8 | — |
| `etl_aggregate_clean` | `0 4 * * *` | Merge, deduplicate, validate, load to DB | C10, C15 | Extraction DAGs |
| `etl_load_warehouse` | `0 5 * * *` | Star schema ETL with SCD procedures | C13, C15, C17 | `etl_aggregate_clean.load_to_database` |
| `etl_datalake_ingest` | `0 5 * * *` | Medallion pipeline: bronze → silver → gold | C18, C20 | `etl_aggregate_clean.clean_data` |

After `etl_aggregate_clean` completes at 04:00, two independent paths fork at 05:00:

```
Extract DAGs (01:00–03:00)
       ↓
etl_aggregate_clean (04:00):
  aggregate → clean → load to PostgreSQL app
       ↓                         ↓
etl_datalake_ingest (05:00):   etl_load_warehouse (05:00):
  bronze → silver → gold         app → dw star schema (SCD)
  (reads silver Parquet,         (reads app + user meals,
   NO PostgreSQL)                 includes RGPD user data)
```

The lake and DW are **parallel consumers** of the same cleaned data. The gold layer reads from silver Parquet (pandas only, no database dependency), while the warehouse reads from PostgreSQL. Both downstream DAGs use `ExternalTaskSensor` to wait for their respective upstream tasks.

Each DAG is independently triggerable and retryable. Task dependencies within DAGs enforce correct execution order (e.g., dimensions load before facts).

---

## 5. MinIO — S3-Compatible Data Lake

**Choice**: MinIO (latest)
**Competencies**: C18 (Data lake architecture), C19 (Infrastructure components), C20 (Data catalog), C21 (Data governance)

### Why MinIO?

| Criterion | MinIO | AWS S3 | HDFS | Local filesystem |
|---|---|---|---|---|
| **S3 API compatible** | 100% compatible | Native | No | No |
| **Self-hosted** | Docker container | Cloud only (paid) | Complex cluster | N/A |
| **Cost** | Free, open-source | Pay per GB/request | Free but heavy infra | Free |
| **Web console** | Built-in (:9001) | AWS Console | Ambari/Cloudera | None |
| **Lifecycle rules** | S3-compatible policies | Native | HDFS policies | Manual |
| **Bucket policies** | IAM-style JSON policies | IAM | POSIX ACLs | POSIX |

### Why not AWS S3 directly?

S3 would be the production choice, but it requires an AWS account with billing enabled. MinIO provides an identical API — any code written against MinIO works unchanged against S3 by simply changing the endpoint URL. This demonstrates the architecture pattern without incurring cloud costs.

### Why not HDFS?

HDFS (Hadoop Distributed File System) is designed for petabyte-scale distributed storage across clusters of commodity hardware. NutriTrack's data lake stores gigabytes, not petabytes. HDFS would add complexity (NameNode, DataNode, Zookeeper) without benefit. MinIO provides object storage semantics (buckets, prefixes, lifecycle rules) that align with modern data lake patterns (S3-style) rather than legacy Hadoop patterns.

### Why a data lake when there's already a data warehouse?

The data warehouse and the data lake serve **different users with different access patterns**. This is not redundancy — it is complementarity.

| | Data Warehouse (`dw` schema in PostgreSQL) | Data Lake (MinIO gold layer) |
|---|---|---|
| **Serves** | BI analysts, dashboards (SQL) | Data scientists, ML engineers (Python) |
| **Optimized for** | Fast JOINs across normalized dimensions | Flat files — `pd.read_parquet()` and go |
| **Content** | Star schema: dims + facts (SCD Type 1/2/3) | Denormalized wide tables, quality reports, ML features, snapshots |
| **History model** | SCD Type 2 (row-level change tracking) | Date-partitioned snapshots (full catalog state per day) |
| **Schema** | Schema-on-write (strict SQL DDL) | Schema-on-read (flexible Parquet) |
| **Example query** | `SELECT AVG(energy_kcal) FROM fact JOIN dim_brand...` (3-table JOIN) | `df = pd.read_parquet("product_wide_denormalized.parquet")` (one line) |

The gold layer does **not** duplicate DW queries. Each gold dataset contains content that genuinely cannot exist in a star schema:

| Gold dataset | What it is | Why the DW can't do this |
|---|---|---|
| `product_wide_denormalized` | Every product with brand + category + all nutrition inlined | DW requires JOINs across 4 tables. Data scientist wants one flat file |
| `data_quality_report` | Completeness rates, null %, anomaly flags per column | Metadata ABOUT data, not business data. Doesn't belong in a star schema |
| `source_comparison` | Row counts, overlap rates per extraction source | Cross-source lineage analysis. The DW doesn't track which source a fact came from |
| `daily_snapshots` | Full product catalog as one dated file | Time-travel without SCD. "Give me the catalog as it was on March 3rd" |
| `ml_nutrition_features` | Scaled/encoded feature matrix (no nulls) | ML preprocessing — the DW stores raw values, not engineered features |

### Medallion architecture implementation

The data lake follows the medallion (multi-hop) architecture, an industry standard pattern popularized by Databricks:

```
Bronze (raw)          Silver (cleaned)         Gold (data science)
├── api/              ├── products/            ├── product_wide_denormalized/
│   └── 2026-03-03/   │   └── 2026-03-03/     │   └── 2026-03-03/
│       └── *.json    │       ├── *.parquet    │       └── product_wide_denormalized.parquet
├── scraping/         │       └── *.csv        ├── data_quality_report/
│   └── 2026-03-03/   ├── _quality/            ├── source_comparison/
│       └── *.json    │   └── 2026-03-03/      ├── daily_snapshots/
├── _manifests/       │       └── data_quality  │   └── 2026-03-03/
├── _lineage/         │           _report.json  │       └── catalog_snapshot.parquet
│   └── 2026-03-03    └── _catalog/             ├── ml_nutrition_features/
│       .json             └── metadata.json     └── _catalog/
└── _catalog/                                       └── metadata.json
```

- **Bronze**: Raw data exactly as extracted. Immutable. 90-day lifecycle rule auto-deletes old data. Includes `_lineage/` metadata recording source availability, file sizes, and row counts before any processing (C20 traceability).
- **Silver**: Cleaned, deduplicated, schema-conformed. 1-year retention. Includes `_quality/` reports with completeness scores, null rates, and cleaning decision logs (C20 quality metadata).
- **Gold**: Denormalized datasets for data scientists. Indefinite retention. Content is structurally different from the DW — flat files, quality metadata, ML features, and point-in-time snapshots.

### Governance configuration

- **Group-based access policies** (C21): `data_scientists` (gold read), `data_stewards` (quality + lineage metadata read), `nutritionists` (silver + gold read), `admins` (full), `etl_service` (write all)
- **Data catalog** (C20): `_catalog/metadata.json` in each bucket describes datasets, formats, lineage, owners, consumers, and retention policies. Gold datasets include `why_not_in_dw` fields explaining why each dataset doesn't belong in the star schema
- **Lifecycle rules** (C20): Automated expiration via S3-compatible lifecycle configuration
- **Lineage metadata** (C20): `_lineage/` in bronze and `_quality/` in silver provide full traceability from raw ingestion through cleaning to gold publication

---

## 6. Redis 7 — Caching and Message Broker

**Choice**: Redis 7 Alpine
**Competencies**: C3 (Technical framework), C14 (DW infrastructure)

### Why Redis?

Redis serves two purposes in NutriTrack:

1. **Airflow Celery broker** (database 0) — distributes tasks from the scheduler to worker(s)
2. **FastAPI response cache** (database 1) — caches product search results and nutrition summaries

### Why not RabbitMQ for the broker?

| Criterion | Redis | RabbitMQ |
|---|---|---|
| **Dual purpose** (broker + cache) | Yes — one service, two uses | No — broker only, need separate cache |
| **Airflow support** | Native CeleryExecutor support | Supported but less common |
| **Operational simplicity** | Single container, no config | Requires management UI, exchanges, queues |
| **Memory footprint** | ~10 MB | ~100 MB |

Redis was chosen because it eliminates an additional service. Instead of running RabbitMQ (broker) + Redis (cache), we run Redis alone for both roles. This reduces the Docker Compose footprint from 11 services to 10 and simplifies monitoring.

### Why not Memcached for caching?

Memcached is a simpler cache but only supports string key-value pairs. Redis supports lists, sets, sorted sets, and TTL-based expiration natively. For caching paginated API responses with metadata, Redis's data structures are more appropriate.

---

## 7. FastAPI — REST API Framework

**Choice**: FastAPI 0.109.0 with Uvicorn
**Competencies**: C12 (REST API), C21 (Data governance — access control)

### Why FastAPI?

| Criterion | FastAPI | Flask | Django REST Framework | Express.js |
|---|---|---|---|---|
| **Performance** | Async (ASGI), one of the fastest | Sync (WSGI), slower | Sync, heavy framework | Fast (Node.js) |
| **Auto-documentation** | OpenAPI/Swagger generated automatically | Manual (Swagger plugin) | Browsable API | Manual |
| **Type validation** | Pydantic models (automatic) | Manual or Marshmallow | Serializers | Manual |
| **Async database** | Native with asyncpg | Requires extensions | Limited | Native |
| **Python ecosystem** | Native | Native | Native | JavaScript |

### Why FastAPI over Flask?

The certification requires demonstrating a REST API that follows standards like OpenAPI (C12). FastAPI generates OpenAPI documentation automatically from type annotations — every endpoint, request body, and response schema appears at `/docs` without writing any documentation code. Flask requires manual Swagger configuration.

FastAPI's async support with `asyncpg` enables non-blocking database queries, which is important for an API serving multiple concurrent users tracking meals in real-time.

### Authentication and authorization design

- **JWT (HS256)** with `python-jose` — stateless authentication, no session storage needed
- **bcrypt** password hashing via `passlib` — industry standard, resistant to brute-force
- **Role-based access control (RBAC)** — `require_role()` dependency that checks user roles from the JWT payload
- **Pydantic validation** — all request/response models are type-checked at the framework level, preventing injection attacks

### API endpoint design

```
/api/v1/auth/register    POST   — Create account
/api/v1/auth/login       POST   — Get JWT token
/api/v1/auth/me          GET    — Current user profile
/api/v1/products/        GET    — Search products (paginated, filtered)
/api/v1/products/{id}    GET    — Product detail
/api/v1/meals/           GET    — List user's meals
/api/v1/meals/           POST   — Log a meal
/api/v1/meals/daily-summary    GET  — Daily nutrition totals
/api/v1/meals/weekly-trends    GET  — Weekly trend analysis
```

The `/api/v1/` prefix enables API versioning. All meal endpoints require authentication. Product search is public but rate-limited via Redis.

---

## 8. Streamlit — Frontend Dashboard

**Choice**: Streamlit 1.31.0
**Competencies**: C7 (Communication supports), C12 (Software interfaces)

### Why Streamlit?

| Criterion | Streamlit | React/Vue | Grafana | Jupyter/Voila |
|---|---|---|---|---|
| **Development speed** | Hours | Days/weeks | Configuration-based | Quick for notebooks |
| **Python-native** | Yes — same language as pipeline | No — JavaScript | No — UI config | Yes |
| **Interactive dashboards** | Built-in with Plotly | Full custom | Pre-built panels | Limited |
| **Deployment** | Single Docker container | Build + serve + API | Container + data source config | Container |
| **Appropriate for** | Data apps, internal tools, demos | Production web apps | Monitoring/ops | Exploration |

### Why not a JavaScript frontend (React/Vue)?

The certification is for Data Engineering, not web development. Streamlit allows building a functional, interactive dashboard in Python — the same language as the rest of the stack. A React frontend would require:

- A separate JavaScript build toolchain (Node.js, npm, webpack)
- API client code duplicating Pydantic schemas
- CSS/HTML knowledge outside the certification scope

Streamlit communicates with FastAPI over HTTP, demonstrating the API-as-interface pattern (C12) without introducing frontend complexity that is not evaluated.

### Why not Grafana?

Grafana excels at monitoring dashboards with time-series data. NutriTrack's frontend is an interactive application (user registration, meal logging, product search), not a monitoring dashboard. Grafana cannot handle form submissions or user authentication flows.

---

## 9. Python Data Libraries — Extraction and Processing

**Choice**: pandas, DuckDB, BeautifulSoup, pyarrow, requests
**Competencies**: C8 (Extraction scripts), C9 (SQL queries), C10 (Aggregation/cleaning)

### Why these specific libraries?

| Library | Purpose | Why this one? |
|---|---|---|
| **pandas 2.2** | Data cleaning, transformation | Industry standard for tabular data manipulation. Every data engineer is expected to know pandas. |
| **DuckDB 0.9** | Analytical SQL on Parquet files | Enables SQL queries directly on Parquet files without loading into a database. Processes the 3M+ product Open Food Facts dump in seconds, not minutes. |
| **BeautifulSoup 4.12** | Web scraping | The most widely-used Python HTML parser. Simpler than Scrapy for targeted scraping of 2-3 websites. |
| **pyarrow 15.0** | Parquet file read/write | The reference Parquet implementation for Python. Required by pandas for Parquet support. |
| **requests 2.31** | HTTP API calls | The standard Python HTTP client. Simple, reliable, well-documented. |
| **SQLAlchemy 2.0** | Database ORM + async queries | Supports both sync (psycopg2 for ETL) and async (asyncpg for FastAPI) access patterns through a single model layer. |

### Why DuckDB instead of loading Parquet into pandas directly?

The Open Food Facts Parquet dump contains 3+ million rows. Loading this entirely into pandas would require ~4-8 GB of RAM. DuckDB processes Parquet files using columnar scanning — it reads only the columns needed and applies filters before loading into memory:

```python
# DuckDB: scans only needed columns, filters in-engine
duckdb.sql("""
    SELECT code, product_name, energy_kcal_100g, nutriscore_grade
    FROM 'products.parquet'
    WHERE countries_en LIKE '%France%'
    LIMIT 200000
""")
```

This approach uses ~200 MB of RAM instead of 8 GB. DuckDB demonstrates handling big data volumes (C8) with appropriate tooling, which is directly relevant to the "massive data infrastructure" aspect of the certification.

### Why not Apache Spark?

Spark is designed for distributed processing across clusters. NutriTrack's data processing runs on a single machine. Using Spark would require:

- A Spark cluster (additional Docker services: master, worker, history server)
- JVM overhead (~500 MB base memory per process)
- Serialization costs for Python ↔ JVM communication (PySpark)

DuckDB achieves the same analytical performance on single-node datasets without these overheads. The architectural decision is documented: for datasets under 10 GB, DuckDB outperforms Spark on a single machine.

---

## 10. Security, RGPD, and Governance Choices

**Competencies**: C3 (RGPD compliance), C11 (RGPD-compliant database), C16 (RGPD maintenance), C20 (RGPD catalog), C21 (Data governance)

### Password security

- **bcrypt** with salt rounds — passwords are never stored in plaintext
- Chosen over SHA-256 because bcrypt is intentionally slow (resistant to brute-force), while SHA-256 is fast (designed for hashing, not password storage)

### JWT authentication

- **HS256 algorithm** — symmetric key, appropriate for single-service architectures
- In a microservices environment, RS256 (asymmetric) would be preferred so that services can verify tokens without knowing the signing key
- **60-minute expiry** — balances security (short-lived tokens) with usability (users don't re-login every 5 minutes)

### RGPD compliance architecture

| Requirement | Implementation |
|---|---|
| **Data registry** | `app.rgpd_data_registry` table documenting all personal data fields, purposes, retention periods, legal basis |
| **Consent tracking** | `consent_data_processing` boolean + `consent_date` timestamp on user registration |
| **Pseudonymization** | User IDs hashed with SHA-256 (`pgcrypto`) before entering the data warehouse. The `dw` schema contains `user_hash`, never `user_id` |
| **Right to deletion** | `cleanup_expired_data()` PostgreSQL function removes data past retention period |
| **Data minimization** | Data lake contains no personal data. User data stays exclusively in PostgreSQL `app` schema |
| **Access control** | PostgreSQL roles limit who can access which schema. MinIO policies limit bucket access by group |

### Why pseudonymization instead of anonymization in the warehouse?

Full anonymization (removing all identifiers) would prevent linking warehouse records back to users for legitimate purposes (e.g., responding to a data subject access request). Pseudonymization with SHA-256 hashing makes re-identification computationally infeasible without the original `user_id`, while maintaining referential integrity in the star schema. This aligns with RGPD Article 4(5) which recognizes pseudonymization as a security measure.

---

## 11. Eco-Responsibility and Resource Optimization

**Competency**: C3 (Eco-responsibility strategy, RGESN framework)

### Docker Alpine images

All base images use Alpine Linux variants (`postgres:16-alpine`, `redis:7-alpine`):

| Image | Standard | Alpine |
|---|---|---|
| PostgreSQL 16 | ~400 MB | ~80 MB |
| Redis 7 | ~130 MB | ~30 MB |

Alpine images reduce disk usage by ~75% and decrease container startup time, contributing to lower energy consumption during development and CI/CD.

### DuckDB over Spark for single-node processing

As discussed in Section 9, DuckDB processes the same data as Spark would, using ~200 MB RAM instead of ~2 GB (JVM + PySpark overhead). On a developer machine running 10 Docker services simultaneously, this memory savings is significant.

### Data lifecycle rules

MinIO lifecycle rules automatically delete expired bronze data (90 days) and old backups (30 days), preventing unbounded storage growth. This is both an operational best practice and an eco-responsibility measure — stored data consumes energy for persistence and replication.

### Batch over real-time processing

All ETL pipelines run on daily/weekly/monthly schedules rather than continuous streaming. For a nutrition tracking application where data freshness of hours (not seconds) is acceptable, batch processing is more resource-efficient than maintaining always-on streaming infrastructure (Kafka, Flink).

---

## 12. Summary — Technology-to-Competency Mapping

| Technology | Version | Competencies Covered | Key Justification |
|---|---|---|---|
| **Docker Compose** | v2 | C3, C14, C19 | Reproducible infrastructure, one-command deployment |
| **PostgreSQL** | 16 | C9, C11, C13, C14, C16, C17, C21 | Dual-schema (OLTP + OLAP), star schema, SCD, RGPD compliance |
| **Apache Airflow** | 2.8.1 | C8, C10, C15, C16 | Industry-standard ETL orchestration, 6 DAGs with monitoring |
| **MinIO** | latest | C18, C19, C20, C21 | S3-compatible data lake, medallion architecture, governance |
| **Redis** | 7 | C3, C14 | Dual-purpose: Celery broker + API cache |
| **FastAPI** | 0.109 | C12, C21 | Async REST API, auto OpenAPI docs, JWT + RBAC |
| **Streamlit** | 1.31 | C7, C12 | Python-native dashboard, rapid prototyping |
| **pandas** | 2.2 | C10, C15 | Data cleaning, transformation, deduplication |
| **DuckDB** | 0.9 | C8, C9 | Analytical SQL on Parquet, memory-efficient big data processing |
| **BeautifulSoup** | 4.12 | C8 | Web scraping for nutritional guidelines |
| **SQLAlchemy** | 2.0 / 1.4 | C9, C11, C14 | ORM for both async API and sync ETL access patterns |
| **python-jose + bcrypt** | — | C12, C21 | JWT authentication, secure password hashing |

### Technologies explicitly NOT chosen (and why)

| Not chosen | Replaced by | Reason |
|---|---|---|
| Kubernetes | Docker Compose | Over-engineered for single-node project |
| Apache Spark | DuckDB + pandas | JVM overhead unjustified for < 10 GB data |
| AWS S3 | MinIO | Identical API, self-hosted, no cloud costs |
| HDFS | MinIO | Legacy pattern, designed for petabyte scale |
| RabbitMQ | Redis | Redis covers both broker and cache roles |
| MongoDB | PostgreSQL | Relational modeling required for star schema |
| React/Vue | Streamlit | Frontend development outside certification scope |
| Grafana | Streamlit | Need interactive app, not monitoring dashboard |
| Kafka | Airflow batch scheduling | Real-time streaming unnecessary for nutrition data |

---

*This document serves as the technical study component required by competency C3 and supports the architecture decisions presentation for evaluations E2 and E4.*
