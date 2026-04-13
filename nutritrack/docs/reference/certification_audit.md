# NutriTrack Certification Audit Report

**Certification**: Expert en infrastructures de donnees massives (Data Engineer) - RNCP37638 - Level 7
**Audit Date**: 2026-04-09
**Previous Audit**: 2026-03-14
**Auditor**: cert-auditor (automated codebase analysis)
**Scope**: All 21 competencies (C1-C21) across 4 blocks, 7 evaluations (E1-E7)

---

## Audit Summary

| Status | Count | Competencies |
|--------|-------|-------------|
| **FULL** | 19 | C1, C2, C3, C5, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20, C21 |
| **PARTIAL** | 2 | C4, C6 |
| **MISSING** | 0 | -- |

**Overall Assessment**: The project provides excellent coverage across all 21 competencies. Since the March 14 audit, significant progress has been made on previously flagged gaps: C16 (alerting/SLA) is now FULL, C20 (data catalog) is now FULL, and PySpark has been added to the cleaning pipeline. 19 competencies are fully evidenced in code and documentation. 2 have minor gaps that are documentation-level issues only. No competency is missing.

**Changes since previous audit (2026-03-14)**:
- C16: PARTIAL -> FULL (added MailHog SMTP, alerting plugin, SLA dashboard, ETL activity log table, ITIL priority matrix)
- C20: PARTIAL -> FULL (added data catalog browser UI in Streamlit, MinIO Grafana alert rules, quality metadata in silver layer, lineage metadata in bronze layer)
- C10: Added PySpark-based cleaning pipeline alongside pandas version
- CI/CD: Added 4 GitHub Actions workflows (lint, test, docker, deploy-docs)
- Tests: Added 3 test files (test_sql_schemas.py, test_api_schemas.py, test_etl_functions.py)
- API: Added analytics and nutritionist routers with role-based access
- SQL: Added migrations for ETL activity log, staging schemas, data quality checks table

---

## Block 1: Piloter la conduite d'un projet data

### C1 - Analyze a data project need expression | FULL

**Evaluation**: E1, E2
**Evidence Files:**
- `docs/rapport_final.md` Ch.1 - Interview grids for data producers and consumers
- `docs/rapport_final.md` Ch.2.1 - Synthesis note with need analysis

**What is covered:**
- Interview grid for data producers (questions covering business activities, metadata, access, storage, treatments)
- Interview grid for data consumers (questions covering usage, granularity, delivery, RGPD)
- Synthesis note with: need analysis, functional scope, available means, feasibility, data governance
- SMART objectives
- Pre-project with macro technical recommendations, RGPD compliance actions
- RICE analysis context in the synthesis note

**Gaps:** None.

---

### C2 - Map available data (data topography) | FULL

**Evaluation**: E2
**Evidence Files:**
- `docs/rapport_final.md` Ch.2.1 - Complete data topography in 4 parts

**What is covered:**
- **Semantics/Metadata**: Business glossary with business objects (Product, Brand, Category, User, Meal, etc.)
- **Data Models**: Structured (PostgreSQL tables in `sql/init/01_schema_operational.sql`), Semi-structured (JSON from OFF API in `data/raw/api/`), File-based (Parquet in `data/raw/parquet/`)
- **Treatments & Data Flows**: Flux matrix with source-to-target flows including format, treatment script, and frequency. Clearly evidenced by the 6 Airflow DAGs in `airflow/dags/`.
- **Access & Usage Conditions**: Role-based access matrix documented and implemented in `sql/init/00_init_databases.sql` (7 PostgreSQL roles), `scripts/setup_minio.py` (4 MinIO group policies), and `api/auth/jwt.py` (3 API roles)

**Gaps:** None.

---

### C3 - Design a technical data exploitation framework | FULL

**Evaluation**: E2
**Evidence Files:**
- `docs/rapport_final.md` Ch.2.2 - Complete technical architecture study
- `docs/technical_stack_choices.md` - 14-section technology justification document
- `docker-compose.yml` - 17 services defined (355 lines)
- `sql/init/*.sql` - Physical data models (4 files)
- `docs/dw_vs_datalake_justification.md` - Architecture decision documentation

**What is covered:**
- **Functional analysis**: System capabilities and business constraints documented in rapport and technical stack doc
- **Non-functional needs**: Performance, scalability, reliability, security, availability table in `docs/technical_stack_choices.md`
- **Functional representation**: Flux matrix with 6 DAGs mapping sources to targets
- **Applicative representation**: Docker Compose architecture diagram with all 17 services and port mappings; service interaction matrix. The `docs/technical_stack_choices.md` contains a complete ASCII architecture diagram with data flows.
- **Infrastructure representation**: Technology stack table with versions (PostgreSQL 16, Airflow 2.8, MinIO, Redis 7, FastAPI, Streamlit, Prometheus, Grafana, DuckDB, PySpark)
- **Operational representation**: ETL schedules (02:00-05:00 UTC pipeline chain), DAG dependencies with ExternalTaskSensors
- **Architecture decisions**: Documented in `docs/technical_stack_choices.md` with rationale, alternatives considered, and competency mapping per technology
- **RGPD processes**: Personal data registry (`app.rgpd_data_registry` with 7 entries after migration 001), sorting/deletion procedures (`rgpd_cleanup_expired_data()`), consent tracking columns
- **Eco-responsibility strategy**: Documented following RGESN framework in rapport and stack choices doc. Practices include: Docker resource limits, Parquet over CSV, batch processing schedule optimization, DuckDB for in-process analytics (no cluster overhead)
- **Flux matrix**: Present in applicative representation
- **Accessibility**: Streamlit provides accessible web UI; OpenAPI docs at `/docs` and `/redoc`

**Gaps:** None significant. Accessibility accommodations could reference WCAG standards more explicitly, but this is a minor documentation enhancement.

---

### C4 - Conduct technical and regulatory monitoring | PARTIAL

**Evaluation**: E2
**Evidence Files:**
- `docs/veille_technologique.md` - Technical monitoring newsletter (80+ lines)
- `docs/rapport_final.md` Ch.2.3 - Monitoring section

