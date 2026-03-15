# NutriTrack Certification Audit Report

**Certification**: Expert en infrastructures de donnees massives (Data Engineer) - RNCP37638 - Level 7
**Audit Date**: 2026-03-14
**Auditor**: cert-auditor (automated codebase analysis)
**Scope**: All 21 competencies (C1-C21) across 4 blocks, 7 evaluations (E1-E7)

---

## Audit Summary

| Status | Count | Competencies |
|--------|-------|-------------|
| **FULL** | 17 | C1, C2, C3, C5, C7, C8, C9, C10, C11, C12, C13, C14, C15, C17, C18, C19, C21 |
| **PARTIAL** | 4 | C4, C6, C16, C20 |
| **MISSING** | 0 | - |

**Overall Assessment**: The project provides strong coverage across all 21 competencies. 17 are fully evidenced in code and documentation. 4 have minor gaps that should be addressed before the defense. No competency is entirely missing.

---

## Block 1: Piloter la conduite d'un projet data

### C1 - Analyze a data project need expression | FULL

**Evidence Files:**
- `docs/rapport_final.md` Ch.1 (lines 98-156) - Interview grids for data producers and consumers
- `docs/rapport_final.md` Ch.2.1 (lines 159-248) - Synthesis note with need analysis

**What's covered:**
- Interview grid for data producers (10 questions covering business activities, metadata, access, storage, treatments)
- Interview grid for data consumers (10 questions covering usage, granularity, delivery, RGPD)
- Synthesis note with: need analysis, functional scope, available means, feasibility, data governance
- SMART objectives (lines 148-153)
- Pre-project with macro technical recommendations, RGPD compliance actions
- RICE analysis context in the synthesis note

**Gaps:** None significant.

---

### C2 - Map available data (data topography) | FULL

**Evidence Files:**
- `docs/rapport_final.md` Ch.2.1 (lines 163-248) - Complete data topography in 4 parts

**What's covered:**
- **Semantics/Metadata**: Business glossary with 9 business objects (Product, Brand, Category, User, Meal, etc.) - lines 169-179
- **Data Models**: Structured (PostgreSQL), Semi-structured (JSON), Unstructured (Parquet) - lines 182-188
- **Treatments & Data Flows**: Flux matrix with 8 source-to-target flows including format, treatment script, and frequency - lines 192-204; data flow diagram (lines 207-237)
- **Access & Usage Conditions**: Role-based access matrix for operational DB, warehouse, and data lake - lines 241-248

**Gaps:** None.

---

### C3 - Design a technical data exploitation framework | FULL

**Evidence Files:**
- `docs/rapport_final.md` Ch.2.2 (lines 249-397) - Complete technical architecture study
- `docker-compose.yml` - 15 services defined, fully functional
- `sql/init/*.sql` - Physical data models

**What's covered:**
- Functional analysis: system capabilities + business constraints (lines 253-265)
- Non-functional needs: performance, scalability, reliability, security, availability table (lines 267-276)
- Functional representation: flux matrix (Ch.2.1.3)
- Applicative representation: Docker Compose service diagram with ports (lines 283-313); service interaction matrix present in architecture
- Infrastructure representation: technology stack table with versions (lines 316-330)
- Operational representation: ETL schedules, DAG dependencies
- Architecture decisions: 7 documented decisions with rationale (lines 332-341)
- RGPD compliance processes: personal data registry table, sorting/deletion procedures (lines 343-357)
- Eco-responsibility strategy following RGESN framework: 5 practices documented (lines 358-366)
- Flux matrix present in the applicative representation
- Accessibility: mentioned in interview grids (consumer Q9); Streamlit frontend provides accessible UI

**Gaps:** None significant. Accessibility accommodations could be more explicitly documented with WCAG references.

---

### C4 - Conduct technical and regulatory monitoring | PARTIAL

**Evidence Files:**
- `docs/rapport_final.md` Ch.2.3 (lines 368-384) - Monitoring section

**What's covered:**
- Monitoring theme: Apache Airflow ETL monitoring (relevant tool used in project)
- Monitoring schedule: "Minimum 1 hour per week" documented
- Aggregation tools: Airflow Web UI, extraction_log table, cleaning report
- Source reliability criteria: OFF API (community), EU Reg 1169/2011 (official), ANSES (peer-reviewed)
- DAG failure alerts via email

