"""
Airflow DAG: Aggregate and clean data from all extraction sources
Schedule: Daily at 04:00 UTC (after extraction DAGs complete)
Covers: C10 (Data aggregation), C15 (ETL pipeline)

This DAG is the single transformation step that feeds BOTH downstream paths:
  - Lake path (etl_datalake_ingest @ 05:00): silver reads cleaned Parquet files
  - DW path  (etl_load_warehouse  @ 05:00): reads from PostgreSQL app schema
Both downstream DAGs use ExternalTaskSensors to wait for this DAG to complete.
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


def aggregate_all_sources(**context):
    """Load and merge data from all raw extraction outputs."""
    import json
    import re
    from pathlib import Path

    import pandas as pd

    raw_dir = Path("/opt/airflow/data/raw")
    dfs = []

    # Load API data
    for f in sorted((raw_dir / "api").glob("*.json"), reverse=True)[:1]:
        with open(f) as fh:
            data = json.load(fh)
        if data.get("products"):
            df = pd.DataFrame(data["products"])
            df["data_source"] = "api"
            dfs.append(df)
            print(f"API: {len(df)} products from {f.name}")

    # Load Parquet data
    for f in sorted((raw_dir / "parquet").glob("*.parquet"), reverse=True)[:1]:
        df = pd.read_parquet(f)
        df["data_source"] = "parquet"
        dfs.append(df)
        print(f"Parquet: {len(df)} products from {f.name}")

    # Load DuckDB analytics data
    for f in sorted((raw_dir / "duckdb").glob("france_*.parquet"), reverse=True)[:1]:
        df = pd.read_parquet(f)
        df["data_source"] = "duckdb"
        dfs.append(df)
        print(f"DuckDB: {len(df)} products from {f.name}")

    if not dfs:
        print("No source data found")
        return None

    merged = pd.concat(dfs, ignore_index=True)
    print(f"Merged: {len(merged)} total rows")
    return len(merged)


def clean_data(**context):
    """Apply cleaning rules: dedup, format homogenization, corruption removal."""
    import json
    import re
    from pathlib import Path

    import pandas as pd

    raw_dir = Path("/opt/airflow/data/raw")
    cleaned_dir = Path("/opt/airflow/data/cleaned")
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    # Load latest merged data
    dfs = []
    for subdir in ["api", "parquet", "duckdb"]:
        dir_path = raw_dir / subdir
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.glob("*.parquet"), reverse=True)[:1]:
            dfs.append(pd.read_parquet(f))
        for f in sorted(dir_path.glob("*.csv"), reverse=True)[:1]:
            dfs.append(pd.read_csv(f, low_memory=False))
        for f in sorted(dir_path.glob("*.json"), reverse=True)[:1]:
            with open(f) as fh:
                data = json.load(fh)
            if isinstance(data, dict) and data.get("products"):
                dfs.append(pd.DataFrame(data["products"]))
            elif isinstance(data, list):
                dfs.append(pd.DataFrame(data))

    if not dfs:
        print("No data to clean")
        return None

    df = pd.concat(dfs, ignore_index=True)

    # Standardize column names
    col_map = {
        "code": "barcode", "brands": "brand_name",
        "categories": "category_name",
        "energy-kcal_100g": "energy_kcal",
        "fat_100g": "fat_g", "proteins_100g": "proteins_g",
        "carbohydrates_100g": "carbohydrates_g",
        "sugars_100g": "sugars_g", "fiber_100g": "fiber_g",
        "salt_100g": "salt_g",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Clean barcodes
    if "barcode" in df.columns:
        df["barcode"] = df["barcode"].astype(str).str.strip().str.replace(r"[^0-9]", "", regex=True)
        df = df[df["barcode"].str.len().between(8, 14)]

    # Remove entries without product name
    if "product_name" in df.columns:
        df = df.dropna(subset=["product_name"])

    # Validate numeric ranges (per 100g)
    for col, max_val in [("energy_kcal", 1000), ("fat_g", 100), ("proteins_g", 100),
                          ("carbohydrates_g", 100), ("sugars_g", 100), ("salt_g", 100)]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] > max_val, col] = None
            df.loc[df[col] < 0, col] = None

    # Normalize Nutri-Score
    if "nutriscore_grade" in df.columns:
        df["nutriscore_grade"] = df["nutriscore_grade"].astype(str).str.upper().str.strip()
        df.loc[~df["nutriscore_grade"].isin(["A", "B", "C", "D", "E"]), "nutriscore_grade"] = None

    # Deduplicate by barcode (keep most complete)
    if "completeness_score" in df.columns:
        df = df.sort_values("completeness_score", ascending=False)
    df = df.drop_duplicates(subset=["barcode"], keep="first")

    # Keep only usable columns (drop nested/complex objects that break Parquet)
    keep_cols = [
        "barcode", "product_name", "generic_name", "brands", "brand_name",
        "categories", "category_name", "countries", "quantity", "packaging",
        "ingredients_text", "energy_kcal", "fat_g", "proteins_g",
        "carbohydrates_g", "sugars_g", "fiber_g", "salt_g",
        "nutriscore_grade", "nutriscore_score", "nova_group",
        "ecoscore_grade", "completeness_score", "data_source",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    # Save
    output_path = cleaned_dir / "products_cleaned.parquet"
    df.to_parquet(str(output_path), index=False)
    df.to_csv(str(cleaned_dir / "products_cleaned.csv"), index=False)

    print(f"Cleaned: {len(df)} products -> {output_path}")
    return str(output_path)


def load_to_database(**context):
    """Load cleaned data into operational PostgreSQL database."""
    import os
    from pathlib import Path

    import pandas as pd
    from sqlalchemy import create_engine, text

    cleaned_path = Path("/opt/airflow/data/cleaned/products_cleaned.parquet")
    if not cleaned_path.exists():
        print("No cleaned data found")
        return 0

    df = pd.read_parquet(cleaned_path)

    db_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('NUTRITRACK_DB_USER', 'nutritrack')}:"
        f"{os.getenv('NUTRITRACK_DB_PASSWORD', 'nutritrack')}@"
        f"{os.getenv('NUTRITRACK_DB_HOST', 'postgres')}:"
        f"{os.getenv('NUTRITRACK_DB_PORT', '5432')}/"
        f"{os.getenv('NUTRITRACK_DB_NAME', 'nutritrack')}"
    )
    engine = create_engine(db_url)

    loaded = 0
    batch_size = 1000

    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start + batch_size]
        records = []
        for _, row in batch.iterrows():
            records.append({
                "barcode": str(row.get("barcode", "")),
                "product_name": str(row.get("product_name", ""))[:500] if pd.notna(row.get("product_name")) else None,
                "energy_kcal": float(row["energy_kcal"]) if pd.notna(row.get("energy_kcal")) else None,
                "fat_g": float(row["fat_g"]) if pd.notna(row.get("fat_g")) else None,
                "carbohydrates_g": float(row["carbohydrates_g"]) if pd.notna(row.get("carbohydrates_g")) else None,
                "proteins_g": float(row["proteins_g"]) if pd.notna(row.get("proteins_g")) else None,
                "fiber_g": float(row["fiber_g"]) if pd.notna(row.get("fiber_g")) else None,
                "salt_g": float(row["salt_g"]) if pd.notna(row.get("salt_g")) else None,
                "nutriscore_grade": str(row["nutriscore_grade"]) if pd.notna(row.get("nutriscore_grade")) else None,
                "nova_group": int(float(row["nova_group"])) if pd.notna(row.get("nova_group")) else None,
                "completeness_score": float(row["completeness_score"]) if pd.notna(row.get("completeness_score")) else None,
                "data_source": "etl_pipeline",
            })

        if records:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.products (barcode, product_name, energy_kcal, fat_g,
                            carbohydrates_g, proteins_g, fiber_g, salt_g,
                            nutriscore_grade, nova_group, completeness_score, data_source)
                        VALUES (:barcode, :product_name, :energy_kcal, :fat_g,
                            :carbohydrates_g, :proteins_g, :fiber_g, :salt_g,
                            :nutriscore_grade, :nova_group, :completeness_score, :data_source)
                        ON CONFLICT (barcode) DO UPDATE SET
                            product_name = EXCLUDED.product_name,
                            energy_kcal = COALESCE(EXCLUDED.energy_kcal, app.products.energy_kcal),
                            nutriscore_grade = COALESCE(EXCLUDED.nutriscore_grade, app.products.nutriscore_grade),
                            updated_at = CURRENT_TIMESTAMP
                    """),
                    records,
                )
                loaded += len(records)

    print(f"Loaded {loaded} products into database")
    return loaded


with DAG(
    "etl_aggregate_clean",
    default_args=default_args,
    description="Aggregate, clean, and load data — single transform feeding both lake and DW paths",
    schedule_interval="0 4 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["aggregation", "cleaning", "loading"],
) as dag:

    aggregate = PythonOperator(
        task_id="aggregate_all_sources",
        python_callable=aggregate_all_sources,
    )

    clean = PythonOperator(
        task_id="clean_data",
        python_callable=clean_data,
    )

    load = PythonOperator(
        task_id="load_to_database",
        python_callable=load_to_database,
    )

    aggregate >> clean >> load
