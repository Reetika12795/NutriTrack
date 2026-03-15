# Medallion Architecture

## Overview (C18, C19)

The data lake uses a **medallion architecture** (Bronze → Silver → Gold) on MinIO, an S3-compatible object store.

```mermaid
graph LR
    subgraph Sources
        S1["OFF API<br/>(JSON)"]
        S2["Parquet Dump"]
        S3["Scraping<br/>(JSON)"]
        S4["PostgreSQL<br/>(SQL export)"]
    end

    subgraph Bronze["Bronze Layer<br/>Raw, immutable"]
        B1["products_api_*.json"]
        B2["products_parquet_*.parquet"]
        B3["guidelines_*.json"]
        B4["db_export_*.csv"]
    end

    subgraph Silver["Silver Layer<br/>Cleaned, validated"]
        SV1["products_cleaned.parquet"]
        SV2["products_deduplicated.parquet"]
        SV3["schema_validated.parquet"]
    end

    subgraph Gold["Gold Layer<br/>Analytics-ready"]
        G1["product_analytics.parquet"]
        G2["nutrition_metrics.parquet"]
        G3["brand_rankings.parquet"]
    end

    S1 --> B1
    S2 --> B2
    S3 --> B3
    S4 --> B4

    B1 --> SV1
    B2 --> SV1
    B3 --> SV1
    B4 --> SV1
    SV1 --> SV2 --> SV3

    SV3 --> G1
    SV3 --> G2
    SV3 --> G3

    style Bronze fill:#cd7f32,color:#fff,stroke:#8b4513
    style Silver fill:#c0c0c0,stroke:#808080
    style Gold fill:#ffd700,stroke:#daa520
```

## Layer Details

### Bronze — Raw Data

| Property | Value |
|----------|-------|
| **MinIO Bucket** | `bronze` |
| **Format** | Original format (JSON, Parquet, CSV) |
| **Treatment** | None — data stored as-is |
| **Retention** | 90 days (lifecycle rule) |
| **Purpose** | Audit trail, reprocessing capability |

### Silver — Cleaned Data

| Property | Value |
|----------|-------|
| **MinIO Bucket** | `silver` |
| **Format** | Parquet (columnar, compressed) |
| **Treatment** | Deduplication, schema validation, type casting, null handling |
| **Retention** | Indefinite |
| **Purpose** | Single source of truth for clean data |

### Gold — Analytics-Ready

| Property | Value |
|----------|-------|
| **MinIO Bucket** | `gold` |
| **Format** | Parquet (optimized for analytics) |
| **Treatment** | Aggregation, metric computation, business logic |
| **Retention** | Indefinite |
| **Purpose** | Direct consumption by analytics tools |

## MinIO Bucket Structure

```mermaid
graph TD
    MN["MinIO :9001"]

    MN --> BR["bronze/"]
    MN --> SL["silver/"]
    MN --> GL["gold/"]
    MN --> BK["backups/"]

    BR --> BR1["products/"]
    BR --> BR2["guidelines/"]
    BR --> BRC["_catalog/metadata.json"]

    SL --> SL1["products/"]
    SL --> SLC["_catalog/metadata.json"]

    GL --> GL1["analytics/"]
    GL --> GL2["metrics/"]
    GL --> GLC["_catalog/metadata.json"]

    BK --> BK1["full/"]
    BK --> BK2["dw/"]
```

## Volume / Velocity / Variety (V/V/V)

| Constraint | Challenge | Solution |
|-----------|-----------|----------|
| **Volume** | 3M+ products in OFF dump | DuckDB for columnar analytics, Parquet for compression |
| **Variety** | JSON, Parquet, CSV, SQL | Bronze layer accepts all formats; Silver normalizes to Parquet |
| **Velocity** | Daily incremental + weekly bulk | Airflow schedules: API daily, Parquet weekly, scraping monthly |

## Catalog Tool Comparison (C18)

| Criteria | Apache Atlas | DataHub | Custom JSON |
|----------|-------------|---------|-------------|
| Setup complexity | High (HBase + Solr) | Medium (Docker) | Low |
| Resource usage | 4GB+ RAM | 2GB+ RAM | Negligible |
| Search capability | Full-text | Full-text | Basic JSON |
| Lineage tracking | Built-in | Built-in | Manual |
| MinIO integration | Plugin | Plugin | Native (S3 API) |
| **Selected** | | | **Yes** |

**Justification**: Custom JSON catalog chosen for minimal overhead, direct MinIO integration, and project-scale sufficiency. The catalog metadata is co-located with the data in each bucket.