**Gaps:**
- **No formal newsletter/bulletin**: The certification requires a "technical monitoring newsletter/bulletin" (veille). The rapport mentions monitoring but does not include an actual sample newsletter or bulletin document showing regular monitoring output. This is a written deliverable for E2.
- **Accessibility-compliant communications**: Not explicitly demonstrated for monitoring outputs.

**Recommendation:** Add a sample technical monitoring bulletin (e.g., 1-page document on Airflow 2.8 features, OFF API changes, or RGPD regulation updates) to `docs/`. This is a quick fix.

---

### C5 - Plan data project execution | FULL

**Evidence Files:**
- `docs/rapport_final.md` Ch.3 (lines 401-481) - Complete project planning

**What's covered:**
- Team composition with required skills (5 roles) - lines 406-413
- Budget allocation context (Docker Compose = minimal infrastructure cost)
- Roadmap broken into 6 phases with durations and deliverables - lines 415-424
- Production calendar with 12 weeks, tasks, deliverables, resources, and effort weighting (story points) - lines 427-442
- Effort weighting method: Fibonacci story points (poker planning equivalent) - line 443
- Tracking tool: Git, Airflow UI, Makefile - lines 449-453
- Rituals: sprint planning, daily standup, sprint review, retrospective - lines 455-459
- Risk evaluation is implicit in the trade-offs section

**Gaps:** None significant. Risk evaluation per stage could be more explicit.

---

### C6 - Supervise data project execution | PARTIAL

**Evidence Files:**
- `docs/rapport_final.md` Ch.2.4 (lines 386-398) - Project supervision
- `docs/rapport_final.md` Ch.3.4 (lines 445-459) - Tracking method
- `Makefile` - Standardized commands
- Airflow DAGs - Execution monitoring

**What's covered:**
- Exchange facilitation: Makefile for standardized commands
- Tracking tools configured: Airflow UI, extraction_log table
- Rituals documented: sprint planning, standup, review, retrospective
- Indicators: records extracted/loaded/rejected, completeness %, DAG success rate

**Gaps:**
- **Indicators not demonstrably updated throughout the project**: The certification requires indicators to be "updated throughout project" with evidence of ongoing tracking. The extraction_log table exists in the schema but there's no evidence of populated data showing ongoing updates over time. A screenshot or sample data showing historical entries would strengthen this.
- **Tracking tool accessibility**: The Airflow UI is functional but there's no evidence of configured access for non-technical stakeholders.

**Recommendation:** Minor. Ensure the live demo shows populated `extraction_log` entries and Airflow DAG run history spanning multiple dates.

---

### C7 - Communicate throughout the data project | FULL

**Evidence Files:**
- `docs/rapport_final.md` Ch.3.5 (lines 461-481) - Communication strategy
- `api/main.py` - OpenAPI documentation configuration
- `app/streamlit_app.py` - User-facing frontend

**What's covered:**
- All communication steps planned: sprint kickoff, progress updates, demos, API docs, user docs, final delivery (table at lines 463-470)
- Accessible supports: Swagger UI, Streamlit app
- Adapted content per audience: technical (Swagger), business (Streamlit), jury (report + slides)
- Chosen orientations and trade-offs communicated (lines 472-476)
- User documentation tasks planned and distributed (line 478)
- End-user onboarding planned in Phase 6 (line 478)
- Feedback collection: post-demo questionnaire (line 480)

**Gaps:** None.

---

## Block 2: Realiser la collecte, le stockage et la mise a disposition des donnees

### C8 - Automate data extraction scripts | FULL

**Evidence Files:**
- `scripts/extract_off_api.py` - REST API extraction (215 lines)
- `scripts/extract_off_parquet.py` - Data file + Big data extraction
- `scripts/extract_scraping.py` - Web scraping (287 lines)
- `scripts/extract_from_db.py` - Database extraction
- `scripts/extract_duckdb.py` - Big data system (DuckDB)
- `airflow/dags/etl_extract_off_api.py` - DAG for API extraction
- `airflow/dags/etl_extract_parquet.py` - DAG for Parquet extraction
- `airflow/dags/etl_extract_scraping.py` - DAG for scraping
- `docs/rapport_final.md` Ch.4 (lines 488-674) - Full documentation