**What is covered:**
- **Monitoring theme**: Apache Superset 6.0 (BI tool used in project) - detailed release analysis with impact assessment
- **Regulatory monitoring**: GDPR and nutritional data - EDPB Guidelines 01/2026 analysis with NutriTrack compliance checklist
- **Tool monitoring**: Apache Airflow 2.8 features relevant to the project
- **Monitoring schedule**: "Minimum 1 hour per week" documented; weekly frequency stated
- **Aggregation tools**: Dedicated monitoring newsletter document (`docs/veille_technologique.md`)
- **Source reliability criteria**: Verified sources table with reliability levels (Official ASF, Official Superset docs, Community verified GitHub issues, EDPB official, Astronomer Blog)
- **Communications**: Newsletter format with prioritized action items table

**Gaps:**
- **Accessibility-compliant communications**: The newsletter is in Markdown format which is screen-reader friendly, but there is no explicit statement about accessibility compliance of monitoring outputs.
- **Regular schedule evidence**: The newsletter covers one period (Week of March 10, 2026). A second newsletter covering a different period would strengthen the evidence of regular ongoing monitoring. The criteria state "regular schedule (min 1h/week)" - having only one bulletin makes it harder to demonstrate regularity.

**Recommendation:** Create one additional brief monitoring bulletin for a different date range (e.g., late March or early April) to demonstrate the ongoing nature of the monitoring practice. Even a half-page update on a recent tool change would suffice.

---

### C5 - Plan data project execution | FULL

**Evaluation**: E3
**Evidence Files:**
- `docs/rapport_final.md` Ch.3 - Complete project planning

**What is covered:**
- Team composition with required skills (roles documented)
- Budget allocation context (Docker Compose = minimal infrastructure cost, all open-source tools)
- Roadmap broken into phases with durations and deliverables
- Production calendar with tasks, deliverables, resources, and effort weighting (story points)
- Effort weighting method: Fibonacci story points (poker planning equivalent)
- Tracking tools: Git, Airflow UI, Makefile (in `Makefile` - 14 targets for standardized operations)
- Rituals: sprint planning, daily standup, sprint review, retrospective
- Risk evaluation: implicit in trade-offs section; phases have associated risks

**Gaps:** None significant.

---

### C6 - Supervise data project execution | PARTIAL

**Evaluation**: E2, E3
**Evidence Files:**
- `docs/rapport_final.md` Ch.2.4 and Ch.3.4 - Project supervision and tracking
- `Makefile` - 14 standardized commands (targets: up, down, logs, init-db, extract, clean, import, warehouse, lake, backup, test, lint, format, docs)
- `airflow/dags/` - 6 DAGs with execution monitoring
- `sql/migrations/001_add_etl_activity_log.sql` - Activity logging table
- `airflow/plugins/alerting.py` - Callback functions logging to activity table

**What is covered:**
- **Exchange facilitation**: Makefile for standardized commands; Airflow Web UI for pipeline visibility
- **Tracking tools configured and accessible**: Airflow UI (port 8080), Grafana (port 3000), Superset (port 8088), FastAPI docs (port 8000/docs)
- **Rituals documented**: Sprint planning, standup, review, retrospective in rapport
- **Indicators**: The `app.etl_activity_log` table (created via migration 001) tracks DAG/task success/failure/retry/SLA-miss events with timestamps, categories, and JSONB details. The `app.extraction_log` table tracks records extracted/loaded/rejected per source.

**Gaps:**
- **Indicators updated throughout the project**: While the logging infrastructure (`etl_activity_log`, `extraction_log`) exists and is functional, the evidence of indicators being "updated throughout the project" with historical data spanning multiple weeks/months depends on the live demo showing populated entries. The backups in `data/backups/` span April 2-8 2026, which provides some evidence of ongoing operation, but more is needed.
- **Tracking tool accessibility for non-technical stakeholders**: The Airflow UI is configured but requires admin credentials. No evidence of a simplified stakeholder-facing status page.

**Recommendation:** During the live demo, ensure the `etl_activity_log` table and `extraction_log` table show entries spanning multiple dates. The existing backup files (April 2-8) demonstrate ongoing automated operations, which helps. Consider briefly demonstrating the Grafana SLA dashboard as the stakeholder-accessible view.

---

### C7 - Communicate throughout the data project | FULL

**Evaluation**: E3
**Evidence Files:**
- `docs/rapport_final.md` Ch.3.5 - Communication strategy
- `docs/defense_slides.tex` - Beamer defense slides
- `docs/final_deck.tex` - Final presentation deck
- `docs/generate_defense_pptx.py` - PPTX generation script
- `docs/speaker_notes.md` - Presenter notes
- `docs/presenter_en_francais.md` - French presenter guide
- `api/main.py` - OpenAPI documentation with role descriptions
- `app/streamlit_app.py` - User-facing frontend with 6 pages

**What is covered:**
- All communication steps planned: sprint kickoff, progress updates, demos, API docs, user docs, final delivery
- Accessible supports: Swagger UI (`/docs`), ReDoc (`/redoc`), Streamlit app (port 8501), MkDocs site
- Adapted content per audience: technical (Swagger/API docs), business (Streamlit dashboard), jury (defense slides + rapport), analysts (Superset dashboards)
- Chosen orientations and trade-offs communicated
- User documentation: MkDocs documentation site at `mkdocs/` with 12 pages covering architecture, data warehouse, data lake, API, monitoring, and certification
- End-user onboarding: Streamlit app provides self-service UI with login/register
- Feedback collection: documented process

**Gaps:** None.

---

## Block 2: Realiser la collecte, le stockage et la mise a disposition des donnees

### C8 - Automate data extraction scripts | FULL

**Evaluation**: E4
**Evidence Files:**
- `scripts/extract_off_api.py` - REST API extraction (221 lines)
- `scripts/extract_off_parquet.py` - Data file extraction (standalone)
- `scripts/extract_scraping.py` - Web scraping (281 lines)
- `scripts/extract_from_db.py` - Database extraction (269 lines)
- `scripts/extract_duckdb.py` - Big data system / DuckDB analytics
- `airflow/dags/etl_extract_off_api.py` - DAG for API extraction
- `airflow/dags/etl_extract_parquet.py` - DAG for Parquet + DuckDB extraction (147 lines)
- `airflow/dags/etl_extract_scraping.py` - DAG for web scraping

