# NutriTrack -- Presenter Document Plan

**Role**: presenter (nutritrack-certification team)
**Date**: 2026-04-09
**Status**: Phase 1 -- Research and Planning (blocked on cert-auditor)

---

## 1. Inventory of Existing LaTeX Deliverables

| File | Lines | Purpose | Status |
|---|---|---|---|
| `rapport_final.tex` | 1854 | Full certification report (report class, 12pt, two-sided) | Complete -- all 21 chapters present (C1-C21), bibliography, title page, TikZ star schema diagram |
| `final_deck.tex` | 1780 | Visual defense slides (Beamer/metropolis, 16:9) | Complete -- ~46 frames, all E1-E7 sections, speaker `\note{}` on most slides, NutriTrack logo TikZ |
| `defense_slides.tex` | 1526 | Earlier version of slides (Beamer/metropolis, 16:9) | Superseded by `final_deck.tex` -- similar structure but lacks some refinements |
| `speaker_notes.md` | ~700 | Talking points per slide | Complete -- covers all slides with timing cues |

### Existing assets worth reusing

- **NutriTrack brand colors** already defined in both files (`ntgreen #2E7D32`, `ntblue #1565C0`, etc.)
- **Custom commands**: `\nutritrack`, `\competency{C1}`, `\fullcov`, `\democallout`, `\whycallout`
- **NutriTrack TikZ logo** in `final_deck.tex` lines 78-106 -- scalable vector logo
- **Star schema TikZ diagram** in `rapport_final.tex` ~line 972-1073
- **Defense agenda TikZ timeline** in `final_deck.tex` lines 130-158

### Existing markdown content to convert

- `rapport_final.md` (103k, 19 chapters) -- source content, much already in .tex
- `technical_stack_choices.md` (48k) -- architecture decisions, comparison tables
- `certification_audit.md` (30k) -- competency coverage evidence, gap analysis
- `dw_vs_datalake_justification.md` (8k) -- why both DW and lake
- `analytics_dashboard.md` (7k) -- Superset dashboard documentation
- `veille_technologique.md` (4k) -- tech monitoring newsletter content

---

## 2. Codebase Architecture Summary (for diagram planning)

### Docker Compose Services (15 services)

| Service | Image/Build | Port | Purpose | Competency |
|---|---|---|---|---|
| postgres | postgres:16-alpine | 5432 | OLTP (app schema) + OLAP (dw schema) | C11, C13, C14 |
| redis | redis:7-alpine | 6379 | Cache + Celery broker | C14 |
| minio | minio/minio:latest | 9000, 9001 | Data lake (S3-compatible) | C18, C19 |
| minio-init | minio/mc:latest | -- | Create bronze/silver/gold/backups buckets | C19 |
| airflow-init | custom build | -- | DB init, user creation, connection setup | C15 |
| airflow-webserver | custom build | 8080 | DAG UI, monitoring | C6, C16 |
| airflow-scheduler | custom build | -- | DAG scheduling | C15 |
| airflow-worker | custom build | -- | Celery task execution | C15 |
| fastapi | custom build | 8000 | REST API (JWT, RBAC) | C12 |
| prometheus | prom/prometheus | 9090 | Metrics collection | C16, C20 |
| statsd-exporter | prom/statsd-exporter | 9102, 9125 | Airflow metrics bridge | C16 |
| cadvisor | gcr.io/cadvisor | 8081 | Container metrics | C16, C20 |
| node-exporter | prom/node-exporter | 9100 | Host metrics | C16 |
| postgres-exporter | prometheuscommunity | 9187 | DB metrics | C16 |
| grafana | grafana/grafana | 3000 | Dashboards (6 provisioned) | C16, C20 |
| streamlit | custom build | 8501 | Frontend app | C7, C12 |
| superset | custom build | 8088 | BI analytics | C13, C14 |
| mailhog | mailhog/mailhog | 1025, 8025 | SMTP testing for alerts | C16 |