**What's covered:**
- **REST API**: Open Food Facts search API with pagination, rate limiting, User-Agent
- **Data file**: Parquet export via DuckDB (3M+ products)
- **Scraping**: ANSES/EFSA websites with BeautifulSoup, fallback RDA values
- **Database**: PostgreSQL extraction with SQLAlchemy
- **Big data system**: DuckDB analytical queries on large Parquet files
- All scripts have: entry point (`main()`), dependency initialization, external connections, logic rules, error handling (`try/except`), result saving
- All versioned on Git

**Gaps:** None. All 5 required source types are covered (API, data file, scraping, database, big data).

---

### C9 - Develop SQL extraction queries | FULL

**Evidence Files:**
- `sql/queries/analytical_queries.sql` - 7 documented queries (226 lines)
- `docs/rapport_final.md` Ch.5 (lines 677-783) - Query documentation

**What's covered:**
- 7 functional queries with increasing complexity
- Full-text search with GIN index (`ts_rank`, `plainto_tsquery`)
- Window functions: `ROW_NUMBER()`, `AVG() OVER (ROWS BETWEEN)`, `LAG()`
- CTEs for code organization
- EXPLAIN ANALYZE notes documenting optimization choices
- Selection/filtering/join choices documented per query
- Query optimizations: composite indexes, aggregate pushdown, partial indexes
- Both operational (app schema) and analytical (dw schema) queries

**Gaps:** None.

---

### C10 - Develop data aggregation rules | FULL

**Evidence Files:**
- `scripts/aggregate_clean.py` - Standalone aggregation script
- `airflow/dags/etl_aggregate_clean.py` - DAG version (267 lines)
- `data/cleaned/products_cleaned.parquet` - Output dataset
- `data/cleaned/cleaning_report.json` - Cleaning report
- `docs/rapport_final.md` Ch.6 (lines 785-800+) - Documentation

**What's covered:**
- Multi-source aggregation: API JSON + Parquet + DuckDB + DB export merged with `pd.concat()`
- Column standardization: 30+ column name mappings
- Barcode cleaning: strip non-numeric, validate length 8-14
- Null product name removal
- Numeric range validation (capped at physiological max per 100g)
- Nutri-Score normalization (uppercase A-E)
- Deduplication by barcode (keep most complete)
- Output: single clean Parquet + CSV dataset
- Script versioned on Git with documented dependencies

**Gaps:** None.

---

### C11 - Create a RGPD-compliant database | FULL

**Evidence Files:**
- `sql/init/01_schema_operational.sql` - Physical data model (279 lines)
- `sql/init/00_init_databases.sql` - Database initialization with roles
- `scripts/import_to_db.py` - Import script
- `docs/rapport_final.md` Ch.7 - Database modeling and RGPD

**What's covered:**
- **Physical model (MPD)**: 8 tables with constraints, indexes, foreign keys
- **MERISE models**: MCD/MLD/MPD documented in rapport_final.md Ch.7
- **DB choice justified**: PostgreSQL 16 for both OLTP/OLAP, justified in architecture decisions
- **Reproducible installation**: Docker Compose with init scripts in `/docker-entrypoint-initdb.d/`
- **Import script**: `import_to_db.py` functional with batch upsert, ON CONFLICT handling
- **RGPD compliance**:
  - Personal data registry: `app.rgpd_data_registry` table with 4 entries (legal basis, retention, security measures)
  - Consent tracking: `consent_data_processing`, `consent_date`, `data_retention_until` columns
  - Automated cleanup: `rgpd_cleanup_expired_data()` function (deletes meals >2 years, deactivates users past retention)
  - Password hashing with bcrypt
  - UUID-based user identification

**Gaps:** None.

---

### C12 - Share the dataset via REST API | FULL

**Evidence Files:**
- `api/main.py` - FastAPI application (62 lines)
- `api/routers/products.py` - Product endpoints (133 lines)
- `api/routers/meals.py` - Meal endpoints (222 lines)
- `api/routers/auth.py` - Auth endpoints (76 lines)
- `api/auth/jwt.py` - JWT authentication (76 lines)
- `api/schemas/` - Pydantic schemas for validation

**What's covered:**
- **REST API documentation**: Auto-generated OpenAPI 3.0 at `/docs` (Swagger), `/redoc`, `/api/v1/openapi.json`
- **All endpoints documented**: Products (search, get by barcode, alternatives), Meals (create, list, daily summary, weekly trends), Auth (register, login, profile)
- **Auth/authz rules**:
  - JWT Bearer token authentication
  - Role-based access control (user, nutritionist, admin)
  - `require_role()` decorator for endpoint protection
  - Password hashing with bcrypt