**What is covered:**
- **REST API**: Open Food Facts search API (`scripts/extract_off_api.py`) with pagination, rate limiting (0.6s delay), User-Agent header, timeout handling, argparse entry point
- **Data file**: OFF Parquet export via DuckDB (`airflow/dags/etl_extract_parquet.py`) - reads 3M+ product Parquet file with complex SQL extraction including nested ARRAY/STRUCT handling
- **Scraping**: ANSES and EFSA websites (`scripts/extract_scraping.py`) with BeautifulSoup/lxml, fallback EU RDA values, multiple source scraping
- **Database**: PostgreSQL extraction (`scripts/extract_from_db.py`) with 5 documented analytical queries, SQLAlchemy connection pooling, EXPLAIN ANALYZE documentation
- **Big data system**: DuckDB analytical queries (`scripts/extract_duckdb.py`) on 3M+ product Parquet dataset with window functions, aggregations
- All scripts have: entry point (`main()` with `argparse`), dependency initialization, external connections (HTTP/DB), logic rules, error handling (`try/except` with logging), result saving (JSON/CSV/Parquet)
- All versioned on Git
- Scripts also exist as Airflow DAG tasks for automated scheduling

**Gaps:** None. All 5 required source types are covered: REST API, data file, scraping, database, big data system.

---

### C9 - Develop SQL extraction queries | FULL

**Evaluation**: E4
**Evidence Files:**
- `sql/queries/analytical_queries.sql` - 7 documented analytical queries (226 lines)
- `scripts/extract_from_db.py` - 5 documented extraction queries with optimization notes
- `airflow/dags/etl_extract_parquet.py` - DuckDB SQL queries for Parquet analytics

**What is covered:**
- 12+ functional queries across 3 files with increasing complexity
- **Full-text search**: GIN index with `ts_rank`, `plainto_tsquery` (Query 2 in analytical_queries.sql)
- **Window functions**: `ROW_NUMBER()`, `AVG() OVER (ROWS BETWEEN)`, `LAG()`, `LEAD()`, `RANK()`, `MODE() WITHIN GROUP`
- **CTEs**: Used for code organization and pre-filtering (Queries 3, 4, 6)
- **EXPLAIN ANALYZE notes**: Documenting optimization choices per query
- **Selection/filtering/join choices documented**: Each query has comments explaining join strategy, filter order, and index usage
- **Query optimizations**: Composite indexes (`idx_meals_user_date`), GIN indexes for full-text search, aggregate pushdown, NULLIF for safe division, HAVING for post-aggregation filtering
- **Both operational and analytical queries**: Operational (app schema) in analytical_queries.sql, warehouse (dw schema) in queries 5-7

**Gaps:** None.

---

### C10 - Develop data aggregation rules | FULL

**Evaluation**: E4
**Evidence Files:**
- `scripts/aggregate_clean.py` - Standalone pandas aggregation script (464 lines)
- `airflow/dags/etl_aggregate_clean.py` - DAG version with PySpark + pandas (539 lines)
- `data/cleaned/products_cleaned.parquet` - Output dataset (exists on disk)
- `data/cleaned/products_cleaned.csv` - CSV output (exists on disk)
- `data/cleaned/cleaning_report.json` - Cleaning report (exists on disk)

**What is covered:**
- **Multi-source aggregation**: API JSON + Parquet + DuckDB + DB export merged
- **Two implementations**: Pandas (standalone) and PySpark (DAG) for distributed-capable processing
- **PySpark pipeline** (`clean_data_spark` in DAG): SparkSession with S3A/MinIO config, schema alignment via `unionByName`, column casting, window functions for deduplication
- **Column standardization**: 10+ column name mappings across sources (e.g., `code` -> `barcode`, `brands` -> `brand_name`)
- **Barcode cleaning**: Strip non-numeric chars, validate length 8-14 digits
- **Null product name removal**: Filter rows without product_name
- **Numeric range validation**: Cap at physiological maximums per 100g (energy_kcal <= 1000, fat_g <= 100, etc.)
- **Nutri-Score normalization**: Uppercase A-E, invalid grades set to null
- **Deduplication**: By barcode, keeping highest completeness_score (window function in PySpark, `sort_values` + `drop_duplicates` in pandas)
- **Data quality validation**: `validate_data_quality` task with 6 checks (row count, null rates, range validation, schema conformance, uniqueness) logged to `staging.data_quality_checks` table
- **Output**: Single clean Parquet + CSV dataset
- **Cleaning report**: JSON with raw/cleaned counts, removal rate, rules applied, Spark version
- Script versioned on Git with documented dependencies

**Gaps:** None.

---

### C11 - Create a RGPD-compliant database | FULL

**Evaluation**: E4
**Evidence Files:**
- `sql/init/01_schema_operational.sql` - Physical data model (279 lines, 8 tables)
- `sql/init/00_init_databases.sql` - Database initialization with 7 roles (61 lines)
- `sql/init/02_schema_warehouse.sql` - Warehouse physical model (360 lines)
- `sql/migrations/001_add_etl_activity_log.sql` - Additional RGPD registry entries
- `sql/migrations/003_add_raw_staging_schemas.sql` - Raw and staging schemas
- `scripts/import_to_db.py` - Import script (287 lines)

**What is covered:**
- **MERISE models**: MCD/MLD/MPD documented in rapport_final.md
- **Functional physical model**: `app` schema with 8 tables (categories, brands, products, users, meals, meal_items, nutritional_guidelines, extraction_log, rgpd_data_registry), `dw` schema with 9 tables, `raw` and `staging` schemas
- **DB choice justified**: PostgreSQL 16 for both OLTP/OLAP, justified in `docs/technical_stack_choices.md` with comparison table (PostgreSQL vs MySQL vs MongoDB vs ClickHouse)
- **Reproducible installation**: Docker Compose with init scripts in `/docker-entrypoint-initdb.d/`, migrations in `sql/migrations/`
- **Import script functional**: `scripts/import_to_db.py` with batch upsert (5000 records/batch), `ON CONFLICT` handling, brand/category foreign key resolution
- **Import script documented on Git**: argparse CLI, logging, dry-run mode
- **RGPD compliance**:
  - Personal data registry: `app.rgpd_data_registry` table with 7 entries (4 initial + 3 from migration 001) covering legal basis (GDPR Art. 6.1.a/f), retention periods, security measures
  - Consent tracking: `consent_data_processing`, `consent_date`, `data_retention_until` columns on users table
  - Automated cleanup: `rgpd_cleanup_expired_data()` function deletes meals >2 years, deactivates users past retention date
  - Sorting procedures: RGPD cleanup function run via Airflow DAG (`etl_backup_maintenance.py` -> `run_rgpd_cleanup`)
  - Password hashing with bcrypt (`api/auth/jwt.py`)
  - UUID-based user identification (no sequential IDs)
  - Pseudonymization in warehouse: SHA-256 hashed user_id in `dw.dim_user`

