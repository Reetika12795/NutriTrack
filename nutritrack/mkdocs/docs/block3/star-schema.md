# Star Schema

**Competencies**: C13 (Star Schema Modeling), C14 (Data Warehouse Creation)
**Evaluation**: E5 (professional report)

---

## Design Approach

The data warehouse follows a **bottom-up (Kimball)** methodology:

1. **Business requirements first** -- analytics needs drove the schema design
2. **Dimensional modeling** -- star schema for optimal query performance
3. **Incremental delivery** -- datamarts built as analytical views on top
4. **Conformed dimensions** -- shared across both fact tables

!!! tip "Why Bottom-Up?"
    The Kimball bottom-up approach was chosen because business requirements were well-defined from the start (nutrition tracking, product analytics). This enabled rapid delivery of functional datamarts without waiting for a full enterprise data model (top-down / Inmon approach).

## Entity Relationship Diagram

```mermaid
erDiagram
    dim_time {
        int time_id PK
        date full_date
        int day_of_week
        int week_of_year
        int month
        int quarter
        int year
        boolean is_weekend
        boolean is_holiday
    }

    dim_product {
        int product_id PK
        varchar barcode
        varchar product_name
        varchar nutriscore_grade
        int nova_group
        numeric energy_kcal
        numeric fat
        numeric sugars
        numeric salt
        numeric proteins
        numeric fiber
        date effective_date
        date end_date
        boolean is_current
    }

    dim_brand {
        int brand_id PK
        varchar brand_name
        varchar parent_company
        timestamp last_updated
    }

    dim_category {
        int category_id PK
        varchar category_name
        varchar parent_category
    }

    dim_country {
        int country_id PK
        varchar country_name
        varchar country_code
        varchar country_list
        varchar previous_country_list
        timestamp last_updated
    }

    dim_user {
        int user_id PK
        varchar user_hash
        varchar age_group
        varchar activity_level
        date registered_date
    }

    dim_nutriscore {
        int nutriscore_id PK
        char grade
        varchar label
        varchar color_code
    }

    fact_daily_nutrition {
        int nutrition_id PK
        int time_id FK
        int user_id FK
        int product_id FK
        int nutriscore_id FK
        numeric quantity_g
        numeric energy_kcal
        numeric fat_g
        numeric sugars_g
        numeric salt_g
        numeric proteins_g
        int meal_count
    }

    fact_product_market {
        int market_id PK
        int time_id FK
        int product_id FK
        int brand_id FK
        int category_id FK
        int country_id FK
        int product_count
        numeric avg_nutriscore
        numeric avg_nova_group
        numeric market_share_pct
    }

    fact_daily_nutrition ||--o{ dim_time : "time_id"
    fact_daily_nutrition ||--o{ dim_user : "user_id"
    fact_daily_nutrition ||--o{ dim_product : "product_id"
    fact_daily_nutrition ||--o{ dim_nutriscore : "nutriscore_id"

    fact_product_market ||--o{ dim_time : "time_id"
    fact_product_market ||--o{ dim_product : "product_id"
    fact_product_market ||--o{ dim_brand : "brand_id"
    fact_product_market ||--o{ dim_category : "category_id"
    fact_product_market ||--o{ dim_country : "country_id"
```

## Dimension Tables

| Dimension | Rows | SCD Type | Key Business Use |
|-----------|------|----------|-----------------|
| `dim_time` | ~7,300 | N/A (pre-populated 20 years) | Date-based analysis, weekday/weekend, holidays |
| `dim_product` | ~777K | **Type 2** (historical) | Product evolution tracking, nutriscore changes |
| `dim_brand` | ~5,000 | **Type 1** (overwrite) | Brand name corrections, parent company |
| `dim_category` | ~500 | Static | Product classification hierarchy |
| `dim_country` | ~200 | **Type 3** (previous value) | Country distribution changes |
| `dim_user` | Anonymized | Static | User nutrition patterns (SHA256 hash, no PII) |
| `dim_nutriscore` | 5 | Static | A--E grade lookup with labels and color codes |

## Fact Tables

| Fact | Grain | Measures | Refresh |
|------|-------|----------|---------|
| `fact_daily_nutrition` | 1 row per user per product per day | energy_kcal, fat_g, sugars_g, salt_g, proteins_g, meal_count | Daily |
| `fact_product_market` | 1 row per product per brand per category per country per day | product_count, avg_nutriscore, avg_nova_group, market_share_pct | Daily |

## Datamart Views

6 views provide pre-aggregated data for specific analytical needs:

| Datamart | Purpose | Key Metrics | Primary Consumer |
|----------|---------|-------------|-----------------|
| `dm_user_daily_nutrition` | User meal tracking | Daily calories, macros, meal count | Streamlit (user role) |
| `dm_product_market_by_category` | Category analysis | Product count, avg nutriscore per category | Streamlit (analyst role) |
| `dm_brand_quality_ranking` | Brand comparison | Avg nutriscore, avg NOVA, product count per brand | Streamlit (analyst role) |
| `dm_nutriscore_distribution` | Grade distribution | Count of products per Nutri-Score grade | Streamlit (analyst role) |
| `dm_nutrition_trends` | Temporal patterns | Weekly/monthly nutrition aggregates | Streamlit (analyst role) |
| `dm_dw_health` | Warehouse monitoring | Row counts, freshness, SCD status | Grafana / SLA dashboard |

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

## Access Control

| Role | Access Level |
|------|-------------|
| `app_readonly` | SELECT on all datamarts |
| `nutritionist_role` | SELECT on nutrition + product datamarts |
| `admin_role` | SELECT on all datamarts + all DW tables |

## Data Needed for Analyses

An exhaustive list of data required, mapped to source:

| Analysis Need | Required Data | Source |
|--------------|--------------|--------|
| Daily nutrition tracking | User meals, product nutrients, time | app.meals + app.products |
| Product quality by brand | Products, brands, nutriscore, NOVA | app.products (cleaned) |
| Category market analysis | Products, categories, countries | app.products (cleaned) |
| Nutri-Score distribution | Products, nutriscore grades | app.products (cleaned) |
| Nutrition trends over time | Daily aggregates, time periods | fact_daily_nutrition + dim_time |
| DW health monitoring | Table row counts, freshness | All DW tables (metadata) |