### Database Schemas

- **app** (operational): categories, brands, products, users, meals, meal_items, nutritional_guidelines, extraction_log, rgpd_data_registry
- **dw** (warehouse): dim_time, dim_product (SCD2), dim_brand (SCD1), dim_category, dim_country (SCD3), dim_user (SCD2), dim_nutriscore; fact_daily_nutrition, fact_product_market
- **Datamarts**: dm_user_daily_nutrition, dm_product_market_by_category, dm_brand_quality_ranking, dm_nutriscore_distribution, dm_nutrition_trends, dm_dw_health

### Roles (C21 Governance)

- `nutritrack` (full access)
- `app_readonly` (read products only)
- `nutritionist_role` (read products + DW analytical views, no raw user data)
- `admin_role` (full)
- `etl_service` (write for data loading)
- `superset` (read DW views)

### Airflow DAGs (7 total)

1. `etl_extract_off_api` -- REST API extraction (daily)
2. `etl_extract_parquet` -- DuckDB extraction from OFF Parquet (weekly Sunday)
3. `etl_extract_scraping` -- Web scraping (weekly)
4. `etl_aggregate_clean` -- PySpark aggregation + cleaning (daily 04:00)
5. `etl_datalake_ingest` -- MinIO medallion ingest (daily 05:00)
6. `etl_load_warehouse` -- Star schema loading with SCD (daily 05:00)
7. `etl_backup_maintenance` -- Backups + RGPD cleanup (daily 02:00)

### Data Pipeline Flow

```
OpenFoodFacts (API, Parquet, Scraping)
       |
       v
  Raw extraction --> data/raw/{api,parquet,scraping,duckdb}/
       |
       v
  etl_aggregate_clean (PySpark + pandas)
       |
   +---+---+
   |       |
   v       v
DW path    Lake path
(PostgreSQL (MinIO Bronze
 app -> dw)  -> Silver -> Gold)
   |       |
   v       v
Superset   Data Catalog
Grafana    (Streamlit page)
```

### API Endpoints (FastAPI)

- Auth: register, login (JWT)
- Products: search, get by barcode, alternatives (Nutri-Score based)
- Meals: CRUD, daily summary, weekly trends
- Analytics: (nutritionist/admin routes)
- Health: root, /api/v1/health

### CI/CD (GitHub Actions)

- `lint.yml` -- Python (ruff) + SQL (sqlfluff)
- `test.yml` -- pytest
- `docker.yml` -- Build all 4 custom images
- `deploy-docs.yml` -- MkDocs site deployment

### Monitoring Stack

- Prometheus scrapes: statsd-exporter, postgres-exporter, cadvisor, node-exporter, MinIO
- Grafana dashboards (6): airflow-dags, airflow, docker-system, minio, postgresql, sla-compliance
- Grafana alerting: minio-alerts.yml (provisioned)
- MailHog: SMTP sink for Airflow email alerts

---

## 3. Document Structure Plan -- rapport_final.tex

The existing `rapport_final.tex` (1854 lines) is **already comprehensive**. It covers:

### Current chapter structure (verified)

```
Chapter 1: Introduction
  - Project Context, Objectives, Certification Scope, Architecture overview

Chapter 2: Block 1 -- Steer a Data Project
  - E1/C1: Interview grids (producer + consumer)
  - E2/C1-C4,C6: Data topography (4 parts), architecture study, monitoring, supervision
  - E3/C5-C7: Roadmap, calendar, communication strategy

Chapter 3: Block 2 -- Data Collection, Storage and Sharing
  - C8: 5 extraction scripts
  - C9: 7 SQL queries
  - C10: Aggregation + cleaning (PySpark)
  - C11: Database modeling + RGPD
  - C12: REST API

Chapter 4: Block 3 -- Data Warehouse
  - C13: Star schema modeling (TikZ diagram)
  - C14: DW implementation
  - C15: ETL pipelines
  - C16: DW maintenance, alerting, SLA, backups
  - C17: SCD Type 1/2/3

Chapter 5: Block 4 -- Data Lake
  - C18: Medallion architecture, 3V, catalog comparison
  - C19: Infrastructure components
  - C20: Data catalog management
  - C21: Data governance (RBAC, policies)

Chapter 6: CI/CD and Documentation
Chapter 7: Conclusion (demo plan, verification matrix, lessons learned, improvements)
Bibliography (10 references)
```