**Gaps:** None.

---

### C12 - Share the dataset via REST API | FULL

**Evaluation**: E4
**Evidence Files:**
- `api/main.py` - FastAPI application (62 lines)
- `api/routers/products.py` - Product endpoints (133 lines)
- `api/routers/meals.py` - Meal endpoints (226 lines)
- `api/routers/auth.py` - Auth endpoints (76 lines)
- `api/routers/analytics.py` - Analytics endpoints (270 lines)
- `api/routers/nutritionist.py` - Nutritionist endpoints (121 lines)
- `api/auth/jwt.py` - JWT authentication with role-based access (75 lines)
- `api/schemas/` - Pydantic request/response schemas (product.py, meal.py, user.py)
- `api/models/` - SQLAlchemy ORM models (product.py, user.py)
- `api/database.py` - Async database connection
- `api/config.py` - Configuration settings

**What is covered:**
- **REST API documentation**: Auto-generated OpenAPI 3.0 at `/docs` (Swagger UI), `/redoc` (ReDoc), `/api/v1/openapi.json`. Description includes authentication instructions, role descriptions, endpoint summaries.
- **All endpoints documented**: 13+ endpoints across 5 routers:
  - Products: GET by barcode, GET search with filters (nutriscore, nova_group), GET healthier alternatives
  - Meals: POST create meal, GET list meals, GET daily nutrition summary, GET weekly trends
  - Auth: POST register, POST login, GET profile
  - Analytics: GET full analytics summary (nutriscore distribution, NOVA distribution, category stats, brand rankings, data quality metrics, top products)
  - Nutritionist: GET user stats, DELETE user
- **Auth/authz rules**:
  - JWT Bearer token authentication with configurable expiry (60 min)
  - 3 roles: user, nutritionist, admin
  - `require_role()` dependency factory for endpoint protection
  - Role-restricted endpoints: analytics requires analyst/admin, nutritionist endpoints require nutritionist/admin
  - Password hashing with bcrypt via passlib
- **Follows OpenAPI standards**: FastAPI generates OpenAPI 3.0 spec automatically
- **API is functional**: All endpoints with proper HTTP status codes (200, 201, 400, 401, 403, 404)
- **Restricted access**: All product/meal/analytics endpoints require JWT authentication
- **Data retrieval**: GET endpoints for product search, alternatives, daily/weekly summaries, analytics

**Gaps:** None.

---

## Block 3: Elaborer et maintenir un entrepot de donnees

### C13 - Model data warehouse structure | FULL

**Evaluation**: E5
**Evidence Files:**
- `sql/init/02_schema_warehouse.sql` - Star schema (360 lines)
- `sql/init/03_schema_datamarts_analytics.sql` - Analytical datamarts (193 lines)

**What is covered:**
- **Data needed for analyses listed exhaustively**: Fact tables serve two analysis domains: daily nutrition tracking (fact_daily_nutrition) and product market analysis (fact_product_market)
- **Logical and physical models without interpretation errors**: Star schema with proper FK relationships, appropriate data types, check constraints
- **Modeling applies DW practices (star schema)**:
  - 7 dimension tables: dim_time (pre-populated 2020-2030), dim_product (SCD Type 2), dim_brand (SCD Type 1), dim_category, dim_country (SCD Type 3), dim_user (SCD Type 2, pseudonymized), dim_nutriscore
  - 2 fact tables: fact_daily_nutrition (user meal tracking), fact_product_market (product analysis)
  - 6 datamart views: dm_user_daily_nutrition, dm_product_market_by_category, dm_brand_quality_ranking, dm_nutriscore_distribution, dm_nutrition_trends, dm_dw_health
- **Bottom-up approach justified**: Datamarts built first, then combined into warehouse

**Gaps:** None.

---

### C14 - Create a data warehouse | FULL

**Evaluation**: E5
**Evidence Files:**
- `sql/init/02_schema_warehouse.sql` - DW schema creation
- `sql/init/03_schema_datamarts_analytics.sql` - Analytics datamarts
- `docker-compose.yml` - PostgreSQL + Superset configuration
- `superset/superset-init.sh` - Superset initialization with RBAC
- `superset/bootstrap_dashboards.py` - Automated dashboard creation
- `superset/superset_config.py` - Superset configuration
- `docs/analytics_dashboard.md` - Dashboard documentation

**What is covered:**
- **DW is functional**: Schema created automatically via Docker init scripts (`sql/init/` mounted at `/docker-entrypoint-initdb.d/`)
- **Main configurations explained**: Schema isolation (`app` vs `dw` vs `raw` vs `staging`), indexes on fact table foreign keys, pre-populated dim_time (2020-2030)
- **Source data access correctly configured**: Environment variables in Docker Compose; Airflow connections to PostgreSQL and MinIO configured in `airflow-init`
- **Analyst access configured**: 6 datamart views with role-based GRANT statements; Superset connected with dedicated `superset` role having SELECT on `dw` schema; Superset RBAC roles (Admin, Alpha, Analyst, Nutritionist) configured in init script
- **Test procedure**: 3 test files in `tests/` (test_sql_schemas.py, test_api_schemas.py, test_etl_functions.py); CI runs via GitHub Actions `test.yml`
- **Technical documentation**: Architecture + install/config in `docs/technical_stack_choices.md`, MkDocs site
- **Tech stack experience feedback**: Documented in rapport and technical stack choices doc

**Gaps:** None.

---

### C15 - Integrate ETLs for data warehouse | FULL

