# NutriTrack Analytics Dashboards — Setup & User Guide

**Tool**: Apache Superset
**URL**: http://localhost:8088
**Certification**: C7 (Communication supports), C14 (Analyst access), C16 (SLA indicators), C21 (RBAC governance)

---

## 1. Access & Credentials

| Role | Username | Password | Capabilities |
|---|---|---|---|
| **Admin** | `admin` | `admin` | Full access: dashboards, SQL Lab, dataset management, user management |
| **Analyst** | `analyst` | `analyst` | All 3 dashboards + SQL Lab (read-only data) |
| **Nutritionist** | `nutritionist` | `nutritionist` | Dashboards only — no SQL Lab, no raw data access |

**First login**: Navigate to http://localhost:8088, enter credentials, and you'll see the dashboard list.

---

## 2. Architecture

```
PostgreSQL :5432 (nutritrack DB, dw schema)
  ├── dm_product_market_by_category    ──┐
  ├── dm_brand_quality_ranking          │
  ├── dm_nutriscore_distribution        ├── Superset :8088
  ├── dm_nutrition_trends               │   ├── Product Market Analysis
  ├── dm_dw_health                      │   ├── Nutrition Trends
  └── dm_user_daily_nutrition          ──┘   └── DW Health & Data Quality
```

**Data flow**: ETL (Airflow) → PostgreSQL DW → Datamart views → Superset datasets → Charts → Dashboards

**Access control**: Superset connects to PostgreSQL using the `superset` role, which has `SELECT`-only access on `dw.*` schema. No write access, no access to `app` schema (user data).

---

## 3. Dashboards

### 3.1 Product Market Analysis

**Audience**: Analysts, Nutritionists
**Data sources**: `dm_product_market_by_category`, `dm_brand_quality_ranking`, `dm_nutriscore_distribution`, `fact_product_market`

| Chart | Type | What it shows |
|---|---|---|
| Nutri-Score Distribution by Category | Bar chart | Count of products per Nutri-Score grade (A-E), grouped by food category |
| Top Brands by Nutrition Quality | Bar chart | Top 20 brands ranked by average Nutri-Score (lower = healthier) |
| Category Nutrition Comparison | Bar chart | Average calories and proteins per food category |
| Products by Nutri-Score Grade | Pie chart | Overall distribution of Nutri-Score grades across all products |

**How to use filters**:
- Click on a bar in any chart to filter all other charts on the dashboard
- Use the filter bar at the top to filter by category, Nutri-Score grade, or brand

### 3.2 Nutrition Trends

**Audience**: Analysts, Nutritionists
**Data sources**: `dm_nutrition_trends`, `dm_user_daily_nutrition`

| Chart | Type | What it shows |
|---|---|---|
| Daily Calorie Intake Trend | Line chart | Total daily caloric intake with 7-day moving average |
| Macro Nutrient Distribution | Stacked area | Protein, fat, and carbohydrate intake over time |
| Meal Type Breakdown | Pie chart | Distribution of meal types (breakfast, lunch, dinner, snacks) |
| Active Users by Dietary Goal | Bar chart | Number of active users per dietary goal category |

**Note**: This dashboard uses anonymized data — user identities are pseudonymized with SHA-256 hashing. The `dm_nutrition_trends` view aggregates at the `age_group` + `dietary_goal` level, not individual users.

### 3.3 DW Health & Data Quality

**Audience**: Admins, Data Engineers
**Data sources**: `dm_dw_health`

| Chart | Type | What it shows |
|---|---|---|
| DW Record Counts by Table | Bar chart | Total rows per dimension and fact table, grouped by table type |
| Data Completeness by Table | Bar chart | Percentage of non-null key fields per table |
| Active vs Total Records (SCD) | Bar chart | Comparison of active (current) vs total rows — reveals SCD history volume |

**SLA indicators** (C16):
- **Record counts** — track data volume growth over time
- **Completeness scores** — alert if data quality drops below threshold
- **Last loaded timestamp** — detect ETL failures (no recent load = problem)

---

## 4. Technical Setup

### 4.1 Docker Compose service

```yaml
superset:
  build:
    context: .
    dockerfile: superset/Dockerfile
  ports:
    - "8088:8088"
  environment:
    SUPERSET_CONFIG_PATH: /app/superset_config.py
    SUPERSET_SECRET_KEY: nutritrack-superset-change-in-production
  depends_on:
    postgres: { condition: service_healthy }
    redis: { condition: service_healthy }
```

### 4.2 Configuration files

| File | Purpose |
|---|---|
| `superset/Dockerfile` | Extends `apache/superset:latest` with `psycopg2-binary` for PostgreSQL |
| `superset/superset_config.py` | Metadata DB URI, SECRET_KEY, Redis cache, feature flags, row limits |
| `superset/superset-init.sh` | Idempotent init: DB upgrade, admin user, datasource, RBAC roles/users |
| `superset/bootstrap_dashboards.py` | Creates 7 datasets, 11 charts, 3 dashboards via REST API |

### 4.3 Datasource configuration

The NutriTrack DW datasource is auto-registered by `superset-init.sh`:
```
superset set-database-uri \
    --database_name "NutriTrack DW" \
    --uri "postgresql+psycopg2://superset:superset@postgres:5432/nutritrack"
```

The `superset` PostgreSQL role has `SELECT`-only access on `dw.*` — it cannot modify data or access `app.*`.

### 4.4 Dashboard bootstrapping

After Superset starts, run the bootstrap script to create dashboards:
```bash
python3 superset/bootstrap_dashboards.py
```

The script is idempotent — re-running it skips existing datasets, charts, and dashboards.

---

## 5. RBAC Configuration (C21)

### PostgreSQL-level access control

| PostgreSQL Role | Access |
|---|---|
| `superset` | `SELECT` on `dw.*` only — read-only, no `app` schema access |
| `nutritionist_role` | `SELECT` on `dm_*` views + `dim_time` + `dim_nutriscore` only |
| `admin_role` | `ALL PRIVILEGES` on `dw.*` |

### Superset-level RBAC

| Superset Role | Permissions | Base Role |
|---|---|---|
| **Admin** | Full access: SQL Lab, datasets, users, settings | Built-in Admin |
| **Analyst** | Gamma (view dashboards) + SQL Lab (ad-hoc queries) | Gamma + sql_lab |
| **Nutritionist** | Gamma (view dashboards only) | Gamma |

**Governance principle (C21)**: Rights are applied to groups (roles), not individuals. Access is limited to the minimum necessary — nutritionists see dashboards but cannot write SQL. Analysts can query but cannot modify datasets.

---

## 6. Exporting & Importing Dashboards

### Export
```bash
# Via Superset UI: Dashboards → ... → Export
# Via API:
curl -H "Authorization: Bearer <token>" \
  http://localhost:8088/api/v1/dashboard/export/?q=[1,2,3]
```

### Import
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -F "formData=@dashboard_export.zip" \
  http://localhost:8088/api/v1/dashboard/import/
```

---

## 7. Troubleshooting

| Issue | Solution |
|---|---|
| Superset not starting | Check logs: `docker compose logs superset`. Verify PostgreSQL is healthy. |
| "No data" in dashboards | Run the ETL pipeline first (`etl_aggregate_clean` → `etl_load_warehouse`). Datamarts need fact data. |
| Login fails | Check `superset-init.sh` created users. Default: admin/admin. |
| Cannot access SQL Lab | Check user role — only Admin and Analyst roles have SQL Lab access. |
| Dashboard bootstrap fails | Ensure Superset is healthy (`curl localhost:8088/health`), then re-run `bootstrap_dashboards.py`. |
