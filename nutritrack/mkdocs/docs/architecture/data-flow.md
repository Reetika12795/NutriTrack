# Data Flow Pipeline

## End-to-End Data Flow

```mermaid
graph TD
    subgraph Extract["1. Extract (C8)"]
        S1["OFF REST API<br/>Daily @ 02:00"]
        S2["Parquet Dump<br/>Weekly SUN 03:00"]
        S3["Web Scraping<br/>Monthly 1st day"]
    end

    subgraph Raw["2. Raw Storage"]
        R1["data/raw/api/*.json"]
        R2["data/raw/parquet/*.parquet"]
        R3["data/raw/scraping/*.json"]
    end

    subgraph Clean["3. Clean & Aggregate (C10)"]
        AGG["aggregate_clean.py<br/>Daily @ 04:00<br/>─────────<br/>Merge sources<br/>Dedup by barcode<br/>Validate ranges<br/>Normalize Nutri-Score"]
    end

    subgraph Load["4. Load"]
        direction LR
        DB["PostgreSQL<br/>app schema<br/>(OLTP)"]
        DW["PostgreSQL<br/>dw schema<br/>(Star Schema)"]
        DL["MinIO S3<br/>Medallion<br/>(Bronze/Silver/Gold)"]
    end

    subgraph Serve["5. Serve"]
        API["FastAPI<br/>REST API"]
        SS["Superset<br/>Dashboards"]
        ST["Streamlit<br/>Frontend"]
    end

    S1 --> R1
    S2 --> R2
    S3 --> R3

    R1 --> AGG
    R2 --> AGG
    R3 --> AGG

    AGG -->|"import_to_db.py<br/>Batch upsert"| DB
    DB -->|"etl_load_warehouse<br/>Daily @ 05:00"| DW
    DB -->|"etl_datalake_ingest<br/>Daily @ 06:00"| DL

    DW --> SS
    DB --> API
    DB --> ST

    style Extract fill:#e8f5e9,stroke:#2e7d32
    style Raw fill:#fff9c4,stroke:#f57f17
    style Clean fill:#ffecb3,stroke:#ff8f00
    style Load fill:#e3f2fd,stroke:#1565c0
    style Serve fill:#fff3e0,stroke:#e65100
```

## Flux Matrix

| Source | Format | Target | Treatment Script | Frequency | Volume |
|--------|--------|--------|-----------------|-----------|--------|
| OFF REST API | JSON | `data/raw/api/` | `extract_off_api.py` | Daily | ~1,000 products |
| OFF Parquet dump | Parquet | `data/raw/parquet/` | `extract_off_parquet.py` | Weekly | 50,000 products |
| ANSES/EFSA websites | HTML→JSON | `data/raw/scraping/` | `extract_scraping.py` | Monthly | Guidelines |
| PostgreSQL (app) | SQL | DW star schema | `etl_load_warehouse.py` | Daily | Incremental |
| PostgreSQL (app) | SQL/Parquet | MinIO bronze | `etl_datalake_ingest.py` | Daily | Full snapshot |
| Raw sources merged | CSV/Parquet | `data/cleaned/` | `aggregate_clean.py` | Daily | ~50,000 rows |

## Extraction Sources (5 types — C8)

```mermaid
graph LR
    subgraph "5 Source Types"
        A["REST API<br/>extract_off_api.py"]
        B["Data File<br/>extract_off_parquet.py"]
        C["Web Scraping<br/>extract_scraping.py"]
        D["Database<br/>extract_from_db.py"]
        E["Big Data System<br/>extract_duckdb.py"]
    end

    A --> M["Merge & Clean<br/>aggregate_clean.py"]
    B --> M
    C --> M
    D --> M
    E --> M

    M --> OUT["products_cleaned.parquet<br/>products_cleaned.csv<br/>cleaning_report.json"]
```

## Data Cleaning Pipeline

The `aggregate_clean.py` script performs:

1. **Column standardization** — 30+ column name mappings across sources
2. **Barcode cleaning** — strip non-numeric, validate length 8–14
3. **Null removal** — drop products without names
4. **Range validation** — cap nutrient values at physiological max per 100g
5. **Nutri-Score normalization** — uppercase A–E
6. **Deduplication** — by barcode, keeping most complete record
7. **Quality report** — outputs `cleaning_report.json` with statistics