**Evaluation**: E5
**Evidence Files:**
- `airflow/dags/etl_load_warehouse.py` - Warehouse ETL with SCD (337 lines)
- `airflow/dags/etl_aggregate_clean.py` - Cleaning/loading ETL with PySpark (539 lines)
- `airflow/dags/etl_datalake_ingest.py` - Data lake ETL (450+ lines)
- `airflow/dags/etl_extract_off_api.py` - API extraction DAG
- `airflow/dags/etl_extract_parquet.py` - Parquet/DuckDB extraction DAG
- `airflow/dags/etl_extract_scraping.py` - Scraping extraction DAG

**What is covered:**
- **Data formats and volumes known/explained**: JSON (API), Parquet (OFF export, 3M+ rows), HTML (scraping), SQL (PostgreSQL)
- **ETLs fed with identified data**: 6 DAGs with clear source-to-target mappings and `ExternalTaskSensor` cross-DAG dependencies
- **Output formats known/explained**: PostgreSQL tables (operational + warehouse), Parquet files (MinIO bronze/silver/gold)
- **Outputs respect expected format**: ETL respects star schema (dimensions loaded before facts, FK integrity via JOIN-based inserts)
- **ETLs apply schema-compliant treatments**: Column mapping, type casting, null handling, SCD processing
- **ETLs apply cleaning treatments**: Format/unit uniformity (column standardization, kJ->kcal conversion), duplicate detection (barcode dedup), range validation (physiological caps)
- **ETL logic clearly explained**: Task dependency chain (`aggregate >> clean >> validate >> load`), sensor-based DAG chaining, parallel dimension loading before fact loading
- **PySpark integration**: `clean_data_spark` function uses SparkSession with S3A connector, schema alignment, window functions for deduplication

**Gaps:** None.

---

### C16 - Manage the data warehouse (admin & supervision) | FULL

**Evaluation**: E6
**Evidence Files:**
- `sql/migrations/001_add_etl_activity_log.sql` - ETL activity log table (86 lines)
- `airflow/plugins/alerting.py` - Alerting callbacks with structured logging (163 lines)
- `airflow/dags/etl_backup_maintenance.py` - Backup and maintenance DAG (179 lines)
- `scripts/backup_database.py` - Backup script with MinIO upload (158 lines)
- `monitoring/prometheus/prometheus.yml` - Prometheus scraping 6 targets
- `monitoring/grafana/dashboards/sla-compliance.json` - SLA compliance dashboard
- `monitoring/grafana/dashboards/airflow.json` - Airflow metrics dashboard
- `monitoring/grafana/dashboards/airflow-dags.json` - Per-DAG dashboard
- `monitoring/grafana/dashboards/postgresql.json` - PostgreSQL monitoring
- `monitoring/grafana/dashboards/docker-system.json` - Docker/system monitoring
- `monitoring/grafana/dashboards/minio.json` - MinIO storage monitoring
- `monitoring/grafana/provisioning/alerting/minio-alerts.yml` - Grafana alert rules (212 lines)
- `monitoring/statsd/mappings.yml` - StatsD metric mappings
- `docker-compose.yml` - MailHog SMTP service (lines 340-348), Airflow SMTP config (lines 15-20)
- `mkdocs/docs/monitoring/alerting.md` - Alerting documentation with ITIL priority matrix
- `mkdocs/docs/monitoring/sla-dashboard.md` - SLA dashboard documentation
- `data/backups/` - 18 actual backup files spanning April 2-8, 2026

**What is covered:**
- **Activity logging with alert/error categories**: `app.etl_activity_log` table with CHECK constraint on `alert_category IN ('CRITICAL', 'WARNING', 'INFO')` and `event_type IN ('task_failure', 'task_success', 'task_retry', 'sla_miss', 'dag_failure', 'dag_success', 'backup_success', 'backup_failure', 'data_quality_alert', 'maintenance')`. Indexed on timestamp, category, DAG, and event type.
- **Alert system (email/notification) on errors**: 
  - `airflow/plugins/alerting.py` provides `on_failure_callback` (CRITICAL), `on_retry_callback` (WARNING), `sla_miss_callback` (WARNING), `on_success_callback` (INFO) - all log to `etl_activity_log` and trigger Airflow email alerts
  - MailHog SMTP server configured in Docker Compose (port 1025 SMTP, port 8025 Web UI)
  - Airflow SMTP environment variables configured (`AIRFLOW__SMTP__SMTP_HOST: mailhog`, port 1025, from `airflow@nutritrack.local`)
  - Grafana alert rules for MinIO: storage >80% (WARNING), service down (CRITICAL), object count anomaly >20% drop (WARNING) with email contact point to `admin@nutritrack.local`
- **Maintenance tasks prioritized and assigned**: ITIL priority matrix documented in `mkdocs/docs/monitoring/alerting.md` with 4 priority levels (P1-P4), response times, examples, and escalation procedure (L1/L2/L3)
- **SLA-based service indicators on dashboard**: Grafana `sla-compliance.json` dashboard with 10 panels tracking 5 SLIs: ETL success rate (>95%), data freshness (<24h), backup completion (100%), query response time (<5s), data completeness (>80%). Prometheus metrics sourced from StatsD exporter (Airflow metrics), postgres-exporter, and MinIO.
- **Scheduled full/partial backups functional**: 
  - `etl_backup_maintenance` DAG runs daily at 02:00 UTC
  - Daily: DW schema partial backup
  - Weekly (Sunday): Full database backup
  - Both uploaded to MinIO `backups` bucket
  - Local cleanup after 7 days
  - 18 actual backup files exist in `data/backups/` from April 2-8
  - SLA timers on backup tasks (30 min for DW, 1 hour for full)
- **Documentation covers**: New source integration, new access creation, storage space, datamarts, compute capacity (in rapport and MkDocs)
- **RGPD**: Personal data registry updated with DW-specific entries (migration 001), cleanup function runs via DAG

**Gaps:** None. All previously identified gaps (SMTP, SLA dashboard, ITIL prioritization) have been addressed.

---

### C17 - Implement dimension variations (SCD) | FULL

**Evaluation**: E6
**Evidence Files:**
- `sql/init/02_schema_warehouse.sql` - SCD Type 1/2/3 functions (lines 210-269)
- `sql/scd_procedures.sql` - Extended SCD procedures with batch operations and history views (140 lines)
- `airflow/dags/etl_load_warehouse.py` - SCD integrated into ETL dimension loading

