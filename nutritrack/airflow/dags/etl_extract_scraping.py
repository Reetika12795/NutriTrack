"""
Airflow DAG: Scrape nutritional guidelines from health authority websites
Schedule: Weekly on Monday at 03:00 UTC
Covers: C8 (Web scraping), C15 (ETL pipeline)
"""

from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator

from airflow import DAG

default_args = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def scrape_nutritional_guidelines(**context):
    """Scrape RDA values from health authority websites."""
    import json
    from pathlib import Path

    import requests
    from bs4 import BeautifulSoup

    # EU Regulation 1169/2011 reference values (reliable fallback)
    guidelines = [
        {"nutrient": "Energy", "daily_value": 2000, "unit": "kcal", "source": "EU Reg 1169/2011"},
        {"nutrient": "Total fat", "daily_value": 70, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Saturated fat", "daily_value": 20, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Carbohydrates", "daily_value": 260, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Sugars", "daily_value": 90, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Protein", "daily_value": 50, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Salt", "daily_value": 6, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Fiber", "daily_value": 25, "unit": "g", "source": "EU Reg 1169/2011"},
        {"nutrient": "Vitamin C", "daily_value": 80, "unit": "mg", "source": "EU Reg 1169/2011"},
        {"nutrient": "Calcium", "daily_value": 800, "unit": "mg", "source": "EU Reg 1169/2011"},
        {"nutrient": "Iron", "daily_value": 14, "unit": "mg", "source": "EU Reg 1169/2011"},
    ]

    # Attempt to scrape ANSES for additional data
    try:
        url = "https://www.anses.fr/fr/content/les-references-nutritionnelles-en-vitamines-et-mineraux"
        resp = requests.get(url, headers={"User-Agent": "NutriTrack-Airflow/1.0"}, timeout=30)
        if resp.ok:
            soup = BeautifulSoup(resp.content, "html.parser")
            tables = soup.find_all("table")
            for table in tables:
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all(["th", "td"])
                    if len(cells) >= 2:
                        guidelines.append({
                            "nutrient": cells[0].get_text(strip=True),
                            "daily_value": cells[1].get_text(strip=True),
                            "unit": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                            "source": "ANSES",
                        })
    except Exception as e:
        print(f"ANSES scraping failed (using fallback): {e}")

    output_dir = Path("/opt/airflow/data/raw/scraping")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"guidelines_{context['ds']}.json"

    with open(output_path, "w") as f:
        json.dump({"guidelines": guidelines, "count": len(guidelines)}, f, indent=2)

    print(f"Scraped {len(guidelines)} guidelines -> {output_path}")
    return str(output_path)


with DAG(
    "etl_extract_scraping",
    default_args=default_args,
    description="Scrape nutritional guidelines from health authority websites",
    schedule_interval="0 3 * * 1",  # Weekly on Monday
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["extraction", "scraping", "guidelines"],
) as dag:

    scrape_task = PythonOperator(
        task_id="scrape_nutritional_guidelines",
        python_callable=scrape_nutritional_guidelines,
    )
