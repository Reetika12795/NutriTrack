# ETL Pipelines

**Competencies**: C15 (ETL Integration)
**Evaluation**: E5 (professional report)

---

## 7 Airflow DAGs

| # | DAG | Schedule | Purpose |
|---|-----|----------|---------|
| 1 | `etl_extract_off_api` | Daily @ 02:00 | Extract products from OFF REST API |
| 2 | `etl_extract_parquet` | Weekly (Sun) @ 03:00 | Bulk extract from OFF Parquet dump via DuckDB |
| 3 | `etl_extract_scraping` | Monthly (1st) @ 03:00 | Scrape ANSES/EFSA nutritional guidelines |
| 4 | `etl_aggregate_clean` | Daily @ 04:00 | Merge + PySpark 7-rule cleaning pipeline |
| 5 | `etl_load_warehouse` | Daily @ 05:00 | Load star schema (dims then facts, with SCD) |
| 6 | `etl_datalake_ingest` | Daily @ 06:00 | Medallion pipeline (Bronze / Silver / Gold) |
| 7 | `etl_backup_maintenance` | Daily @ 02:00 | Backup + RGPD cleanup + storage checks |

![All 7 DAGs in Airflow with execution history](assets/screenshots/airflow_dags_list.png)

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

## Pipeline Details

### 1. etl_extract_off_api

```mermaid
graph LR
    A["check_api_health"] --> B["extract_products"]
    B --> C["validate_data"]
    C --> D["save_to_raw"]
    D --> E["log_extraction"]
```

- **Source**: Open Food Facts REST API (French products)
- **Output**: `data/raw/api/off_api_*.json`
- **Volume**: ~1,000 products per daily run
- **Features**: Pagination, rate limiting, retry on failure

### 2. etl_extract_parquet

- **Source**: OFF Parquet dump queried via DuckDB
- **Output**: `data/raw/parquet/off_parquet_50k.parquet`
- **Volume**: 50,000+ products per weekly run
- **Features**: Columnar pushdown filtering, SQL on Parquet

### 3. etl_extract_scraping

- **Source**: ANSES/EFSA nutritional guidelines (HTML)
- **Output**: `data/raw/scraping/guidelines_*.json`
- **Features**: BeautifulSoup parsing, fallback RDA values

### 4. etl_aggregate_clean

![Aggregate clean DAG graph](assets/screenshots/airflow_dag_graph.png)

```mermaid
graph LR
    A["wait_for_extraction"] --> B["merge_sources"]
    B --> C["pyspark_clean"]
    C --> D["quality_checks"]
    D --> E["save_cleaned"]
```

- **Input**: All raw data files from 3 sources
- **Output**: `data/cleaned/products_cleaned.parquet` + CSV + quality report
- **Engine**: PySpark 3.5 (7 cleaning rules)
- **Volume**: 798,177 in / 777,116 out (2.6% removal)

### 5. etl_load_warehouse

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

- **Pattern**: Dimensions first, then facts (FK integrity)
- **SCD**: Type 1 (brands), Type 2 (products), Type 3 (countries)
- **Datamarts**: 6 views refreshed after fact loading

### 6. etl_datalake_ingest

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

- **Storage**: MinIO S3 buckets (bronze / silver / gold)
- **Catalog**: Updates `_catalog/metadata.json` per bucket

### 7. etl_backup_maintenance

```mermaid
graph TD
    DW["dw_backup<br/>(DW schema only)"] --> FB["full_backup<br/>(entire database)"]
    DW --> SC["storage_check<br/>(PostgreSQL + MinIO)"]
    FB --> RC["rgpd_cleanup<br/>(expired data removal)"]
```

- **Backup**: `pg_dump` to MinIO `backups/` bucket
- **RGPD**: Calls `rgpd_cleanup_expired_data()` stored procedure
- **Alerting**: On failure, logs CRITICAL to `etl_activity_log` + email via MailHog

## Data Formats and Volumes

| Pipeline Stage | Format | Volume | Compression |
|---------------|--------|--------|-------------|
| Raw extraction | JSON + Parquet | ~2 GB | None (JSON), Snappy (Parquet) |
| Cleaned output | Parquet + CSV | ~800 MB | Snappy (Parquet), None (CSV) |
| DW load | PostgreSQL tables | ~500 MB | PostgreSQL TOAST |
| Lake Bronze | Original formats | ~2 GB | Varies |
| Lake Silver | Parquet | ~600 MB | Snappy |
| Lake Gold | Parquet | ~100 MB | Snappy |

## Error Handling

All DAGs use standardized callbacks:

| Event | Callback | Alert Level | Action |
|-------|----------|-------------|--------|
| Task failure | `on_failure_callback` | CRITICAL | Log to DB + email via MailHog |
| Task retry | `on_retry_callback` | WARNING | Log to DB |
| SLA miss | `sla_miss_callback` | WARNING | Log to DB + email |
| Task success | `on_success_callback` | INFO | Log to DB |