### Gaps / improvements needed in rapport_final.tex

1. **PySpark content** -- The recent PySpark cleaning pipeline (commit 3b48398) added PySpark to etl_aggregate_clean.py. The report section on C10 may need updating to reflect PySpark vs pandas-only cleaning.
2. **Gold aggregates** -- The gold layer now has anonymized aggregates (commit 3b48398). The C20 section should reference these.
3. **Data quality checks** -- The staging.data_quality_checks table (migration 003) should be documented in the C15/C16 sections.
4. **Parquet extraction DAG** -- The etl_extract_parquet.py was recently modified (git status shows staged changes). Report may need updating.

### TikZ diagrams already present

- Star schema (lines ~972-1073) -- full dimensional model
- Various inline architecture diagrams

### TikZ diagrams to ADD or IMPROVE

1. **System Architecture** (all 18 Docker services with connections) -- currently text-only ASCII art in rapport; should be TikZ
2. **ETL DAG dependency graph** -- show the 7 DAGs with scheduling and ExternalTaskSensor dependencies
3. **Medallion Architecture** -- bronze/silver/gold layers with data flow
4. **RGPD Process Flow** -- consent -> processing -> retention -> cleanup cycle
5. **CI/CD Pipeline** -- 4 GitHub Actions workflows with triggers

---

## 4. Document Structure Plan -- final_deck.tex (Defense Slides)

### Current slide structure (verified, ~46 frames)

```
Slide 1:  Title (standout, NutriTrack logo)
Slide 2:  Defense Agenda (TikZ timeline)
Slide 3:  Client persona (Sophie Yang)

Section E1 -- Need Analysis (C1):
  Slide 4:  Interview Grids
  Slide 5:  SMART Objectives
  Slide 6:  NutriTrack built for Sophie
  Slide 7:  Open Food Facts source
  Slide 8:  OFF data formats
  Slide 9:  Data cleaning before/after
  Slide 10: End-to-end data flow
  Slide 11: One command, 14 services
  Slide 12: Tech stack
  Slide 13: Key technical decisions
  Slide 14: PostgreSQL three zones
  Slide 15: Why both DW and lake

Section E2 -- Architecture (C2, C3, C4, C6):
  Slide 16: Data topography 4 parts
  Slide 17: System architecture 14 services
  Slide 18: Flux matrix
  Slide 19: Technical monitoring newsletter
  Slide 20: RGPD compliance

Section E3 -- Project Kickoff (C5, C6, C7):
  Slide 21: 6-phase roadmap
  Slide 22: Tracking indicators
  Slide 23: Multi-audience communication

Section E4 -- Data Collection (C8-C12):
  Slide 24: 5 extraction sources overview
  Slide 25: REST API extraction
  Slide 26: Scraping + DuckDB
  Slide 27: Cleaning pipeline
  Slide 28: 7 SQL queries
  Slide 29: RGPD-compliant database
  Slide 30: FastAPI REST API
  Slide 31: Streamlit frontend

Section E5 -- Data Warehouse (C13-C15):
  Slide 32: Star schema
  Slide 33: 6 datamart views
  Slide 34: ETL pipeline (7 DAGs)
  Slide 35: SCD dimension variations

Section E6 -- DW Maintenance (C16, C17):
  Slide 36: Alert system
  Slide 37: SLA dashboard
  Slide 38: Backup & maintenance

Section E7 -- Data Lake (C18-C21):
  Slide 39: Medallion architecture
  Slide 40: Volume, Variety, Velocity
  Slide 41: Catalog tool comparison
  Slide 42: Data catalog browser
  Slide 43: Access governance
  Slide 44: Monitoring stack
  Slide 45: 6 Grafana dashboards

Conclusion:
  Slide 46: 21/21 competencies covered (matrix)
  Slide 47: Lessons learned
  Slide 48: Live demo plan
  Slide 49: Thank you (standout)
```