- **API is functional**: Endpoints return proper HTTP responses with Pydantic validation
- **Restricted access**: All product/meal endpoints require authentication
- **Data retrieval**: GET endpoints for product search, alternatives, daily summaries

**Gaps:** None.

---

## Block 3: Elaborer et maintenir un entrepot de donnees

### C13 - Model data warehouse structure | FULL

**Evidence Files:**
- `sql/init/02_schema_warehouse.sql` - Star schema (360 lines)
- `sql/init/03_schema_datamarts_analytics.sql` - Datamarts (193 lines)
- `docs/rapport_final.md` Ch.9 (lines 1096-1186) - Star schema documentation

**What's covered:**
- **Data needed for analyses**: Listed exhaustively in table (5 analysis types) - lines 1101-1108
- **Logical and physical models**: Star schema diagram with all dimensions and facts (lines 1118-1166)
- **DW practices**: Star schema with 7 dimensions and 2 fact tables
- **Dimension tables**: dim_time, dim_product, dim_brand, dim_category, dim_country, dim_user, dim_nutriscore
- **Fact tables**: fact_daily_nutrition, fact_product_market
- **6 datamart views**: dm_user_daily_nutrition, dm_product_market_by_category, dm_brand_quality_ranking, dm_nutriscore_distribution, dm_nutrition_trends, dm_dw_health
- **Bottom-up approach justified**: 4 reasons documented (lines 1112-1116)
- No interpretation errors in the model

**Gaps:** None.

---

### C14 - Create a data warehouse | FULL

**Evidence Files:**
- `sql/init/02_schema_warehouse.sql` - DW schema creation
- `docker-compose.yml` - PostgreSQL + Airflow configuration
- `superset/superset-init.sh` - Superset RBAC configuration
- `superset/bootstrap_dashboards.py` - Dashboard creation
- `docs/rapport_final.md` Ch.10 (lines 1189-1313) - DW implementation

**What's covered:**
- **DW is functional**: Schema created automatically via Docker init scripts
- **Main configurations explained**: Schema isolation, indexes, pre-populated dim_time (lines 1199-1203)
- **Source data access**: Configured via environment variables in Docker Compose (lines 1206-1231)
- **Analyst access**: 6 datamart views with role-based GRANT statements; Superset connected with read-only access; RBAC roles (Analyst, Nutritionist) configured in Superset
- **Test procedure**: 7 test categories covering schema creation, dimension population, SCD, fact loading, views, access control (lines 1294-1303)
- **Technical documentation**: Architecture + install/config procedure in Docker Compose and docs
- **Tech stack feedback**: 4-entry table covering coherence, advantages, difficulties (lines 1307-1312)

**Gaps:** None.

---

### C15 - Integrate ETLs for data warehouse | FULL

**Evidence Files:**
- `airflow/dags/etl_load_warehouse.py` - Warehouse ETL (310 lines)
- `airflow/dags/etl_aggregate_clean.py` - Cleaning ETL (267 lines)
- `airflow/dags/etl_datalake_ingest.py` - Data lake ETL (659 lines)
- `docs/rapport_final.md` Ch.11 (lines 1316-1467) - ETL documentation

**What's covered:**
- **Data formats and volumes**: Known and explained (table at lines 1335-1342)
- **ETLs fed with identified data**: 6 DAGs with clear source-to-target mappings
- **Output formats**: SQL tables + Parquet files
- **Schema-compliant treatments**: ETL respects star schema (dimensions before facts, FK integrity)
- **Cleaning treatments**: Format/unit uniformity (column standardization), duplicate detection (barcode dedup), range validation
- **ETL logic clearly explained**: Task dependency chain documented, SCD logic in dimension loading
- **ExternalTaskSensor**: Cross-DAG dependencies properly configured

**Gaps:** None.

---

### C16 - Manage the data warehouse (admin & supervision) | PARTIAL

**Evidence Files:**
- `sql/init/01_schema_operational.sql` lines 162-173 - `extraction_log` table
- `scripts/backup_database.py` - Backup script (154 lines)
- `airflow/dags/*.py` - `email_on_failure: True` in all DAG default_args
- `monitoring/` - Prometheus, Grafana, StatsD exporter configs
- `monitoring/grafana/dashboards/` - 5 Grafana dashboards (airflow.json, airflow-dags.json, postgresql.json, docker-system.json, minio.json)
- `docs/rapport_final.md` Ch.12 (lines 1470-1580) - Maintenance documentation

