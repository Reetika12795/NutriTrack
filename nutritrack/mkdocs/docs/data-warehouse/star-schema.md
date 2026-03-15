# Star Schema

## Data Warehouse Design (C13)

The data warehouse uses a **star schema** with 7 dimension tables and 2 fact tables, implemented in the `dw` schema of PostgreSQL.

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

## Design Decisions

### Bottom-Up Approach (Kimball)

The warehouse follows a **bottom-up** (Kimball) methodology:

1. **Business requirements first** — analytics needs drove the schema
2. **Dimensional modeling** — star schema for query performance
3. **Incremental delivery** — datamarts built as analytical views
4. **Conformed dimensions** — shared across fact tables

### Dimension Details

| Dimension | Rows | SCD Type | Key Business Use |
|-----------|------|----------|-----------------|
| `dim_time` | ~7,300 | N/A (pre-populated 20 years) | Date-based analysis |
| `dim_product` | ~50,000 | **Type 2** (historical) | Product evolution tracking |
| `dim_brand` | ~5,000 | **Type 1** (overwrite) | Brand corrections |
| `dim_category` | ~500 | Static | Product classification |
| `dim_country` | ~200 | **Type 3** (previous value) | Country changes |
| `dim_user` | Anonymized | Static | User nutrition patterns |
| `dim_nutriscore` | 5 | Static | A–E grade lookup |

### Fact Tables

| Fact | Grain | Measures | Refresh |
|------|-------|----------|---------|
| `fact_daily_nutrition` | 1 row per user per product per day | energy, fat, sugars, salt, proteins, meal_count | Daily |
| `fact_product_market` | 1 row per product per brand per category per country per day | product_count, avg_nutriscore, avg_nova, market_share | Daily |
