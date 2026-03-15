# Datamarts

## Analytics Views

6 datamart views provide pre-aggregated data for specific analytical needs, built on top of the star schema.

```mermaid
graph TD
    subgraph "Star Schema"
        F1["fact_daily_nutrition"]
        F2["fact_product_market"]
        D1["dim_time"]
        D2["dim_product"]
        D3["dim_brand"]
        D4["dim_category"]
        D5["dim_user"]
        D6["dim_nutriscore"]
    end

    subgraph "Datamarts"
        M1["dm_user_daily_nutrition"]
        M2["dm_product_market_by_category"]
        M3["dm_brand_quality_ranking"]
        M4["dm_nutriscore_distribution"]
        M5["dm_nutrition_trends"]
        M6["dm_dw_health"]
    end

    F1 --> M1
    F1 --> M5
    D5 --> M1
    D1 --> M1

    F2 --> M2
    D4 --> M2

    F2 --> M3
    D3 --> M3

    D6 --> M4
    F2 --> M4

    F1 --> M5
    D1 --> M5

    F1 --> M6
    F2 --> M6

    style Datamarts fill:#e8f5e9,stroke:#2e7d32
```

## Datamart Details

| Datamart | Purpose | Key Metrics | Consumer |
|----------|---------|-------------|----------|
| `dm_user_daily_nutrition` | User meal tracking | Daily calories, macros, meal count | Streamlit app |
| `dm_product_market_by_category` | Category analysis | Product count, avg nutriscore per category | Superset |
| `dm_brand_quality_ranking` | Brand comparison | Avg nutriscore, avg NOVA, product count per brand | Superset |
| `dm_nutriscore_distribution` | Grade distribution | Count of products per Nutri-Score grade | Superset |
| `dm_nutrition_trends` | Temporal patterns | Weekly/monthly nutrition aggregates | Superset |
| `dm_dw_health` | Warehouse monitoring | Row counts, freshness, SCD status | Grafana / SLA |

## Access Control

Datamarts are accessible through role-based views:

| Role | Access Level |
|------|-------------|
| `app_readonly` | SELECT on all datamarts |
| `nutritionist_role` | SELECT on nutrition + product datamarts |
| `admin_role` | SELECT on all datamarts + DW tables |
| Superset | Connects as `app_readonly` to `dw` schema |
