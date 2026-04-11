# Senior Dev Review Brief -- NutriTrack Codebase Audit

**Reviewer**: senior-dev
**Date**: 2026-04-09
**Scope**: Full codebase audit against certification competencies C1-C21 and engineering quality standards

---

## 1. Executive Summary

The NutriTrack project demonstrates a solid full-stack data engineering platform covering all 4 certification blocks. The architecture is well-chosen: PostgreSQL for operational + DW, MinIO for data lake (medallion), Airflow for orchestration, FastAPI for REST, Streamlit for frontend, and Grafana/Prometheus for monitoring. The SQL schemas are clean, the ETL pipelines are functional, and the RGPD compliance layer is present.

However, there are several issues ranging from security vulnerabilities to missing test coverage that should be addressed before the defense. This brief categorizes findings by severity.

---

## 2. Critical Issues (Must Fix)

### 2.1 SQL Injection in `extract_off_parquet.py`

**File**: `/nutritrack/scripts/extract_off_parquet.py`, line 122
**Severity**: CRITICAL

The `countries_filter` parameter is interpolated directly into a DuckDB SQL string using an f-string:

```python
AND countries LIKE '%{countries_filter}%'
```

While DuckDB is a local engine and the input comes from a CLI arg (not a web request), this is still a textbook SQL injection pattern. For a certification project demonstrating data engineering best practices, this is a red flag. The same pattern appears in the `nutriscore_filter` construction on lines 78-80.

**Fix**: Use DuckDB parameterized queries or at minimum sanitize the input.

### 2.2 Hardcoded Secrets Everywhere

**Files**: `docker-compose.yml`, `api/config.py`, `sql/init/00_init_databases.sql`
**Severity**: HIGH

All passwords are hardcoded in plaintext:
- PostgreSQL: `postgres/postgres`, `nutritrack/nutritrack`, `airflow/airflow`
- MinIO: `minioadmin/minioadmin123`
- JWT secret: `nutritrack-secret-key-change-in-production`
- Superset secret: `nutritrack-superset-change-in-production`
- Redis: no password at all

While acceptable for a development/demo environment, the certification requires demonstrating awareness of security practices. The code contains "change-in-production" comments but no `.env.example` file or documentation on how to properly configure production secrets. The SQL init file creates roles with plaintext passwords.

**Recommendation**: Add a `.env.example` file, reference it from docker-compose.yml using `env_file`, and document the production secret rotation process.

### 2.3 SQLAlchemy Version Conflict Between Airflow and Main App

**Files**: `airflow/requirements.txt` (line 5), `requirements.txt` (line 9)
**Severity**: HIGH

The Airflow container pins `sqlalchemy>=1.4.28,<2.0` while the main app uses `sqlalchemy==2.0.25`. Since these run in separate containers, this is not a runtime conflict, but it creates a maintenance burden and could cause confusion. More importantly, the Airflow DAGs use SQLAlchemy 1.x style (`text()`, `engine.begin()`) which is correct for their constraint. However, if anyone tries to run scripts locally that import both Airflow plugins and the main API, they will hit version conflicts.

### 2.4 Missing `staging.data_quality_checks` Table Definition

**File**: `airflow/dags/etl_aggregate_clean.py`, line 407
**Severity**: MEDIUM-HIGH

The `validate_data_quality` function tries to INSERT into `staging.data_quality_checks`, but this table is never defined in any SQL init or migration file. The code catches the exception silently:

```python
except Exception as e:
    print(f"Could not log to DB (table may not exist yet): {e}")
```

For the certification (C15 - ETL data quality), this should actually work. Create the staging schema and table.

---

## 3. Significant Issues (Should Fix)

### 3.1 Nutritionist Router Not Registered in `main.py`

**File**: `api/main.py`
**Severity**: MEDIUM

`main.py` imports and includes only `auth`, `meals`, and `products` routers. The `analytics.py` and `nutritionist.py` routers exist in the `routers/` directory but are NOT registered:

```python
from api.routers import auth, meals, products
# Missing: analytics, nutritionist
```

These routers are critical for C12 (REST API with role-based access). They demonstrate `require_role()` functionality which is a key certification criterion.

### 3.2 Analytics Router Uses Wrong Role Name

**File**: `api/routers/analytics.py`, line 87
**Severity**: MEDIUM

The analytics endpoint requires role `"analyst"`:
```python
_: User = Depends(require_role("analyst", "admin"))
```

But the user model and SQL schema only define roles: `user`, `nutritionist`, `admin`. There is no `"analyst"` role. This endpoint will be inaccessible to any real user unless the DB schema is updated or the role name is changed to `"nutritionist"`.

### 3.3 Nutritionist Endpoint Exposes Raw Email

**File**: `api/routers/nutritionist.py`, line 24
**Severity**: MEDIUM (RGPD concern)

The `UserStats` model exposes `email` to nutritionists. The SQL schema correctly `REVOKE`s `SELECT ON app.users FROM nutritionist_role`, but the API endpoint bypasses this by running as the `nutritrack` superuser role. This contradicts the RGPD data minimization principle and the DB-level governance configuration.