### Gaps / improvements needed in final_deck.tex

1. **Speaker notes** -- Most slides have `\note{}` but verify completeness. The `speaker_notes.md` has full notes; ensure all are embedded.
2. **PySpark slide** -- The cleaning pipeline slide should mention PySpark (not just pandas).
3. **Gold aggregates** -- E7 section should highlight anonymized gold-layer aggregates.
4. **Service count** -- Some slides say "14 services", others list 17-18. Normalize to actual count from docker-compose.yml (count: 18 services defined including init containers).
5. **Demo callouts** -- Ensure `\democallout{}` markers are on the right slides for live demo transitions.

---

## 5. Planned TikZ Diagrams (with specification)

### Diagram 1: Full System Architecture

**Purpose**: Replace ASCII art with professional TikZ diagram for rapport chapter 1 and slide 17.

**Layout**: 4 horizontal layers (top to bottom):
- Layer 1 (External): OpenFoodFacts API, OFF Parquet dump, ANSES website
- Layer 2 (Processing): Airflow (webserver, scheduler, worker), PySpark
- Layer 3 (Storage): PostgreSQL (app + dw schemas), MinIO (bronze/silver/gold), Redis
- Layer 4 (Presentation): FastAPI, Streamlit, Superset, Grafana

**Connections**: Arrows showing data flow between services with labeled protocols (HTTP, SQL, S3, SMTP).

**Colors**: Use ntgreen for data flow, ntblue for API calls, ntorange for monitoring.

### Diagram 2: Data Flow Pipeline

**Purpose**: Show the complete data journey from source to consumption.

**Layout**: Left-to-right flow:
```
OFF API ---|
OFF Parquet-|-> Extraction -> Aggregation/Clean -> [fork]
ANSES -------|                                        |-> DW path (PostgreSQL dw)
                                                      |-> Lake path (MinIO Bronze->Silver->Gold)
```

**Annotations**: File formats at each stage (JSON, Parquet, SQL), record counts, schedule times.

### Diagram 3: Star Schema (already exists in rapport, enhance)

**Purpose**: Show dimensional model with fact and dimension tables.

**Existing**: Lines 972-1073 of rapport_final.tex -- full TikZ star schema.

**Enhancement**: Add SCD type annotations (Type 1/2/3) on relevant dimensions.

### Diagram 4: ETL DAG Dependencies

**Purpose**: Show Airflow DAG scheduling and sensor dependencies.

**Layout**: Timeline-based (02:00 -> 03:00 -> 04:00 -> 05:00):
```
02:00  etl_backup_maintenance
03:00  etl_extract_off_api | etl_extract_scraping | etl_extract_parquet (weekly)
04:00  etl_aggregate_clean (waits for extractors)
05:00  etl_datalake_ingest (waits for clean) || etl_load_warehouse (waits for clean)
```

**Colors**: Bronze for extraction, silver for cleaning, gold for loading.

### Diagram 5: Medallion Architecture

**Purpose**: Show Bronze/Silver/Gold layers in MinIO.

**Layout**: 3-column with descriptions:
- Bronze: Raw data, as-is (JSON, Parquet), partitioned by date
- Silver: Cleaned, validated, standardized columns
- Gold: Anonymized aggregates, catalog metadata, ready for consumption

**Annotations**: File formats, record counts, quality checks applied.

### Diagram 6: RGPD Process Flow

**Purpose**: Show data protection lifecycle.