**What's covered:**
- **Activity logging**: `extraction_log` table with alert/error categories (running/completed/failed)
- **Alert system**: Airflow `email_on_failure: True` configured (email to `admin@nutritrack.local`)
- **Backup procedures**: `backup_database.py` with full/partial modes, MinIO upload, local cleanup
- **Documentation**: New source integration procedure (6 steps), new access creation (3 steps)
- **RGPD**: Registry maintained, cleanup function exists
- **Monitoring infrastructure**: Prometheus scraping 6 targets (postgres-exporter, cadvisor, node-exporter, minio, statsd-exporter, prometheus); StatsD mapping for 50+ Airflow metrics; 5 Grafana dashboards provisioned
- **Service indicators**: 5 SLI targets documented (ETL success >95%, freshness <24h, query <5s, backup 100%, completeness >80%)

**Gaps:**
- **SLA-based service indicators on a dashboard**: The SLI targets are documented in the report (Ch.12.4) but there is no dedicated **Superset or Grafana dashboard panel** specifically showing these SLA metrics in a live dashboard. The Grafana dashboards cover Airflow metrics, PostgreSQL stats, Docker containers, and MinIO, but none explicitly present "SLA compliance" panels (e.g., % ETL success over time, data freshness gauge).
- **Maintenance tasks prioritized and assigned**: The documentation describes maintenance procedures but doesn't show an actual task prioritization/assignment system (e.g., a ticketing/ITIL approach). This is a documentation-level gap.
- **Alert system functional verification**: The `email_on_failure` is configured but the SMTP server is not configured in `docker-compose.yml` (no `AIRFLOW__SMTP__*` environment variables), so email alerts would not actually send. This could be a problem during the live demo.

**Recommendation:**
1. Add SMTP configuration to Airflow (even a test setup with MailHog) or add a Slack/webhook notification callback to demonstrate working alerts.
2. Add an "SLA Dashboard" panel in Grafana showing ETL success rates, data freshness, and backup status.
3. Add a brief maintenance task prioritization section (even a simple priority matrix in documentation).

---

### C17 - Implement dimension variations (SCD) | FULL

**Evidence Files:**
- `sql/init/02_schema_warehouse.sql` - SCD Type 1/2/3 functions (lines 210-269)
- `sql/scd_procedures.sql` - Extended SCD procedures (140 lines)
- `airflow/dags/etl_load_warehouse.py` - SCD integrated into ETL
- `docs/rapport_final.md` Ch.13 (lines 1582-1745) - SCD documentation

**What's covered:**
- **SCD Type 1 (Overwrite)**: `scd_type1_update_brand()` + batch correction function; applied in `load_dim_brands` ETL task
- **SCD Type 2 (Historical)**: `scd_type2_update_product()` with effective_date/end_date/is_current; automated detection via `scd_type2_check_and_update_products()`; `v_product_history` view for querying history; applied in `load_dim_products` ETL task
- **SCD Type 3 (Add Column)**: `scd_type3_update_country()` with `previous_country_list` column in dim_country
- **Variation modeling fully integrates source data changes**: IS DISTINCT FROM logic in ETL for change detection
- **ETLs updated**: Warehouse ETL includes SCD processing in dimension loading tasks
- **Documentation updated**: Physical models updated with SCD fields (effective_date, end_date, is_current, last_updated, previous_country_list)

**Gaps:** None. All three SCD types are implemented, documented, and integrated into ETLs.

---

## Block 4: Encadrer la collecte massive et la mise a disposition des donnees avec un data lake

### C18 - Design data lake architecture | FULL

**Evidence Files:**
- `docker-compose.yml` - MinIO service configuration (lines 79-112)
- `airflow/dags/etl_datalake_ingest.py` - Medallion architecture DAG (659 lines)
- `scripts/setup_minio.py` - Data lake setup script (268 lines)
- `docs/rapport_final.md` Ch.14 (lines 1752-1827) - Architecture documentation

**What's covered:**
- **Technical proposals coherent with framework**: MinIO with S3 API compatibility documented
- **Architecture schema for V/V/V**: Medallion (bronze/silver/gold) addressing volume (3M+ products), variety (JSON/Parquet/CSV/SQL), velocity (daily/weekly schedules) - table at lines 1807-1811
- **Schema uses appropriate formalism**: ASCII art architecture diagram with clear layer separation
- **Catalog comparison**: 3-tool comparison table (Apache Atlas vs DataHub vs Custom JSON) with 7 criteria - lines 1815-1824
- **Selected catalog justified**: Custom JSON chosen for minimal overhead, MinIO integration, project-scale sufficiency