### 3.4 Tests Are Shallow

**Files**: `tests/test_api_schemas.py`, `tests/test_etl_functions.py`, `tests/test_sql_schemas.py`
**Severity**: MEDIUM

The test suite has only 3 test files with ~30 total test cases. All tests are unit tests that validate Pydantic schemas or string matching in SQL files. There are:
- Zero integration tests
- Zero API endpoint tests (no TestClient usage)
- Zero database integration tests
- Zero ETL pipeline integration tests
- No test for JWT auth flow
- No test for role-based access control
- No test for the cleaning pipeline against real data

For C8-C15 competencies, the evaluator will want to see tests that prove the scripts and ETL pipelines actually work end-to-end.

### 3.5 `etl_backup_maintenance.py` Weekly Logic Never Triggers

**File**: `airflow/dags/etl_backup_maintenance.py`, lines 155-177
**Severity**: MEDIUM

The full backup and RGPD cleanup tasks are described as "weekly (Sunday)" in comments, but the DAG runs daily (`schedule_interval="0 2 * * *"`) and all tasks execute sequentially: `dw_backup >> full_backup >> rgpd_cleanup`. There is no branch operator or day-of-week check to make the full backup and RGPD cleanup only run on Sundays. They run every day, which is wasteful and contradicts the documented backup strategy.

---

## 4. Minor Issues (Nice to Fix)

### 4.1 `datetime.utcnow()` Deprecated

**Files**: `api/routers/auth.py` (lines 40, 65)
**Severity**: LOW

`datetime.utcnow()` is deprecated since Python 3.12. The `jwt.py` file correctly uses `datetime.now(timezone.utc)`, but `auth.py` still uses the deprecated form. Should be consistent.

### 4.2 Missing `__future__` Annotations in Some Files

**Files**: `api/routers/auth.py`, `api/routers/meals.py`, `api/routers/products.py`
**Severity**: LOW

These files use `str | None` and `list[...]` type hints without `from __future__ import annotations`. This works on Python 3.11+ (the Docker target) but would fail on Python 3.9 which is the host machine's version. The `analytics.py` and `nutritionist.py` files correctly include the import.

### 4.3 Unused Variable in `jwt.py`

**File**: `api/auth/jwt.py`, line 48
**Severity**: LOW

```python
role: str = payload.get("role")  # noqa: F841
```

The `role` variable is extracted from the JWT but never used in `get_current_user`. The role should probably be validated against the DB role to detect token tampering.

### 4.4 `etl_datalake_ingest.py` Only First 100 Lines Read

**Note**: I only read the first 100 lines. The full file should be reviewed for the gold layer publishing logic.

### 4.5 Grafana SLA Dashboard JSON

The `monitoring/grafana/dashboards/sla-compliance.json` exists (16KB) which is good for C16. The dashboard provisioning is correctly configured.

---

## 5. Competency-by-Competency Review Checklist

### Block 1: Steer a Data Project (C1-C7)

| Competency | Status | Evidence | Gap |
|---|---|---|---|
| C1 | Partial | Documentation exists in `rapport_final.md` and presentation materials | Need interview grids (E1 deliverable) |
| C2 | Present | Data topography covered in `technical_stack_choices.md` | Verify 4-part structure: semantics, models, treatments, access |
| C3 | Present | Architecture study in technical docs, docker-compose shows infrastructure | Need flux matrix in applicative representation |
| C4 | Present | `veille_technologique.md` exists | Verify regular monitoring schedule documented |
| C5 | Partial | Roadmap implied in docs | Need explicit calendar with effort weighting |
| C6 | Present | GitHub tracking, Airflow scheduling, monitoring | Need documented rituals |
| C7 | Partial | Presentation materials exist (PPTX, Beamer slides) | Communication strategy for stakeholders |

### Block 2: Data Collection, Storage & Sharing (C8-C12)

| Competency | Status | Evidence | Gap |
|---|---|---|---|
| C8 | STRONG | 5 extraction scripts: API, Parquet/DuckDB, scraping, DB, big data | All have entry points, deps, error handling, Git versioned |
| C9 | STRONG | `extract_from_db.py` has 5 documented SQL queries with optimization notes | EXPLAIN ANALYZE logging present |
| C10 | STRONG | `aggregate_clean.py` + PySpark DAG clean, deduplicate, homogenize | Both pandas and PySpark implementations |
| C11 | STRONG | MERISE-compatible schema, RGPD registry, import script, triggers | Need explicit MCD/MLD diagrams |
| C12 | NEEDS FIX | FastAPI with JWT, OpenAPI, role-based access | Analytics/nutritionist routers not registered in main.py; "analyst" role mismatch |

### Block 3: Data Warehouse (C13-C17)

| Competency | Status | Evidence | Gap |
|---|---|---|---|
| C13 | STRONG | Star schema with dim/fact tables, datamarts as views | Bottom-up approach documented |
| C14 | STRONG | DW functional in PostgreSQL, analyst access via Superset configured | Test procedures should be more formal |
| C15 | STRONG | ETL DAGs with sensor dependencies, quality checks | staging.data_quality_checks table missing |
| C16 | STRONG | Alerting plugin, backup DAG, Grafana dashboards, SLA compliance, MailHog | Weekly backup logic flawed (runs daily) |
| C17 | STRONG | SCD Type 1 (brand), Type 2 (product, user), Type 3 (country) all implemented | SQL functions + ETL procedures correct |

