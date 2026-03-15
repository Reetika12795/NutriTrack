# ETL Pipelines

## Airflow DAG Overview

7 DAGs orchestrate the full data pipeline, from extraction to warehouse loading and data lake ingestion.

```mermaid
gantt
    title Daily ETL Schedule (UTC)
    dateFormat HH:mm
    axisFormat %H:%M

    section Extraction
    OFF API Extract       :api, 02:00, 60min
    Parquet Extract (SUN) :pq, 03:00, 90min
    Scraping (1st of month):sc, 03:00, 60min

    section Transform
    Aggregate & Clean     :clean, 04:00, 45min

    section Load
    Load Warehouse        :dw, 05:00, 30min
    Datalake Ingest       :dl, 06:00, 45min

    section Maintenance
    Backup & Maintenance  :bk, 02:00, 30min
```

## DAG Dependency Graph

```mermaid
graph TD
    E1["etl_extract_off_api<br/>Daily @ 02:00"]
    E2["etl_extract_parquet<br/>Weekly SUN 03:00"]
    E3["etl_extract_scraping<br/>Monthly 1st"]

    AGG["etl_aggregate_clean<br/>Daily @ 04:00"]

    DW["etl_load_warehouse<br/>Daily @ 05:00"]

    DL["etl_datalake_ingest<br/>Daily @ 06:00"]

    BK["etl_backup_maintenance<br/>Daily @ 02:00"]

    E1 -->|ExternalTaskSensor| AGG
    E2 -.->|weekly trigger| AGG
    E3 -.->|monthly trigger| AGG

    AGG -->|ExternalTaskSensor| DW
    AGG -->|ExternalTaskSensor| DL

    style E1 fill:#e8f5e9,stroke:#2e7d32
    style E2 fill:#e8f5e9,stroke:#2e7d32
    style E3 fill:#e8f5e9,stroke:#2e7d32
    style AGG fill:#fff3e0,stroke:#e65100
    style DW fill:#e3f2fd,stroke:#1565c0
    style DL fill:#f3e5f5,stroke:#6a1b9a
    style BK fill:#fce4ec,stroke:#c62828
```

## DAG Details

### 1. `etl_extract_off_api` — Daily API Extraction

```mermaid
graph LR
    A["check_api_health"] --> B["extract_products"]
    B --> C["validate_data"]
    C --> D["save_to_raw"]
    D --> E["log_extraction"]
```

- **Schedule**: Daily at 02:00 UTC
- **Source**: Open Food Facts REST API
- **Output**: `data/raw/api/off_api_*.json`
- **Features**: Pagination, rate limiting, User-Agent header

### 2. `etl_extract_parquet` — Weekly Bulk Extraction

- **Schedule**: Weekly, Sundays at 03:00 UTC
- **Source**: OFF Parquet dump via DuckDB
- **Output**: `data/raw/parquet/off_parquet_50k.parquet`
- **Volume**: 50,000+ products per run

### 3. `etl_extract_scraping` — Monthly Web Scraping

- **Schedule**: Monthly, 1st day at 03:00 UTC
- **Source**: ANSES/EFSA nutritional guidelines
- **Output**: `data/raw/scraping/guidelines_*.json`
- **Tech**: BeautifulSoup with fallback RDA values

### 4. `etl_aggregate_clean` — Daily Cleaning

```mermaid
graph LR
    A["wait_for_extraction"] --> B["merge_sources"]
    B --> C["standardize_columns"]
    C --> D["clean_barcodes"]
    D --> E["validate_ranges"]
    E --> F["deduplicate"]
    F --> G["save_cleaned"]
    G --> H["generate_report"]
```

- **Schedule**: Daily at 04:00 UTC
- **Input**: All raw data files
- **Output**: `data/cleaned/products_cleaned.parquet`
- **Quality**: `cleaning_report.json` with statistics

### 5. `etl_load_warehouse` — Daily Star Schema Load

```mermaid
graph TD
    W["wait_for_clean"] --> D1["load_dim_time"]
    W --> D2["load_dim_brands<br/>(SCD Type 1)"]
    W --> D3["load_dim_categories"]
    W --> D4["load_dim_countries<br/>(SCD Type 3)"]
    W --> D5["load_dim_nutriscore"]

    D2 --> D6["load_dim_products<br/>(SCD Type 2)"]
    D3 --> D6

    D1 --> F1["load_fact_daily_nutrition"]
    D5 --> F1
    D6 --> F1

    D1 --> F2["load_fact_product_market"]
    D2 --> F2
    D3 --> F2
    D4 --> F2
    D6 --> F2

    F1 --> R["refresh_datamarts"]
    F2 --> R
```

- **Schedule**: Daily at 05:00 UTC
- **Pattern**: Dimensions first, then facts (FK integrity)
- **SCD**: Type 1 (brands), Type 2 (products), Type 3 (countries)

### 6. `etl_datalake_ingest` — Daily Medallion Pipeline

```mermaid
graph LR
    subgraph Bronze
        B1["ingest_raw_json"]
        B2["ingest_raw_parquet"]
        B3["ingest_raw_csv"]
    end

    subgraph Silver
        S1["clean_and_validate"]
        S2["deduplicate"]
        S3["standardize_schema"]
    end

    subgraph Gold
        G1["aggregate_analytics"]
        G2["compute_metrics"]
        G3["update_catalog"]
    end

    B1 --> S1
    B2 --> S1
    B3 --> S1
    S1 --> S2 --> S3
    S3 --> G1 --> G2 --> G3

    style Bronze fill:#cd7f32,color:#fff
    style Silver fill:#c0c0c0
    style Gold fill:#ffd700
```

- **Schedule**: Daily at 06:00 UTC
- **Storage**: MinIO S3 buckets (bronze/silver/gold)
- **Catalog**: Updates `_catalog/metadata.json` per bucket

### 7. `etl_backup_maintenance` — Daily Backup

```mermaid
graph TD
    DW["dw_backup<br/>(DW schema only)"] --> FB["full_backup<br/>(entire database)"]
    DW --> SC["storage_check<br/>(PostgreSQL + MinIO)"]
    FB --> RC["rgpd_cleanup<br/>(expired data removal)"]
```

- **Schedule**: Daily at 02:00 UTC
- **Backup**: pg_dump to MinIO `backups/` bucket
- **RGPD**: Calls `rgpd_cleanup_expired_data()` stored procedure
- **Alerting**: On failure → log to `etl_activity_log` + email via MailHog
