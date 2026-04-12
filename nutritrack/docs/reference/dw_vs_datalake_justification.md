# Data Warehouse vs Data Lake — Architecture Justification

**Project**: NutriTrack — Fitness Nutrition Tracker
**Context**: Why NutriTrack maintains both a PostgreSQL data warehouse and a MinIO data lake, and why neither can replace the other.

---

## The Lakehouse Challenge

Modern data platforms (Databricks Delta Lake, Apache Iceberg + Trino, Snowflake) have blurred the line between data warehouses and data lakes. You can:

- Model a star schema in Parquet files on object storage
- Query it with SQL engines (Trino, Spark SQL, DuckDB, Athena)
- Manage transformations with dbt
- Get sub-second latency with caching layers

So **why keep a separate PostgreSQL DW when you could do everything in the lake?**

The answer is not "SQL vs files" — data scientists write SQL all the time, and query engines make Parquet queryable. The answer is about **what data lives where and why**.

---

## The Real Differentiator: RGPD Boundary

The data lake contains **only product data** (public Open Food Facts data — no personal information).

The data warehouse contains **product data AND user data** (pseudonymized meal tracking, user dimensions, consumption patterns).

This is not an arbitrary split. It is the **RGPD compliance boundary**.

### Why user data cannot enter the lake

| RGPD Requirement | PostgreSQL DW | MinIO Lake (Parquet files) |
|---|---|---|
| **Row-level security** | Native (`CREATE POLICY ... USING (user_id = current_user)`) | Not possible — Parquet files are all-or-nothing |
| **Granular deletion** (Right to erasure, Art. 17) | `DELETE FROM fact_daily_nutrition WHERE user_key = X` — atomic, auditable | No granular row deletion on immutable Parquet files |
| **Access audit trail** | PostgreSQL `pg_audit` logs who queried what | MinIO access logs exist but lack query-level granularity |
| **Consent-based filtering** | SQL `WHERE consent_data_processing = TRUE` at query time | Would require rewriting entire Parquet files |
| **Data registry integration** | `app.rgpd_data_registry` table documents all personal data fields, purposes, retention, legal basis | No equivalent mechanism in object storage |
| **Automated cleanup** | `cleanup_expired_data()` PostgreSQL function runs on schedule | Lifecycle rules delete whole files, not individual records |

Even with pseudonymization (`encode(digest(user_id::text, 'sha256'), 'hex')`), the `fact_daily_nutrition` table contains personal data under RGPD because:
- Meal patterns + timestamps + age group can potentially re-identify individuals
- RGPD Article 4(5) recognizes pseudonymized data as personal data requiring protection

**The lake is the RGPD-safe zone**: only public product data, no personal information, no re-identification risk.

---

## Secondary Differentiators

### ACID Transactions

The star schema requires transactional consistency:
- SCD Type 2 closes an old record and opens a new one — this must be **atomic** (both happen or neither happens)
- `fact_daily_nutrition` inserts reference dimension keys that must exist — **referential integrity**
- Concurrent operations (user logs a meal while ETL updates product dimensions) need **isolation**

Parquet files on MinIO are append-only. Delta Lake and Iceberg add transaction support to object storage, but introducing them means adding Spark or Trino to the stack — over-engineering for NutriTrack's scale (hundreds of thousands of products, not billions).

### Query Latency for Interactive Dashboards

| Access Pattern | PostgreSQL DW | MinIO + Query Engine |
|---|---|---|
| Dashboard query (indexed star schema) | **<100ms** | Seconds (file scan, even with Trino) |
| Full table scan for ML training | Slow (row-oriented storage) | **Fast** (columnar Parquet, read only needed columns) |
| Point-in-time historical query | Complex temporal SQL on SCD | **Simple** (load dated snapshot file) |
| Concurrent dashboard users | Handles well (connection pooling) | Requires dedicated query engine cluster |

The DW is optimized for **many small queries** (dashboards). The lake is optimized for **few large reads** (data science).

---

## Architecture Summary

```
                  Extract DAGs → /data/raw/
                         │
              etl_aggregate_clean (04:00)
              aggregate → clean → load to PostgreSQL app
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
    etl_datalake_ingest (05:00)  etl_load_warehouse (05:00)
    Lake Path                    DW Path
    (product data only,          (product + user data)
     NO PostgreSQL dependency)
              │                     │
     Bronze (raw archive)      PostgreSQL app schema
              │                     │
     Silver (cleaned Parquet)  dw schema (star schema,
              │                 SCD Type 1/2/3,
     Gold (denormalized,        fact tables with
      ML features,              user meal data)
      quality reports,               │
      daily snapshots)          Consumers:
              │                 BI analysts,
         Consumers:             Metabase dashboards
      Data scientists,
      ML engineers
```

The two paths are **parallel and independent**. The gold layer reads from silver Parquet files (pandas only), while the DW reads from PostgreSQL `app` schema (SQL ETL with SCD and user data). Both use `ExternalTaskSensor` to wait for `etl_aggregate_clean` to complete.

### What each system contains

| Content | DW (`dw` schema) | Lake (MinIO gold) |
|---|---|---|
| Product dimensions | `dim_product`, `dim_brand`, `dim_category` (normalized) | `product_wide_denormalized.parquet` (flat) |
| User dimensions | `dim_user` (pseudonymized) | **Not present** (RGPD) |
| Meal tracking facts | `fact_daily_nutrition` | **Not present** (RGPD) |
| Product market facts | `fact_product_market` | Equivalent data exists in wide table but structured differently |
| Data quality metadata | Not present (not business data) | `data_quality_report.parquet` |
| Source lineage | Not present | `source_comparison.parquet` |
| ML-ready features | Not present (raw values only) | `ml_nutrition_features.parquet` (scaled, encoded, imputed) |
| Point-in-time snapshots | Reconstructable via SCD temporal queries | `daily_snapshots/` (one file per date) |

### The one-sentence justification

> The DW handles RGPD-controlled personal data (user meals, pseudonymized dimensions) with ACID transactions and sub-100ms dashboard queries. The lake handles public product data for data science workflows where bulk access, schema flexibility, and point-in-time reproducibility matter more than transactional consistency. User data never enters the lake — that is our RGPD boundary.

---

## Could we replace both with a single lakehouse?

**Yes, technically.** With Delta Lake + Spark + Trino + fine-grained access control, you could unify everything into one system. Many companies are moving in this direction.

**Why we don't for NutriTrack:**
1. **Complexity cost**: Adding Spark + Trino + Delta Lake to a 10-service Docker Compose stack would double the infrastructure for marginal benefit at this scale
2. **RGPD simplicity**: Having a clear physical boundary ("user data = PostgreSQL, product data = MinIO") is easier to audit and explain than row-level policies across a unified lakehouse
3. **The right tool for the right scale**: At hundreds of thousands of products and hundreds of users, PostgreSQL handles both OLTP and OLAP efficiently. A lakehouse makes sense at petabyte scale with thousands of concurrent analysts

The architecture is designed to be **evolvable**: migrating the DW to a lakehouse would require changing the ETL target connection, not redesigning the schema.

---

*This document supports competencies C3 (technical framework justification), C18 (data lake architecture), and the oral defense argumentation for E5/E7.*