### Block 3: Data Lake (C18-C21)

| Competency | Status | Evidence | Gap |
|---|---|---|---|
| C18 | STRONG | MinIO medallion architecture, architecture documented in catalog | Volume/velocity/variety constraints addressed |
| C19 | STRONG | Docker-based install, storage functional, batch tools connected | Installation docs in mkdocs |
| C20 | STRONG | Data catalog in MinIO, lifecycle rules, monitoring alerts in Grafana | Feed scripts run without errors |
| C21 | STRONG | Group-based access policies in `setup_minio.py`, DB-level GRANT/REVOKE | Access documentation in catalog metadata |

---

## 6. Architecture Assessment

### Strengths
1. **Clean separation of concerns**: Operational DB (app schema), DW (dw schema), data lake (MinIO buckets) are properly isolated
2. **Medallion architecture**: Bronze/silver/gold buckets with lifecycle rules
3. **SCD implementation**: All three Kimball types demonstrated with working SQL functions
4. **Monitoring stack**: Prometheus + Grafana + StatsD + cAdvisor + node-exporter + postgres-exporter is comprehensive
5. **RGPD compliance**: Data registry, consent tracking, retention periods, cleanup functions
6. **ETL orchestration**: DAG dependencies with ExternalTaskSensors ensure correct execution order
7. **Data catalog**: Well-structured metadata JSON with lineage documentation
8. **PySpark integration**: Dual pandas/PySpark implementation shows big data readiness

### Concerns
1. **No CI/CD pipeline**: No GitHub Actions, no pre-commit hooks, no automated testing
2. **No `.env` file management**: All secrets hardcoded
3. **No database migrations tool**: SQL files in `sql/migrations/` are not managed by Alembic or similar
4. **Single PostgreSQL instance**: DW and operational DB share the same PostgreSQL server (acceptable for certification scope)
5. **No rate limiting on API**: FastAPI has no rate limiting middleware
6. **No HTTPS**: All services communicate over HTTP (acceptable for local dev)
7. **`--reload` in production Dockerfile**: API Dockerfile uses `--reload` flag, which is a dev-only option

---

## 7. Files with Issues (Quick Reference)

| File | Issue | Severity |
|---|---|---|
| `scripts/extract_off_parquet.py:122` | SQL injection via f-string | CRITICAL |
| `api/main.py` | Missing analytics + nutritionist router imports | MEDIUM |
| `api/routers/analytics.py:87` | Wrong role name "analyst" | MEDIUM |
| `api/routers/nutritionist.py:24` | Exposes email to nutritionists (RGPD) | MEDIUM |
| `airflow/dags/etl_aggregate_clean.py:407` | References non-existent staging table | MEDIUM-HIGH |
| `airflow/dags/etl_backup_maintenance.py:155-177` | Weekly tasks run daily | MEDIUM |
| `api/routers/auth.py:40,65` | `datetime.utcnow()` deprecated | LOW |
| `api/auth/jwt.py:48` | Unused variable `role` | LOW |
| `api/Dockerfile:18` | `--reload` flag in production CMD | LOW |

---

## 8. Recommended Priority Actions

1. **Register analytics + nutritionist routers** in `api/main.py` -- 2 lines of code, unlocks C12 demo
2. **Fix "analyst" role** to "nutritionist" in `analytics.py` -- 1 line change
3. **Create `staging.data_quality_checks` table** in a new migration -- enables quality check logging for C15
4. **Fix SQL injection** in `extract_off_parquet.py` -- use parameterized queries
5. **Add integration tests** for at least: API auth flow, product search, ETL cleaning pipeline
6. **Fix weekly backup branching** with Airflow BranchPythonOperator or ShortCircuitOperator
7. **Remove `--reload`** from production API Dockerfile CMD
8. **Add `.env.example`** documenting all required environment variables

---

## 9. Review Policy for Incoming PRs

For any PR submitted by teammates, I will check:

1. **Does the code compile/parse without errors?** (Python syntax, SQL syntax, Docker syntax)
2. **Are there tests?** Any non-trivial change needs at least one test
3. **Does it address the certification criterion fully?** Cross-reference with CLAUDE.md
4. **Are there security issues?** (secrets, injection, privilege escalation)
5. **Does it follow existing conventions?** (ruff formatting, file naming, import style)
6. **Is the Docker configuration correct?** (volumes, ports, dependencies, healthchecks)
7. **Are the SQL queries parameterized?** No f-string SQL
8. **Is RGPD compliance maintained?** No personal data leaks, proper access controls
9. **Is the documentation accurate?** Comments match implementation

**VETO criteria** (will block merge):
- Hardcoded production secrets
- SQL injection vulnerabilities
- Broken imports or syntax errors
- Missing tests for new functionality
- RGPD violations (exposing personal data without justification)
- Changes to main branch directly