**What is covered:**
- **SCD Type 1 (Overwrite)**: `dw.scd_type1_update_brand()` for brand name corrections + `dw.scd_type1_batch_brand_corrections()` for batch operations; applied in `load_dim_brands` ETL task
- **SCD Type 2 (Historical tracking)**: `dw.scd_type2_update_product()` with `effective_date`, `end_date`, `is_current` columns; automated detection via `dw.scd_type2_check_and_update_products()` using `IS DISTINCT FROM` logic; `dw.v_product_history` view for querying version history; applied in `load_dim_products` ETL task (detects changes, closes old records, inserts new versions); also implemented for `dim_user` (profile changes tracked)
- **SCD Type 3 (Add Column)**: `dw.scd_type3_update_country()` with `previous_country_list` column in dim_country for tracking expansion
- **Variation modeling fully integrates source data changes**: `IS DISTINCT FROM` comparison on `product_name`, `ingredients_text`, `completeness_score` fields
- **Modeling enables change historization**: SCD Type 2 maintains full history with effective/end dates
- **Variations integrated into DW respecting initial modeling**: SCD fields are part of the original dimension table definitions
- **ETLs updated**: `load_dim_brands` (SCD1), `load_dim_products` (SCD2), dimension loading in warehouse ETL
- **Documentation updated**: Physical models include SCD fields, demonstration queries provided in `sql/scd_procedures.sql`

**Gaps:** None. All three Kimball SCD types are implemented, documented, integrated into ETLs, and have demonstration queries.

---

## Block 4: Encadrer la collecte massive et la mise a disposition des donnees avec un data lake

### C18 - Design data lake architecture | FULL

**Evaluation**: E7
**Evidence Files:**
- `docker-compose.yml` - MinIO service configuration (lines 82-118)
- `airflow/dags/etl_datalake_ingest.py` - Medallion architecture DAG
- `scripts/setup_minio.py` - Data lake setup and governance script (296 lines)
- `docs/technical_stack_choices.md` - Architecture justification
- `docs/dw_vs_datalake_justification.md` - DW vs Lake comparison

**What is covered:**
- **Technical proposals coherent with exploitation framework**: MinIO with S3 API compatibility, medallion architecture (bronze/silver/gold) documented and justified
- **Architecture schema accounts for V/V/V constraints**: 
  - Volume: 3M+ products in OFF Parquet dataset, handled by DuckDB and PySpark
  - Variety: JSON (API), Parquet (OFF export), HTML (scraping), CSV, SQL - all handled by multi-source ETL
  - Velocity: Daily/weekly batch schedules with parallel DAG execution
- **Schema uses appropriate formalism**: Architecture diagrams in `docs/technical_stack_choices.md` with service-level detail
- **Multiple catalogs compared**: 3-tool comparison (Apache Atlas vs DataHub vs Custom JSON) with criteria including complexity, overhead, integration, cost
- **Selected catalog meets exploitability and access rights constraints**: Custom JSON catalog chosen for minimal overhead, native MinIO integration, project-scale sufficiency. Justified with explicit reasoning.

**Gaps:** None.

---

### C19 - Integrate data lake infrastructure components | FULL

**Evaluation**: E7
**Evidence Files:**
- `docker-compose.yml` - MinIO service + minio-init bucket creation (lines 82-118)
- `scripts/setup_minio.py` - Setup automation with lifecycle rules, access policies, catalog upload
- `airflow/dags/etl_datalake_ingest.py` - Batch processing (bronze/silver/gold pipeline)
- `airflow/dags/etl_aggregate_clean.py` - PySpark processing with S3A MinIO connector
- `app/pages/data_catalog.py` - Catalog browser UI connected to storage
- `mkdocs/docs/data-lake/catalog.md` - Catalog documentation
- `mkdocs/docs/data-lake/medallion.md` - Medallion architecture documentation

**What is covered:**
- **Installation procedure documentation complete**: Docker Compose + Makefile commands; `scripts/setup_minio.py` automates bucket creation, lifecycle rules, access policies, catalog upload
- **Installation runs without errors in test environment**: `docker compose up -d` starts all services with healthchecks; `minio-init` service creates buckets automatically
- **Storage system installed and functional**: MinIO with 4 buckets (bronze, silver, gold, backups) and public read on gold
- **Batch tools functional and connected to storage**: 
  - Airflow `etl_datalake_ingest` DAG (bronze ingestion, silver transformation, gold publishing)
  - PySpark in `etl_aggregate_clean` configured with S3A connector to MinIO (`spark.hadoop.fs.s3a.endpoint`)
- **Catalog connected to storage**: `_catalog/metadata.json` stored in each bucket, read by `app/pages/data_catalog.py` Streamlit UI
- **Documentation covers install/config**: Storage (MinIO), batch tools (Airflow + PySpark), catalog tool (JSON + Streamlit browser)

**Gaps:** None.

---

### C20 - Manage the data catalog | FULL

**Evaluation**: E7
**Evidence Files:**
- `scripts/setup_minio.py` - `upload_initial_catalog()` with comprehensive catalog structure (lines 160-241)
- `airflow/dags/etl_datalake_ingest.py` - Automated catalog updates in bronze (`_lineage/`), silver (`_quality/`), and gold layers
- `app/pages/data_catalog.py` - Interactive data catalog browser UI (336 lines)
- `monitoring/grafana/provisioning/alerting/minio-alerts.yml` - 3 alert rules for MinIO monitoring (212 lines)
- `monitoring/grafana/dashboards/minio.json` - MinIO storage dashboard
- `mkdocs/docs/data-lake/catalog.md` - Catalog documentation with feed methods table

