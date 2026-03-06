"""
Airflow DAG: Ingest data into MinIO Data Lake (Medallion Architecture)
Schedule: Daily at 05:00 UTC (parallel with etl_load_warehouse, after etl_aggregate_clean)
Covers: C18 (Data lake architecture), C19 (Infrastructure), C20 (Catalog)

Architecture: This DAG is one of two parallel consumers of etl_aggregate_clean output.
  - Lake path: silver Parquet → gold (pandas only, NO PostgreSQL dependency)
  - DW path:   PostgreSQL app → dw star schema (SQL ETL with SCD + user data)
Both paths are independent. The gold layer reads from silver, not from PostgreSQL.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _get_minio_client():
    import os
    from minio import Minio
    return Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
        secure=False,
    )


def ingest_to_bronze(**context):
    """
    Bronze layer: Raw data ingestion (as-is from sources).
    Medallion architecture: Bronze = raw, unprocessed data.
    """
    import json
    from pathlib import Path
    from io import BytesIO

    client = _get_minio_client()
    ds = context["ds"]
    ingested = 0

    # Ingest raw API data
    api_dir = Path("/opt/airflow/data/raw/api")
    for f in api_dir.glob("*.json"):
        object_name = f"api/{ds}/{f.name}"
        client.fput_object("bronze", object_name, str(f))
        print(f"Bronze: {f.name} -> bronze/{object_name}")
        ingested += 1

    # Ingest raw Parquet data
    parquet_dir = Path("/opt/airflow/data/raw/parquet")
    for f in parquet_dir.glob("*.parquet"):
        object_name = f"parquet/{ds}/{f.name}"
        client.fput_object("bronze", object_name, str(f))
        print(f"Bronze: {f.name} -> bronze/{object_name}")
        ingested += 1

    # Ingest scraping data
    scraping_dir = Path("/opt/airflow/data/raw/scraping")
    for f in scraping_dir.glob("*.json"):
        object_name = f"scraping/{ds}/{f.name}"
        client.fput_object("bronze", object_name, str(f))
        print(f"Bronze: {f.name} -> bronze/{object_name}")
        ingested += 1

    # Ingest DuckDB analytics
    duckdb_dir = Path("/opt/airflow/data/raw/duckdb")
    for f in duckdb_dir.glob("*.parquet"):
        object_name = f"duckdb/{ds}/{f.name}"
        client.fput_object("bronze", object_name, str(f))
        print(f"Bronze: {f.name} -> bronze/{object_name}")
        ingested += 1

    # Write manifest
    manifest = {
        "ingestion_date": ds,
        "files_ingested": ingested,
        "layer": "bronze",
    }
    manifest_bytes = json.dumps(manifest, indent=2).encode()
    client.put_object(
        "bronze", f"_manifests/{ds}.json",
        BytesIO(manifest_bytes), len(manifest_bytes),
        content_type="application/json",
    )

    # ── Lineage metadata ─────────────────────────────────────────────
    # Records which sources were available, file sizes, row counts
    # before any processing. Supports traceability (C20).
    lineage = {
        "ingestion_date": ds,
        "sources": {},
    }

    for source_name, source_dir, extensions in [
        ("api", Path("/opt/airflow/data/raw/api"), ["*.json"]),
        ("parquet", Path("/opt/airflow/data/raw/parquet"), ["*.parquet"]),
        ("scraping", Path("/opt/airflow/data/raw/scraping"), ["*.json"]),
        ("duckdb", Path("/opt/airflow/data/raw/duckdb"), ["*.parquet"]),
    ]:
        files_info = []
        for ext in extensions:
            for f in source_dir.glob(ext):
                file_info = {
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                    "modified": str(datetime.fromtimestamp(f.stat().st_mtime)),
                }
                # Count rows for structured files
                if f.suffix == ".parquet":
                    try:
                        import pyarrow.parquet as pq
                        file_info["row_count"] = pq.read_metadata(str(f)).num_rows
                    except Exception:
                        pass
                elif f.suffix == ".json":
                    try:
                        with open(f) as fh:
                            data = json.load(fh)
                        if isinstance(data, dict) and data.get("products"):
                            file_info["row_count"] = len(data["products"])
                        elif isinstance(data, list):
                            file_info["row_count"] = len(data)
                    except Exception:
                        pass
                files_info.append(file_info)

        lineage["sources"][source_name] = {
            "available": len(files_info) > 0,
            "file_count": len(files_info),
            "total_size_bytes": sum(f["size_bytes"] for f in files_info),
            "total_rows": sum(f.get("row_count", 0) for f in files_info),
            "files": files_info,
        }

    lineage_bytes = json.dumps(lineage, indent=2).encode()
    client.put_object(
        "bronze", f"_lineage/{ds}.json",
        BytesIO(lineage_bytes), len(lineage_bytes),
        content_type="application/json",
    )
    print(f"Bronze: lineage metadata -> bronze/_lineage/{ds}.json")

    print(f"Bronze layer: {ingested} files ingested for {ds}")
    return ingested


def transform_to_silver(**context):
    """
    Silver layer: Cleaned and validated data.
    Medallion architecture: Silver = cleaned, deduplicated, schema-conformed.
    Also produces data quality metadata (C20 — catalog management).
    """
    import json
    from pathlib import Path
    from io import BytesIO

    import pandas as pd

    client = _get_minio_client()
    ds = context["ds"]

    cleaned_dir = Path("/opt/airflow/data/cleaned")

    # Upload cleaned products
    for f in cleaned_dir.glob("products_cleaned.*"):
        object_name = f"products/{ds}/{f.name}"
        client.fput_object("silver", object_name, str(f))
        print(f"Silver: {f.name} -> silver/{object_name}")

    # Upload cleaning report
    report_path = cleaned_dir / "cleaning_report.json"
    if report_path.exists():
        object_name = f"_reports/{ds}/cleaning_report.json"
        client.fput_object("silver", object_name, str(report_path))

    # ── Data quality metadata ────────────────────────────────────────
    # Completeness scores, rows dropped, null rates per column,
    # cleaning decisions log. Supports C20 (catalog — metadata about
    # data quality) and provides traceability for the silver layer.
    parquet_path = cleaned_dir / "products_cleaned.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)

        # Count raw rows from bronze sources for comparison
        raw_dir = Path("/opt/airflow/data/raw")
        raw_row_counts = {}
        for subdir in ["api", "parquet", "duckdb"]:
            dir_path = raw_dir / subdir
            if not dir_path.exists():
                continue
            count = 0
            for f in dir_path.glob("*.parquet"):
                count += len(pd.read_parquet(f))
            for f in dir_path.glob("*.json"):
                import json as json_mod
                with open(f) as fh:
                    data = json_mod.load(fh)
                if isinstance(data, dict) and data.get("products"):
                    count += len(data["products"])
                elif isinstance(data, list):
                    count += len(data)
            if count > 0:
                raw_row_counts[subdir] = count

        total_raw = sum(raw_row_counts.values()) if raw_row_counts else 0

        quality_report = {
            "report_date": ds,
            "cleaned_row_count": len(df),
            "raw_row_counts": raw_row_counts,
            "total_raw_rows": total_raw,
            "rows_dropped": total_raw - len(df) if total_raw > 0 else None,
            "drop_rate_pct": round((total_raw - len(df)) / total_raw * 100, 2) if total_raw > 0 else None,
            "column_quality": {
                col: {
                    "null_count": int(df[col].isna().sum()),
                    "null_pct": round(df[col].isna().sum() / len(df) * 100, 2),
                    "completeness_pct": round((1 - df[col].isna().sum() / len(df)) * 100, 2),
                    "unique_values": int(df[col].nunique()),
                }
                for col in df.columns
            },
            "cleaning_decisions": [
                "Barcodes: stripped non-numeric chars, kept 8-14 digits only",
                "Product name: dropped rows with null product_name",
                "Numeric columns: coerced to numeric, capped at physiological max per 100g",
                "Nutriscore: normalized to uppercase A-E, invalid grades set to null",
                "Deduplication: by barcode, kept row with highest completeness_score",
            ],
        }

        quality_bytes = json.dumps(quality_report, indent=2, default=str).encode()
        quality_name = f"_quality/{ds}/data_quality_report.json"
        client.put_object(
            "silver", quality_name,
            BytesIO(quality_bytes), len(quality_bytes),
            content_type="application/json",
        )
        print(f"Silver: quality report -> silver/{quality_name}")

    print(f"Silver layer updated for {ds}")


def _download_silver_parquet(client, ds):
    """Download the silver products Parquet file from MinIO."""
    from io import BytesIO
    import pandas as pd

    # Try date-partitioned path first, then fall back to latest
    paths_to_try = [
        f"products/{ds}/products_cleaned.parquet",
        "products/latest/products_cleaned.parquet",
    ]

    for object_name in paths_to_try:
        try:
            response = client.get_object("silver", object_name)
            data = response.read()
            response.close()
            response.release_conn()
            df = pd.read_parquet(BytesIO(data))
            print(f"Silver: loaded {len(df)} rows from silver/{object_name}")
            return df
        except Exception:
            continue

    # Last resort: list silver/products/ and grab the most recent file
    try:
        objects = list(client.list_objects("silver", prefix="products/", recursive=True))
        parquet_objects = [o for o in objects if o.object_name.endswith(".parquet")]
        if parquet_objects:
            latest = sorted(parquet_objects, key=lambda o: o.last_modified, reverse=True)[0]
            response = client.get_object("silver", latest.object_name)
            data = response.read()
            response.close()
            response.release_conn()
            df = pd.read_parquet(BytesIO(data))
            print(f"Silver: loaded {len(df)} rows from silver/{latest.object_name}")
            return df
    except Exception as e:
        print(f"Error listing silver objects: {e}")

    return pd.DataFrame()


def publish_to_gold(**context):
    """
    Gold layer: Denormalized, ML-ready, and metadata datasets for data scientists.

    Source: Silver layer Parquet (NOT PostgreSQL).
    The gold layer reads from silver — making the lake independent of the DW.
    Both the lake (silver → gold) and the DW (app → dw) are parallel consumers
    of the cleaned data produced by etl_aggregate_clean.

    Datasets produced:
    1. product_wide_denormalized — every product with all nutrition columns inlined
    2. data_quality_report — completeness rates, null %, anomaly flags per column
    3. source_comparison — row counts per extraction source, coverage rates
    4. daily_snapshot — full product catalog as one dated file (time-travel)
    5. ml_nutrition_features — scaled/encoded feature matrix for model training
    """
    from io import BytesIO

    import numpy as np
    import pandas as pd

    client = _get_minio_client()
    ds = context["ds"]

    def _upload_parquet(df, name):
        """Helper to upload a DataFrame as Parquet to the gold bucket."""
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        object_name = f"{name}/{ds}/{name.split('/')[-1]}.parquet"
        client.put_object("gold", object_name, buffer, len(buffer.getvalue()))
        print(f"Gold: {name} -> gold/{object_name} ({len(df)} rows)")

    # ── Load silver data ─────────────────────────────────────────────
    df_wide = _download_silver_parquet(client, ds)
    if df_wide.empty:
        print("No silver data available — skipping gold layer")
        return

    # ── 1. Product Wide Denormalized ─────────────────────────────────
    # The silver Parquet already contains all product columns in a flat
    # structure. Unlike the DW (which requires JOINs across dim_product,
    # dim_brand, dim_category), data scientists get pd.read_parquet() → go.
    try:
        _upload_parquet(df_wide, "product_wide_denormalized")
    except Exception as e:
        print(f"Error building product_wide_denormalized: {e}")

    # ── 2. Data Quality Report ───────────────────────────────────────
    # Metadata ABOUT the data: completeness rates, null percentages,
    # anomaly flags per column. This doesn't belong in a star schema —
    # it's observatory data for data stewards and scientists.
    try:
        numeric_cols = df_wide.select_dtypes(include=[np.number]).columns.tolist()
        quality_rows = []
        for col in df_wide.columns:
            total = len(df_wide)
            null_count = int(df_wide[col].isna().sum())
            completeness = round((total - null_count) / total * 100, 2) if total > 0 else 0
            row = {
                "column_name": col,
                "total_rows": total,
                "null_count": null_count,
                "null_pct": round(null_count / total * 100, 2) if total > 0 else 0,
                "completeness_pct": completeness,
                "unique_count": int(df_wide[col].nunique()),
            }
            if col in numeric_cols:
                row["min"] = float(df_wide[col].min()) if not df_wide[col].isna().all() else None
                row["max"] = float(df_wide[col].max()) if not df_wide[col].isna().all() else None
                row["mean"] = round(float(df_wide[col].mean()), 2) if not df_wide[col].isna().all() else None
                row["std"] = round(float(df_wide[col].std()), 2) if not df_wide[col].isna().all() else None
                # Flag anomalies: values beyond 3 standard deviations
                if row["std"] and row["std"] > 0:
                    outlier_mask = (df_wide[col] - row["mean"]).abs() > 3 * row["std"]
                    row["outlier_count"] = int(outlier_mask.sum())
                else:
                    row["outlier_count"] = 0
            quality_rows.append(row)

        df_quality = pd.DataFrame(quality_rows)
        _upload_parquet(df_quality, "data_quality_report")
    except Exception as e:
        print(f"Error building data_quality_report: {e}")

    # ── 3. Source Comparison ─────────────────────────────────────────
    # Cross-source lineage analysis built from the data_source column
    # in the silver dataset. No PostgreSQL needed.
    try:
        if "data_source" in df_wide.columns:
            source_groups = df_wide.groupby("data_source")
            source_rows = []
            total_unique = df_wide["barcode"].nunique() if "barcode" in df_wide.columns else len(df_wide)

            for source, group in source_groups:
                unique_barcodes = group["barcode"].nunique() if "barcode" in group.columns else len(group)
                row = {
                    "data_source": source,
                    "product_count": len(group),
                    "unique_barcodes": unique_barcodes,
                    "avg_completeness": round(group["completeness_score"].mean(), 2) if "completeness_score" in group.columns else None,
                    "has_nutriscore": int(group["nutriscore_grade"].notna().sum()) if "nutriscore_grade" in group.columns else 0,
                    "has_energy": int(group["energy_kcal"].notna().sum()) if "energy_kcal" in group.columns else 0,
                    "has_proteins": int(group["proteins_g"].notna().sum()) if "proteins_g" in group.columns else 0,
                    "total_unique_products": total_unique,
                    "source_share_pct": round(unique_barcodes / total_unique * 100, 2) if total_unique > 0 else 0,
                }
                source_rows.append(row)

            df_sources = pd.DataFrame(source_rows)
            _upload_parquet(df_sources, "source_comparison")
        else:
            print("No data_source column in silver data — skipping source_comparison")
    except Exception as e:
        print(f"Error building source_comparison: {e}")

    # ── 4. Daily Snapshot ────────────────────────────────────────────
    # Full product catalog as one dated file. Enables time-travel without
    # SCD: "give me the entire catalog as it was on March 3rd."
    try:
        snapshot_buffer = BytesIO()
        df_wide.to_parquet(snapshot_buffer, index=False)
        snapshot_buffer.seek(0)
        snapshot_name = f"daily_snapshots/{ds}/catalog_snapshot.parquet"
        client.put_object("gold", snapshot_name, snapshot_buffer, len(snapshot_buffer.getvalue()))
        print(f"Gold: daily_snapshot -> gold/{snapshot_name} ({len(df_wide)} rows)")
    except Exception as e:
        print(f"Error building daily_snapshot: {e}")

    # ── 5. ML Nutrition Features ─────────────────────────────────────
    # Numeric feature matrix ready for model training: scaled, encoded,
    # no nulls. The DW stores raw values — this is engineered features
    # that a data scientist can load directly into scikit-learn.
    try:
        feature_cols = [
            "energy_kcal", "fat_g", "carbohydrates_g", "proteins_g",
            "fiber_g", "salt_g", "sugars_g", "nutriscore_score",
            "nova_group", "completeness_score",
        ]
        available_cols = [c for c in feature_cols if c in df_wide.columns]
        if available_cols:
            df_features = df_wide[["barcode"] + available_cols].copy() if "barcode" in df_wide.columns else df_wide[available_cols].copy()

            # Drop rows where ALL numeric features are null
            df_features = df_features.dropna(subset=available_cols, how="all")

            # Fill remaining nulls with column median (standard ML imputation)
            for col in available_cols:
                median_val = df_features[col].median()
                df_features[col] = df_features[col].fillna(median_val if pd.notna(median_val) else 0)

            # Min-max scaling to [0, 1] for each feature
            for col in available_cols:
                col_min = df_features[col].min()
                col_max = df_features[col].max()
                if col_max > col_min:
                    df_features[f"{col}_scaled"] = (
                        (df_features[col] - col_min) / (col_max - col_min)
                    ).round(4)
                else:
                    df_features[f"{col}_scaled"] = 0.0

            # One-hot encode nutriscore_grade if available in silver data
            if "nutriscore_grade" in df_wide.columns:
                grades = df_wide.loc[df_features.index, "nutriscore_grade"]
                for grade in ["A", "B", "C", "D", "E"]:
                    df_features[f"nutriscore_is_{grade}"] = (grades == grade).astype(int)

            _upload_parquet(df_features, "ml_nutrition_features")
    except Exception as e:
        print(f"Error building ml_nutrition_features: {e}")

    print(f"Gold layer published for {ds} (source: silver Parquet)")


def update_catalog_metadata(**context):
    """
    Update data catalog metadata in MinIO.
    Covers: C20 - Data catalog management.
    """
    import json
    from io import BytesIO

    client = _get_minio_client()
    ds = context["ds"]

    # Build catalog metadata
    catalog = {
        "last_updated": ds,
        "architecture": {
            "principle": "The DW and the Lake answer different questions for different people",
            "data_warehouse": {
                "serves": "BI analysts, dashboards (SQL)",
                "optimized_for": "Fast JOINs across normalized dimensions",
                "content": "Star schema: dims + facts (SCD Type 1/2/3)",
                "schema_strategy": "Schema-on-write (strict)",
            },
            "data_lake": {
                "serves": "Data scientists, ML engineers (Python/Spark)",
                "optimized_for": "Flat files, no schema knowledge needed",
                "content": "Denormalized wide tables, quality reports, ML features, snapshots",
                "schema_strategy": "Schema-on-read (flexible)",
            },
        },
        "datasets": {
            "bronze/api": {
                "description": "Raw product data from Open Food Facts REST API",
                "format": "JSON",
                "update_frequency": "daily",
                "source": "Open Food Facts API",
                "schema": "OFF product schema (barcode, product_name, nutrition, scores)",
                "owner": "etl_service",
                "quality": "raw, unvalidated",
                "consumers": ["etl_aggregate_clean DAG"],
            },
            "bronze/parquet": {
                "description": "Raw product data from OFF Parquet export",
                "format": "Parquet",
                "update_frequency": "weekly",
                "source": "Open Food Facts data export",
                "schema": "OFF full product schema (3M+ products)",
                "owner": "etl_service",
                "quality": "raw, may contain nulls and duplicates",
                "consumers": ["etl_aggregate_clean DAG"],
            },
            "bronze/scraping": {
                "description": "Nutritional guidelines from health authority websites",
                "format": "JSON",
                "update_frequency": "weekly",
                "source": "ANSES, EFSA, EU Regulation 1169/2011",
                "owner": "etl_service",
                "quality": "raw, may include parsing errors",
                "consumers": ["etl_aggregate_clean DAG"],
            },
            "bronze/_lineage": {
                "description": "Ingestion lineage: source availability, file sizes, row counts before processing",
                "format": "JSON (one file per ingestion date)",
                "purpose": "Traceability and auditing of raw data ingestion",
                "consumers": ["data stewards", "audit"],
            },
            "silver/products": {
                "description": "Cleaned, deduplicated product dataset",
                "format": "Parquet, CSV",
                "update_frequency": "daily",
                "source": "Aggregation of all bronze sources",
                "schema": "Standardized product schema (barcode, name, nutrition, scores)",
                "owner": "etl_service",
                "quality": "validated, deduplicated, format-normalized",
                "lineage": ["bronze/api", "bronze/parquet", "bronze/duckdb"],
                "consumers": ["etl_load_warehouse DAG", "gold layer ETL"],
            },
            "silver/_quality": {
                "description": "Data quality reports: completeness, null rates, cleaning decisions per ingestion",
                "format": "JSON (one file per date)",
                "purpose": "Quality monitoring and cleaning traceability",
                "consumers": ["data stewards", "gold/data_quality_report"],
            },
            "gold/product_wide_denormalized": {
                "description": "Every product with all nutrition columns inlined into ONE flat table",
                "format": "Parquet",
                "update_frequency": "daily",
                "why_not_in_dw": "DW requires JOINs across 4 tables. Data scientist wants pd.read_parquet() and go",
                "consumers": ["data scientists", "ML engineers", "exploratory analysis"],
                "lineage": ["silver/products (Parquet)"],
            },
            "gold/data_quality_report": {
                "description": "Completeness rates, null percentages, anomaly flags per column per source",
                "format": "Parquet",
                "update_frequency": "daily",
                "why_not_in_dw": "Metadata ABOUT data, not business data. Doesn't belong in a star schema",
                "consumers": ["data stewards", "data quality dashboards"],
                "lineage": ["silver/products (Parquet)"],
            },
            "gold/source_comparison": {
                "description": "Row counts, overlap rates, unique products per extraction source",
                "format": "Parquet",
                "update_frequency": "daily",
                "why_not_in_dw": "Cross-source lineage analysis. The DW doesn't track which source a fact came from",
                "consumers": ["data engineers", "pipeline monitoring"],
                "lineage": ["silver/products (data_source column in Parquet)"],
            },
            "gold/daily_snapshots": {
                "description": "Full product catalog as one dated file — time-travel without SCD",
                "format": "Parquet (date-partitioned)",
                "update_frequency": "daily",
                "why_not_in_dw": "DW historizes row-level changes (SCD). Snapshots provide full-state-at-a-date files",
                "consumers": ["data scientists", "historical analysis", "model training"],
                "lineage": ["silver/products (Parquet)"],
            },
            "gold/ml_nutrition_features": {
                "description": "Numeric feature matrix (scaled, encoded, no nulls) ready for ML model training",
                "format": "Parquet",
                "update_frequency": "daily",
                "why_not_in_dw": "ML preprocessing — DW stores raw values, not engineered features",
                "consumers": ["ML engineers", "model training pipelines"],
                "lineage": ["silver/products (Parquet)"],
            },
        },
        "governance": {
            "rgpd_compliance": True,
            "personal_data_datasets": [
                "No personal data in data lake (user data stays in PostgreSQL app schema only)",
            ],
            "retention_policy": {
                "bronze": "90 days (lifecycle auto-delete)",
                "silver": "1 year",
                "gold": "indefinite",
            },
            "access_groups": {
                "data_scientists": ["gold/* (read) — primary consumers of denormalized + ML datasets"],
                "data_stewards": ["silver/_quality (read)", "gold/data_quality_report (read)", "bronze/_lineage (read)"],
                "app_users": ["gold/product_wide_denormalized (read)"],
                "nutritionists": ["silver/products (read)", "gold/product_wide_denormalized (read)"],
                "admins": ["all buckets (full)"],
                "etl_service": ["all buckets (write)"],
            },
        },
    }

    catalog_bytes = json.dumps(catalog, indent=2).encode()

    # Store in each bucket
    for bucket in ["bronze", "silver", "gold"]:
        client.put_object(
            bucket, "_catalog/metadata.json",
            BytesIO(catalog_bytes), len(catalog_bytes),
            content_type="application/json",
        )

    print(f"Catalog metadata updated for {ds}")


with DAG(
    "etl_datalake_ingest",
    default_args=default_args,
    description="Ingest data into MinIO Data Lake with Medallion Architecture (parallel with DW, reads silver not PostgreSQL)",
    schedule_interval="0 5 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["datalake", "minio", "medallion", "bronze", "silver", "gold"],
) as dag:

    # Wait for etl_aggregate_clean.clean_data before starting silver/gold
    # (bronze can run independently since it reads raw files)
    wait_for_clean = ExternalTaskSensor(
        task_id="wait_for_aggregate_clean",
        external_dag_id="etl_aggregate_clean",
        external_task_id="clean_data",
        execution_delta=timedelta(hours=1),  # this DAG runs at 05:00, aggregate_clean at 04:00
        timeout=3600,
        poke_interval=60,
        mode="reschedule",
    )

    bronze = PythonOperator(task_id="ingest_to_bronze", python_callable=ingest_to_bronze)
    silver = PythonOperator(task_id="transform_to_silver", python_callable=transform_to_silver)
    gold = PythonOperator(task_id="publish_to_gold", python_callable=publish_to_gold)
    catalog = PythonOperator(task_id="update_catalog_metadata", python_callable=update_catalog_metadata)

    # Bronze runs in parallel with the sensor wait.
    # Silver needs both bronze and cleaned data to be ready.
    wait_for_clean >> silver
    bronze >> silver >> gold >> catalog
