"""
Airflow DAG: Extract products from Open Food Facts API
Schedule: Daily at 02:00 UTC
Covers: C8 (REST API extraction), C15 (ETL pipeline)
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def extract_off_api(**context):
    """Extract products from Open Food Facts API."""
    import json
    import time
    from pathlib import Path

    import requests

    base_url = "https://world.openfoodfacts.org/cgi/search.pl"
    categories = ["breakfast cereals", "yogurts", "chocolate", "beverages", "snacks"]
    all_products = []

    for category in categories:
        for page in range(1, 6):
            params = {
                "search_terms": category,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page": page,
                "page_size": 50,
            }
            try:
                resp = requests.get(
                    base_url,
                    params=params,
                    headers={"User-Agent": "NutriTrack-Airflow/1.0"},
                    timeout=30,
                )
                resp.raise_for_status()
                products = resp.json().get("products", [])
                if not products:
                    break
                all_products.extend(products)
                time.sleep(0.6)
            except Exception as e:
                print(f"Error fetching {category} page {page}: {e}")
                break

    output_dir = Path("/opt/airflow/data/raw/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"off_api_{context['ds']}.json"

    with open(output_path, "w") as f:
        json.dump({"products": all_products, "count": len(all_products)}, f)

    print(f"Extracted {len(all_products)} products -> {output_path}")
    return str(output_path)


with DAG(
    "etl_extract_off_api",
    default_args=default_args,
    description="Extract products from Open Food Facts REST API",
    schedule_interval="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["extraction", "api", "off"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_off_api",
        python_callable=extract_off_api,
    )
