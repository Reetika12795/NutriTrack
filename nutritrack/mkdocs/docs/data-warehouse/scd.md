# Slowly Changing Dimensions

## SCD Implementation (C17)

NutriTrack implements all three Kimball SCD types to track how dimension data evolves over time.

## SCD Type Comparison

```mermaid
graph LR
    subgraph "Type 1: Overwrite"
        T1A["brand_name: 'Danon'"] -->|"correction"| T1B["brand_name: 'Danone'"]
    end

    subgraph "Type 2: Historical"
        T2A["nutriscore: B<br/>is_current: false<br/>end_date: 2026-02-01"] --- T2B["nutriscore: A<br/>is_current: true<br/>end_date: NULL"]
    end

    subgraph "Type 3: Previous Value"
        T3["country_list: 'FR,DE'<br/>previous_country_list: 'FR'"]
    end
```

## SCD Type 1 — Overwrite (dim_brand)

Used for **corrections** where history is not needed.

```sql
-- scd_type1_update_brand()
UPDATE dw.dim_brand
SET brand_name = NEW.brand_name,
    parent_company = NEW.parent_company,
    last_updated = NOW()
WHERE brand_id = NEW.brand_id
  AND (brand_name IS DISTINCT FROM NEW.brand_name
    OR parent_company IS DISTINCT FROM NEW.parent_company);
```

**When to use**: Typo corrections, data quality fixes where the old value was simply wrong.

## SCD Type 2 — Historical Tracking (dim_product)

Used for **tracking changes over time** with full history preservation.

```mermaid
sequenceDiagram
    participant ETL
    participant DW as dim_product

    ETL->>DW: Product "ABC" arrives with nutriscore=A
    Note over DW: Row 1: nutriscore=A, is_current=true, end_date=NULL

    ETL->>DW: Product "ABC" changes to nutriscore=B
    Note over DW: Row 1: nutriscore=A, is_current=false, end_date=today
    Note over DW: Row 2: nutriscore=B, is_current=true, end_date=NULL

    ETL->>DW: Query current state
    DW-->>ETL: WHERE is_current = true → nutriscore=B

    ETL->>DW: Query history
    DW-->>ETL: v_product_history shows both rows
```

**Key columns**:

| Column | Purpose |
|--------|---------|
| `effective_date` | When this version became active |
| `end_date` | When this version was superseded (NULL = current) |
| `is_current` | Boolean flag for easy filtering |

**Change detection**: Uses `IS DISTINCT FROM` to compare all tracked columns.

## SCD Type 3 — Previous Value (dim_country)

Used when only the **immediately previous value** needs to be retained.

```sql
-- scd_type3_update_country()
UPDATE dw.dim_country
SET previous_country_list = country_list,  -- save old value
    country_list = NEW.country_list,       -- apply new value
    last_updated = NOW()
WHERE country_id = NEW.country_id
  AND country_list IS DISTINCT FROM NEW.country_list;
```

**Trade-off**: Only stores one level of history (current + previous), but uses no additional rows.

## Integration into ETL

All SCD operations are integrated into the `etl_load_warehouse` DAG:

```mermaid
graph TD
    L["Load source data"] --> C{"Change<br/>detected?"}
    C -->|"No change"| S["Skip"]
    C -->|"Type 1 (brand)"| T1["Overwrite in place"]
    C -->|"Type 2 (product)"| T2["Close old row<br/>Insert new row"]
    C -->|"Type 3 (country)"| T3["Save previous<br/>Update current"]

    T1 --> D["Done"]
    T2 --> D
    T3 --> D
```

## History Query Views

```sql
-- v_product_history: See all versions of a product
SELECT barcode, product_name, nutriscore_grade,
       effective_date, end_date, is_current
FROM dw.v_product_history
WHERE barcode = '3017620422003'
ORDER BY effective_date;
```