**What is covered:**
- **Feed method choices justified and appropriate per source**: 5 sources documented with methods and justifications in `mkdocs/docs/data-lake/catalog.md` (REST API pull, S3 download, web scraping, SQL export, DuckDB analytics)
- **Feed scripts run without errors**: All DAGs functional with error handling and fallbacks
- **Data correctly imported**: Bronze (raw JSON/Parquet), silver (cleaned Parquet + CSV + quality reports), gold (denormalized, quality reports, source comparison, ML features, daily snapshots)
- **Metadata integrated into catalog**: 
  - `_catalog/metadata.json` in each bucket with dataset descriptions, formats, lineage, consumers, governance, retention policies
  - Bronze `_lineage/` metadata: per-source file counts, sizes, row counts before processing
  - Bronze `_manifests/` metadata: ingestion date and file counts
  - Silver `_quality/` metadata: column-level completeness, null rates, cleaning decisions
  - Silver `_reports/` metadata: cleaning execution reports
  - Gold datasets include data quality report (per-column stats with outlier detection) and source comparison
- **Deletion procedures comply with constraints**: Lifecycle rules auto-delete bronze data after 90 days, backups after 30 days (configured in `setup_minio.py`). Manual deletion procedure documented.
- **Monitoring tracks material and application conditions**: 
  - `check_storage_health` task in backup DAG reports PostgreSQL schema sizes and MinIO bucket sizes
  - Grafana MinIO dashboard tracks object counts, bucket sizes, request rates
  - Prometheus scrapes MinIO metrics at `/minio/v2/metrics/cluster`
- **Monitoring generates alerts on service disruption**: 3 Grafana alert rules provisioned in `minio-alerts.yml`:
  1. Storage usage >80% (WARNING, 5min threshold)
  2. Service down (CRITICAL, 1min threshold)
  3. Object count anomaly >20% drop (WARNING, 5min threshold)
  - Contact point: email to `admin@nutritrack.local` via MailHog
- **Interactive catalog browser**: `app/pages/data_catalog.py` Streamlit page with:
  - MinIO connection with bucket listing
  - Per-bucket tabs showing object count and total size
  - Dataset search/filter functionality
  - Dataset detail views (description, format, schema, lineage, quality, consumers)
  - Governance section (RGPD compliance, retention policy, access groups)
  - Data lineage overview section
- **RGPD**: No personal data in data lake documented; registry references maintained in `_catalog/metadata.json` governance section

**Gaps:** None. All previously identified gaps (catalog interactivity, monitoring alerts) have been addressed with the Streamlit data catalog browser UI and Grafana MinIO alert rules.

---

### C21 - Implement data governance rules | FULL

**Evaluation**: E7
**Evidence Files:**
- `sql/init/00_init_databases.sql` - 7 PostgreSQL roles with differentiated grants (61 lines)
- `sql/init/01_schema_operational.sql` - App schema grants (lines 257-278)
- `sql/init/02_schema_warehouse.sql` - DW schema grants (lines 339-359)
- `sql/init/03_schema_datamarts_analytics.sql` - Datamart grants (lines 186-193)
- `scripts/setup_minio.py` - MinIO group policies (4 groups, lines 34-52)
- `api/auth/jwt.py` - API role-based access with `require_role()` factory (lines 63-74)
- `api/routers/analytics.py` - Role-restricted analytics endpoint (analyst/admin only)
- `api/routers/nutritionist.py` - Role-restricted nutritionist endpoint
- `superset/superset-init.sh` - Superset RBAC role creation
- `mkdocs/docs/data-lake/governance.md` - Governance documentation with architecture diagrams

**What is covered:**
- **Rights applied to groups (not individuals) when possible**: 
  - PostgreSQL: `app_readonly` (NOLOGIN group), `nutritionist_role` (NOLOGIN group), `admin_role` (NOLOGIN group), `etl_service` (login role for service accounts)
  - MinIO: 4 group policies (app_users, nutritionists, admins, etl_service) with bucket-level permissions
  - API: 3 roles (user, nutritionist, admin) enforced via JWT claims
  - Superset: RBAC roles (Admin, Alpha, Analyst, Nutritionist)
- **Access meets group needs**: 
  - app_readonly: SELECT on products/categories/brands only (read-only browsing)
  - nutritionist_role: SELECT on all app tables EXCEPT users (no PII access), SELECT on DW analytical views
  - admin_role: ALL PRIVILEGES on all tables
  - etl_service: SELECT + INSERT + UPDATE (no DELETE) for data loading
  - superset: SELECT on dw schema only (read-only analytics)
- **Access limited to necessary resources**: Principle of least privilege enforced throughout:
  - `REVOKE SELECT ON app.users FROM nutritionist_role` (explicit deny of PII access)
  - app_readonly has no access to warehouse
  - Superset has SELECT only on dw schema, not app schema
  - MinIO gold bucket is public read (for app users), but bronze/silver require authentication
- **Access RGPD-compliant**: No personal data in data lake; pseudonymization in warehouse (SHA-256 hashed user_id); consent tracking; retention periods enforced
- **Documentation covers access groups, associated rights, and update procedures**: 
  - `mkdocs/docs/data-lake/governance.md` contains complete access control architecture diagram (PostgreSQL + API + MinIO + Superset), role/permission tables, RGPD compliance diagram, personal data registry table, automated cleanup documentation
  - `scripts/setup_minio.py` contains `GROUP_POLICIES` dict with descriptions and bucket permissions
  - SQL files contain inline comments mapping grants to C21

**Gaps:** None. MinIO IAM policy enforcement is documented and coded. The `gold` bucket public read policy is applied via `minio-init` and `setup_minio.py`. Group-based access is consistently implemented across all 4 layers (PostgreSQL, MinIO, FastAPI, Superset).

---

## Cross-Cutting Concerns

### CI/CD Pipelines
- **Status**: PRESENT (4 GitHub Actions workflows)
- `/.github/workflows/lint.yml` - Python (ruff) and SQL (sqlfluff) linting on push/PR to main
- `/.github/workflows/test.yml` - Python tests with pytest on push/PR to main
- `/.github/workflows/docker.yml` - Docker build verification for all 4 images (API, App, Airflow, Superset)
- `/.github/workflows/deploy-docs.yml` - Documentation deployment
- **Impact**: While CI/CD is not a certification competency (C1-C21), it demonstrates professional engineering practices and strengthens the overall project quality.

### Tests
- **Status**: PRESENT (3 test files)
- `tests/test_sql_schemas.py` - 14 tests validating SQL schema structure (tables, constraints, grants, SCD fields)
- `tests/test_api_schemas.py` - 8 tests validating Pydantic request/response models
- `tests/test_etl_functions.py` - ETL function tests
- **Impact**: Supports C14 test procedure requirement. Tests run in CI via GitHub Actions.

