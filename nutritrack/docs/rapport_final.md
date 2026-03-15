# NutriTrack - Comprehensive Final Report

**Certification**: Expert en infrastructures de donnees massives (Data Engineer) - RNCP37638 - Level 7
**Candidate**: [Candidate Name]
**Date**: March 2026
**Project**: NutriTrack - Fitness Nutrition Tracking Platform

---

## Table of Contents

1. [Executive Summary](#executive-summary)

**Block 1 - Steer a Data Project**
2. [Chapter 1 - Need Analysis & Interview Grids (E1 - C1)](#chapter-1---need-analysis--interview-grids)
3. [Chapter 2 - Data Topography, Architecture & Monitoring (E2 - C1-C4, C6)](#chapter-2---data-topography-architecture--monitoring)
4. [Chapter 3 - Project Planning & Communication (E3 - C5-C7)](#chapter-3---project-planning--communication)

**Block 2 - Data Collection, Storage & Sharing**
5. [Chapter 4 - Extraction Scripts (E4 - C8)](#chapter-4---extraction-scripts)
6. [Chapter 5 - SQL Queries (E4 - C9)](#chapter-5---sql-queries)
7. [Chapter 6 - Aggregation & Cleaning Pipeline (E4 - C10)](#chapter-6---aggregation--cleaning-pipeline)
8. [Chapter 7 - Database Modeling & RGPD (E4 - C11)](#chapter-7---database-modeling--rgpd)
9. [Chapter 8 - REST API (E4 - C12)](#chapter-8---rest-api)

**Block 3 - Data Warehouse**
10. [Chapter 9 - Star Schema Modeling (E5 - C13)](#chapter-9---star-schema-modeling)
11. [Chapter 10 - Data Warehouse Implementation (E5 - C14)](#chapter-10---data-warehouse-implementation)
12. [Chapter 11 - ETL Pipelines (E5 - C15)](#chapter-11---etl-pipelines)
13. [Chapter 12 - DW Maintenance & Monitoring (E6 - C16)](#chapter-12---dw-maintenance--monitoring)
14. [Chapter 13 - SCD Dimension Variations (E6 - C17)](#chapter-13---scd-dimension-variations)

**Block 4 - Data Lake**
15. [Chapter 14 - Data Lake Architecture (E7 - C18)](#chapter-14---data-lake-architecture)
16. [Chapter 15 - Infrastructure Components (E7 - C19)](#chapter-15---infrastructure-components)
17. [Chapter 16 - Data Catalog Management (E7 - C20)](#chapter-16---data-catalog-management)
18. [Chapter 17 - Data Governance (E7 - C21)](#chapter-17---data-governance)

**Conclusions**
19. [Chapter 18 - Demo Plan & Competency Verification Matrix](#chapter-18---demo-plan--competency-verification-matrix)
20. [Chapter 19 - Lessons Learned & Improvements](#chapter-19---lessons-learned--improvements)

---

## Executive Summary

NutriTrack is an end-to-end data engineering platform for fitness nutrition tracking built as a single project to demonstrate mastery of all 21 competencies (C1-C21) required for the RNCP37638 Data Engineer certification. The platform collects food product data from Open Food Facts, cleans and transforms it through automated ETL pipelines, stores it in a star-schema data warehouse, and exposes it through a REST API consumed by a Streamlit frontend. A MinIO-based data lake implements the medallion architecture (bronze/silver/gold) with full data governance and RGPD compliance.

**Key technical choices:**

- **PostgreSQL 16** for both operational (OLTP) and analytical (OLAP) workloads
- **Apache Airflow 2.8** for ETL orchestration with 6 DAGs
- **MinIO** as an S3-compatible data lake with medallion architecture
- **FastAPI** for an async REST API with JWT authentication
- **DuckDB** for big-data analytics on Parquet files (3M+ products)
- **Docker Compose** to orchestrate 10 services in a reproducible environment
- **Streamlit** for the user-facing frontend

**Infrastructure overview:**

```
                              +------------------+
                              |   Streamlit UI   |
                              |   (port 8501)    |
                              +--------+---------+
                                       |
                              +--------v---------+
                              |    FastAPI REST   |
                              |    (port 8000)    |
                              +--------+---------+
                                       |
              +------------------------+------------------------+
              |                        |                        |
    +---------v---------+   +----------v---------+   +----------v--------+
    |   PostgreSQL 16   |   |      Redis 7       |   |     MinIO         |
    | (port 5432)       |   |   (port 6379)      |   | (port 9000/9001)  |
    | - app schema      |   | - Cache            |   | - bronze bucket   |
    | - dw schema       |   | - Celery broker    |   | - silver bucket   |
    +-------------------+   +--------------------+   | - gold bucket     |
              ^                                      | - backups bucket  |
              |                                      +---------+---------+
    +---------+---------+                                      ^
    | Airflow 2.8       |                                      |
    | - Webserver (8080)|--------------------------------------+
    | - Scheduler       |
    | - Worker (Celery) |
    +-------------------+
```

The project addresses all 4 certification blocks across 7 evaluations (E1-E7), covering project management, data collection from 5 source types, SQL optimization, RGPD compliance, star-schema modeling, SCD procedures, and data lake governance.

---

# Block 1: Steer a Data Project

---

## Chapter 1 - Need Analysis & Interview Grids

*Evaluation E1 | Competency C1 | Deliverable: Interview grids*

### 1.1 Context and Business Need

NutriTrack addresses a growing demand for personalized nutrition tracking. The business need originates from three stakeholder groups: (1) end-users who want to track their food intake and receive healthier alternatives, (2) nutritionists who need aggregated dietary data for research and recommendations, and (3) administrators who manage the platform and ensure data quality.

The feasibility study identified Open Food Facts as the primary data source -- a collaborative, open-source database of food products with over 3 million entries, including Nutri-Score ratings and detailed nutritional values. This validated the technical hypothesis that a comprehensive product database could be built without proprietary data licensing.

### 1.2 Interview Grid: Data Producers

This grid targets stakeholders who produce or contribute data to the system.

| # | Question | Domain | Expected Answer Type |
|---|----------|--------|---------------------|
| 1 | What food product databases do you currently maintain or contribute to? | Business activity | Data source inventory |
| 2 | How frequently is product information updated (e.g., reformulations, new products)? | Data characterization | Update cadence (daily, weekly) |
| 3 | What metadata accompanies each product entry (barcode, brand, category, nutrition)? | Metadata | Field inventory |
| 4 | In what format is data stored or exported (JSON, CSV, Parquet, database dump)? | Storage format | Technical format list |
| 5 | What access methods are available (REST API, bulk export, database connection)? | Data access | Access protocol list |
| 6 | Are there rate limits or authentication requirements for API access? | Access constraints | Technical limits |
| 7 | What data quality issues have been observed (missing fields, inconsistencies)? | Data quality | Known defect categories |
| 8 | How are user contributions validated before publication? | Data governance | Validation process |
| 9 | Is there a data retention or archival policy? | Data lifecycle | Retention rules |
| 10 | Are there personal data elements in the food product data? | RGPD | Personal data identification |

### 1.3 Interview Grid: Data Consumers

This grid targets stakeholders who consume or will consume data from the system.

| # | Question | Domain | Expected Answer Type |
|---|----------|--------|---------------------|
| 1 | What nutritional analyses do you perform today, and what data is missing? | Business need | Gap analysis |
| 2 | How do you currently search for product information (barcode, name, category)? | Usage patterns | User journey |
| 3 | What level of nutritional detail do you need (macros only, or micronutrients)? | Data granularity | Requirements spec |
| 4 | Do you need historical data to track product reformulations over time? | Temporal analysis | Historization needs |
| 5 | What aggregation level is useful (per-product, per-brand, per-category)? | Analytical granularity | Aggregation spec |
| 6 | How should data be delivered (API, dashboard, export, embedded analytics)? | Data access | Delivery preference |
| 7 | What response time is acceptable for product searches and analytics? | Performance | SLA expectations |
| 8 | Do you need to track individual user meal data (with RGPD implications)? | RGPD | Consent requirements |
| 9 | What accessibility accommodations are needed for the interface? | Accessibility | WCAG requirements |
| 10 | Are there regulatory constraints on nutritional data display (EU Regulation 1169/2011)? | Regulatory | Compliance requirements |

### 1.4 Synthesis Note

**Need analysis:** The project addresses the need for a centralized platform that combines food product data from multiple sources (API, bulk exports, web scraping) with personal meal tracking, enabling users to make informed nutritional decisions.

**Functional scope:** Product search, meal logging, daily nutrition dashboards, weekly trend analysis, and healthier alternative suggestions.

**SMART objectives:**
- **S**: Build a nutrition tracking platform integrating data from 5 source types
- **M**: Process 100,000+ products with 95%+ data completeness on key nutritional fields
- **A**: Use open-source technologies within a Docker Compose environment
- **R**: Align with Open Food Facts data model and EU nutritional standards
- **T**: Deliver within a 3-month sprint cycle

**RGPD compliance actions:** Consent-based user registration, data retention limits, SHA256 pseudonymization in the warehouse, automated data cleanup via `rgpd_cleanup_expired_data()`.

---

## Chapter 2 - Data Topography, Architecture & Monitoring

*Evaluation E2 | Competencies C1, C2, C3, C4, C6 | Deliverable: Professional report*

### 2.1 Data Topography (C2)

The data topography is structured in the four required parts: semantics, data models, treatments and flows, and access conditions.

#### 2.1.1 Semantics - Business Glossary

| Business Object | Description | Key Metadata |
|----------------|-------------|--------------|
| **Product** | A food product identified by barcode | barcode, product_name, brand, category, nutrition per 100g, Nutri-Score (A-E), NOVA group (1-4), Eco-Score |
| **Brand** | A product manufacturer or distributor | brand_name, parent_company |
| **Category** | Hierarchical food classification | category_name, parent_category, level |
| **User** | An app user tracking their nutrition | user_id (UUID), email, username, role, dietary_goal, activity_level |
| **Meal** | A logged eating occasion | meal_type (breakfast/lunch/dinner/snack), meal_date, user_id |
| **Meal Item** | A single product within a meal | product_id, quantity_g, computed nutrition |
| **Nutritional Guideline** | Reference Daily Allowance values | nutrient, daily_value, unit, source (EU Regulation 1169/2011) |
| **Nutri-Score** | Nutritional quality grade (A best to E worst) | grade, score (-15 to +40), color_code |
| **NOVA Group** | Food processing classification (1 minimal to 4 ultra-processed) | group number, description |

#### 2.1.2 Data Models

| Data Type | Model | Storage Format |
|-----------|-------|---------------|
| **Structured** | Relational (PostgreSQL) | Products, users, meals, guidelines in normalized tables with foreign keys |
| **Semi-structured** | JSON | API responses, scraping results, data catalog metadata |
| **Unstructured** | Binary / columnar | Parquet files (3M+ products), compressed CSV exports |

#### 2.1.3 Treatments and Data Flows

**Flux Matrix:**

| Source | Format | Treatment | Target | Frequency |
|--------|--------|-----------|--------|-----------|
| OFF REST API | JSON | `extract_off_api.py` - Paginated extraction with rate limiting | `data/raw/api/` | Daily |
| OFF Parquet Export | Parquet | `extract_off_parquet.py` - DuckDB SQL queries | `data/raw/parquet/` | Weekly |
| ANSES/EFSA Websites | HTML | `extract_scraping.py` - BeautifulSoup scraping | `data/raw/scraping/` | Weekly |
| PostgreSQL (operational) | SQL | `extract_from_db.py` - Database query extraction | `data/raw/database/` | On-demand |
| DuckDB Analytics | Parquet | `extract_duckdb.py` - Analytical queries | `data/raw/duckdb/` | Weekly |
| All raw sources | Mixed | `aggregate_clean.py` - Merge, clean, deduplicate | `data/cleaned/` | Daily |
| Cleaned dataset | Parquet/CSV | `import_to_db.py` - Batch PostgreSQL upsert | `app` schema | Daily |
| Operational DB | SQL | `etl_load_warehouse.py` - Star schema ETL + SCD | `dw` schema | Daily |
| All layers | Mixed | `etl_datalake_ingest.py` - Medallion architecture | MinIO (bronze/silver/gold) | Daily |

**Data Flow Diagram:**

```
[Open Food Facts]          [ANSES/EFSA]        [OFF Parquet]
    |  REST API               |  Scraping          |  DuckDB
    v                         v                     v
+---+----+   +------+   +----+----+   +-------+   +-----+
|  API   |   | Scra |   | Parquet |   |DuckDB |   | DB  |
| Extract|   | ping |   | Extract |   |Extract|   |Extr.|
+---+----+   +--+---+   +----+----+   +---+---+   +--+--+
    |           |             |            |          |
    +-----+-----+------+------+------+-----+
          |                   |
    +-----v------+     +-----v-------+
    |  Aggregate |     |   Bronze    |
    |  & Clean   |     | (MinIO raw) |
    +-----+------+     +-----+-------+
          |                   |
    +-----v------+     +-----v-------+
    |  Import    |     |   Silver    |
    |  to DB     |     | (cleaned)   |
    +-----+------+     +-----+-------+
          |                   |
    +-----v------+     +-----v-------+
    |  Star      |     |   Gold      |
    |  Schema DW |     | (analytics) |
    +-----+------+     +-----+-------+
          |                   |
    +-----v------+     +-----v-------+
    |  Datamarts |     |   Catalog   |
    |  (views)   |     | (metadata)  |
    +------------+     +-------------+
```

#### 2.1.4 Data Access and Usage Conditions

| Role | Operational DB (app) | Data Warehouse (dw) | Data Lake (MinIO) |
|------|---------------------|--------------------|--------------------|
| **app_readonly** | SELECT on products, categories, brands, guidelines | No access | No access |
| **nutritionist_role** | SELECT on all tables except users | SELECT on analytical views (datamarts), dim_time, dim_nutriscore | Read silver, gold |
| **admin_role** | Full DML access | Full access | Full access to all buckets |
| **etl_service** | INSERT, UPDATE for data loading | SELECT, INSERT, UPDATE, DELETE for ETL | Write to all data buckets |
| **nutritrack (app)** | Full operational access | Full access | N/A |

### 2.2 Technical Architecture Study (C3)

#### 2.2.1 Functional Analysis

**What does the system do?**
- Collect food product data from 5 heterogeneous sources
- Clean, normalize, and deduplicate data into a unified dataset
- Store structured data in PostgreSQL (operational + warehouse)
- Expose data through a secured REST API
- Provide a user-facing nutrition tracking frontend
- Maintain a data lake with medallion architecture for analytics

**Business constraints:**
- Must handle 3M+ products from Open Food Facts
- Must comply with RGPD for user data
- Must provide sub-second response times for product searches
- Must support daily incremental data updates

#### 2.2.2 Non-Functional Needs

| Constraint | Requirement | Solution |
|-----------|-------------|----------|
| **Performance** | Product search < 1s | GIN index for full-text search, connection pooling (pool_size=10) |
| **Scalability** | Handle 3M+ products | DuckDB for in-memory analytics on Parquet files |
| **Reliability** | Zero data loss on pipeline failures | Airflow retries (2-3 attempts), extraction audit log |
| **Security** | No plaintext passwords, token-based auth | bcrypt hashing, JWT with HS256, role-based access |
| **Availability** | Service health monitoring | Docker healthchecks, Airflow web UI, /health endpoints |

#### 2.2.3 Architecture Representations

**Functional representation:** See the flux matrix in Section 2.1.3 above.

**Applicative representation (Docker Compose services):**

```
+--------------------------------------------------------------------+
|                    docker-compose.yml (10 services)                 |
|                                                                    |
|  +------------+  +---------+  +----------+                         |
|  | PostgreSQL |  |  Redis  |  |  MinIO   |                         |
|  |  16-alpine |  | 7-alpine|  | S3-compat|                         |
|  | :5432      |  | :6379   |  | :9000    |                         |
|  +-----+------+  +----+----+  | :9001    |                         |
|        |              |       +-----+----+                         |
|  +-----+--------------+------------+--+                            |
|  |                                    |                            |
|  |  +----------------------------+    |                            |
|  |  |     Airflow 2.8.1         |    |                            |
|  |  | +----------+ +----------+ |    |                            |
|  |  | | Webserver| | Scheduler| |    |                            |
|  |  | | :8080    | +----------+ |    |                            |
|  |  | +----------+ +--------+  |    |                            |
|  |  |              | Worker |  |    |                            |
|  |  |              | Celery |  |    |                            |
|  |  |              +--------+  |    |                            |
|  |  +----------------------------+    |                            |
|  |                                    |                            |
|  |  +-------------+  +-----------+    |                            |
|  |  |   FastAPI   |  | Streamlit |    |                            |
|  |  |   :8000     |  |  :8501    |    |                            |
|  |  +-------------+  +-----------+    |                            |
|  +------------------------------------+                            |
+--------------------------------------------------------------------+
  Volumes: postgres_data, redis_data, minio_data
```

**Infrastructure representation:**

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Container runtime | Docker Compose | v2 | Service orchestration |
| Database | PostgreSQL | 16-alpine | OLTP + OLAP storage |
| Cache / Queue | Redis | 7-alpine | Session cache + Celery broker |
| Object Storage | MinIO | latest | S3-compatible data lake |
| ETL Orchestration | Apache Airflow | 2.8.1 | DAG scheduling & execution |
| Python ETL | pandas, duckdb, requests, bs4 | Various | Data processing |
| REST API | FastAPI | 0.100+ | Async HTTP API |
| ORM | SQLAlchemy | 2.0 | Async database access |
| Frontend | Streamlit | 1.30+ | Interactive web UI |
| Auth | python-jose, passlib (bcrypt) | - | JWT + password hashing |
| Charts | Plotly | 5.x | Interactive visualizations |

#### 2.2.4 Architecture Decisions

| Decision | Chosen Option | Rationale |
|----------|--------------|-----------|
| Single vs. separate DBs for OLTP/OLAP | Single PostgreSQL instance with separate schemas (app, dw) | Simplifies deployment; adequate for current scale; can split later |
| ETL orchestrator | Apache Airflow | Industry standard, DAG-based, web UI for monitoring, Celery for parallel execution |
| Data lake storage | MinIO (S3-compatible) | Open-source, self-hosted, same API as AWS S3, easy Docker deployment |
| API framework | FastAPI (async) | Native async support, auto-generated OpenAPI docs, Pydantic validation |
| Big data querying | DuckDB | Reads Parquet directly without loading into memory, SQL interface, zero config |
| Authentication | JWT (HS256) + bcrypt | Stateless, scalable, standard for REST APIs |
| Bottom-up vs. top-down DW | Bottom-up (datamarts first) | Faster value delivery; build fact tables for known analyses, extend later |

#### 2.2.5 RGPD Compliance Processes

**Personal data registry** (from `app.rgpd_data_registry`):

| Data Category | Legal Basis | Retention | Security Measures |
|--------------|-------------|-----------|-------------------|
| User account data (email, username, hashed password) | Consent (Art. 6.1.a GDPR) | 3 years after last login | bcrypt password hashing, encrypted storage |
| User profile data (age group, activity level, dietary goal) | Consent (Art. 6.1.a GDPR) | 3 years or until consent withdrawal | Pseudonymized (SHA256) in analytics |
| Meal tracking data (meal logs, food consumption history) | Consent (Art. 6.1.a GDPR) | 2 years after creation | Associated with UUID, deletable on request |
| Product data (Open Food Facts) | Legitimate interest (Art. 6.1.f GDPR) | Indefinite (public data) | Public data, no personal information |

**Sorting/deletion procedures:**
- `rgpd_cleanup_expired_data()`: Automated PL/pgSQL function that deletes meal data older than 2 years and deactivates users past their retention date.
- Data lake lifecycle rules: Bronze data auto-expires after 90 days, backups after 30 days.

#### 2.2.6 Eco-Responsibility Strategy

Following the French RGESN framework (Referentiel general d'ecoconception de services numeriques):

1. **Efficient queries**: DuckDB processes 3M+ products in memory without full dataset loading; composite indexes reduce query scan volume.
2. **Minimal data transfers**: API pagination limits response size; only delta changes loaded in warehouse ETL.
3. **Data lifecycle management**: Bronze layer auto-expires at 90 days; old backups purged after 30 days.
4. **Lightweight containers**: Alpine-based Docker images (PostgreSQL, Redis) minimize resource usage.
5. **Batch processing**: All ETL runs during off-peak hours (02:00-06:00 UTC) to optimize infrastructure utilization.

### 2.3 Technical Monitoring (C4)

**Monitoring theme:** Apache Airflow - ETL orchestration monitoring and observability.

**Monitoring schedule:** Minimum 1 hour per week dedicated to reviewing DAG execution logs, pipeline health, and data quality metrics via the Airflow web interface (port 8080).

**Aggregation tools:**
- **Airflow Web UI**: DAG run history, task duration, success/failure rates, Gantt charts
- **extraction_log table**: Audit trail tracking records extracted, loaded, rejected per source
- **Cleaning report**: JSON report generated by `aggregate_clean.py` with completeness statistics per column

**Source reliability criteria:**
- Open Food Facts API: Verified by community of 30,000+ contributors; products validated before publication
- EU Regulation 1169/2011: Official EU legislative source for nutritional reference values
- ANSES: French national health authority with peer-reviewed nutritional reference values

**Monitoring communication:** DAG failure alerts sent via email to `admin@nutritrack.local`; Airflow is configured with `email_on_failure: True`.

### 2.4 Project Supervision (C6)

**Exchange facilitation:** The Makefile provides standardized commands for all team operations (`make pipeline`, `make backup`, `make test-api`), ensuring consistent execution across developers.

**Tracking tools:** Airflow web UI at port 8080 provides real-time DAG status, task logs, and historical run data. The `extraction_log` table tracks every data operation with timestamps, record counts, and error messages.

**Documented rituals:** Daily ETL runs are scheduled sequentially (02:00-06:00 UTC) with dependency chains. Weekly data quality reviews use the cleaning report.

**Indicators updated throughout project:**
- Records extracted/loaded/rejected per source (extraction_log)
- Data completeness percentage per column (cleaning_report.json)
- DAG success rate over time (Airflow metrics)

---

## Chapter 3 - Project Planning & Communication

*Evaluation E3 | Competencies C5, C6, C7 | Deliverable: Kickoff meeting simulation*

### 3.1 Team Composition and Skills (C5)

| Role | Required Skills | Tools |
|------|---------------|-------|
| **Data Engineer** (lead) | Python, SQL, Docker, Airflow, ETL design | VS Code, pgAdmin, Airflow UI |
| **Backend Developer** | FastAPI, SQLAlchemy, JWT authentication | Swagger UI, Postman |
| **Frontend Developer** | Streamlit, Plotly, UX design | Streamlit, Chrome DevTools |
| **DBA / Data Architect** | PostgreSQL, star schema, SCD, performance tuning | pgAdmin, EXPLAIN ANALYZE |
| **DevOps** | Docker Compose, MinIO, CI/CD | Docker, MinIO Console |

### 3.2 Project Roadmap

| Phase | Duration | Deliverables | Key Milestones |
|-------|----------|-------------|----------------|
| **Phase 1**: Planning & Design | 2 weeks | Interview grids, feasibility study, data topography, architecture study | Architecture validated |
| **Phase 2**: Data Collection | 3 weeks | 5 extraction scripts, SQL queries, aggregation/cleaning pipeline | Data pipeline operational |
| **Phase 3**: Database & API | 2 weeks | Operational DB (MCD/MLD/MPD), REST API with JWT, import scripts | API functional with docs |
| **Phase 4**: Data Warehouse | 2 weeks | Star schema, ETL DAGs, SCD procedures, datamarts | DW populated with data |
| **Phase 5**: Data Lake | 2 weeks | MinIO setup, medallion architecture, catalog, governance | Full lake operational |
| **Phase 6**: Frontend & Integration | 1 week | Streamlit app, end-to-end testing, demo preparation | Platform demo-ready |

### 3.3 Production Calendar

| Week | Tasks | Deliverable | Resources | Effort (Story Points) |
|------|-------|------------|-----------|----------------------|
| W1 | Interview grids, need analysis, feasibility study | E1 deliverables | Data Engineer | 8 |
| W2 | Data topography, architecture design | E2 data mapping | Data Engineer, DBA | 13 |
| W3 | REST API extraction, Parquet extraction, web scraping | 3 extraction scripts | Data Engineer | 8 |
| W4 | DB extraction, DuckDB analytics, aggregation pipeline | 2 scripts + cleaning | Data Engineer | 8 |
| W5 | SQL query optimization, import script | 7 queries + import | DBA, Data Engineer | 13 |
| W6 | Operational DB schema, RGPD registry | MCD/MLD/MPD | DBA | 8 |
| W7 | REST API development, JWT auth | API endpoints + docs | Backend Developer | 13 |
| W8 | Star schema design, dimension tables | DW schema | DBA | 8 |
| W9 | Warehouse ETL DAGs, SCD procedures | 6 Airflow DAGs | Data Engineer | 13 |
| W10 | MinIO setup, medallion architecture | Data lake | Data Engineer, DevOps | 8 |
| W11 | Data catalog, governance, access control | Catalog + policies | Data Engineer | 8 |
| W12 | Streamlit frontend, integration testing, demo | Working platform | Frontend Dev | 13 |

**Effort weighting method:** Fibonacci story points using team estimation (similar to poker planning). Points represent relative complexity, not hours.

### 3.4 Project Tracking Method

**Methodology:** Agile with 2-week sprints, Kanban board for task tracking.

**Tools:**
- **Git**: Version control for all code, SQL, and configuration
- **Airflow UI**: DAG execution monitoring and scheduling
- **Makefile**: Standardized developer commands
- **Docker Compose**: Reproducible environment management

**Rituals:**
- Sprint planning (every 2 weeks): Define sprint goals and select backlog items
- Daily standup (15 min): Blockers, progress, plan for the day
- Sprint review: Demo completed features to stakeholders
- Sprint retrospective: Identify process improvements

### 3.5 Communication Strategy (C7)

| Communication | Audience | Format | Frequency | Content |
|--------------|----------|--------|-----------|---------|
| **Sprint kickoff** | All stakeholders | Presentation | Every 2 weeks | Sprint goals, planned features |
| **Progress update** | Project sponsor | Email summary | Weekly | Milestones reached, blockers, metrics |
| **Technical demo** | Dev team + nutritionists | Live demo | End of each phase | Working features, data quality stats |
| **API documentation** | Developers, consumers | OpenAPI/Swagger | Continuous | Endpoint specs, auth rules |
| **User documentation** | End users | Help pages in Streamlit | At delivery | How to search, log meals, read charts |
| **Final delivery** | Jury, stakeholders | Oral presentation + report | End of project | Full platform demo, architecture review |

**Chosen orientations and trade-offs communicated:**
- Single PostgreSQL instance for OLTP+OLAP (simplicity vs. optimal separation)
- MinIO instead of AWS S3 (cost and self-hosting vs. managed service)
- DuckDB for big data analytics (simplicity vs. Spark cluster)
- Bottom-up DW approach (faster value delivery vs. comprehensive top-down design)

**User documentation tasks:** Planned in Phase 6 (W12), distributed to the frontend developer. End-user onboarding session planned as part of the final demo.

**Feedback collection:** Post-demo questionnaire integrated into communication strategy, collecting user satisfaction and feature requests.

---

# Block 2: Data Collection, Storage & Sharing

---

## Chapter 4 - Extraction Scripts

*Evaluation E4 | Competency C8 | 5 extraction scripts from diverse sources*

All extraction scripts follow a consistent structure: entry point (`main()`), dependency initialization, external connection setup, business logic rules, error handling, and result saving. All scripts are versioned on Git.

### 4.1 Source 1: REST API Extraction

**File:** `scripts/extract_off_api.py`
**Source type:** REST API
**Target:** Open Food Facts search API (`https://world.openfoodfacts.org/cgi/search.pl`)

```python
OFF_API_BASE = "https://world.openfoodfacts.org"
OFF_API_SEARCH = f"{OFF_API_BASE}/cgi/search.pl"
USER_AGENT = "NutriTrack/1.0 (https://github.com/nutritrack; contact@nutritrack.local)"

def search_products(query: str, page: int = 1, page_size: int = 50) -> list[dict]:
    """Search products by query string with pagination."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": ",".join(PRODUCT_FIELDS),
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(
            OFF_API_SEARCH, params=params, headers=headers, timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])
    except requests.RequestException as e:
        logger.error("Error searching products for '%s': %s", query, e)
        return []

def extract_products_by_category(
    category: str, max_pages: int = 10, page_size: int = 50
) -> list[dict]:
    """Extract all products in a category with pagination and rate limiting."""
    all_products = []
    for page in range(1, max_pages + 1):
        products = search_products(category, page=page, page_size=page_size)
        if not products:
            break
        all_products.extend(products)
        time.sleep(0.6)  # Rate limiting: max ~100 req/min
    return all_products
```

**Key features:**
- Entry point: `main()` with argparse (modes: barcode, search, category)
- Dependency initialization: `requests`, `json`, `logging`
- External connection: HTTP GET to OFF API with User-Agent header
- Logic rules: 5 categories x 5 pages x 50 items = up to 1,250 products per run
- Error handling: `try/except RequestException`, timeout (30-60s), graceful fallback
- Result saving: JSON with metadata (extraction_date, source, record_count)

### 4.2 Source 2: Data File (Parquet) with DuckDB

**File:** `scripts/extract_off_parquet.py`
**Source type:** Data file + Big data system
**Target:** Open Food Facts Parquet export (3M+ products)

```python
def extract_with_duckdb(
    data_path: Path,
    countries_filter: str = "France",
    limit: int | None = None,
) -> pd.DataFrame:
    con = duckdb.connect()
    query = f"""
    SELECT
        code AS barcode, product_name, generic_name,
        "energy-kcal_100g" AS energy_kcal,
        fat_100g AS fat_g, proteins_100g AS proteins_g,
        nutriscore_grade, nutriscore_score, nova_group,
        completeness AS completeness_score
    FROM read_parquet('{data_path}')
    WHERE code IS NOT NULL
      AND product_name IS NOT NULL
      AND LENGTH(code) >= 8
      AND countries LIKE '%{countries_filter}%'
    ORDER BY completeness DESC
    """
    df = con.execute(query).fetchdf()
    con.close()
    return df
```

**Key features:**
- DuckDB reads Parquet files directly without loading into memory
- SQL-based filtering on 3M+ products executes in seconds
- Field mapping from OFF schema to internal schema
- Output: Parquet + CSV formats

### 4.3 Source 3: Web Scraping

**File:** `scripts/extract_scraping.py`
**Source type:** Web scraping (HTML)
**Target:** ANSES (French health authority) and EFSA nutritional reference values

```python
def scrape_anses_guidelines(url: str) -> list[dict]:
    soup = fetch_page(url)
    if not soup:
        logger.warning("Could not fetch ANSES page, using fallback data")
        return []
    tables = soup.find_all("table")
    guidelines = []
    for table in tables:
        rows = table.find_all("tr")
        for row_idx, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            if row_idx > 0 and len(cell_texts) >= 2:
                guidelines.append({
                    "nutrient": cell_texts[0],
                    "daily_value": cell_texts[1],
                    "unit": cell_texts[2] if len(cell_texts) > 2 else "",
                    "source": "ANSES",
                })
    return guidelines
```

**Key features:**
- BeautifulSoup with `lxml` parser for HTML table extraction
- Graceful fallback to EU Regulation 1169/2011 hardcoded RDA values (25 nutrients)
- Numeric value parsing handling ranges ("10-15" -> midpoint), prefixes ("<", ">"), and locales
- Polite crawling with `time.sleep(1)` between requests

### 4.4 Source 4: Database Extraction

**File:** `scripts/extract_from_db.py`
**Source type:** PostgreSQL database
**Target:** Operational database (app schema)

This script extracts product data with brand and category joins from the PostgreSQL operational database, outputting to Parquet and CSV for further processing.

### 4.5 Source 5: Big Data System (DuckDB Analytics)

**File:** `scripts/extract_duckdb.py`
**Source type:** Analytical engine on large datasets
**Target:** DuckDB in-memory analytics on the full OFF Parquet dataset

This script performs complex analytical queries on the 3M+ product dataset, including Nutri-Score distribution by country using `UNNEST` on comma-separated country fields, and outputs aggregated results for the gold layer.

### 4.6 Airflow DAG Orchestration

Each extraction script has a corresponding Airflow DAG for automated scheduling:

| DAG | Schedule | Script | Description |
|-----|----------|--------|-------------|
| `etl_extract_off_api` | Daily 02:00 UTC | `extract_off_api.py` | REST API extraction |
| `etl_extract_parquet` | Weekly Sun 01:00 | `extract_off_parquet.py` | Parquet/DuckDB extraction |
| `etl_extract_scraping` | Weekly Mon 03:00 | `extract_scraping.py` | Web scraping |
| `etl_aggregate_clean` | Daily 04:00 UTC | `aggregate_clean.py` | Aggregation & cleaning |
| `etl_load_warehouse` | Daily 05:00 UTC | (inline SQL) | Star schema loading |
| `etl_datalake_ingest` | Daily 06:00 UTC | (inline) | Medallion data lake |

---

## Chapter 5 - SQL Queries

*Evaluation E4 | Competency C9 | SQL extraction queries with optimization notes*

**File:** `sql/queries/analytical_queries.sql` (7 queries)

### 5.1 Query 1: Daily Nutrition Summary per User with RDA%

```sql
SELECT
    u.username,
    m.meal_date,
    COUNT(DISTINCT m.meal_id) AS meals_count,
    SUM(mi.energy_kcal) AS total_kcal,
    SUM(mi.proteins_g) AS total_proteins_g,
    SUM(mi.fiber_g) AS total_fiber_g,
    ROUND(SUM(mi.energy_kcal) / 2000.0 * 100, 1) AS pct_rda_energy,
    ROUND(SUM(mi.proteins_g) / 50.0 * 100, 1) AS pct_rda_proteins
FROM app.users u
JOIN app.meals m ON u.user_id = m.user_id
JOIN app.meal_items mi ON m.meal_id = mi.meal_id
WHERE m.meal_date = CURRENT_DATE AND u.is_active = TRUE
GROUP BY u.username, m.meal_date
ORDER BY total_kcal DESC;
```

**Optimization:** Composite index `idx_meals_user_date` on `(user_id, meal_date)` enables fast lookup. Aggregate pushdown reduces rows before final sort.

### 5.2 Query 2: Full-Text Product Search with Nutri-Score Filter

```sql
SELECT
    p.barcode, p.product_name, b.brand_name, c.category_name,
    p.nutriscore_grade, p.energy_kcal,
    ts_rank(to_tsvector('french', p.product_name),
            plainto_tsquery('french', 'chocolat noir')) AS relevance
FROM app.products p
LEFT JOIN app.brands b ON p.brand_id = b.brand_id
LEFT JOIN app.categories c ON p.category_id = c.category_id
WHERE to_tsvector('french', p.product_name)
      @@ plainto_tsquery('french', 'chocolat noir')
  AND p.nutriscore_grade IN ('A', 'B', 'C')
ORDER BY relevance DESC, p.nutriscore_grade ASC
LIMIT 20;
```

**Optimization:** GIN index `idx_products_name` on `to_tsvector('french', product_name)` enables sub-second full-text search across 100,000+ products. LEFT JOINs allow products without brand/category to appear in results.

### 5.3 Query 3: Healthier Alternatives (Window Function)

```sql
WITH product_ranking AS (
    SELECT
        p.product_id, p.barcode, p.product_name, b.brand_name,
        p.nutriscore_grade, p.nutriscore_score,
        ROW_NUMBER() OVER (
            PARTITION BY p.category_id
            ORDER BY p.nutriscore_score ASC, p.nova_group ASC
        ) AS rank_in_category
    FROM app.products p
    LEFT JOIN app.brands b ON p.brand_id = b.brand_id
    WHERE p.category_id = (
        SELECT category_id FROM app.products WHERE barcode = '3017620422003'
    )
    AND p.nutriscore_score IS NOT NULL
)
SELECT * FROM product_ranking WHERE rank_in_category <= 5;
```

**Optimization:** Window function `ROW_NUMBER() OVER (PARTITION BY category_id)` avoids an expensive self-join. The subquery on barcode uses the unique index for constant-time lookup.

### 5.4 Query 4: Weekly Trends with Moving Average

```sql
WITH daily_totals AS (
    SELECT m.meal_date, SUM(mi.energy_kcal) AS daily_kcal,
           SUM(mi.proteins_g) AS daily_proteins
    FROM app.meals m
    JOIN app.meal_items mi ON m.meal_id = mi.meal_id
    WHERE m.user_id = '...'::UUID
      AND m.meal_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY m.meal_date
)
SELECT meal_date, daily_kcal,
    ROUND(AVG(daily_kcal) OVER (
        ORDER BY meal_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) AS moving_avg_kcal_7d,
    daily_kcal - LAG(daily_kcal) OVER (ORDER BY meal_date) AS kcal_change,
    ROUND(daily_proteins * 4 / NULLIF(daily_kcal, 0) * 100, 1) AS protein_pct
FROM daily_totals ORDER BY meal_date;
```

**Optimization:** Window functions `AVG() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` and `LAG()` avoid multiple self-joins. `NULLIF` prevents division by zero.

### 5.5 Query 5: Nutri-Score Distribution (Warehouse)

Uses pre-aggregated fact table `dw.fact_product_market` with `SUM(COUNT(*)) OVER (PARTITION BY category_name)` for percentage calculations. Joins through star schema dimensions.

### 5.6 Query 6: Brand Quality with NOVA Analysis

Uses CTE with `HAVING COUNT(*) >= 10` to filter statistically significant brands. `PERCENTILE_CONT(0.5)` computes median energy per 100g. `CASE WHEN` aggregation counts good (A/B) vs. poor (D/E) products.

### 5.7 Query 7: User Meal Pattern Analysis

Uses `STDDEV(f.energy_kcal)` to measure caloric intake variability. Groups by `user_hash` (pseudonymized), `dietary_goal`, `day_name`, and `meal_type` for behavioral analysis.

---

## Chapter 6 - Aggregation & Cleaning Pipeline

*Evaluation E4 | Competency C10 | Data aggregation from different sources*

**File:** `scripts/aggregate_clean.py`

### 6.1 Pipeline Overview

The cleaning pipeline aggregates data from all 5 sources, removes corruption, and homogenizes formats into a single clean dataset.

```
[API JSON] + [Parquet] + [DuckDB] + [DB Export]
                    |
            Standardize Columns (30+ mappings)
                    |
            Clean Barcodes (trim, validate 8-14 digits)
                    |
            Clean Text (normalize whitespace, remove control chars)
                    |
            Remove entries without product_name
                    |
            Convert kJ -> kcal where kcal is missing
                    |
            Validate Numeric Ranges (energy <= 1000, fats <= 100, etc.)
                    |
            Normalize Nutri-Score (A-E only)
                    |
            Validate NOVA Group (1-4 only)
                    |
            Deduplicate by barcode (keep most complete)
                    |
        [products_cleaned.parquet + .csv + cleaning_report.json]
```

### 6.2 Key Cleaning Functions

**Column standardization** (30+ mappings):

```python
STANDARD_COLUMNS = {
    "code": "barcode",
    "energy-kcal_100g": "energy_kcal",
    "fat_100g": "fat_g",
    "saturated-fat_100g": "saturated_fat_g",
    "carbohydrates_100g": "carbohydrates_g",
    "proteins_100g": "proteins_g",
    "completeness": "completeness_score",
    # ... 30+ more mappings
}
```

**Barcode validation:**

```python
def clean_barcode(barcode) -> str | None:
    if pd.isna(barcode):
        return None
    barcode = str(barcode).strip()
    barcode = re.sub(r"[^0-9]", "", barcode)  # Remove non-numeric
    if len(barcode) < 8 or len(barcode) > 14:
        return None
    return barcode
```

**Numeric range validation:**

```python
numeric_ranges = {
    "energy_kcal": (0, 1000),   # kcal per 100g cannot exceed 1000
    "fat_g": (0, 100),           # grams per 100g cannot exceed 100
    "carbohydrates_g": (0, 100),
    "proteins_g": (0, 100),
    "salt_g": (0, 100),
}
```

**Deduplication:** Sort by `completeness_score` descending, then `drop_duplicates(subset=["barcode"], keep="first")` to retain the most complete version of each product.

### 6.3 Quality Report

The pipeline generates a JSON cleaning report with:
- Initial vs. final record counts
- Removal rate percentage
- Per-column completeness statistics (non-null count and percentage)

---

## Chapter 7 - Database Modeling & RGPD

*Evaluation E4 | Competency C11 | RGPD-compliant database creation*

### 7.1 Conceptual Model (MCD)

```
+----------+       +----------+       +------------+
| BRAND    |1    N | PRODUCT  |N    1 | CATEGORY   |
|----------|-------+----------|-------+------------|
| brand_id |       | barcode  |       | category_id|
| name     |       | name     |       | name       |
| parent   |       | nutrition|       | parent_id  |
+----------+       | scores   |       | level      |
                   +----+-----+       +------------+
                        |N
                        |
                   +----+-----+
                   | MEAL_ITEM|
                   |----------|
                   | quantity |
                   | nutrition|
                   +----+-----+
                        |N
                   +----+-----+       +-----------+
                   |   MEAL   |N    1 |   USER    |
                   |----------|-------+-----------|
                   | meal_type|       | user_id   |
                   | date     |       | email     |
                   | notes    |       | username  |
                   +----------+       | role      |
                                      | consent   |
                                      +-----------+
```

### 7.2 Logical Model (MLD)

- **brands** (brand_id PK, brand_name UNIQUE, parent_company)
- **categories** (category_id PK, category_name UNIQUE, parent_category_id FK -> categories)
- **products** (product_id PK, barcode UNIQUE, product_name, brand_id FK, category_id FK, energy_kcal, fat_g, carbohydrates_g, proteins_g, fiber_g, salt_g, nutriscore_grade, nova_group, completeness_score)
- **users** (user_id PK UUID, email UNIQUE, password_hash, username UNIQUE, role, consent_data_processing, consent_date, data_retention_until)
- **meals** (meal_id PK, user_id FK -> users ON DELETE CASCADE, meal_type, meal_date)
- **meal_items** (meal_item_id PK, meal_id FK -> meals ON DELETE CASCADE, product_id FK -> products, quantity_g, energy_kcal, fat_g, carbohydrates_g, proteins_g)

### 7.3 Physical Model (MPD)

**File:** `sql/init/01_schema_operational.sql` (279 lines)

Key physical design choices:
- **UUID** for user_id (anonymization-friendly, RGPD-compliant)
- **GIN index** on `to_tsvector('french', product_name)` for full-text search
- **Composite index** on `(user_id, meal_date)` for fast meal queries
- **CHECK constraints** on role, activity_level, dietary_goal, nova_group
- **CASCADE deletes** from users -> meals -> meal_items

**Trigger for computed nutrition:**

```sql
CREATE OR REPLACE FUNCTION app.compute_meal_item_nutrition()
RETURNS TRIGGER AS $$
BEGIN
    SELECT
        ROUND((p.energy_kcal * NEW.quantity_g / 100), 2),
        ROUND((p.fat_g * NEW.quantity_g / 100), 2),
        ROUND((p.carbohydrates_g * NEW.quantity_g / 100), 2),
        ROUND((p.proteins_g * NEW.quantity_g / 100), 2)
    INTO NEW.energy_kcal, NEW.fat_g, NEW.carbohydrates_g, NEW.proteins_g
    FROM app.products p
    WHERE p.product_id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 7.4 RGPD Personal Data Treatment Registry

The `app.rgpd_data_registry` table stores the complete RGPD registry:

```sql
INSERT INTO app.rgpd_data_registry
  (data_category, data_description, legal_basis, retention_period,
   data_subjects, processing_purpose, recipients, security_measures)
VALUES
('User account data',
 'Email, username, hashed password',
 'Consent (Art. 6.1.a GDPR)',
 '3 years after last login',
 'App users',
 'User authentication and account management',
 'NutriTrack application',
 'Password hashing (bcrypt), encrypted storage'),
-- ... (4 entries total)
```

**Automated RGPD cleanup:**

```sql
CREATE OR REPLACE FUNCTION app.rgpd_cleanup_expired_data()
RETURNS INTEGER AS $$
BEGIN
    DELETE FROM app.meal_items
    WHERE meal_id IN (
        SELECT meal_id FROM app.meals
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '2 years'
    );
    DELETE FROM app.meals
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '2 years';
    UPDATE app.users
    SET is_active = FALSE
    WHERE data_retention_until < CURRENT_DATE AND is_active = TRUE;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

### 7.5 Import Script

**File:** `scripts/import_to_db.py`

The import script performs batch upsert operations with `ON CONFLICT (barcode) DO UPDATE`, preserving existing data where the new record has NULL values:

```sql
INSERT INTO app.products (barcode, product_name, energy_kcal, ...)
VALUES (:barcode, :product_name, :energy_kcal, ...)
ON CONFLICT (barcode) DO UPDATE SET
    product_name = EXCLUDED.product_name,
    energy_kcal = COALESCE(EXCLUDED.energy_kcal, app.products.energy_kcal),
    nutriscore_grade = COALESCE(EXCLUDED.nutriscore_grade, app.products.nutriscore_grade),
    completeness_score = GREATEST(EXCLUDED.completeness_score, app.products.completeness_score),
    updated_at = CURRENT_TIMESTAMP
```

Batch size: 5,000 records per transaction for optimal throughput.

---

## Chapter 8 - REST API

*Evaluation E4 | Competency C12 | REST API documentation*

**File:** `api/main.py`, `api/routers/auth.py`, `api/routers/products.py`, `api/routers/meals.py`

### 8.1 API Endpoint Documentation

| Method | Endpoint | Auth | Description | Request | Response |
|--------|----------|------|-------------|---------|----------|
| `POST` | `/api/v1/auth/register` | None | Create user account | `UserCreate` (email, username, password, consent) | `UserOut` (201) |
| `POST` | `/api/v1/auth/login` | None | Authenticate user | `LoginRequest` (username, password) | `Token` (access_token) |
| `GET` | `/api/v1/auth/me` | Bearer | Get current user profile | - | `UserOut` |
| `GET` | `/api/v1/products/{barcode}` | Bearer | Get product by barcode | - | `ProductOut` |
| `GET` | `/api/v1/products/?q=...` | Bearer | Search products | q, nutriscore, nova_group, page, page_size | `ProductSearchResult` |
| `GET` | `/api/v1/products/{barcode}/alternatives` | Bearer | Find healthier alternatives | limit | `list[ProductAlternative]` |
| `POST` | `/api/v1/meals/` | Bearer | Log a meal | `MealCreate` (meal_type, items[]) | `MealOut` (201) |
| `GET` | `/api/v1/meals/` | Bearer | List user's meals | meal_date, meal_type, page | `list[MealOut]` |
| `GET` | `/api/v1/meals/daily-summary` | Bearer | Daily nutrition summary | target_date | `DailyNutritionSummary` |
| `GET` | `/api/v1/meals/weekly-trends` | Bearer | Weekly nutrition trends | weeks (1-12) | `WeeklyTrend` |
| `GET` | `/api/v1/health` | None | Health check | - | `{"status": "healthy"}` |
| `GET` | `/docs` | None | Swagger UI | - | Interactive API docs |
| `GET` | `/redoc` | None | ReDoc | - | API documentation |

### 8.2 Authentication & Authorization (JWT)

**File:** `api/auth/jwt.py`

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def require_role(*roles: str):
    """Dependency that checks if the current user has one of the required roles."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized.",
            )
        return current_user
    return role_checker
```

**Auth/authz rules:**
- All product and meal endpoints require a valid Bearer token
- Token contains `sub` (user_id) and `role` claims
- `require_role()` decorator enforces role-based access control (RBAC)
- Roles: `user`, `nutritionist`, `admin`
- Account deactivation check: inactive accounts are rejected at login
- Password hashing: bcrypt (passlib)
- Token expiry: configurable (default 60 minutes)

### 8.3 OpenAPI Standards

The API auto-generates OpenAPI 3.0 documentation at:
- `/docs` - Swagger UI (interactive testing)
- `/redoc` - ReDoc (readable documentation)
- `/api/v1/openapi.json` - Machine-readable schema

All endpoints use Pydantic schemas for request/response validation, ensuring type safety and auto-documentation.

---

# Block 3: Data Warehouse

---

## Chapter 9 - Star Schema Modeling

*Evaluation E5 | Competency C13 | Data warehouse structure modeling*

### 9.1 Data Needed for Analyses

| Analysis | Required Data | Source |
|----------|--------------|--------|
| User daily nutrition tracking | User profile, meal items, product nutrition, date | app.users, app.meals, app.meal_items, app.products |
| Nutri-Score distribution by category | Product scores, category hierarchy | app.products, app.categories |
| Brand quality ranking | Products per brand, nutriscore/nova scores | app.products, app.brands |
| Product reformulation history | Product name, ingredients, scores over time | app.products (SCD Type 2) |
| Country market analysis | Products per country, scores, nutrition | app.products (countries field) |

### 9.2 Modeling Approach: Bottom-Up

**Justification:** The bottom-up approach (Kimball methodology) was chosen because:
1. Specific analytical questions were identified upfront (nutrition tracking, product comparison)
2. Faster time-to-value: datamarts deliver usable analytics from day one
3. The operational schema is well-defined, making dimensional extraction straightforward
4. Additional datamarts can be added incrementally without restructuring

### 9.3 Star Schema Diagram

```
                           +----------------+
                           |   dim_time     |
                           |----------------|
                           | time_key (PK)  |
                           | full_date      |
                           | day_of_week    |
                           | month, quarter |
                           | year           |
                           | is_weekend     |
                           +-------+--------+
                                   |
+----------------+    +------------+------------+    +----------------+
|  dim_brand     |    | fact_daily_nutrition     |    |  dim_user      |
|----------------|    |--------------------------|    |----------------|
| brand_key (PK) +--->| daily_nutrition_id (PK)  |<---+ user_key (PK)  |
| brand_name     |    | user_key (FK)            |    | user_hash      |
| parent_company |    | time_key (FK)            |    | age_group      |
| last_updated   |    | product_key (FK)         |    | activity_level |
| [SCD Type 1]   |    | category_key (FK)        |    | dietary_goal   |
+----------------+    | brand_key (FK)           |    | [SCD Type 2]   |
                      | meal_type                |    +----------------+
                      | quantity_g               |
                      | energy_kcal              |
+----------------+    | fat_g, proteins_g        |    +----------------+
| dim_category   |    | carbohydrates_g, fiber_g |    | dim_nutriscore |
|----------------|    | salt_g                   |    |----------------|
| category_key   +--->| nutriscore_score         |    | nutriscore_key |
| category_name  |    | nova_group               |    | grade (A-E)    |
| parent_category|    +--------------------------+    | description    |
| category_level |                                    | color_code     |
+----------------+    +---------------------------+   | score_range    |
                      | fact_product_market        |   +----------------+
+----------------+    |---------------------------|
| dim_product    |    | product_market_id (PK)    |   +----------------+
|----------------|    | product_key (FK)           |   | dim_country    |
| product_key    +--->| brand_key (FK)            |   |----------------|
| barcode        |    | category_key (FK)          |<--+ country_key    |
| product_name   |    | country_key (FK)           |   | country_name   |
| ingredients    |    | time_key (FK)              |   | country_code   |
| completeness   |    | nutriscore_grade/score     |   | region         |
| [SCD Type 2]   |    | nova_group, ecoscore_grade |   | [SCD Type 3]   |
+----------------+    | energy_kcal_per_100g       |   +----------------+
                      | fat, sugars, salt, fiber   |
                      | proteins_per_100g          |
                      +----------------------------+
```

### 9.4 Dimension Tables

| Dimension | Type | SCD | Row Count | Description |
|-----------|------|-----|-----------|-------------|
| **dim_time** | Conformed | N/A | ~4,018 (2020-2030) | Pre-populated date dimension |
| **dim_product** | Regular | Type 2 | Grows with products + versions | Product attributes with history |
| **dim_brand** | Regular | Type 1 | Grows with brands | Brand info (overwrite corrections) |
| **dim_category** | Hierarchical | None | Grows with categories | Category hierarchy |
| **dim_country** | Regular | Type 3 | Small reference set | Country info with expansion tracking |
| **dim_user** | Regular | Type 2 | Grows with users + profile changes | Anonymized (SHA256) user profiles |
| **dim_nutriscore** | Reference | None | 5 (A-E) | Static Nutri-Score reference |

### 9.5 Fact Tables

| Fact Table | Grain | Dimensions | Measures |
|-----------|-------|------------|----------|
| **fact_daily_nutrition** | One row per user + day + product + meal_type | dim_user, dim_time, dim_product, dim_category, dim_brand | quantity_g, energy_kcal, fat_g, carbohydrates_g, proteins_g, fiber_g, salt_g, nutriscore_score, nova_group |
| **fact_product_market** | One row per product + time snapshot | dim_product, dim_brand, dim_category, dim_country, dim_time | nutriscore_grade/score, nova_group, ecoscore_grade, completeness, energy/fat/sugars/salt/fiber/proteins per 100g |

---

## Chapter 10 - Data Warehouse Implementation

*Evaluation E5 | Competency C14 | DW creation and configuration*

### 10.1 DW Implementation

**File:** `sql/init/02_schema_warehouse.sql` (360 lines)

The data warehouse is implemented as a separate schema (`dw`) within the same PostgreSQL 16 instance, created automatically during Docker Compose initialization via the SQL init scripts mounted to `/docker-entrypoint-initdb.d/`.

**Main configurations:**
- Schema isolation: `app` (operational) vs. `dw` (analytical)
- Separate indexes optimized for analytical queries (e.g., `idx_fact_nutrition_user_time`)
- Pre-populated dim_time using `generate_series('2020-01-01', '2030-12-31', '1 day')`
- Partial indexes on `is_current = TRUE` for SCD Type 2 dimensions

### 10.2 Source Data Access Configuration

Source data access is configured through environment variables in Docker Compose, shared between the Airflow DAGs and the PostgreSQL instance:

```yaml
# docker-compose.yml (Airflow environment)
NUTRITRACK_DB_HOST: postgres
NUTRITRACK_DB_PORT: "5432"
NUTRITRACK_DB_NAME: nutritrack
NUTRITRACK_DB_USER: nutritrack
NUTRITRACK_DB_PASSWORD: nutritrack
```

The ETL DAGs construct the connection URL dynamically:

```python
def _get_db_engine():
    db_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('NUTRITRACK_DB_USER', 'nutritrack')}:"
        f"{os.getenv('NUTRITRACK_DB_PASSWORD', 'nutritrack')}@"
        f"{os.getenv('NUTRITRACK_DB_HOST', 'postgres')}:"
        f"{os.getenv('NUTRITRACK_DB_PORT', '5432')}/"
        f"{os.getenv('NUTRITRACK_DB_NAME', 'nutritrack')}"
    )
    return create_engine(db_url)
```

### 10.3 Analyst Access to DW/Datamarts

Three analytical views (datamarts) are created for analyst access:

```sql
-- Datamart: User daily nutrition summary
CREATE OR REPLACE VIEW dw.dm_user_daily_nutrition AS
SELECT u.user_hash, u.age_group, u.dietary_goal,
       t.full_date, f.meal_type,
       SUM(f.energy_kcal) AS total_kcal,
       SUM(f.proteins_g) AS total_proteins_g,
       AVG(f.nutriscore_score) AS avg_nutriscore
FROM dw.fact_daily_nutrition f
JOIN dw.dim_user u ON f.user_key = u.user_key AND u.is_current = TRUE
JOIN dw.dim_time t ON f.time_key = t.time_key
GROUP BY u.user_hash, u.age_group, u.dietary_goal,
         t.full_date, f.meal_type;

-- Datamart: Product market by category
CREATE OR REPLACE VIEW dw.dm_product_market_by_category AS ...

-- Datamart: Brand quality ranking
CREATE OR REPLACE VIEW dw.dm_brand_quality_ranking AS ...
```

Access grants are differentiated by role:

```sql
-- nutritionist_role: read analytical views only (no raw fact/dimension access)
GRANT SELECT ON dw.dm_user_daily_nutrition,
                dw.dm_product_market_by_category,
                dw.dm_brand_quality_ranking TO nutritionist_role;
GRANT SELECT ON dw.dim_time, dw.dim_nutriscore TO nutritionist_role;

-- etl_service: write access for ETL loading
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dw TO etl_service;
```

### 10.4 Test Procedure

| Test | Scope | Verification |
|------|-------|-------------|
| Schema creation | Technical | All tables, indexes, views created without errors |
| Dimension population | Functional | dim_time has 4,018 rows (2020-2030); dim_nutriscore has 5 rows (A-E) |
| SCD Type 2 | Functional | Product update creates new row with `is_current=TRUE`, closes old with `end_date` |
| SCD Type 1 | Functional | Brand correction overwrites in place, updates `last_updated` |
| Fact loading | Functional | Facts reference valid dimension keys; no orphan foreign keys |
| Datamart views | Functional | Views return aggregated results; nutritionist_role can SELECT |
| Access control | Security | `app_readonly` cannot access `dw` schema; `etl_service` can INSERT |

### 10.5 Tech Stack Feedback

| Technology | Coherence with Project | Advantages | Difficulties |
|-----------|----------------------|------------|--------------|
| PostgreSQL (dual OLTP/OLAP) | Good for small-to-medium scale | Single instance simplifies deployment | Would need separation at larger scale |
| Airflow for ETL | Industry standard for batch ETL | Web UI, retries, dependency management | Complex setup (Celery, Redis, init containers) |
| SQL-based ETL (no Spark) | Appropriate for current data volume | Simple, debuggable, no additional cluster | Limited parallel processing |
| Schema isolation (app/dw) | Clean separation of concerns | No cross-contamination of operational/analytical | Requires cross-schema queries in ETL |

---

## Chapter 11 - ETL Pipelines

*Evaluation E5 | Competency C15 | ETL for data warehouse input/output*

### 11.1 ETL Overview

**File:** `airflow/dags/etl_load_warehouse.py` (297 lines)

The warehouse ETL DAG (`etl_load_warehouse`) runs daily at 05:00 UTC with 6 tasks organized in a dependency chain: dimensions load first (in parallel), then facts load after all dimensions are ready.

```
[load_dim_brands] ----+
[load_dim_categories] -+----> [load_fact_product_market]
[load_dim_products] ---+----> [load_fact_daily_nutrition]
[load_dim_users] ------+
```

### 11.2 Data Formats and Volumes

| Source | Format | Estimated Volume | Target |
|--------|--------|-----------------|--------|
| app.brands | SQL rows | ~5,000 unique brands | dw.dim_brand |
| app.categories | SQL rows | ~2,000 categories | dw.dim_category |
| app.products | SQL rows | ~100,000 products | dw.dim_product |
| app.users | SQL rows | ~1,000 users | dw.dim_user (anonymized) |
| app.meals + meal_items | SQL rows | ~10,000 daily records | dw.fact_daily_nutrition |
| Cross-dimensional | SQL joins | ~100,000 product snapshots | dw.fact_product_market |

### 11.3 Dimension Loading with SCD

**Task: load_dim_brands (SCD Type 1)**

```python
def load_dim_brands(**context):
    """Load brand dimension with SCD Type 1 (overwrite on correction)."""
    with engine.begin() as conn:
        # Insert new brands
        conn.execute(text("""
            INSERT INTO dw.dim_brand (brand_name, parent_company)
            SELECT DISTINCT b.brand_name, b.parent_company
            FROM app.brands b
            LEFT JOIN dw.dim_brand db ON b.brand_name = db.brand_name
            WHERE db.brand_key IS NULL
        """))
        # SCD Type 1: update changed brands
        conn.execute(text("""
            UPDATE dw.dim_brand db
            SET parent_company = b.parent_company,
                last_updated = CURRENT_TIMESTAMP
            FROM app.brands b
            WHERE db.brand_name = b.brand_name
              AND db.parent_company IS DISTINCT FROM b.parent_company
        """))
```

**Task: load_dim_products (SCD Type 2)**

```python
def load_dim_products(**context):
    with engine.begin() as conn:
        # Insert new products
        conn.execute(text("""
            INSERT INTO dw.dim_product (barcode, product_name, ...)
            SELECT p.barcode, p.product_name, ...
            FROM app.products p
            LEFT JOIN dw.dim_product dp ON p.barcode = dp.barcode
                AND dp.is_current = TRUE
            WHERE dp.product_key IS NULL
        """))
        # Detect changes -> close old records
        conn.execute(text("""
            UPDATE dw.dim_product dp
            SET end_date = CURRENT_DATE - 1, is_current = FALSE
            FROM app.products p
            WHERE dp.barcode = p.barcode AND dp.is_current = TRUE
              AND (p.product_name IS DISTINCT FROM dp.product_name
                OR p.ingredients_text IS DISTINCT FROM dp.ingredients_text)
        """))
        # Insert new current versions for changed products
        ...
```

**Task: load_dim_users (Anonymized, SCD Type 2)**

```python
# SHA256 pseudonymization for RGPD compliance
conn.execute(text("""
    INSERT INTO dw.dim_user (user_hash, age_group, activity_level, ...)
    SELECT
        encode(digest(u.user_id::text, 'sha256'), 'hex') AS user_hash,
        u.age_group, u.activity_level, u.dietary_goal, u.created_at::date
    FROM app.users u
    LEFT JOIN dw.dim_user du
        ON encode(digest(u.user_id::text, 'sha256'), 'hex') = du.user_hash
        AND du.is_current = TRUE
    WHERE du.user_key IS NULL AND u.is_active = TRUE
"""))
```

### 11.4 Fact Loading

**Task: load_fact_daily_nutrition**

Loads yesterday's meal data with joins through 5 dimensions:

```python
conn.execute(text("""
    INSERT INTO dw.fact_daily_nutrition (
        user_key, time_key, product_key, category_key, brand_key,
        meal_type, quantity_g, energy_kcal, fat_g, proteins_g, ...)
    SELECT
        du.user_key,
        TO_CHAR(m.meal_date, 'YYYYMMDD')::INTEGER AS time_key,
        dp.product_key, dc.category_key, db.brand_key,
        m.meal_type, mi.quantity_g, mi.energy_kcal, ...
    FROM app.meal_items mi
    JOIN app.meals m ON mi.meal_id = m.meal_id
    JOIN app.products p ON mi.product_id = p.product_id
    JOIN dw.dim_user du ON encode(digest(m.user_id::text, 'sha256'), 'hex')
        = du.user_hash AND du.is_current = TRUE
    JOIN dw.dim_product dp ON p.barcode = dp.barcode AND dp.is_current = TRUE
    LEFT JOIN dw.dim_brand db ON b.brand_name = db.brand_name
    LEFT JOIN dw.dim_category dc ON c.category_name = dc.category_name
    WHERE m.meal_date = CURRENT_DATE - 1
      AND NOT EXISTS (
          SELECT 1 FROM dw.fact_daily_nutrition fdn
          WHERE fdn.user_key = du.user_key
            AND fdn.time_key = TO_CHAR(m.meal_date, 'YYYYMMDD')::INTEGER
            AND fdn.product_key = dp.product_key
      )
"""))
```

### 11.5 Output Formats

| Output | Format | Consumer |
|--------|--------|----------|
| dw.fact_daily_nutrition | SQL table | Datamart views (dm_user_daily_nutrition) |
| dw.fact_product_market | SQL table | Datamart views (dm_product_market_by_category, dm_brand_quality_ranking) |
| gold/analytics/*.parquet | Parquet files | Data lake gold layer |
| gold/analytics/*.csv | CSV files | External consumers, Excel users |

---

## Chapter 12 - DW Maintenance & Monitoring

*Evaluation E6 | Competency C16 | DW administration and supervision*

### 12.1 Activity Logging

The `app.extraction_log` table tracks all data operations:

```sql
CREATE TABLE app.extraction_log (
    log_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    records_extracted INTEGER,
    records_loaded INTEGER,
    records_rejected INTEGER,
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

**Alert categories:**
- `running`: Operation in progress
- `completed`: Successful completion with record counts
- `failed`: Error occurred (error_message populated)

### 12.2 Alert System

Airflow DAGs are configured with email alerts on failure:

```python
default_args = {
    "email_on_failure": True,
    "email": ["admin@nutritrack.local"],
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
```

When a task fails after 2 retries, an email notification is sent to `admin@nutritrack.local` with the task name, error message, and execution timestamp.

### 12.3 Backup Procedures

**File:** `scripts/backup_database.py`

**Full backup:**
```bash
make backup  # Full database backup (app + dw schemas)
```

**Partial backup (DW only):**
```bash
make backup-dw  # Data warehouse schema only
```

The backup script:
1. Runs `pg_dump` with `--format=custom --compress=6`
2. Optionally uploads to MinIO backups bucket (`backups/YYYY/MM/DD/`)
3. Cleans up local backups older than 7 days

```python
def run_pg_dump(backup_type: str = "full", schemas: list[str] | None = None) -> Path:
    cmd = [
        "pg_dump", "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME,
        "--format=custom", "--compress=6", f"--file={backup_path}",
    ]
    if schemas:
        for schema in schemas:
            cmd.extend(["--schema", schema])
    result = subprocess.run(cmd, env=env, capture_output=True, timeout=300)
    ...
```

### 12.4 Service Level Indicators

| Indicator | Target | Measurement |
|-----------|--------|-------------|
| ETL pipeline success rate | > 95% | Airflow DAG run history |
| Daily data freshness | Data < 24h old | Last successful run timestamp |
| Warehouse query response time | < 5 seconds | EXPLAIN ANALYZE on datamart views |
| Backup success rate | 100% | Backup log entries |
| Data completeness | > 80% on key fields | Cleaning report statistics |

### 12.5 Documentation: New Source Integration

To add a new data source to the warehouse:
1. Create extraction script in `scripts/` following the C8 pattern
2. Create an Airflow DAG in `airflow/dags/` with appropriate schedule
3. Add column mappings to `STANDARD_COLUMNS` in `aggregate_clean.py`
4. Add dimension mappings in `etl_load_warehouse.py` tasks
5. Update `etl_datalake_ingest.py` bronze ingestion for the new source
6. Update data catalog metadata

### 12.6 Documentation: New Access Creation

To grant access to a new analyst:
1. Create a PostgreSQL role and assign the appropriate group role:
   ```sql
   CREATE ROLE new_analyst WITH LOGIN PASSWORD '...';
   GRANT nutritionist_role TO new_analyst;
   ```
2. For data lake access, assign the MinIO policy matching their group (e.g., `nutritionists` -> readonly on silver/gold)
3. Update the groups and rights documentation

### 12.7 RGPD Compliance (Maintenance)

The RGPD personal data registry is maintained in `app.rgpd_data_registry`. The automated cleanup function `rgpd_cleanup_expired_data()` runs periodically to enforce retention policies.

### 12.8 Maintenance Task Prioritization (ITIL-Aligned)

Maintenance tasks are classified using a four-tier priority matrix inspired by ITIL v4 incident management practices. Each priority level defines a maximum response time, resolution target, and escalation path.

#### Priority Matrix

| Priority | Severity | Response Time | Resolution Target | Examples |
|----------|----------|---------------|-------------------|----------|
| **P1 - Critical** | Service down or data loss risk | < 1 hour | < 4 hours | ETL pipeline failure blocking all downstream analytics; database corruption; backup system failure; security breach |
| **P2 - High** | Major degradation, no workaround | < 4 hours | < 8 hours | SLA breach (ETL success < 95%); data freshness > 24h; single DAG repeated failure; MinIO storage > 90% |
| **P3 - Medium** | Partial impact, workaround exists | < 24 hours | < 3 business days | Non-critical DAG failure with manual fallback; slow query performance (> 5s); Grafana dashboard errors; minor data quality issues |
| **P4 - Low** | Cosmetic or improvement request | Next sprint | Next release | Documentation updates; dashboard cosmetic changes; new datamart view requests; dependency version upgrades |

#### Assignment Rules

1. **P1 incidents** are assigned to the on-call data engineer immediately. If unresolved within 2 hours, escalate to the project lead.
2. **P2 incidents** are assigned during business hours to the data engineer responsible for the affected component. Escalation to project lead after 4 hours.
3. **P3 incidents** are triaged in the daily standup and assigned to the next available engineer.
4. **P4 requests** are added to the sprint backlog and prioritized during sprint planning.

#### Escalation Procedures

| Escalation Level | Trigger | Action |
|-------------------|---------|--------|
| **L1 - Engineer** | Initial assignment | Investigate, diagnose, apply fix |
| **L2 - Senior Engineer** | L1 unable to resolve within response time | Deep investigation, architecture review |
| **L3 - Project Lead** | P1 unresolved > 2h or P2 unresolved > 4h | Coordinate cross-team response, stakeholder communication |

#### Tracking

All maintenance tasks are tracked via:
- **Airflow UI**: DAG run history, task logs, and SLA monitoring
- **Grafana SLA Dashboard**: Real-time service level compliance (`monitoring/grafana/dashboards/sla-compliance.json`)
- **`app.etl_activity_log` table**: Structured logging with alert categories (CRITICAL, WARNING, INFO)
- **MailHog Web UI** (port 8025): Email alert verification during development

### 12.9 SLA Dashboard

A dedicated Grafana dashboard (`NutriTrack SLA Compliance`) provides real-time visibility into all service level indicators:

| Panel | Metric | SLA Target | Source |
|-------|--------|------------|--------|
| Overall SLA Compliance | Weighted composite score | > 95% | All indicators below |
| ETL Success Rate | DAG run success / total | > 95% | `airflow_dagrun_duration_*` |
| Data Freshness | Hours since last successful ETL | < 24h | `airflow_dagrun_start_timestamp` |
| Backup Completion | Backup task success rate (7d) | 100% | `airflow_ti_successes` |
| Query Response Time | Max transaction duration | < 5s | `pg_stat_activity_max_tx_duration` |
| Storage Usage | Database size as % of capacity | < 85% | `pg_database_size_bytes` |

The dashboard also includes 7-day trend charts for ETL success rate and DAG run outcomes, enabling proactive identification of degrading performance before SLA breaches occur.

---

## Chapter 13 - SCD Dimension Variations

*Evaluation E6 | Competency C17 | Kimball SCD Type 1, 2, 3*

**File:** `sql/scd_procedures.sql` (140 lines)

### 13.1 SCD Type 1: Overwrite (Brand Corrections)

**Use case:** A brand name has a typo that needs correction (e.g., "Dannon" -> "Danone"). The correction overwrites the old value everywhere.

```sql
CREATE OR REPLACE FUNCTION dw.scd_type1_update_brand(
    p_brand_key INTEGER,
    p_new_brand_name VARCHAR(255)
) RETURNS VOID AS $$
BEGIN
    UPDATE dw.dim_brand
    SET brand_name = p_new_brand_name,
        last_updated = CURRENT_TIMESTAMP
    WHERE brand_key = p_brand_key;
END;
$$ LANGUAGE plpgsql;
```

**Batch corrections:**

```sql
CREATE OR REPLACE FUNCTION dw.scd_type1_batch_brand_corrections(
    p_corrections JSONB
) RETURNS INTEGER AS $$
DECLARE
    correction RECORD;
    update_count INTEGER := 0;
BEGIN
    FOR correction IN
        SELECT * FROM jsonb_to_recordset(p_corrections)
        AS x(brand_key INTEGER, new_brand_name VARCHAR(255))
    LOOP
        PERFORM dw.scd_type1_update_brand(correction.brand_key,
                                           correction.new_brand_name);
        update_count := update_count + 1;
    END LOOP;
    RETURN update_count;
END;
$$ LANGUAGE plpgsql;
```

**Impact:** No history preserved. Suitable for corrections where the old value was wrong.

### 13.2 SCD Type 2: Historical Tracking (Product Reformulations)

**Use case:** A product is reformulated (ingredients change, Nutri-Score changes from D to B). Both the old and new versions must be preserved with effective dates.

```sql
CREATE OR REPLACE FUNCTION dw.scd_type2_update_product(
    p_barcode VARCHAR(20),
    p_product_name VARCHAR(500),
    p_ingredients_text TEXT,
    p_completeness_score NUMERIC(5,2),
    p_source_product_id INTEGER
) RETURNS VOID AS $$
BEGIN
    -- Close the current record
    UPDATE dw.dim_product
    SET end_date = CURRENT_DATE - 1,
        is_current = FALSE
    WHERE barcode = p_barcode AND is_current = TRUE;

    -- Insert new current record
    INSERT INTO dw.dim_product (
        barcode, product_name, ingredients_text, completeness_score,
        effective_date, end_date, is_current, source_product_id
    ) VALUES (
        p_barcode, p_product_name, p_ingredients_text,
        p_completeness_score, CURRENT_DATE, '9999-12-31',
        TRUE, p_source_product_id
    );
END;
$$ LANGUAGE plpgsql;
```

**Automated change detection:**

```sql
CREATE OR REPLACE FUNCTION dw.scd_type2_check_and_update_products()
RETURNS TABLE(barcode VARCHAR, change_type TEXT) AS $$
BEGIN
    FOR src IN SELECT ... FROM app.products p LOOP
        SELECT * INTO existing FROM dw.dim_product dp
        WHERE dp.barcode = src.barcode AND dp.is_current = TRUE;

        IF NOT FOUND THEN
            INSERT INTO dw.dim_product (...) VALUES (...);
            change_type := 'NEW'; RETURN NEXT;
        ELSIF existing.product_name IS DISTINCT FROM src.product_name
           OR existing.ingredients_text IS DISTINCT FROM src.ingredients_text
        THEN
            PERFORM dw.scd_type2_update_product(...);
            change_type := 'UPDATED'; RETURN NEXT;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

**History view:**

```sql
CREATE OR REPLACE VIEW dw.v_product_history AS
SELECT barcode, product_name, effective_date, end_date, is_current,
       CASE WHEN is_current THEN 'Current version'
            ELSE 'Historical version (ended ' || end_date::TEXT || ')'
       END AS version_status
FROM dw.dim_product
ORDER BY barcode, effective_date DESC;
```

### 13.3 SCD Type 3: Add Column (Country Expansion)

**Use case:** A product previously sold only in "France" now expands to "France, Belgium, Luxembourg". The previous value is stored in an adjacent column.

```sql
CREATE OR REPLACE FUNCTION dw.scd_type3_update_country(
    p_country_key INTEGER,
    p_new_country_name VARCHAR(100)
) RETURNS VOID AS $$
BEGIN
    UPDATE dw.dim_country
    SET previous_country_list = country_name,
        country_name = p_new_country_name
    WHERE country_key = p_country_key;
END;
$$ LANGUAGE plpgsql;
```

**dim_country table structure:**

```sql
CREATE TABLE dw.dim_country (
    country_key SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10),
    region VARCHAR(100),
    continent VARCHAR(50),
    previous_country_list VARCHAR(500),  -- SCD Type 3 column
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 13.4 SCD Integration into ETL

The `etl_load_warehouse.py` DAG integrates SCD processing in the dimension loading tasks:
- `load_dim_brands`: Applies SCD Type 1 (overwrite parent_company changes)
- `load_dim_products`: Applies SCD Type 2 (close old records, insert new current versions)
- `load_dim_users`: Applies SCD Type 2 (track profile changes with SHA256 hashing)

### 13.5 Updated Logical and Physical Models

After SCD integration:
- `dim_product`: Added `effective_date`, `end_date`, `is_current` (SCD Type 2)
- `dim_brand`: Added `last_updated` (SCD Type 1 tracking)
- `dim_country`: Added `previous_country_list` (SCD Type 3)
- `dim_user`: Added `effective_date`, `end_date`, `is_current` (SCD Type 2)

---

# Block 4: Data Lake

---

## Chapter 14 - Data Lake Architecture

*Evaluation E7 | Competency C18 | Data lake architecture design*

### 14.1 Technical Proposal

The data lake uses MinIO, an S3-compatible object storage system, implementing a medallion architecture (bronze/silver/gold) to address volume, velocity, and variety constraints.

**Coherence with exploitation framework:**
- MinIO's S3 API is compatible with the broader AWS ecosystem, enabling future migration
- Parquet format provides efficient columnar storage for analytical queries
- Medallion pattern separates raw ingestion from curated analytics

### 14.2 Architecture Schema (Volume / Velocity / Variety)

```
+-------------------------------------------------------------+
|                    NutriTrack Data Lake                      |
|                       (MinIO S3)                             |
|                                                              |
|  +------------------+  +------------------+  +-----------+   |
|  |     BRONZE       |  |      SILVER      |  |   GOLD    |   |
|  |  (Raw Data)      |  |  (Cleaned)       |  | (Analyt.) |   |
|  |                  |  |                  |  |           |   |
|  | api/             |  | products/        |  | analytics/|   |
|  |  {ds}/           |  |  {ds}/           |  |  {ds}/    |   |
|  |   *.json         |  |   products_      |  |  nutri-   |   |
|  |                  |  |   cleaned.parquet|  |  score_   |   |
|  | parquet/         |  |                  |  |  dist.    |   |
|  |  {ds}/           |  | _reports/        |  |  parquet  |   |
|  |   *.parquet      |  |  cleaning_       |  |           |   |
|  |                  |  |  report.json     |  |  category |   |
|  | scraping/        |  |                  |  |  _stats.  |   |
|  |  {ds}/           |  +------------------+  |  parquet  |   |
|  |   *.json         |                        |           |   |
|  |                  |                        |  brand_   |   |
|  | duckdb/          |                        |  ranking. |   |
|  |  {ds}/           |                        |  parquet  |   |
|  |   *.parquet      |                        +-----------+   |
|  |                  |                                        |
|  | _manifests/      |         _catalog/                      |
|  |  {ds}.json       |         metadata.json                  |
|  +------------------+         (in all buckets)               |
|                                                              |
|  +------------------+                                        |
|  |     BACKUPS      |  Retention:                            |
|  | YYYY/MM/DD/      |  - Bronze: 90 days                    |
|  |  nutritrack_     |  - Silver: 1 year                     |
|  |  *.sql.gz        |  - Gold: indefinite                   |
|  +------------------+  - Backups: 30 days                   |
+-------------------------------------------------------------+
```

**Addressing the 3 V's:**

| V | Challenge | Solution |
|---|-----------|----------|
| **Volume** | 3M+ products in OFF dataset (~5 GB Parquet) | DuckDB reads Parquet without memory loading; MinIO scales to petabytes |
| **Variety** | JSON (API, scraping), Parquet, CSV, SQL | Bronze stores raw formats as-is; Silver normalizes to unified Parquet |
| **Velocity** | Daily incremental updates from API; weekly bulk updates | Airflow DAGs run on schedule; bronze preserves each day's snapshot by `{ds}/` partitioning |

### 14.3 Catalog Tool Comparison

| Criteria | Apache Atlas | DataHub | Custom JSON Catalog |
|----------|-------------|---------|-------------------|
| **Complexity** | High (Hadoop ecosystem) | Medium (standalone) | Low |
| **Setup time** | Days | Hours | Minutes |
| **Integration** | Deep Hadoop integration | REST API, plugins | MinIO-native storage |
| **Features** | Full lineage, governance | Search, lineage, profiling | Schema, lineage, access docs |
| **Resource cost** | High (JVM-based) | Medium | Minimal |
| **RGPD features** | Tag-based classification | Policies and tags | Manual registry |
| **Exploitability** | Requires dedicated admin | Self-service | Developer-maintained |

**Selection: Custom JSON Catalog** - Chosen for its minimal overhead, direct MinIO integration, and sufficiency for the project's scale. The metadata is stored as `_catalog/metadata.json` in each bucket, updated daily by the ETL pipeline.

---

## Chapter 15 - Infrastructure Components

*Evaluation E7 | Competency C19 | Infrastructure installation and configuration*

### 15.1 Storage System Installation

**MinIO installation** (via Docker Compose):

```yaml
minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin123
  ports:
    - "9000:9000"   # S3 API
    - "9001:9001"   # Web Console
  volumes:
    - minio_data:/data
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
```

**Bucket initialization** (via `minio-init` service):

```yaml
minio-init:
  image: minio/mc:latest
  entrypoint: >
    /bin/sh -c "
    mc alias set local http://minio:9000 minioadmin minioadmin123;
    mc mb --ignore-existing local/bronze;
    mc mb --ignore-existing local/silver;
    mc mb --ignore-existing local/gold;
    mc mb --ignore-existing local/backups;
    mc anonymous set download local/gold;
    echo 'MinIO buckets created successfully';
    "
```

### 15.2 MinIO Setup Script

**File:** `scripts/setup_minio.py`

```python
BUCKETS = {
    "bronze": "Raw data layer - as-is from sources",
    "silver": "Cleaned and validated data layer",
    "gold": "Analytics-ready, aggregated data layer",
    "backups": "Database backups and system snapshots",
}

def create_buckets(client: Minio):
    for bucket, description in BUCKETS.items():
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

def setup_lifecycle_rules(client: Minio):
    bronze_config = LifecycleConfig([
        Rule(ENABLED, rule_filter=Filter(prefix="api/"),
             expiration=Expiration(days=90),
             rule_id="expire-api-raw-90d"),
        Rule(ENABLED, rule_filter=Filter(prefix="scraping/"),
             expiration=Expiration(days=90),
             rule_id="expire-scraping-raw-90d"),
    ])
    client.set_bucket_lifecycle("bronze", bronze_config)
```

### 15.3 Batch Tool: Airflow Warehouse ETL

The Airflow `etl_load_warehouse` DAG (detailed in Chapter 11) serves as the batch processing tool, running daily at 05:00 UTC to load data from the operational database into the star-schema warehouse.

### 15.4 Real-Time-Like Tool: Airflow Data Lake Ingest

The Airflow `etl_datalake_ingest` DAG runs daily at 06:00 UTC, processing the medallion pipeline (bronze -> silver -> gold -> catalog). While not truly real-time, the daily schedule provides near-real-time data freshness for analytics.

### 15.5 Installation Procedure Testing

The entire infrastructure is testable in a development environment using Docker Compose:

```bash
# Full platform startup
docker compose up -d

# Verify all services are healthy
docker compose ps

# Expected output: 10 services running
# postgres, redis, minio, minio-init (exited), airflow-init (exited),
# airflow-webserver, airflow-scheduler, airflow-worker, fastapi, streamlit
```

**Makefile commands for testing:**

```makefile
make up           # Start all services
make logs         # View all service logs
make test-api     # Test API endpoints with curl
make setup-lake   # Initialize MinIO buckets
make lake-status  # Check storage status
make pipeline     # Run full extraction -> clean -> import
```

### 15.6 Documentation Summary

| Component | Installation | Configuration | Access |
|-----------|-------------|---------------|--------|
| **MinIO** | Docker image `minio/minio:latest` | `server /data --console-address ":9001"` | API: localhost:9000, Console: localhost:9001 |
| **Airflow** | Docker image `apache/airflow:2.8.1` | CeleryExecutor, Redis broker, PostgreSQL backend | Web UI: localhost:8080 (admin/admin) |
| **PostgreSQL** | Docker image `postgres:16-alpine` | Init scripts in `/docker-entrypoint-initdb.d/` | localhost:5432 (nutritrack/nutritrack) |

---

## Chapter 16 - Data Catalog Management

*Evaluation E7 | Competency C20 | Data catalog management*

### 16.1 Feed Method Selection

| Data Source | Feed Method | Justification |
|-------------|------------|---------------|
| OFF REST API | Daily pull via `etl_extract_off_api` DAG | API provides incremental updates; daily frequency matches API rate limits |
| OFF Parquet Export | Weekly pull via `etl_extract_parquet` DAG | Bulk export updated weekly; DuckDB enables efficient filtering |
| ANSES/EFSA Scraping | Weekly pull via `etl_extract_scraping` DAG | Reference values change infrequently; weekly is sufficient |
| Database Export | On-demand via script | Used for ad-hoc analysis; not scheduled |
| DuckDB Analytics | Weekly via `etl_extract_parquet` DAG | Analytical queries run on same schedule as source data refresh |

### 16.2 Feed Scripts and Data Import

All feed scripts are documented in Chapter 4 (C8). Each produces output files that flow through the medallion architecture:

```python
# Bronze ingestion (from etl_datalake_ingest.py)
def ingest_to_bronze(**context):
    client = _get_minio_client()
    ds = context["ds"]
    # Upload raw files with date partitioning
    for f in api_dir.glob("*.json"):
        client.fput_object("bronze", f"api/{ds}/{f.name}", str(f))
    for f in parquet_dir.glob("*.parquet"):
        client.fput_object("bronze", f"parquet/{ds}/{f.name}", str(f))
    # Write manifest
    manifest = {"ingestion_date": ds, "files_ingested": ingested}
    client.put_object("bronze", f"_manifests/{ds}.json", ...)
```

### 16.3 Catalog Metadata

The data catalog is stored as `_catalog/metadata.json` in each MinIO bucket:

```python
def update_catalog_metadata(**context):
    catalog = {
        "last_updated": ds,
        "datasets": {
            "bronze/api": {
                "description": "Raw product data from Open Food Facts REST API",
                "format": "JSON",
                "update_frequency": "daily",
                "source": "Open Food Facts API",
                "schema": "OFF product schema (barcode, product_name, nutrition, scores)",
                "owner": "etl_service",
                "quality": "raw, unvalidated",
            },
            "silver/products": {
                "description": "Cleaned, deduplicated product dataset",
                "format": "Parquet, CSV",
                "update_frequency": "daily",
                "lineage": ["bronze/api", "bronze/parquet", "bronze/duckdb"],
            },
            "gold/analytics": {
                "description": "Analytics-ready aggregated datasets",
                "datasets": ["nutriscore_distribution", "category_stats", "brand_ranking"],
                "lineage": ["silver/products", "dw.fact_product_market"],
            },
        },
        "governance": {
            "rgpd_compliance": True,
            "retention_policy": {
                "bronze": "90 days",
                "silver": "1 year",
                "gold": "indefinite",
            },
            "access_groups": {
                "app_users": ["gold/analytics (read)"],
                "nutritionists": ["silver/products (read)", "gold/analytics (read)"],
                "admins": ["all buckets (full)"],
                "etl_service": ["all buckets (write)"],
            },
        },
    }
    # Store in each bucket
    for bucket in ["bronze", "silver", "gold"]:
        client.put_object(bucket, "_catalog/metadata.json", ...)
```

### 16.4 Update and Deletion Procedures

**Lifecycle-based deletion:**
- Bronze `api/` and `scraping/` data auto-expires after 90 days
- Backup `daily/` data auto-expires after 30 days
- Silver and gold data are retained longer (1 year and indefinite respectively)

**Manual deletion procedure:**
1. Identify the dataset and date range to delete
2. Use `mc rm --recursive local/{bucket}/{prefix}/{date_range}/`
3. Update the catalog metadata to reflect the deletion
4. Log the deletion in the governance audit trail

### 16.5 Storage Monitoring

**File:** `scripts/setup_minio.py`

```python
def check_storage_status(client: Minio):
    for bucket in BUCKETS:
        if client.bucket_exists(bucket):
            objects = list(client.list_objects(bucket, recursive=True))
            total_size = sum(obj.size for obj in objects if obj.size)
            logger.info("  %s: %d objects, %.2f MB",
                        bucket, len(objects), total_size / (1024 * 1024))
```

Run via: `make lake-status`

Monitors:
- Available space per bucket
- Object count and total size
- Server health (MinIO healthcheck endpoint)

---

## Chapter 17 - Data Governance

*Evaluation E7 | Competency C21 | Data governance rules*

### 17.1 Role-Based Access Control

**File:** `sql/init/00_init_databases.sql`

PostgreSQL roles are created with principle of least privilege:

```sql
-- Group roles (not login-capable)
CREATE ROLE app_readonly WITH NOLOGIN;
CREATE ROLE nutritionist_role WITH NOLOGIN;
CREATE ROLE admin_role WITH NOLOGIN;

-- Service roles (login-capable)
CREATE ROLE nutritrack WITH LOGIN PASSWORD 'nutritrack';
CREATE ROLE etl_service WITH LOGIN PASSWORD 'etl_service';
```

**Access matrix (PostgreSQL):**

| Role | app.products | app.users | dw.fact_* | dw.dm_* views | dw.dim_* |
|------|-------------|-----------|-----------|---------------|----------|
| app_readonly | SELECT | - | - | - | - |
| nutritionist_role | SELECT | - (REVOKED) | - | SELECT | SELECT (time, nutriscore) |
| admin_role | ALL | ALL | ALL | ALL | ALL |
| etl_service | SELECT, INSERT, UPDATE | SELECT, INSERT, UPDATE | ALL | SELECT | ALL |
| nutritrack | ALL | ALL | ALL | ALL | ALL |

### 17.2 Data Lake Access Groups

**File:** `scripts/setup_minio.py`

```python
GROUP_POLICIES = {
    "app_users": {
        "description": "End-users: read-only access to gold analytics",
        "buckets": {"gold": "readonly"},
    },
    "nutritionists": {
        "description": "Nutritionists: read access to silver and gold",
        "buckets": {"silver": "readonly", "gold": "readonly"},
    },
    "admins": {
        "description": "Administrators: full access to all buckets",
        "buckets": {"bronze": "readwrite", "silver": "readwrite",
                    "gold": "readwrite", "backups": "readwrite"},
    },
    "etl_service": {
        "description": "ETL pipeline: write access to all data buckets",
        "buckets": {"bronze": "readwrite", "silver": "readwrite",
                    "gold": "readwrite"},
    },
}
```

**Policy enforcement:**
- Rights applied to groups (not individuals) when possible
- Access limited to necessary resources per group
- Gold bucket has public read for anonymous analytics consumption
- No personal data exists in the data lake (user data stays in PostgreSQL only)

### 17.3 API-Level Access Control

```python
# JWT-based authentication (api/auth/jwt.py)
def require_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized.",
            )
        return current_user
    return role_checker
```

| API Endpoint | Required Auth | Required Role |
|-------------|--------------|---------------|
| `POST /auth/register` | None | None |
| `POST /auth/login` | None | None |
| `GET /products/*` | Bearer token | Any authenticated user |
| `POST /meals/` | Bearer token | Any authenticated user |
| `GET /meals/*` | Bearer token | User sees only their own data |

### 17.4 RGPD Compliance in Governance

| Requirement | Implementation |
|-------------|---------------|
| Personal data minimization | Only email, username, hashed password stored; profile data optional with consent |
| Pseudonymization | User IDs hashed with SHA256 in warehouse (dim_user.user_hash) |
| Right to deletion | CASCADE deletes from users -> meals -> meal_items; `rgpd_cleanup_expired_data()` |
| Consent tracking | `consent_data_processing`, `consent_date`, `data_retention_until` in users table |
| Data registry | `app.rgpd_data_registry` table with legal basis, retention period, security measures |
| No personal data in lake | Data lake contains only product data (public) and anonymized aggregations |

### 17.5 Groups and Rights Documentation

| Group | PostgreSQL Role | MinIO Policy | API Role | Description |
|-------|---------------|--------------|----------|-------------|
| **End Users** | app_readonly | gold: readonly | `user` | Search products, log meals, view personal dashboards |
| **Nutritionists** | nutritionist_role | silver: readonly, gold: readonly | `nutritionist` | Access cleaned data and analytics, no raw user data |
| **Administrators** | admin_role | all: readwrite | `admin` | Full system access, user management, monitoring |
| **ETL Service** | etl_service | bronze/silver/gold: readwrite | N/A (service account) | Automated data pipeline execution |

**Update procedure:** When adding a new group, create the PostgreSQL role with appropriate grants, define the MinIO policy, add the API role check to `require_role()`, and update this documentation.

---

# Conclusions

---

## Chapter 18 - Demo Plan & Competency Verification Matrix

### 18.1 Live Demo Plan

| Step | Duration | Action | Demonstrates |
|------|----------|--------|-------------|
| 1 | 2 min | Start infrastructure: `docker compose up -d` and show all 10 services running | C3, C14, C19 |
| 2 | 3 min | Open Airflow UI (localhost:8080), show 6 DAGs, trigger `etl_extract_off_api` | C8, C15 |
| 3 | 3 min | Show extraction script execution and data output in `data/raw/api/` | C8 |
| 4 | 2 min | Trigger `etl_aggregate_clean` DAG, show cleaning report | C10 |
| 5 | 3 min | Connect to PostgreSQL with pgAdmin, show `app` schema tables with data | C11 |
| 6 | 2 min | Execute analytical SQL queries (Q1-Q3) with EXPLAIN ANALYZE | C9 |
| 7 | 3 min | Show `dw` schema: dimension tables, fact tables, datamart views | C13, C14 |
| 8 | 2 min | Demonstrate SCD Type 2: update a product, show v_product_history | C17 |
| 9 | 3 min | Open Swagger UI (localhost:8000/docs), test login -> search -> alternatives | C12 |
| 10 | 3 min | Open Streamlit (localhost:8501), login, search products, view daily dashboard | C7, C12 |
| 11 | 2 min | Open MinIO Console (localhost:9001), show bronze/silver/gold buckets and catalog | C18, C19, C20 |
| 12 | 2 min | Run `make backup` and show backup uploaded to MinIO | C16 |
| 13 | 2 min | Show access control: different roles see different data | C21 |
| **Total** | **32 min** | | |

### 18.2 Competency-to-Artifact Verification Matrix

| Competency | Evaluation | Artifacts | Report Section |
|-----------|-----------|-----------|----------------|
| **C1** | E1, E2 | Interview grids, synthesis note | Ch.1, Ch.2.1 |
| **C2** | E2 | Data topography (4 parts), flux matrix | Ch.2.1 |
| **C3** | E2 | Architecture study, Docker Compose, decision log | Ch.2.2 |
| **C4** | E2 | Airflow monitoring, extraction_log, cleaning report | Ch.2.3 |
| **C5** | E3 | Roadmap, calendar, effort weighting | Ch.3.2, Ch.3.3 |
| **C6** | E2, E3 | Makefile, Airflow UI, tracking indicators | Ch.2.4, Ch.3.4 |
| **C7** | E3 | Communication strategy, Swagger docs, Streamlit UI | Ch.3.5 |
| **C8** | E4 | 5 extraction scripts (API, Parquet, scraping, DB, DuckDB) | Ch.4 |
| **C9** | E4 | 7 SQL queries with EXPLAIN notes | Ch.5 |
| **C10** | E4 | aggregate_clean.py, cleaning report | Ch.6 |
| **C11** | E4 | MCD/MLD/MPD, RGPD registry, import script | Ch.7 |
| **C12** | E4 | FastAPI REST API, JWT auth, OpenAPI docs | Ch.8 |
| **C13** | E5 | Star schema (2 facts, 7 dimensions), bottom-up justification | Ch.9 |
| **C14** | E5 | DW creation, access config, test procedure | Ch.10 |
| **C15** | E5 | 6 Airflow DAGs, ETL logic | Ch.11 |
| **C16** | E6 | Logging, alerts, backups, maintenance docs | Ch.12 |
| **C17** | E6 | SCD Type 1/2/3 procedures, v_product_history | Ch.13 |
| **C18** | E7 | Medallion architecture, V/V/V analysis, catalog comparison | Ch.14 |
| **C19** | E7 | Docker Compose, MinIO setup, Airflow config | Ch.15 |
| **C20** | E7 | Data catalog, lifecycle rules, monitoring | Ch.16 |
| **C21** | E7 | Role-based access, group policies, RGPD governance | Ch.17 |

---

## Chapter 19 - Lessons Learned & Improvements

### 19.1 Lessons Learned

**1. Single PostgreSQL for OLTP + OLAP works at small scale but has limits.**
Using schema isolation (app vs. dw) within one PostgreSQL instance simplified deployment significantly. However, heavy analytical queries on fact tables could impact operational performance under high load. At larger scale, a dedicated analytical engine (e.g., ClickHouse, Redshift) would be necessary.

**2. DuckDB is remarkably effective for big data analytics without infrastructure.**
Querying a 3M+ product Parquet file with DuckDB completed in seconds, without any cluster setup. This validated the choice to avoid Spark for the current data volume, keeping the stack simple.

**3. Airflow's CeleryExecutor adds complexity but enables parallelism.**
The initial setup with Redis as broker, PostgreSQL as result backend, and separate worker containers was time-consuming. However, it enabled parallel dimension loading in the warehouse ETL, reducing total pipeline time.

**4. SCD Type 2 detection requires careful IS DISTINCT FROM logic.**
Simple equality checks fail on NULL values. Using `IS DISTINCT FROM` in PostgreSQL correctly handles NULL comparisons, which was critical for detecting product changes where some fields may be NULL.

**5. RGPD compliance must be designed in from the start, not retrofitted.**
Building consent tracking, UUID-based user identification, SHA256 pseudonymization, and automated cleanup functions from the initial schema design was far simpler than adding them later.

### 19.2 Trade-offs

| Trade-off | Chosen Option | Alternative | Rationale |
|-----------|--------------|-------------|-----------|
| Deployment | Docker Compose | Kubernetes | Compose is simpler for single-host development; K8s warranted only for production clustering |
| Data lake | MinIO (self-hosted) | AWS S3 | Self-hosted avoids cloud costs and vendor lock-in; same S3 API |
| ETL engine | SQL-based (in Airflow) | Apache Spark | SQL is simpler, debuggable, sufficient for current volume; Spark adds cluster management overhead |
| API framework | FastAPI (async) | Flask/Django | FastAPI provides native async, auto-generated OpenAPI docs, and Pydantic validation |
| Frontend | Streamlit | React/Vue.js | Streamlit enables rapid prototyping with Python-only code; sufficient for data exploration |
| DW approach | Bottom-up | Top-down (Inmon) | Faster value delivery; builds incrementally from known analytical needs |

### 19.3 Planned Improvements

1. **Real-time streaming**: Add Apache Kafka for real-time product update ingestion, replacing the daily batch pull from the OFF API.

2. **Data quality framework**: Implement Great Expectations for automated data quality checks between pipeline stages, replacing the current custom validation in `aggregate_clean.py`.

3. **CI/CD pipeline**: Add GitHub Actions to run SQL schema migrations, Python linting, and integration tests on every commit.

4. **Monitoring dashboard**: Build a Grafana dashboard connected to Airflow metrics and PostgreSQL statistics for real-time observability.

5. **Machine learning integration**: Add a recommendation engine in the gold layer that suggests products based on user dietary goals and historical consumption patterns.

6. **Horizontal scaling**: Split PostgreSQL into separate OLTP and OLAP instances, and migrate to Kubernetes for container orchestration.

7. **Advanced RGPD**: Implement data subject access requests (DSAR) via an API endpoint that generates a full export of a user's personal data, as required by GDPR Article 15.

---

*End of Report*

**Git repository:** All source code, SQL schemas, and configuration files are versioned in the project repository.
**Technology stack:** PostgreSQL 16, Apache Airflow 2.8, MinIO, FastAPI, DuckDB, Streamlit, Docker Compose
**Competencies covered:** C1 through C21 (all 21 competencies across 4 blocks)
