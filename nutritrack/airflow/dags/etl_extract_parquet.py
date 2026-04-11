"""
Airflow DAG: Extract products from OFF Parquet export using DuckDB
Schedule: Weekly on Sunday at 01:00 UTC
Covers: C8 (Data file + Big data), C9 (SQL queries), C15 (ETL pipeline)
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
}


def extract_from_parquet(**context):
    """Extract French products from the full OFF Parquet dataset using DuckDB."""
    from pathlib import Path

    import duckdb

    data_path = Path("/opt/airflow/data/source/openfoodfacts-products.parquet")
    if not data_path.exists():
        print(f"Parquet file not found at {data_path}. Skipping.")
        return None

    con = duckdb.connect()
    source = f"read_parquet('{data_path}')"

    # Parquet dump stores multilingual fields as ARRAY<STRUCT<lang,text>>.
    # Extract the 'main' entry text. Nutrition data is in a nutriments array.
    query = f"""
    SELECT
        code AS barcode,
        list_extract(list_filter(product_name, x -> x.lang = 'main'), 1)."text" AS product_name,
        list_extract(list_filter(generic_name, x -> x.lang = 'main'), 1)."text" AS generic_name,
        quantity,
        packaging,
        brands AS brand_name,
        categories AS category_name,
        countries_tags AS countries,
        list_extract(list_filter(nutriments, x -> x.name = 'energy-kcal'), 1)."100g" AS energy_kcal,
        list_extract(list_filter(nutriments, x -> x.name = 'fat'), 1)."100g" AS fat_g,
        list_extract(list_filter(nutriments, x -> x.name = 'saturated-fat'), 1)."100g" AS saturated_fat_g,
        list_extract(list_filter(nutriments, x -> x.name = 'carbohydrates'), 1)."100g" AS carbohydrates_g,
        list_extract(list_filter(nutriments, x -> x.name = 'sugars'), 1)."100g" AS sugars_g,
        list_extract(list_filter(nutriments, x -> x.name = 'fiber'), 1)."100g" AS fiber_g,
        list_extract(list_filter(nutriments, x -> x.name = 'proteins'), 1)."100g" AS proteins_g,
        list_extract(list_filter(nutriments, x -> x.name = 'salt'), 1)."100g" AS salt_g,
        list_extract(list_filter(nutriments, x -> x.name = 'sodium'), 1)."100g" AS sodium_g,
        nutriscore_grade,
        nutriscore_score,
        nova_group,
        ecoscore_grade,
        list_extract(list_filter(ingredients_text, x -> x.lang = 'main'), 1)."text" AS ingredients_text,
        array_to_string(allergens_tags, ', ') AS allergens,
        array_to_string(traces_tags, ', ') AS traces,
        link AS off_url,
        completeness AS completeness_score,
        last_modified_t
    FROM {source}
    WHERE countries_tags LIKE '%en:france%'
      AND code IS NOT NULL
      AND product_name IS NOT NULL
      AND LENGTH(CAST(code AS VARCHAR)) >= 8
      AND completeness >= 0.3
    ORDER BY completeness DESC
    """

    df = con.execute(query).fetchdf()
    con.close()

    output_dir = Path("/opt/airflow/data/raw/parquet")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"off_parquet_{context['ds']}.parquet"
    df.to_parquet(str(output_path), index=False)

    print(f"Extracted {len(df)} products -> {output_path}")
    return str(output_path)


def run_analytics(**context):
    """Run analytical queries on the full dataset for market analysis."""
    from pathlib import Path

    import duckdb

    data_path = Path("/opt/airflow/data/source/openfoodfacts-products.parquet")
    if not data_path.exists():
        return None

    con = duckdb.connect()
    source = f"read_parquet('{data_path}')"

    # Nutri-Score distribution by country
    query = f"""
    SELECT
        TRIM(UNNEST(string_split(countries, ','))) AS country,
        nutriscore_grade,
        COUNT(*) AS product_count,
        ROUND(AVG("energy-kcal_100g"), 0) AS avg_kcal
    FROM {source}
    WHERE nutriscore_grade IS NOT NULL AND countries IS NOT NULL
    GROUP BY country, nutriscore_grade
    HAVING COUNT(*) >= 100
    ORDER BY product_count DESC
    """

    df = con.execute(query).fetchdf()
    con.close()

    output_dir = Path("/opt/airflow/data/raw/duckdb")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"analytics_{context['ds']}.parquet"
    df.to_parquet(str(output_path), index=False)

    print(f"Analytics: {len(df)} rows -> {output_path}")
    return str(output_path)


with DAG(
    "etl_extract_parquet",
    default_args=default_args,
    description="Extract products from OFF Parquet export using DuckDB",
    schedule_interval="0 1 * * 0",  # Weekly on Sunday
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["extraction", "parquet", "duckdb", "bigdata"],
) as dag:
    extract = PythonOperator(
        task_id="extract_from_parquet",
        python_callable=extract_from_parquet,
    )

    analytics = PythonOperator(
        task_id="run_analytics",
        python_callable=run_analytics,
    )

    extract >> analytics
