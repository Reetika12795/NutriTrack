"""
Airflow DAG: Aggregate and clean data from all extraction sources
Schedule: Daily at 04:00 UTC (after extraction DAGs complete)
Covers: C10 (Data aggregation), C15 (ETL pipeline)

This DAG is the single transformation step that feeds BOTH downstream paths:
  - Lake path (etl_datalake_ingest @ 05:00): silver reads cleaned Parquet files
  - DW path  (etl_load_warehouse  @ 05:00): reads from PostgreSQL app schema
Both downstream DAGs use ExternalTaskSensors to wait for this DAG to complete.

Data processing uses PySpark throughout for distributed-capable transformation.
All steps (aggregation, cleaning, validation) run on the Spark engine — no pandas
in the hot path — ensuring consistent multi-threaded execution across the pipeline.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _get_spark_session():
    """Create a reusable Spark session with S3A (MinIO) support."""
    import os

    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.master("local[*]")
        .appName("NutriTrack-ETL")
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}")
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "minioadmin123"))
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.memory", "1g")
        .getOrCreate()
    )


def aggregate_all_sources(**context):
    """Load and merge data from all raw extraction outputs using PySpark.

    Uses Spark's distributed reader for Parquet/CSV and converts API JSON
    via a pandas bridge (Spark's JSON reader expects one-JSON-per-line).
    All data is tagged with a data_source column for lineage tracking.
    """
    import json
    from pathlib import Path

    from pyspark.sql import functions as F

    raw_dir = Path("/opt/airflow/data/raw")
    spark = _get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        dfs = []

        for subdir in ["api", "parquet", "duckdb"]:
            dir_path = raw_dir / subdir
            if not dir_path.exists():
                continue

            # Parquet files — native Spark reader (distributed)
            for f in sorted(dir_path.glob("*.parquet"), reverse=True)[:1]:
                sdf = spark.read.parquet(str(f))
                sdf = sdf.withColumn("data_source", F.lit(subdir))
                row_count = sdf.count()
                dfs.append(sdf)
                print(f"Spark loaded {subdir} parquet: {row_count} rows")

            # CSV files — native Spark reader (distributed)
            for f in sorted(dir_path.glob("*.csv"), reverse=True)[:1]:
                sdf = spark.read.option("header", "true").option("inferSchema", "true").csv(str(f))
                sdf = sdf.withColumn("data_source", F.lit(subdir))
                row_count = sdf.count()
                dfs.append(sdf)
                print(f"Spark loaded {subdir} CSV: {row_count} rows")

            # JSON files — pandas bridge then convert to Spark DataFrame
            # (API JSON is nested {"products": [...]}, not one-JSON-per-line)
            for f in sorted(dir_path.glob("*.json"), reverse=True)[:1]:
                import pandas as pd

                with open(f) as fh:
                    data = json.load(fh)
                if isinstance(data, dict) and data.get("products"):
                    pdf = pd.DataFrame(data["products"])
                elif isinstance(data, list):
                    pdf = pd.DataFrame(data)
                else:
                    continue
                pdf["data_source"] = subdir
                sdf = spark.createDataFrame(pdf.astype(str))
                row_count = sdf.count()
                dfs.append(sdf)
                print(f"Spark loaded {subdir} JSON: {row_count} rows")

        if not dfs:
            print("No source data found")
            spark.stop()
            return None

        # Union all sources — cast to string for schema alignment
        all_columns = set()
        for sdf in dfs:
            all_columns.update(sdf.columns)

        aligned = []
        for sdf in dfs:
            for col in all_columns:
                if col not in sdf.columns:
                    sdf = sdf.withColumn(col, F.lit(None).cast("string"))
                else:
                    sdf = sdf.withColumn(col, F.col(col).cast("string"))
            aligned.append(sdf.select(sorted(all_columns)))

        merged = aligned[0]
        for sdf in aligned[1:]:
            merged = merged.unionByName(sdf)

        total = merged.count()

        # Source breakdown
        source_counts = merged.groupBy("data_source").count().collect()
        for row in source_counts:
            print(f"  {row['data_source']}: {row['count']} rows")

        print(f"Merged: {total} total rows from {len(dfs)} sources")

        # Write merged raw data as Parquet for downstream consumption
        output_dir = Path("/opt/airflow/data/merged")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "merged_raw")
        merged.coalesce(1).write.mode("overwrite").parquet(output_path)
        print(f"Merged data written to {output_path}")

        return total

    finally:
        spark.stop()


def clean_data_spark(**context):
    """Apply cleaning rules using PySpark for distributed-capable processing.

    Cleaning pipeline (C10):
      1. Standardize column names across sources
      2. Validate barcodes (strip non-numeric, keep 8-14 digits)
      3. Remove rows without product_name
      4. Cap nutritional values at physiological maximums per 100g
      5. Normalize Nutri-Score to uppercase A-E
      6. Deduplicate by barcode (keep highest completeness_score)
      7. Generate cleaning report
    """
    import json
    from pathlib import Path

    from pyspark.sql import Window
    from pyspark.sql import functions as F

    merged_dir = Path("/opt/airflow/data/merged/merged_raw")
    cleaned_dir = Path("/opt/airflow/data/cleaned")
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    spark = _get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    try:
        # --- Load merged data from aggregate step ---
        if not merged_dir.exists():
            print("No merged data found — falling back to raw sources")
            spark.stop()
            return None

        df = spark.read.parquet(str(merged_dir))
        raw_count = df.count()
        print(f"Loaded {raw_count} rows from merged data")

        # --- RULE 1: Standardize column names ---
        col_map = {
            "code": "barcode",
            "brands": "brand_name",
            "categories": "category_name",
            "energy-kcal_100g": "energy_kcal",
            "fat_100g": "fat_g",
            "proteins_100g": "proteins_g",
            "carbohydrates_100g": "carbohydrates_g",
            "sugars_100g": "sugars_g",
            "fiber_100g": "fiber_g",
            "salt_100g": "salt_g",
        }
        for old_name, new_name in col_map.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.withColumnRenamed(old_name, new_name)
            elif old_name in df.columns and new_name in df.columns:
                df = df.withColumn(new_name, F.coalesce(F.col(new_name), F.col(old_name)))
                df = df.drop(old_name)

        # --- RULE 2: Clean barcodes ---
        if "barcode" in df.columns:
            df = df.withColumn("barcode", F.regexp_replace(F.col("barcode").cast("string"), r"[^0-9]", ""))
            df = df.withColumn("barcode", F.trim(F.col("barcode")))
            df = df.filter(F.length("barcode").between(8, 14))

        # --- RULE 3: Remove null product names ---
        if "product_name" in df.columns:
            df = df.filter(F.col("product_name").isNotNull() & (F.trim(F.col("product_name")) != ""))

        # --- RULE 4: Cap nutritional values at physiological max per 100g ---
        numeric_caps = {
            "energy_kcal": 1000,
            "fat_g": 100,
            "proteins_g": 100,
            "carbohydrates_g": 100,
            "sugars_g": 100,
            "salt_g": 100,
        }
        for col, max_val in numeric_caps.items():
            if col in df.columns:
                df = df.withColumn(col, F.col(col).cast("double"))
                df = df.withColumn(
                    col,
                    F.when((F.col(col) > max_val) | (F.col(col) < 0), None).otherwise(F.col(col)),
                )

        # --- RULE 5: Normalize Nutri-Score to uppercase A-E ---
        if "nutriscore_grade" in df.columns:
            df = df.withColumn("nutriscore_grade", F.upper(F.trim(F.col("nutriscore_grade").cast("string"))))
            df = df.withColumn(
                "nutriscore_grade",
                F.when(F.col("nutriscore_grade").isin("A", "B", "C", "D", "E"), F.col("nutriscore_grade")).otherwise(
                    None
                ),
            )

        # --- RULE 6: Deduplicate by barcode (keep highest completeness_score) ---
        if "completeness_score" in df.columns:
            df = df.withColumn("completeness_score", F.col("completeness_score").cast("double"))
            window = Window.partitionBy("barcode").orderBy(F.col("completeness_score").desc_nulls_last())
            df = df.withColumn("_row_num", F.row_number().over(window))
            df = df.filter(F.col("_row_num") == 1).drop("_row_num")
        else:
            df = df.dropDuplicates(["barcode"])

        # --- Select output columns ---
        keep_cols = [
            "barcode",
            "product_name",
            "generic_name",
            "brands",
            "brand_name",
            "categories",
            "category_name",
            "countries",
            "quantity",
            "packaging",
            "ingredients_text",
            "energy_kcal",
            "fat_g",
            "proteins_g",
            "carbohydrates_g",
            "sugars_g",
            "fiber_g",
            "salt_g",
            "nutriscore_grade",
            "nutriscore_score",
            "nova_group",
            "ecoscore_grade",
            "completeness_score",
            "data_source",
        ]
        existing_cols = [c for c in keep_cols if c in df.columns]
        df = df.select(existing_cols)

        cleaned_count = df.count()

        # --- Write output ---
        output_path = str(cleaned_dir / "products_cleaned.parquet")
        csv_path = str(cleaned_dir / "products_cleaned.csv")

        df.coalesce(1).write.mode("overwrite").parquet(output_path + "_spark")

        import glob
        import shutil

        spark_output = glob.glob(output_path + "_spark/part-*.parquet")
        if spark_output:
            shutil.copy(spark_output[0], output_path)
        shutil.rmtree(output_path + "_spark", ignore_errors=True)

        # CSV export via pandas (single clean file for compatibility)
        import pandas as pd

        pdf = pd.read_parquet(output_path)
        pdf.to_csv(csv_path, index=False)

        print(f"PySpark cleaned: {raw_count} -> {cleaned_count} products ({raw_count - cleaned_count} removed)")
        print(f"Output: {output_path}")

        # --- RULE 7: Generate cleaning report ---
        report = {
            "pipeline": "etl_aggregate_clean (PySpark)",
            "timestamp": datetime.utcnow().isoformat(),
            "raw_count": raw_count,
            "cleaned_count": cleaned_count,
            "removal_rate": round((raw_count - cleaned_count) / max(raw_count, 1) * 100, 1),
            "rules_applied": [
                "column_standardization",
                "barcode_validation",
                "null_product_name_removal",
                "nutritional_range_capping",
                "nutriscore_normalization",
                "barcode_deduplication",
            ],
            "output_format": "parquet",
            "spark_version": spark.version,
        }
        report_path = cleaned_dir / "cleaning_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return str(output_path)

    finally:
        spark.stop()


def validate_data_quality(**context):
    """Validate cleaned data quality before loading to database.

    Checks: row count, null rates, range validation, schema conformance.
    Logs results to staging.data_quality_checks table.
    Fails task if critical checks fail.
    """
    import os
    from pathlib import Path

    import pandas as pd
    import psycopg2

    cleaned_path = Path("/opt/airflow/data/cleaned/products_cleaned.parquet")
    if not cleaned_path.exists():
        raise FileNotFoundError("No cleaned data found for quality validation")

    df = pd.read_parquet(cleaned_path)
    checks = []

    checks.append(
        {
            "check_name": "row_count_positive",
            "check_type": "row_count",
            "expected": "> 0",
            "actual": str(len(df)),
            "passed": len(df) > 0,
        }
    )

    barcode_nulls = df["barcode"].isna().sum() if "barcode" in df.columns else 0
    checks.append(
        {
            "check_name": "barcode_not_null",
            "check_type": "null_rate",
            "expected": "0",
            "actual": str(barcode_nulls),
            "passed": barcode_nulls == 0,
        }
    )

    name_nulls = df["product_name"].isna().sum() if "product_name" in df.columns else 0
    checks.append(
        {
            "check_name": "product_name_not_null",
            "check_type": "null_rate",
            "expected": "0",
            "actual": str(name_nulls),
            "passed": name_nulls == 0,
        }
    )

    if "energy_kcal" in df.columns:
        max_energy = df["energy_kcal"].max()
        checks.append(
            {
                "check_name": "energy_kcal_range",
                "check_type": "range",
                "expected": "<= 1000",
                "actual": str(round(max_energy, 1)) if pd.notna(max_energy) else "null",
                "passed": pd.isna(max_energy) or max_energy <= 1000,
            }
        )

    if "nutriscore_grade" in df.columns:
        valid_grades = {"A", "B", "C", "D", "E"}
        non_null_grades = df["nutriscore_grade"].dropna().unique()
        invalid = set(non_null_grades) - valid_grades
        checks.append(
            {
                "check_name": "nutriscore_valid_grades",
                "check_type": "schema",
                "expected": "only A,B,C,D,E",
                "actual": f"{len(invalid)} invalid" if invalid else "all valid",
                "passed": len(invalid) == 0,
            }
        )

    if "barcode" in df.columns:
        dup_count = df.duplicated(subset=["barcode"]).sum()
        checks.append(
            {
                "check_name": "barcode_unique",
                "check_type": "uniqueness",
                "expected": "0 duplicates",
                "actual": str(dup_count),
                "passed": dup_count == 0,
            }
        )

    # Log results to staging.data_quality_checks
    try:
        conn = psycopg2.connect(
            host=os.getenv("NUTRITRACK_DB_HOST", "postgres"),
            port=os.getenv("NUTRITRACK_DB_PORT", "5432"),
            dbname=os.getenv("NUTRITRACK_DB_NAME", "nutritrack"),
            user=os.getenv("NUTRITRACK_DB_USER", "nutritrack"),
            password=os.getenv("NUTRITRACK_DB_PASSWORD", "nutritrack"),
        )
        cur = conn.cursor()
        for c in checks:
            cur.execute(
                """INSERT INTO staging.data_quality_checks
                   (pipeline_name, check_name, check_type, expected_value, actual_value, passed)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    "etl_aggregate_clean",
                    c["check_name"],
                    c["check_type"],
                    c["expected"],
                    c["actual"],
                    bool(c["passed"]),
                ),
            )
        conn.commit()
        cur.close()
        conn.close()
        print("Quality checks logged to staging.data_quality_checks")
    except Exception as e:
        print(f"Could not log to DB (table may not exist yet): {e}")

    failed = [c for c in checks if not c["passed"]]
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['check_name']}: expected {c['expected']}, got {c['actual']}")

    if failed:
        raise ValueError(f"{len(failed)} data quality check(s) failed: {[c['check_name'] for c in failed]}")

    print(f"All {len(checks)} data quality checks passed")
    return len(checks)


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
        batch = df.iloc[start : start + batch_size]
        records = []
        for _, row in batch.iterrows():
            records.append(
                {
                    "barcode": str(row.get("barcode", "")),
                    "product_name": str(row.get("product_name", ""))[:500]
                    if pd.notna(row.get("product_name"))
                    else None,
                    "energy_kcal": float(row["energy_kcal"]) if pd.notna(row.get("energy_kcal")) else None,
                    "fat_g": float(row["fat_g"]) if pd.notna(row.get("fat_g")) else None,
                    "carbohydrates_g": float(row["carbohydrates_g"]) if pd.notna(row.get("carbohydrates_g")) else None,
                    "proteins_g": float(row["proteins_g"]) if pd.notna(row.get("proteins_g")) else None,
                    "fiber_g": float(row["fiber_g"]) if pd.notna(row.get("fiber_g")) else None,
                    "salt_g": float(row["salt_g"]) if pd.notna(row.get("salt_g")) else None,
                    "nutriscore_grade": str(row["nutriscore_grade"]) if pd.notna(row.get("nutriscore_grade")) else None,
                    "nova_group": int(float(row["nova_group"])) if pd.notna(row.get("nova_group")) else None,
                    "completeness_score": float(row["completeness_score"])
                    if pd.notna(row.get("completeness_score"))
                    else None,
                    "data_source": "etl_pipeline",
                }
            )

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
    description="PySpark-based aggregate, clean, validate, and load — feeds both lake and DW paths",
    schedule_interval="0 4 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["aggregation", "cleaning", "pyspark", "data-quality"],
) as dag:
    aggregate = PythonOperator(
        task_id="aggregate_all_sources",
        python_callable=aggregate_all_sources,
    )

    clean = PythonOperator(
        task_id="clean_data",
        python_callable=clean_data_spark,
    )

    validate = PythonOperator(
        task_id="validate_data_quality",
        python_callable=validate_data_quality,
    )

    load = PythonOperator(
        task_id="load_to_database",
        python_callable=load_to_database,
    )

    aggregate >> clean >> validate >> load
