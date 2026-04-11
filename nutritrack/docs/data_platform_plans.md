# Data Platform Implementation Plans

**Author**: data-platform engineer
**Date**: 2026-04-09
**Status**: PLANNING (blocked on CI/CD — Task #2)

This document contains detailed implementation plans for the three certification
gap-closing tasks assigned to the data-platform role: C16 alerting/SLA/maintenance,
C20 data catalog, and C21 data governance. Each section includes architecture
decisions with alternatives, estimated file changes, and justifications tied to
the official referential criteria.

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Task #3 — C16: DW Alerting, SLA, and Maintenance](#task-3--c16-dw-alerting-sla-and-maintenance)
3. [Task #4 — C20: Data Catalog (BIGGEST GAP)](#task-4--c20-data-catalog-biggest-gap)
4. [Task #5 — C21: Data Governance](#task-5--c21-data-governance)
5. [Cross-cutting Concerns](#cross-cutting-concerns)
6. [Implementation Order and Dependencies](#implementation-order-and-dependencies)

---

## Current State Assessment

### What already exists

| Area | Component | Status | Files |
|------|-----------|--------|-------|
| **Alerting** | Airflow callbacks (on_failure, on_success, on_retry, sla_miss) | Implemented | `airflow/plugins/alerting.py` |
| **Alerting** | MailHog SMTP for email alerts | Docker service running | `docker-compose.yml` (mailhog service) |
| **Alerting** | `etl_activity_log` table with category/event_type | Implemented | `sql/migrations/001_add_etl_activity_log.sql` |
| **Alerting** | MinIO Grafana alert rules (storage, downtime, object drop) | Implemented | `monitoring/grafana/provisioning/alerting/minio-alerts.yml` |
| **SLA** | SLA compliance dashboard | Implemented | `monitoring/grafana/dashboards/sla-compliance.json` |
| **SLA** | SLA timers on backup tasks | Implemented | `airflow/dags/etl_backup_maintenance.py` |
| **Backups** | Full + partial backup procedures | Implemented | `scripts/backup_database.py`, `airflow/dags/etl_backup_maintenance.py` |
| **Backups** | MinIO upload of backups | Implemented | `scripts/backup_database.py` |
| **RGPD** | Personal data registry in `app.rgpd_data_registry` | Implemented | `sql/init/01_schema_operational.sql` |
| **RGPD** | DW-specific RGPD entries | Implemented | `sql/migrations/001_add_etl_activity_log.sql` |
| **RGPD** | Auto-cleanup function | Implemented | `sql/init/01_schema_operational.sql` (rgpd_cleanup_expired_data) |
| **Catalog** | Static JSON metadata in MinIO buckets | Implemented | `airflow/dags/etl_datalake_ingest.py` (update_catalog_metadata) |
| **Catalog** | Data quality reports (silver layer) | Implemented | `airflow/dags/etl_datalake_ingest.py` (transform_to_silver) |
| **Catalog** | Bronze lineage metadata | Implemented | `airflow/dags/etl_datalake_ingest.py` (ingest_to_bronze) |
| **Governance** | PostgreSQL roles (app_readonly, nutritionist_role, admin_role, etl_service) | Implemented | `sql/init/00_init_databases.sql` |
| **Governance** | Schema-level GRANTs (app, dw) | Implemented | `sql/init/01_schema_operational.sql`, `02_schema_warehouse.sql` |
| **Governance** | REVOKE on users table from nutritionist_role | Implemented | `sql/init/01_schema_operational.sql` |
| **Monitoring** | Prometheus + Grafana + StatsD + cAdvisor + node-exporter + postgres-exporter | All running | `docker-compose.yml`, `monitoring/` |

### Identified gaps per certification requirement

**C16 gaps:**
- `etl_backup_maintenance.py` uses `ALERTING_DEFAULT_ARGS` but other DAGs do NOT (etl_aggregate_clean, etl_load_warehouse, etl_extract_parquet, etl_extract_off_api, etl_extract_scraping) — they use plain `default_args` without callbacks
- No SLA timers on ETL DAGs other than backup
- No Grafana alert rules for Airflow ETL failures (only MinIO alerts exist)
- Missing: maintenance task prioritization and assignment methodology
- Missing: SLA-based service indicators referencing contractual targets
- Missing: documentation for new source integration and new access creation procedures

**C20 gaps:**
- Catalog is a static JSON blob in MinIO — not an interactive, searchable catalog
- No catalog UI or API endpoint for browsing datasets
- Metadata is generated once per DAG run but not queryable
- No feed scripts per source that run independently
- No deletion/lifecycle procedures integrated into catalog management
- Monitoring generates alerts for MinIO but not for catalog staleness

**C21 gaps:**
- Roles exist but no documentation of access groups, associated rights, and update procedures
- MinIO bucket policies are not group-based (current: anonymous download on gold, admin on everything else)
- No formal access request/update workflow documented
- Missing: explicit group-to-right mapping for MinIO objects

---

## Task #3 -- C16: DW Alerting, SLA, and Maintenance

### Referential requirements (p.20-22)

1. Activity logging with alert/error categories
2. Alert system (email/sms/notification) on errors
3. Maintenance tasks prioritized and assigned
4. SLA-based service indicators on dashboard
5. Scheduled full/partial backups functional
6. Documentation: new source integration, new access creation, storage space, datamarts, compute capacity
7. New sources correctly configured + ETLs updated
8. New accesses configured
9. RGPD personal data registry and sorting procedures

### Gap analysis summary

Items 1, 2, 5, 9 are already substantially covered. The gaps are:

- **Gap A**: Not all DAGs use the alerting callbacks
- **Gap B**: No SLA timers on non-backup DAGs
- **Gap C**: No Grafana Airflow-specific alert rules (only MinIO alerts)
- **Gap D**: No documented maintenance prioritization methodology
- **Gap E**: Missing operational documentation procedures

### Implementation plan

#### Gap A: Propagate alerting callbacks to all DAGs

**Decision: Centralized import vs. per-DAG copy-paste**

| Option | Pros | Cons |
|--------|------|------|
| **A1: Import from alerting.py plugin** (RECOMMENDED) | Single source of truth, DRY, already works for etl_backup_maintenance | Requires each DAG to import from plugin |
| A2: Airflow variable/connection-based config | More dynamic | Over-engineered for 6 DAGs |

**Action**: Update the `default_args` in the following DAGs to use `ALERTING_DEFAULT_ARGS`:
- `etl_aggregate_clean.py` — replace plain default_args
- `etl_load_warehouse.py` — replace plain default_args
- `etl_extract_parquet.py` — replace plain default_args
- `etl_extract_off_api.py` — replace plain default_args
- `etl_extract_scraping.py` — replace plain default_args

Also add `sla_miss_callback=sla_miss_callback` to each DAG definition.

**Estimated file changes**: 5 files (one import line + default_args replacement + sla_miss_callback per file)

#### Gap B: Add SLA timers to ETL tasks

Add `sla=timedelta(...)` to each PythonOperator in all DAGs:

| DAG | Task | Proposed SLA |
|-----|------|--------------|
| etl_extract_parquet | extract_from_parquet | 45 min |
| etl_extract_parquet | run_analytics | 15 min |
| etl_extract_off_api | extract_from_api | 30 min |
| etl_extract_scraping | scrape_guidelines | 20 min |
| etl_aggregate_clean | aggregate_all_sources | 15 min |
| etl_aggregate_clean | clean_data | 30 min |
| etl_aggregate_clean | validate_data_quality | 10 min |
| etl_aggregate_clean | load_to_database | 20 min |
| etl_load_warehouse | load_dim_* (each) | 15 min |
| etl_load_warehouse | load_fact_* (each) | 30 min |
| etl_datalake_ingest | ingest_to_bronze | 15 min |
| etl_datalake_ingest | transform_to_silver | 20 min |
| etl_datalake_ingest | publish_to_gold | 30 min |
| etl_datalake_ingest | update_catalog_metadata | 5 min |

**Estimated file changes**: 5 DAG files (add sla= parameter to each operator)

#### Gap C: Add Grafana alert rules for Airflow ETL

**Decision: Provisioned YAML vs. dashboard-embedded alerts**

| Option | Pros | Cons |
|--------|------|------|
| **C1: Provisioned YAML file** (RECOMMENDED) | Version-controlled, reproducible, consistent with existing minio-alerts.yml | Requires Prometheus metrics from Airflow StatsD |
| C2: Dashboard-embedded alerts | Easier to set up initially | Not version-controlled, lost on Grafana reset |

**Action**: Create `monitoring/grafana/provisioning/alerting/airflow-alerts.yml` with:

1. **ETL DAG failure rate** — alert when `airflow_dagrun_failed` count > 0 in last 15 min
2. **DAG duration anomaly** — alert when DAG run duration exceeds 2x historical average
3. **Task queue depth** — alert when Celery queue depth > 10 tasks for > 5 min
4. **Scheduler heartbeat** — alert when scheduler is down (no heartbeat metric for > 2 min)

All alerts route to the existing `nutritrack-email` contact point.

**Estimated file changes**: 1 new file (`monitoring/grafana/provisioning/alerting/airflow-alerts.yml`)

#### Gap D: Maintenance prioritization methodology

**Decision: ITIL-lite vs. custom priority matrix**

| Option | Pros | Cons |
|--------|------|------|
| **D1: Severity-based priority matrix using existing alert_category** (RECOMMENDED) | Maps directly to existing CRITICAL/WARNING/INFO categories | Simple, may not cover all ITIL scenarios |
| D2: Full ITIL service desk with ticketing | More comprehensive | Overkill for a certification project |

**Action**: Add a SQL migration that creates an `app.maintenance_tasks` table:

```
maintenance_tasks (
    task_id SERIAL PK,
    alert_log_id INTEGER FK -> etl_activity_log,
    priority VARCHAR(10) CHECK IN ('P1','P2','P3','P4'),
    status VARCHAR(20) CHECK IN ('open','in_progress','resolved','deferred'),
    assigned_to VARCHAR(100),
    title VARCHAR(500),
    description TEXT,
    resolution TEXT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    sla_target INTERVAL
)
```

Priority mapping:
- **P1 (Critical)**: Data loss, service down, backup failure -> resolve within 1 hour
- **P2 (High)**: ETL failure, SLA miss -> resolve within 4 hours
- **P3 (Medium)**: Data quality degradation, warning alerts -> resolve within 24 hours
- **P4 (Low)**: Optimization, cleanup tasks -> resolve within 1 week

**Estimated file changes**: 1 new migration file, documentation in mkdocs

#### Gap E: Operational documentation procedures

Add to mkdocs or a dedicated procedures file:
1. New source integration procedure (step-by-step)
2. New access creation procedure
3. Storage capacity management
4. Datamart creation procedure
5. Compute capacity scaling

**Estimated file changes**: 1-2 documentation files in `mkdocs/docs/monitoring/`

### Total estimated changes for Task #3

| Type | Count |
|------|-------|
| Modified DAG files | 5 |
| New alerting YAML | 1 |
| New SQL migration | 1 |
| New/updated documentation | 2 |
| **Total files** | **9** |

---

## Task #4 -- C20: Data Catalog (BIGGEST GAP)

### Referential requirements (p.24-25)

1. Feed method choices justified and appropriate per source
2. Feed scripts run without errors
3. Data correctly imported
4. Metadata integrated into catalog
5. Deletion procedures comply with access/regulatory/operational constraints
6. Monitoring tracks material and application conditions
7. Monitoring generates alerts on service disruption
8. RGPD registry and sorting procedures

### Architecture Decision: Catalog Tool Selection

This is the most critical decision for C20. The evaluation explicitly requires a
**catalog tool comparison and justified selection** (E7 requirement #3).

#### Option A: DataHub (LinkedIn open-source)

| Aspect | Assessment |
|--------|------------|
| **Description** | Full-featured metadata platform with UI, lineage graph, search, governance |
| **Docker footprint** | Heavy: requires MySQL/PostgreSQL + Elasticsearch + Kafka + GMS + Frontend (5+ containers, ~4-6GB RAM) |
| **Integration** | Native Airflow integration (DataHub Airflow plugin), PostgreSQL connector, S3/MinIO connector |
| **Catalog features** | Dataset discovery, schema browser, lineage visualization, tags, glossary, ownership |
| **Access control** | Fine-grained policies, OIDC/LDAP auth |
| **Pros** | Industry-standard, impressive demo, auto-lineage from Airflow, search/discovery UI |
| **Cons** | Extremely heavy for a single-machine certification project. Kafka + Elasticsearch + GMS each need 1-2GB RAM. Docker Compose would grow from ~12 to ~18 services. Setup complexity high. May crash on a laptop during demo |
| **Risk** | HIGH — demo reliability is paramount for oral defense |

#### Option B: Apache Atlas

| Aspect | Assessment |
|--------|------------|
| **Description** | Hadoop ecosystem metadata governance tool |
| **Docker footprint** | Heavy: requires HBase, Solr, Kafka, Atlas server (~3-5GB RAM) |
| **Integration** | Designed for Hadoop/Hive, limited native PostgreSQL/MinIO integration |
| **Catalog features** | Type system, lineage, classification, glossary |
| **Access control** | Apache Ranger integration |
| **Pros** | Enterprise-grade, well-known in big data circles |
| **Cons** | Hadoop-centric, poor fit for PostgreSQL+MinIO stack. Even heavier than DataHub. Complex setup. Not actively maintained for non-Hadoop use cases |
| **Risk** | HIGH — poor stack fit, maintenance burden |

#### Option C: Lightweight custom catalog with Streamlit UI and PostgreSQL backend (RECOMMENDED)

| Aspect | Assessment |
|--------|------------|
| **Description** | Custom catalog stored in PostgreSQL (new `catalog` schema), browsable via Streamlit UI page and REST API endpoint, fed by Airflow DAG tasks |
| **Docker footprint** | Zero new containers — uses existing PostgreSQL + Streamlit + FastAPI |
| **Integration** | Native: Airflow tasks write directly to PostgreSQL catalog tables; FastAPI serves catalog API; Streamlit renders browse UI |
| **Catalog features** | Dataset listing, schema/column metadata, quality metrics, lineage tracking, owner/access info, search by name/tag |
| **Access control** | PostgreSQL role-based GRANTs (reuses existing governance roles) |
| **Pros** | Lightweight, reliable, zero new infra, demo-proof, tightly integrated with existing stack, fast to implement, easy to explain during defense |
| **Cons** | Not an "industry-standard" tool. No automatic lineage graph visualization (can be argued as a tradeoff) |
| **Risk** | LOW — built on existing proven infrastructure |

#### Decision justification

**Selected: Option C (Lightweight custom catalog)**

Rationale:
1. **Demo reliability**: The oral defense requires a live demo. Adding 5+ containers (DataHub) or Hadoop dependencies (Atlas) significantly increases failure risk on a single machine. The custom solution uses existing containers that are already proven stable.

2. **Stack coherence**: The NutriTrack project already uses PostgreSQL for operational data and the data warehouse, Streamlit for the frontend, and FastAPI for the API. A catalog built on these same technologies demonstrates architectural coherence rather than tool sprawl.

3. **Certification fit**: The referential requires that "feed scripts run without errors" and "metadata integrated into catalog." A custom solution lets us demonstrate complete control over feed scripts and metadata integration — more convincing than plugging in a black-box tool.

4. **Tradeoff acknowledgment**: DataHub would provide automatic lineage graphs and search powered by Elasticsearch. We trade those features for simplicity, reliability, and faster delivery. This tradeoff should be explicitly mentioned during the defense as evidence of pragmatic engineering judgment.

5. **Resource constraints**: The Docker Compose already runs 14+ services. Adding 5 more would likely cause memory pressure during demos.

### Implementation plan

#### 4.1 PostgreSQL catalog schema

Create `sql/migrations/004_add_catalog_schema.sql`:

```sql
CREATE SCHEMA IF NOT EXISTS catalog;

-- Datasets: one row per logical dataset (e.g., "bronze/api", "silver/products")
CREATE TABLE catalog.datasets (
    dataset_id SERIAL PRIMARY KEY,
    dataset_name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    layer VARCHAR(20) CHECK (layer IN ('bronze','silver','gold','operational','warehouse')),
    format VARCHAR(50),
    storage_location VARCHAR(500),  -- e.g., "minio://bronze/api/" or "postgresql://nutritrack/app.products"
    owner VARCHAR(100),
    update_frequency VARCHAR(50),
    schema_type VARCHAR(50),  -- 'structured','semi-structured','unstructured'
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Columns: schema metadata per dataset
CREATE TABLE catalog.columns (
    column_id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES catalog.datasets(dataset_id),
    column_name VARCHAR(200) NOT NULL,
    data_type VARCHAR(100),
    is_nullable BOOLEAN DEFAULT TRUE,
    is_pii BOOLEAN DEFAULT FALSE,  -- RGPD flag
    description TEXT,
    sample_values TEXT,
    UNIQUE(dataset_id, column_name)
);

-- Quality metrics: latest quality snapshot per dataset
CREATE TABLE catalog.quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES catalog.datasets(dataset_id),
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    row_count BIGINT,
    null_rate_avg NUMERIC(5,2),
    completeness_pct NUMERIC(5,2),
    freshness_hours NUMERIC(8,2),  -- hours since last update
    details JSONB,
    UNIQUE(dataset_id, metric_date)
);

-- Lineage: source-to-target relationships
CREATE TABLE catalog.lineage (
    lineage_id SERIAL PRIMARY KEY,
    source_dataset_id INTEGER REFERENCES catalog.datasets(dataset_id),
    target_dataset_id INTEGER REFERENCES catalog.datasets(dataset_id),
    transformation_type VARCHAR(100),  -- 'etl','aggregation','copy','filter'
    etl_dag_id VARCHAR(100),
    description TEXT,
    UNIQUE(source_dataset_id, target_dataset_id)
);

-- Access log: who accessed what (for governance audit)
CREATE TABLE catalog.access_log (
    access_id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES catalog.datasets(dataset_id),
    accessed_by VARCHAR(100),
    access_type VARCHAR(20) CHECK (access_type IN ('read','write','admin')),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

GRANTs:
- `catalog_reader` (new role): SELECT on all catalog tables
- `catalog_writer` (new role): SELECT, INSERT, UPDATE on datasets, columns, quality_metrics, lineage
- `etl_service`: inherits catalog_writer
- `admin_role`: ALL on catalog schema
- `nutritionist_role`: inherits catalog_reader
- `app_readonly`: inherits catalog_reader

**Estimated file changes**: 1 new SQL migration

#### 4.2 Catalog seed script

Create `scripts/seed_catalog.py` that pre-populates `catalog.datasets`, `catalog.columns`,
and `catalog.lineage` with all known datasets:

Datasets to register:
1. `bronze/api` — Raw OFF API JSON
2. `bronze/parquet` — Raw OFF Parquet export
3. `bronze/scraping` — Raw scraped guidelines
4. `bronze/duckdb` — Raw DuckDB analytics
5. `silver/products` — Cleaned product dataset
6. `gold/product_wide_denormalized` — Flat product table
7. `gold/data_quality_report` — Quality metrics
8. `gold/source_comparison` — Cross-source analysis
9. `gold/daily_snapshots` — Full catalog snapshots
10. `gold/ml_nutrition_features` — ML feature matrix
11. `gold/nutrition_patterns` — Anonymized nutrition aggregates
12. `gold/popular_products` — Anonymized popular product aggregates
13. `gold/brand_rankings` — Brand quality rankings
14. `gold/category_stats` — Category statistics
15. `operational/app.products` — Operational product table
16. `operational/app.users` — User accounts (PII flagged)
17. `operational/app.meals` — Meal tracking
18. `warehouse/dw.dim_product` — Product dimension (SCD2)
19. `warehouse/dw.dim_user` — User dimension (pseudonymized)
20. `warehouse/dw.fact_daily_nutrition` — Nutrition facts
21. `warehouse/dw.fact_product_market` — Market analysis facts

Lineage relationships:
- bronze/* -> silver/products (via etl_aggregate_clean)
- silver/products -> gold/* (via etl_datalake_ingest)
- silver/products -> operational/app.products (via etl_aggregate_clean.load_to_database)
- operational/app.* -> warehouse/dw.* (via etl_load_warehouse)
- warehouse/dw.* -> gold/nutrition_patterns, gold/popular_products, etc. (via etl_datalake_ingest.publish_anonymized_aggregates)

**Estimated file changes**: 1 new script

#### 4.3 Airflow catalog feed tasks

Modify existing DAGs to update catalog metadata after each run:

1. **etl_aggregate_clean.py**: After `load_to_database`, add a task `update_catalog_quality`
   that writes row counts, null rates, and freshness to `catalog.quality_metrics`

2. **etl_datalake_ingest.py**: The existing `update_catalog_metadata` task currently writes
   a JSON to MinIO. Extend it to ALSO write to `catalog.quality_metrics` and update
   `catalog.datasets.updated_at` for all lake datasets

3. **etl_load_warehouse.py**: Add a final task `update_catalog_dw` that writes
   dimension/fact row counts to `catalog.quality_metrics`

**Estimated file changes**: 3 modified DAG files

#### 4.4 Streamlit catalog browser UI

Create `app/pages/catalog.py` (Streamlit multi-page app page):

Features:
- Dataset listing with search/filter by layer, tag, owner
- Dataset detail view: description, columns, quality metrics, lineage
- Quality trend chart per dataset (freshness, completeness over time)
- PII column highlighting (RGPD)
- Lineage display (simple table showing source -> target relationships)

**Decision: Streamlit page vs. separate React app**

| Option | Pros | Cons |
|--------|------|------|
| **Streamlit page** (RECOMMENDED) | Reuses existing Streamlit app, zero new infrastructure, Python-native | Limited interactivity vs React |
| Separate React app | More polished UI | New container, new build pipeline, overkill |

**Estimated file changes**: 1 new Streamlit page

#### 4.5 FastAPI catalog endpoints

Add `api/routers/catalog.py`:

Endpoints:
- `GET /api/v1/catalog/datasets` — list all datasets (filterable by layer, tag)
- `GET /api/v1/catalog/datasets/{id}` — dataset detail with columns, quality, lineage
- `GET /api/v1/catalog/search?q=...` — search datasets by name/description
- `GET /api/v1/catalog/lineage/{dataset_id}` — upstream/downstream lineage

Access: restricted to authenticated users with at least `app_readonly` role.

**Estimated file changes**: 1 new router + update to `api/main.py` to include router

#### 4.6 Deletion and lifecycle procedures

Add lifecycle management to catalog:

1. **Bronze cleanup**: Airflow task in `etl_backup_maintenance.py` that deletes
   bronze objects older than 90 days (matching the stated retention policy in the
   existing catalog JSON)

2. **Catalog staleness alert**: Grafana alert rule when `catalog.quality_metrics.freshness_hours`
   exceeds threshold (e.g., 48 hours for daily datasets)

3. **Deletion procedure documentation**: Step-by-step in mkdocs for removing a dataset
   from the catalog (mark as deprecated -> stop feeds -> archive -> delete)

**Estimated file changes**: 1 modified DAG, 1 new Grafana alert rule, 1 documentation file

#### 4.7 Monitoring integration

Add catalog-specific metrics to existing monitoring:

1. Add a `catalog_freshness_exporter` task in `etl_backup_maintenance.py` that writes
   catalog freshness metrics to a Prometheus-compatible format (or query directly
   from PostgreSQL via the existing postgres-exporter)

2. Add Grafana dashboard panel for catalog health (datasets by freshness, quality trends)
   to the existing SLA dashboard or a new catalog dashboard

**Estimated file changes**: 1 modified DAG, 1 new or modified Grafana dashboard JSON

### Total estimated changes for Task #4

| Type | Count |
|------|-------|
| New SQL migration | 1 |
| New script (seed_catalog.py) | 1 |
| Modified DAG files | 3-4 |
| New Streamlit page | 1 |
| New API router + main.py update | 2 |
| New/modified Grafana dashboards | 1 |
| New Grafana alert rule | 1 |
| Documentation | 1 |
| **Total files** | **11-12** |

---

## Task #5 -- C21: Data Governance

### Referential requirements (p.25)

1. Rights applied to groups (not individuals) when possible
2. Access meets group needs
3. Access limited to necessary resources (least privilege)
4. Access RGPD-compliant
5. Documentation covers access groups, associated rights, and update procedures

### Current state

PostgreSQL roles and GRANTs are already well-structured:

| Role | Type | Current Access |
|------|------|----------------|
| `app_readonly` | NOLOGIN group | SELECT on products, categories, brands, guidelines (app schema) |
| `nutritionist_role` | NOLOGIN group | SELECT on all app tables EXCEPT users; SELECT on DW analytical views |
| `admin_role` | NOLOGIN group | ALL on app + dw schemas |
| `etl_service` | LOGIN | SELECT, INSERT, UPDATE on app + dw; INSERT on etl_activity_log |
| `nutritrack` | LOGIN (app owner) | ALL on app + dw |
| `superset` | LOGIN | SELECT on dw schema |

### Gap analysis

1. **MinIO access is not group-based**: Currently `minioadmin` is used everywhere; gold bucket has anonymous download. No MinIO policies map to the PostgreSQL role model
2. **No governance documentation**: Rights are defined in SQL files but not documented in a human-readable format for auditors
3. **No access update procedure**: No documented workflow for granting/revoking access
4. **Catalog schema not yet governed** (depends on Task #4)

### Implementation plan

#### 5.1 MinIO group-based policies

**Decision: MinIO built-in policies vs. external IAM**

| Option | Pros | Cons |
|--------|------|------|
| **MinIO built-in IAM policies** (RECOMMENDED) | Native, no extra infrastructure, maps to existing roles | Limited compared to full IAM |
| External IAM (Keycloak/OIDC) | Enterprise-grade, SSO | New container, complex setup, overkill |

**Action**: Create MinIO policies and users via the `minio-init` service in docker-compose:

| MinIO User | Maps to PG Role | Policy | Buckets |
|------------|-----------------|--------|---------|
| `etl-writer` | etl_service | Read/Write all buckets | bronze, silver, gold, backups |
| `analyst-reader` | app_readonly + nutritionist_role | Read only gold + silver | gold (read), silver/products (read) |
| `ds-reader` | (data scientist) | Read gold only | gold (read) |
| `admin-full` | admin_role | Full access | all buckets (full) |

Remove anonymous download from gold bucket (replace with explicit reader policy).

**Estimated file changes**: 1 modified `docker-compose.yml` (minio-init entrypoint), 1 new `scripts/setup_minio_policies.py`

#### 5.2 Catalog schema governance

After Task #4 creates the catalog schema, add GRANTs:

```sql
-- New roles for catalog
CREATE ROLE catalog_reader WITH NOLOGIN;
CREATE ROLE catalog_writer WITH NOLOGIN;

GRANT USAGE ON SCHEMA catalog TO catalog_reader, catalog_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog TO catalog_reader;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA catalog TO catalog_writer;

-- Map existing roles
GRANT catalog_reader TO app_readonly, nutritionist_role, superset;
GRANT catalog_writer TO etl_service;
GRANT ALL ON SCHEMA catalog TO admin_role;
```

**Estimated file changes**: included in the Task #4 migration (004_add_catalog_schema.sql)

#### 5.3 Governance documentation

Create comprehensive access documentation. This should include:

1. **Access groups table**: all PostgreSQL roles, their purpose, and members
2. **Per-schema access matrix**: which role can do what on which schema/table
3. **MinIO access matrix**: which MinIO user/policy can access which bucket
4. **RGPD compliance mapping**: which datasets contain PII, retention periods, legal basis
5. **Access request procedure**: step-by-step for granting new access
6. **Access revocation procedure**: step-by-step for removing access
7. **Periodic review process**: quarterly audit checklist

**Decision: mkdocs page vs. standalone markdown**

| Option | Pros | Cons |
|--------|------|------|
| **mkdocs page** (RECOMMENDED) | Integrated with existing documentation site, searchable | Requires mkdocs build |
| Standalone markdown | Simpler | Disconnected from main docs |

**Action**: Create `mkdocs/docs/governance/access-control.md` with all of the above.

**Estimated file changes**: 1 new documentation file, update `mkdocs/mkdocs.yml` nav

#### 5.4 Automated governance validation

Create a test/script that validates governance rules are correctly applied:

`scripts/validate_governance.py`:
- Connect as each role and verify expected permissions
- Verify etl_service CANNOT read app.users directly
- Verify nutritionist_role CANNOT access raw user data
- Verify app_readonly CANNOT write to any table
- Verify MinIO policies deny unauthorized access

This can also be integrated as a test in `tests/test_sql_schemas.py`.

**Estimated file changes**: 1 new script or test file

### Total estimated changes for Task #5

| Type | Count |
|------|-------|
| Modified docker-compose.yml | 1 |
| New MinIO policy script | 1 |
| New/modified SQL migration (part of Task #4) | 0 (already counted) |
| New governance documentation | 1 |
| Modified mkdocs.yml | 1 |
| New governance validation script | 1 |
| **Total files** | **5** |

---

## Cross-cutting Concerns

### RGPD compliance (spans C16, C20, C21)

The RGPD registry (`app.rgpd_data_registry`) already has entries for user data, meals,
products, DW analytics, DW user dimension, ETL logs, and backups. New entries needed:

| Data Category | Task | Migration |
|---------------|------|-----------|
| Catalog metadata | Task #4 | 004_add_catalog_schema.sql |
| Catalog access logs | Task #4 | 004_add_catalog_schema.sql |
| Maintenance task records | Task #3 | new migration |

### Testing strategy

All new code should have corresponding tests:
- SQL migrations: extend `tests/test_sql_schemas.py`
- API endpoints: extend `tests/test_api_schemas.py`
- ETL functions: extend `tests/test_etl_functions.py`
- Governance: new `tests/test_governance.py` or `scripts/validate_governance.py`

### Documentation consistency

All documentation must be in English (per team rules). New docs go into mkdocs
for the technical site. The certification defense report references these docs.

---

## Implementation Order and Dependencies

```
Task #2 (CI/CD) must complete first
         |
         v
Task #3 (C16) -- can start immediately after CI/CD
  |       |
  |       +-- Gap A+B: DAG alerting propagation (no dependencies)
  |       +-- Gap C: Grafana alerting rules (no dependencies)
  |       +-- Gap D: Maintenance table migration (no dependencies)
  |       +-- Gap E: Operational docs (no dependencies)
  |
  v
Task #4 (C20) -- depends on nothing from Task #3, can run in parallel
  |       |
  |       +-- Step 4.1: SQL migration (must be first)
  |       +-- Step 4.2: Seed script (after 4.1)
  |       +-- Step 4.3: DAG feed tasks (after 4.1)
  |       +-- Step 4.4: Streamlit UI (after 4.1)
  |       +-- Step 4.5: API endpoints (after 4.1)
  |       +-- Step 4.6: Lifecycle procedures (after 4.3)
  |       +-- Step 4.7: Monitoring (after 4.3)
  |
  v
Task #5 (C21) -- depends on Task #4 for catalog governance
  |       |
  |       +-- Step 5.1: MinIO policies (no dependencies)
  |       +-- Step 5.2: Catalog GRANTs (after Task #4 step 4.1)
  |       +-- Step 5.3: Documentation (after 5.1 + 5.2)
  |       +-- Step 5.4: Validation script (after 5.1 + 5.2)
```

**Recommended execution order**: Tasks #3 and #4 in parallel (both unblock independently after CI/CD), then Task #5 last since it requires catalog schema to exist for full governance coverage.

### Total estimated file changes across all tasks

| Task | New Files | Modified Files | Total |
|------|-----------|----------------|-------|
| Task #3 (C16) | 4 | 5 | 9 |
| Task #4 (C20) | 6 | 5 | 11 |
| Task #5 (C21) | 3 | 2 | 5 |
| **Grand total** | **13** | **12** | **25** |
