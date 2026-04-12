# Data Flow

## End-to-End Pipeline

Data flows through 5 stages: Extract, Clean, Load (DB), Transform (DW), and Ingest (Lake).

```mermaid
graph TD
    subgraph Extract["1. Extract"]
        S1["OFF REST API<br/>Daily @ 02:00"]
        S2["Parquet via DuckDB<br/>Weekly SUN 03:00"]
        S3["Web Scraping<br/>Monthly 1st"]
    end

    subgraph Raw["2. Raw Storage"]
        R1["data/raw/api/*.json"]
        R2["data/raw/parquet/*.parquet"]
        R3["data/raw/scraping/*.json"]
    end

    subgraph Clean["3. Clean (PySpark)"]
        AGG["etl_aggregate_clean<br/>Daily @ 04:00<br/>7 cleaning rules<br/>798K in / 777K out"]
    end

    subgraph Load["4. Load"]
        direction LR
        DB["PostgreSQL<br/>app + raw + staging"]
        DW["PostgreSQL<br/>dw (star schema)"]
        DL["MinIO S3<br/>Bronze / Silver / Gold"]
    end

    subgraph Serve["5. Serve"]
        API["FastAPI REST"]
        ST["Streamlit Frontend"]
    end

    S1 --> R1
    S2 --> R2
    S3 --> R3

    R1 --> AGG
    R2 --> AGG
    R3 --> AGG

    AGG -->|"import to DB"| DB
    DB -->|"etl_load_warehouse<br/>Daily @ 05:00"| DW
    DB -->|"etl_datalake_ingest<br/>Daily @ 06:00"| DL

    DW --> ST
    DB --> API
    DB --> ST

    style Extract fill:#e8f5e9,stroke:#2e7d32
    style Raw fill:#fff9c4,stroke:#f57f17
    style Clean fill:#ffecb3,stroke:#ff8f00
    style Load fill:#e3f2fd,stroke:#1565c0
    style Serve fill:#fff3e0,stroke:#e65100
```

## Daily Schedule

All times in UTC. Orchestrated by Apache Airflow.

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

![Airflow DAGs list showing all 7 DAGs with execution history](assets/screenshots/airflow_dags_list.png)

## Flux Matrix

| Source | Format | Target | Script | Frequency | Volume |
|--------|--------|--------|--------|-----------|--------|
| OFF REST API | JSON | `data/raw/api/` | `extract_off_api.py` | Daily | ~1,000 products |
| OFF Parquet dump | Parquet | `data/raw/parquet/` | `extract_off_parquet.py` | Weekly (Sun) | 50,000+ products |
| ANSES/EFSA websites | HTML to JSON | `data/raw/scraping/` | `extract_scraping.py` | Monthly (1st) | Guidelines |
| Raw sources merged | Mixed | `data/cleaned/` | `aggregate_clean.py` | Daily | 798K in / 777K out |
| PostgreSQL (app) | SQL | DW star schema | `etl_load_warehouse.py` | Daily | Incremental |
| PostgreSQL (app) | Parquet/CSV | MinIO buckets | `etl_datalake_ingest.py` | Daily | Full snapshot |

## Data Volume Summary

| Stage | Records | Format | Storage |
|-------|---------|--------|---------|
| Raw (all sources combined) | 798,177 | JSON + Parquet | ~2 GB |
| Cleaned | 777,116 | Parquet + CSV | ~800 MB |
| Data Warehouse | 777K products + dimensions | PostgreSQL | ~500 MB |
| Data Lake (Bronze) | Raw copies | Original formats | ~2 GB |
| Data Lake (Silver) | Cleaned | Parquet | ~600 MB |
| Data Lake (Gold) | Aggregated | Parquet | ~100 MB |

!!! info "Extraction Sources"
    NutriTrack demonstrates 3 distinct extraction methods required by the certification: REST API, data file (Parquet via DuckDB), and web scraping (BeautifulSoup).