### Monitoring Stack
- **Status**: FULL
- **Components**: Prometheus (6 scrape targets), Grafana (6 dashboards, auto-provisioned), StatsD exporter (Airflow metrics), postgres-exporter, cAdvisor, node-exporter, MinIO metrics
- **Alerting**: Grafana alert rules for MinIO (3 rules) + Airflow email alerts via MailHog (SMTP)
- **SLA Dashboard**: Dedicated `sla-compliance.json` with 10 panels tracking 5 SLIs

### Documentation Quality
- **Status**: EXCELLENT
- `docs/rapport_final.md` - Comprehensive final report covering all 21 competencies
- `docs/rapport_final.tex` - LaTeX version of the final report
- `docs/technical_stack_choices.md` - 14-section technology justification document
- `docs/veille_technologique.md` - Technical monitoring newsletter
- `docs/analytics_dashboard.md` - Dashboard documentation
- `docs/dw_vs_datalake_justification.md` - Architecture decision documentation
- `docs/defense_slides.tex` and `docs/final_deck.tex` - Defense presentation slides
- `docs/speaker_notes.md` and `docs/presenter_en_francais.md` - Presentation aids
- `mkdocs/` - Full MkDocs documentation site with 12 pages (architecture, data warehouse, data lake, API, monitoring, certification)
- `README.md` - Project overview

### Data Artifacts
- **Actual data present**: Raw API extractions (10 JSON files spanning March-April 2026), Parquet exports, scraping results, cleaned output (Parquet + CSV), cleaning reports, 18 backup files spanning April 2-8 2026
- **Impact**: Demonstrates the system has been running in production, not just theoretically designed

---

## Priority Actions Before Defense

### Important (strengthen the defense)
1. **C4 - Second monitoring bulletin**: Create one additional brief monitoring newsletter for a different time period to demonstrate regular ongoing monitoring practice. A half-page update covering a recent tool or regulation change would suffice.
2. **C6 - Populated indicators**: During the live demo, ensure `etl_activity_log` and `extraction_log` tables show entries spanning multiple dates. Run the ETL pipeline at least once before the demo to generate fresh entries.

### Nice-to-have (polish for defense)
3. **C3 - Accessibility references**: Add a brief mention of WCAG 2.1 compliance considerations in the accessibility section of the technical architecture study.
4. **Demo rehearsal**: Practice the full demo flow including: login to Streamlit -> search products -> log meal -> view dashboard -> show Airflow DAGs -> show Grafana SLA dashboard -> show MinIO data catalog browser -> demonstrate API docs -> show SCD history query.

---

## Evaluation-Level Readiness

| Evaluation | Competencies | Status | Notes |
|-----------|-------------|--------|-------|
| **E1** | C1 | READY | Interview grids complete |
| **E2** | C1, C2, C3, C4, C6 | MOSTLY READY | C4 needs second monitoring bulletin; C6 minor gap on populated indicators |
| **E3** | C5, C6, C7 | READY | Planning, tracking, communication all documented |
| **E4** | C8, C9, C10, C11, C12 | READY | All 5 extraction sources, SQL queries, aggregation, DB, API complete |
| **E5** | C13, C14, C15 | READY | Star schema, DW implementation, ETL all fully evidenced |
| **E6** | C16, C17 | READY | Alerting, SLA, backups, ITIL, SCD all fully evidenced |
| **E7** | C18, C19, C20, C21 | READY | Architecture, infrastructure, catalog, governance all fully evidenced |

---

## Competency Coverage Matrix

| Competency | Block | Evaluation | Status | Key Evidence |
|-----------|-------|-----------|--------|-------------|
| C1 | 1 | E1, E2 | FULL | Interview grids, synthesis note, SMART objectives |
| C2 | 1 | E2 | FULL | 4-part data topography, business glossary, flux matrix |
| C3 | 1 | E2 | FULL | Technical architecture, docker-compose (17 services), RGPD, eco-responsibility |
| C4 | 1 | E2 | PARTIAL | Monitoring newsletter exists; needs second bulletin for regularity evidence |
| C5 | 1 | E3 | FULL | Roadmap, calendar, effort weighting, rituals |
| C6 | 1 | E2, E3 | PARTIAL | Tracking tools configured; need populated indicator evidence in demo |
| C7 | 1 | E3 | FULL | Communication strategy, multiple adapted supports, defense slides |
| C8 | 2 | E4 | FULL | 5 extraction types: REST API, data file, scraping, database, big data (DuckDB) |
| C9 | 2 | E4 | FULL | 12+ SQL queries, full-text search, window functions, CTEs, EXPLAIN notes |
| C10 | 2 | E4 | FULL | PySpark + pandas pipelines, 7 cleaning rules, quality validation, reports |
| C11 | 2 | E4 | FULL | MPD with 8+ tables, RGPD registry (7 entries), consent tracking, automated cleanup |
| C12 | 2 | E4 | FULL | FastAPI with OpenAPI, 13+ endpoints, JWT auth, 3 roles, Pydantic validation |
| C13 | 3 | E5 | FULL | Star schema (7 dims, 2 facts, 6 datamarts), bottom-up approach justified |
| C14 | 3 | E5 | FULL | Functional DW, Superset RBAC, automated tests, tech stack feedback |
| C15 | 3 | E5 | FULL | 6 DAGs, PySpark, ExternalTaskSensors, SCD in ETL, quality checks |
| C16 | 3 | E6 | FULL | Activity log (3 categories), MailHog SMTP, SLA dashboard (5 SLIs), backups, ITIL |
| C17 | 3 | E6 | FULL | SCD Types 1/2/3 implemented, integrated in ETL, history views, documentation |
| C18 | 4 | E7 | FULL | MinIO medallion architecture, V/V/V addressed, catalog comparison (3 tools) |
| C19 | 4 | E7 | FULL | Docker installation, MinIO + Airflow + PySpark functional, catalog connected |
| C20 | 4 | E7 | FULL | Catalog browser UI, quality metadata, lineage metadata, 3 Grafana alert rules |
| C21 | 4 | E7 | FULL | Group-based access (4 layers), least privilege, RGPD compliant, documented |

---

*End of Audit Report*