**Layout**: Circular flow:
1. Consent collection (user registration, consent_data_processing flag)
2. Data processing (minimal collection, purpose limitation)
3. Pseudonymization (user_id -> user_hash in DW)
4. Retention enforcement (data_retention_until, auto-cleanup)
5. Right to erasure (API endpoint, cascading deletes)
6. Audit trail (rgpd_data_registry, extraction_log)

### Diagram 7: CI/CD Pipeline

**Purpose**: Show GitHub Actions workflow.

**Layout**: Horizontal pipeline:
```
Push/PR to main -> [parallel] Lint (ruff+sqlfluff) | Test (pytest) | Docker Build (4 images)
                                                                      |
                                                                      v
                                                                Deploy Docs (MkDocs)
```

---

## 6. Code Listings Plan

### For rapport_final.tex

| Listing | Source File | Lines | Competency |
|---|---|---|---|
| API extraction | scripts/extract_off_api.py | ~20 lines (key function) | C8 |
| DuckDB query | airflow/dags/etl_extract_parquet.py | lines 38-74 (SQL query) | C8, C9 |
| PySpark cleaning | airflow/dags/etl_aggregate_clean.py | ~30 lines (clean function) | C10 |
| Aggregation merge | airflow/dags/etl_aggregate_clean.py | ~15 lines (merge logic) | C10 |
| RGPD cleanup function | sql/init/01_schema_operational.sql | lines 229-253 | C11 |
| JWT auth | api/auth/jwt.py | ~15 lines | C12 |
| SCD Type 2 procedure | sql/init/02_schema_warehouse.sql | lines 225-255 | C17 |
| Dimension loading | airflow/dags/etl_load_warehouse.py | ~20 lines | C15 |
| MinIO bronze ingest | airflow/dags/etl_datalake_ingest.py | ~20 lines | C18, C19 |
| Alerting callback | airflow/plugins/alerting.py | ~20 lines | C16 |
| Role grants | sql/init/00_init_databases.sql | lines 13-47 | C21 |

### For final_deck.tex

Code listings in slides should be minimal (5-10 lines max, `\tiny\ttfamily`). Show:
- DuckDB extraction query (1 slide)
- SCD Type 2 procedure (1 slide)
- API endpoint example (1 slide)
- PySpark cleaning snippet (1 slide)

---

## 7. LaTeX Package and Class Plan

### rapport_final.tex

Already uses:
- `report` class (a4paper, 12pt, twoside)
- `geometry`, `fancyhdr`, `setspace`, `parskip`
- `tikz` with many libraries
- `listings` for code
- `booktabs`, `tabularx`, `longtable`, `multirow`
- `hyperref`, `natbib`
- `graphicx`, `xcolor`, `float`, `enumitem`
- `caption`, `subcaption`, `pdfpages`

No changes needed. The preamble is well-structured.

### final_deck.tex

Already uses:
- `beamer` with `metropolis` theme (16:9)
- `tikz` with positioning, shapes, calc, fit, backgrounds, matrix, shadows
- `fontawesome5` for icons
- `booktabs`, `listings`, `multicol`, `hyperref`

Consider adding for enhancements:
- `pgfplots` if we need chart diagrams (bar charts for Nutri-Score distribution)
- `tcolorbox` for better callout boxes (alternative to current TikZ approach)

---

## 8. Competency-to-Section Cross-Reference (for both documents)

This table maps each competency to its location in BOTH the report and the slides.