**Gaps:** None.

---

### C19 - Integrate data lake infrastructure components | FULL

**Evidence Files:**
- `docker-compose.yml` - MinIO, minio-init services (lines 79-112)
- `scripts/setup_minio.py` - Setup automation
- `airflow/dags/etl_datalake_ingest.py` - Batch + near-real-time tools
- `airflow/dags/etl_load_warehouse.py` - Batch processing
- `docs/rapport_final.md` Ch.15 (lines 1829-1941) - Infrastructure documentation

**What's covered:**
- **Installation procedure complete**: Docker Compose + Makefile commands documented
- **Installation runs without errors**: `docker compose up -d` starts all services with healthchecks
- **Storage system installed and functional**: MinIO with 4 buckets (bronze/silver/gold/backups)
- **Batch tool functional**: Airflow `etl_load_warehouse` DAG (star schema ETL)
- **Near-real-time tool functional**: Airflow `etl_datalake_ingest` DAG (medallion pipeline)
- **Catalog connected to storage**: `_catalog/metadata.json` stored in each MinIO bucket, updated by ETL
- **Documentation covers install/config**: Storage (MinIO), batch tools (Airflow), catalog tool - table at lines 1936-1940

**Gaps:** None.

---

### C20 - Manage the data catalog | PARTIAL

**Evidence Files:**
- `airflow/dags/etl_datalake_ingest.py` - `update_catalog_metadata()` function (lines 471-626)
- `scripts/setup_minio.py` - `upload_initial_catalog()` function (lines 140-219)
- `docs/rapport_final.md` Ch.16 (lines 1944-2060) - Catalog documentation

**What's covered:**
- **Feed method choices justified**: Table with 5 sources, methods, and justifications (lines 1950-1956)
- **Feed scripts run without errors**: All DAGs functional with error handling
- **Data correctly imported**: Bronze/silver/gold layers populated via ETL
- **Metadata integrated into catalog**: `_catalog/metadata.json` with dataset descriptions, formats, lineage, owners, consumers (lines 1982-2024)
- **Deletion procedures**: Lifecycle rules (90-day bronze, 30-day backups) + manual deletion procedure documented (lines 2029-2038)
- **Storage monitoring**: `check_storage_status()` shows object counts, sizes per bucket (lines 2045-2052)
- **RGPD**: No personal data in lake documented; registry reference

**Gaps:**
- **No dedicated catalog tool**: The project uses a custom JSON file (`_catalog/metadata.json`) rather than a dedicated data catalog tool (OpenMetadata, DataHub, etc.). While this was justified in the catalog comparison (C18), the evaluation criteria expect the catalog to be a **connected tool** with search/browse capabilities, not just a static JSON file. The JSON approach lacks:
  - Interactive search/browse interface for datasets
  - Automated metadata discovery (manual updates only)
  - Data lineage visualization
  - Data profiling integration
- **Monitoring generates alerts on service disruption**: The MinIO healthcheck exists in Docker Compose, but there's no explicit alert mechanism when the data lake storage service is disrupted. The Grafana MinIO dashboard exists but doesn't have alert rules configured.

**Recommendation:**
1. Consider adding a lightweight catalog UI. Even a simple script that reads `_catalog/metadata.json` and renders it as a searchable HTML page would improve the demo. Alternatively, demonstrate the catalog via MinIO Console's object browser + the JSON metadata.
2. Add Grafana alert rules for MinIO storage (disk space thresholds, service downtime) to demonstrate monitoring alerts.

---

### C21 - Implement data governance rules | FULL

**Evidence Files:**
- `sql/init/00_init_databases.sql` - PostgreSQL roles and grants (61 lines)
- `sql/init/01_schema_operational.sql` - App schema grants (lines 257-278)
- `sql/init/02_schema_warehouse.sql` - DW schema grants (lines 339-359)
- `scripts/setup_minio.py` - MinIO group policies (lines 35-52)
- `api/auth/jwt.py` - API role-based access (lines 66-75)
- `superset/superset-init.sh` - Superset RBAC roles
- `docs/rapport_final.md` Ch.17 (lines 2063-2171) - Governance documentation