| Comp | Block | Eval | rapport_final.tex Section | final_deck.tex Slide(s) |
|---|---|---|---|---|
| C1 | 1 | E1,E2 | sec:e1 (grids), sec:e2 (synthesis) | 4 (grids), 5 (SMART) |
| C2 | 1 | E2 | sec:e2 subsec topography | 16 (topography), 18 (flux) |
| C3 | 1 | E2 | sec:e2 subsec architecture | 13 (decisions), 17 (arch), 20 (RGPD) |
| C4 | 1 | E2 | sec:e2 subsec monitoring | 19 (newsletter) |
| C5 | 1 | E3 | sec:e3 subsec roadmap | 21 (roadmap) |
| C6 | 1 | E2,E3 | sec:e2 subsec supervision, sec:e3 | 22 (indicators) |
| C7 | 1 | E3 | sec:e3 subsec communication | 23 (multi-audience) |
| C8 | 2 | E4 | sec:c8 (5 sources) | 24-26 (extraction) |
| C9 | 2 | E4 | sec:c9 (SQL queries) | 28 (SQL) |
| C10 | 2 | E4 | sec:c10 (aggregation) | 27 (cleaning), 9 (before/after) |
| C11 | 2 | E4 | sec:c11 (MCD/MLD/MPD) | 29 (database) |
| C12 | 2 | E4 | sec:c12 (REST API) | 30 (FastAPI) |
| C13 | 3 | E5 | sec:c13 (star schema) | 32 (star schema) |
| C14 | 3 | E5 | sec:c14 (DW implementation) | 33 (datamarts) |
| C15 | 3 | E5 | sec:c15 (ETL pipelines) | 34 (DAGs) |
| C16 | 3 | E6 | sec:c16 (maintenance) | 36-38 (alerts, SLA, backups) |
| C17 | 3 | E6 | sec:c17 (SCD) | 35 (SCD) |
| C18 | 4 | E7 | sec:c18 (lake architecture) | 39-41 (medallion, 3V, catalog) |
| C19 | 4 | E7 | sec:c19 (infrastructure) | 39 (part of medallion) |
| C20 | 4 | E7 | sec:c20 (catalog) | 42 (catalog browser) |
| C21 | 4 | E7 | sec:c21 (governance) | 43 (access governance) |

---

## 9. Priority Actions When Unblocked

### Immediate (Phase 2 -- after audit):

1. **Update rapport_final.tex C10 section** -- Add PySpark cleaning content, reference `clean_data_spark()` function.
2. **Update rapport_final.tex C20 section** -- Add gold-layer anonymized aggregates, reference data_catalog.py Streamlit page.
3. **Update final_deck.tex slide 27** -- PySpark cleaning mention.
4. **Add TikZ system architecture diagram** to rapport ch1 (replace ASCII art).
5. **Add TikZ ETL DAG dependency diagram** to rapport C15 section.
6. **Add TikZ medallion architecture diagram** to rapport C18 section.
7. **Verify all speaker notes** are embedded as `\note{}` in final_deck.tex.
8. **Normalize service count** across all documents (settle on actual count).

### Secondary:

9. Add TikZ RGPD process flow to rapport C11 section.
10. Add TikZ CI/CD pipeline to rapport chapter 6.
11. Add `\democallout{}` markers at correct transitions in slides.
12. Review bibliography -- add any missing references.
13. Generate a compilable Makefile target for `latexmk` (if not in docs/Makefile already).

### Final polish:

14. Cross-reference check (all `\ref{}` resolve).
15. Consistent terminology audit (14 vs 15 vs 17 vs 18 services).
16. Proofread all English text.
17. Verify page count targets (E2: 10-15 pages, E4: 5-10 pages, E5: 5-10 pages, E6: 5-10 pages, E7: individual report).

---

## 10. Key Codebase File Paths (for code listings)

```
/Users/reegauta/Documents/Simplon/nutritrack/
  docker-compose.yml              -- 18 services (C3, C14, C19)
  sql/init/00_init_databases.sql  -- Roles and databases (C21)
  sql/init/01_schema_operational.sql -- app schema with RGPD (C11)
  sql/init/02_schema_warehouse.sql   -- Star schema + SCD (C13, C14, C17)
  sql/init/03_schema_datamarts_analytics.sql -- Datamart views (C13, C14)
  sql/scd_procedures.sql          -- SCD Type 1/2/3 (C17)
  sql/queries/analytical_queries.sql -- 7 optimized queries (C9)
  sql/migrations/001_add_etl_activity_log.sql -- Activity logging (C16)
  sql/migrations/003_add_raw_staging_schemas.sql -- Staging schemas
  airflow/dags/etl_extract_off_api.py -- API extraction (C8)
  airflow/dags/etl_extract_parquet.py -- DuckDB extraction (C8, C9)
  airflow/dags/etl_extract_scraping.py -- Web scraping (C8)
  airflow/dags/etl_aggregate_clean.py -- PySpark cleaning (C10, C15)
  airflow/dags/etl_datalake_ingest.py -- Medallion ingest (C18, C19, C20)
  airflow/dags/etl_load_warehouse.py -- DW loading + SCD (C13-C15, C17)
  airflow/dags/etl_backup_maintenance.py -- Backups + RGPD cleanup (C16)
  airflow/plugins/alerting.py     -- Alert callbacks + activity log (C16)
  scripts/aggregate_clean.py      -- Standalone cleaning script (C10)
  scripts/extract_off_api.py      -- Standalone API extraction (C8)
  scripts/extract_off_parquet.py  -- Standalone Parquet extraction (C8)
  scripts/extract_scraping.py     -- Standalone scraping (C8)
  scripts/extract_duckdb.py       -- DuckDB analytics (C8, C9)
  scripts/extract_from_db.py      -- DB extraction (C8)
  scripts/import_to_db.py         -- Database import (C11)
  scripts/backup_database.py      -- Backup script (C16)
  scripts/setup_minio.py          -- MinIO bucket + catalog setup (C19, C20)
  api/main.py                     -- FastAPI app (C12)
  api/auth/jwt.py                 -- JWT authentication (C12)
  api/routers/auth.py             -- Auth endpoints (C12)
  api/routers/products.py         -- Product endpoints (C12)
  api/routers/meals.py            -- Meal endpoints (C12)
  api/routers/analytics.py        -- Analytics endpoints (C12)
  api/routers/nutritionist.py     -- Nutritionist endpoints (C12)
  api/models/user.py              -- User model (C11)
  api/models/product.py           -- Product model (C11)
  app/streamlit_app.py            -- Frontend app (C7, C12)
  app/pages/data_catalog.py       -- Data catalog browser (C20)
  monitoring/prometheus/prometheus.yml -- Prometheus config (C16, C20)
  monitoring/grafana/dashboards/  -- 6 Grafana dashboards (C16)
  monitoring/grafana/provisioning/alerting/minio-alerts.yml -- Alerts (C16, C20)
  monitoring/statsd/mappings.yml  -- StatsD to Prometheus mapping (C16)
  superset/superset_config.py     -- Superset config (C14)
  superset/bootstrap_dashboards.py -- Auto-provisioned dashboards (C14)
  .github/workflows/lint.yml      -- Linting CI (C6)
  .github/workflows/test.yml      -- Testing CI (C6)
  .github/workflows/docker.yml    -- Docker build CI (C6)
  .github/workflows/deploy-docs.yml -- Docs deployment (C7)
  tests/test_api_schemas.py       -- API schema tests
  tests/test_etl_functions.py     -- ETL function tests
  tests/test_sql_schemas.py       -- SQL schema tests
```

---

## 11. Open Questions for Team

1. Should the rapport_final.tex be split into separate documents per evaluation (E1.tex, E2.tex, etc.) or kept as one monolithic report?
   - Current approach: single report is simpler for cross-references.
   - Jury may expect separate booklets per evaluation.

2. The `defense_slides.tex` appears to be an older version. Should it be deleted or kept as backup?
   - Recommendation: keep as-is but mark `final_deck.tex` as the canonical slides.

3. Service count discrepancy: docker-compose.yml defines 18 service entries (including init containers). Should we count init containers? Current slides say "14 services" in some places.
   - Recommendation: say "14 persistent services" (excluding init containers and one-shot jobs).

4. The `presenter_en_francais.md` -- is a French translation needed for the defense? The instructions say English.
   - Clarify with team lead.