**What's covered:**
- **Rights applied to groups**: PostgreSQL group roles (app_readonly, nutritionist_role, admin_role) - not individual users
- **Access meets group needs**: Differentiated access per role across DB, lake, and API
- **Access limited to necessary resources**: Principle of least privilege (e.g., nutritionist_role has REVOKE on app.users, app_readonly can only SELECT products)
- **Access RGPD-compliant**: No personal data in lake, pseudonymization in warehouse (SHA256), consent tracking
- **Documentation covers access groups**: Complete access matrix table (lines 2086-2092), MinIO policies (lines 2099-2118), API roles (lines 2142-2148), groups and rights summary table (lines 2163-2168)
- **Update procedures**: Documented how to add new groups (line 2170)

**Gaps:** None significant. The MinIO policies are documented and coded in `setup_minio.py` but the actual MinIO IAM policy attachment (via `mc admin policy`) is not explicitly scripted - only the `gold` bucket public read policy is applied. However, the documentation and code intent clearly demonstrate understanding of group-based governance.

---

## Cross-Cutting Concerns

### CI/CD Pipelines
- **Status**: MISSING (no `.github/workflows/` directory exists)
- **Impact**: Not a certification competency (C1-C21 don't require CI/CD), but mentioned in `CLAUDE.md` as a priority gap. Does not affect certification evaluation.

### Tests
- **Status**: MISSING (empty `tests/` directory)
- **Impact**: Tests are not explicitly required by any competency. The test procedure for C14 is documented in the report. However, having automated tests would strengthen the demo.

### Monitoring Stack
- **Status**: FULL infrastructure, PARTIAL alerting
- **Components present**: Prometheus, Grafana (5 dashboards), StatsD exporter, postgres-exporter, cadvisor, node-exporter, minio metrics
- **Gap**: No Grafana alerting rules configured; no functional SMTP for Airflow email alerts

### Documentation Quality
- **Status**: STRONG
- `docs/rapport_final.md` is 2,279 lines covering all 21 competencies with code snippets, diagrams, tables, and explanations
- All chapters map to specific evaluations and competencies
- Competency verification matrix provided (Ch.18.2)
- Live demo plan with 32-minute schedule (Ch.18.1)
- Lessons learned and trade-offs documented (Ch.19)

---

## Priority Actions Before Defense

### Critical (address before defense)
1. **C16 - SMTP/Alerting**: Configure Airflow SMTP or add a webhook-based alert (e.g., Slack callback) to demonstrate functional alerts during the live demo. Without this, the alert system claim cannot be verified.

### Important (strengthen the defense)
2. **C4 - Technical Monitoring Bulletin**: Create a 1-page sample monitoring newsletter in `docs/` showing technology watch results (e.g., Airflow 2.x release notes, OFF API changes, RGPD updates).
3. **C16 - SLA Dashboard**: Add 2-3 Grafana panels showing ETL success rate, data freshness, and backup status to make SLA monitoring demonstrable.
4. **C20 - Catalog Interactivity**: Prepare a demo script or simple UI that reads `_catalog/metadata.json` and shows it in a browsable format, or demonstrate catalog browsing via MinIO Console.

### Nice-to-have (polish for defense)
5. **C6 - Populated extraction_log**: Ensure the live demo shows populated `extraction_log` entries from actual pipeline runs.
6. **C20 - Monitoring alerts**: Add Grafana alert rules for MinIO storage metrics.

---

## Evaluation-Level Readiness

| Evaluation | Competencies | Status | Notes |
|-----------|-------------|--------|-------|
| **E1** | C1 | READY | Interview grids complete |
| **E2** | C1, C2, C3, C4, C6 | MOSTLY READY | C4 needs monitoring bulletin; C6 minor gap on indicator evidence |
| **E3** | C5, C6, C7 | READY | Planning, tracking, communication all documented |
| **E4** | C8, C9, C10, C11, C12 | READY | All 5 extraction sources, SQL queries, aggregation, DB, API complete |
| **E5** | C13, C14, C15 | READY | Star schema, DW implementation, ETL all fully evidenced |
| **E6** | C16, C17 | MOSTLY READY | C17 fully covered; C16 needs alerting fix and SLA dashboard |
| **E7** | C18, C19, C20, C21 | MOSTLY READY | C18, C19, C21 full; C20 catalog interactivity gap |

---

*End of Audit Report*
