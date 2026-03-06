"""
NutriTrack - Big data extraction using DuckDB on full OFF dataset
Source type: Big data system (C8)
Performs analytical SQL queries on the 3M+ product Parquet dataset.
Entry point: main()
Dependencies: duckdb, pandas
"""

import argparse
import logging
import os
import time
from pathlib import Path

import duckdb
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "data/source"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/raw/duckdb"))


def get_parquet_path() -> Path:
    """Locate the OFF Parquet file."""
    parquet_path = DATA_DIR / "openfoodfacts-products.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"OFF Parquet file not found at {parquet_path}. "
            "Download from: https://static.openfoodfacts.org/data/openfoodfacts-products.parquet"
        )
    return parquet_path


# =============================================================
# Analytical Queries for Big Data Processing (C8 + C9)
# =============================================================

ANALYTICAL_QUERIES = {
    "global_nutrition_overview": {
        "description": "Global statistics across the entire 3M+ product dataset",
        "sql": """
            SELECT
                COUNT(*) AS total_products,
                COUNT(CASE WHEN nutriscore_grade IS NOT NULL THEN 1 END) AS with_nutriscore,
                COUNT(CASE WHEN nova_group IS NOT NULL THEN 1 END) AS with_nova,
                COUNT(CASE WHEN ecoscore_grade IS NOT NULL THEN 1 END) AS with_ecoscore,
                ROUND(AVG("energy-kcal_100g"), 1) AS avg_energy_kcal,
                ROUND(MEDIAN("energy-kcal_100g"), 1) AS median_energy_kcal,
                ROUND(AVG(fat_100g), 1) AS avg_fat,
                ROUND(AVG(sugars_100g), 1) AS avg_sugars,
                ROUND(AVG(proteins_100g), 1) AS avg_proteins,
                ROUND(AVG(fiber_100g), 1) AS avg_fiber,
                ROUND(AVG(salt_100g), 2) AS avg_salt,
                COUNT(DISTINCT brands) AS unique_brands,
                COUNT(DISTINCT countries) AS unique_countries,
                MIN(last_modified_t) AS oldest_record,
                MAX(last_modified_t) AS newest_record
            FROM {source}
            WHERE code IS NOT NULL AND product_name IS NOT NULL
        """,
    },
    "nutriscore_by_country": {
        "description": "Nutri-Score distribution per country (top 20 countries)",
        "sql": """
            WITH countries_exploded AS (
                SELECT
                    TRIM(UNNEST(string_split(countries, ','))) AS country,
                    nutriscore_grade,
                    "energy-kcal_100g" AS energy_kcal,
                    nova_group
                FROM {source}
                WHERE nutriscore_grade IS NOT NULL
                  AND countries IS NOT NULL
            ),
            country_stats AS (
                SELECT
                    country,
                    nutriscore_grade,
                    COUNT(*) AS product_count,
                    ROUND(AVG(energy_kcal), 0) AS avg_kcal,
                    ROUND(AVG(nova_group), 1) AS avg_nova
                FROM countries_exploded
                WHERE LENGTH(country) > 1
                GROUP BY country, nutriscore_grade
            )
            SELECT *
            FROM country_stats
            WHERE country IN (
                SELECT country
                FROM countries_exploded
                GROUP BY country
                ORDER BY COUNT(*) DESC
                LIMIT 20
            )
            ORDER BY country, nutriscore_grade
        """,
    },
    "ultra_processed_analysis": {
        "description": "NOVA ultra-processed food analysis by category",
        "sql": """
            WITH categorized AS (
                SELECT
                    CASE
                        WHEN categories LIKE '%breakfast%' OR categories LIKE '%cereal%' THEN 'Breakfast cereals'
                        WHEN categories LIKE '%yogurt%' OR categories LIKE '%yaourt%' THEN 'Yogurts'
                        WHEN categories LIKE '%chocolate%' OR categories LIKE '%chocolat%' THEN 'Chocolate'
                        WHEN categories LIKE '%beverage%' OR categories LIKE '%boisson%' THEN 'Beverages'
                        WHEN categories LIKE '%snack%' THEN 'Snacks'
                        WHEN categories LIKE '%bread%' OR categories LIKE '%pain%' THEN 'Bread'
                        WHEN categories LIKE '%cheese%' OR categories LIKE '%fromage%' THEN 'Cheese'
                        WHEN categories LIKE '%meat%' OR categories LIKE '%viande%' THEN 'Meat'
                        ELSE 'Other'
                    END AS food_category,
                    nova_group,
                    nutriscore_grade,
                    "energy-kcal_100g" AS energy_kcal,
                    sugars_100g AS sugars,
                    salt_100g AS salt,
                    fat_100g AS fat,
                    fiber_100g AS fiber
                FROM {source}
                WHERE nova_group IS NOT NULL
                  AND categories IS NOT NULL
            )
            SELECT
                food_category,
                nova_group,
                COUNT(*) AS product_count,
                ROUND(AVG(energy_kcal), 0) AS avg_kcal,
                ROUND(AVG(sugars), 1) AS avg_sugars,
                ROUND(AVG(salt), 2) AS avg_salt,
                ROUND(AVG(fat), 1) AS avg_fat,
                ROUND(AVG(fiber), 1) AS avg_fiber,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY food_category), 1) AS pct_in_category
            FROM categorized
            WHERE food_category != 'Other'
            GROUP BY food_category, nova_group
            ORDER BY food_category, nova_group
        """,
    },
    "completeness_analysis": {
        "description": "Data completeness analysis across the dataset",
        "sql": """
            SELECT
                CASE
                    WHEN completeness >= 0.8 THEN 'High (>= 80%)'
                    WHEN completeness >= 0.5 THEN 'Medium (50-79%)'
                    WHEN completeness >= 0.2 THEN 'Low (20-49%)'
                    ELSE 'Very Low (< 20%)'
                END AS completeness_tier,
                COUNT(*) AS product_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_total,
                COUNT(CASE WHEN nutriscore_grade IS NOT NULL THEN 1 END) AS with_nutriscore,
                COUNT(CASE WHEN nova_group IS NOT NULL THEN 1 END) AS with_nova,
                COUNT(CASE WHEN ingredients_text IS NOT NULL AND LENGTH(ingredients_text) > 10 THEN 1 END) AS with_ingredients,
                COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) AS with_image
            FROM {source}
            WHERE code IS NOT NULL
            GROUP BY completeness_tier
            ORDER BY completeness_tier
        """,
    },
    "france_products_for_import": {
        "description": "Extract French products with high completeness for DB import",
        "sql": """
            SELECT
                code AS barcode,
                product_name,
                generic_name,
                quantity,
                packaging,
                brands AS brand_name,
                categories AS category_name,
                countries,
                "energy-kcal_100g" AS energy_kcal,
                "energy-kj_100g" AS energy_kj,
                fat_100g AS fat_g,
                "saturated-fat_100g" AS saturated_fat_g,
                carbohydrates_100g AS carbohydrates_g,
                sugars_100g AS sugars_g,
                fiber_100g AS fiber_g,
                proteins_100g AS proteins_g,
                salt_100g AS salt_g,
                sodium_100g AS sodium_g,
                nutriscore_grade,
                nutriscore_score,
                nova_group,
                ecoscore_grade,
                ingredients_text,
                allergens,
                traces,
                image_url,
                url AS off_url,
                completeness AS completeness_score,
                last_modified_t
            FROM {source}
            WHERE countries LIKE '%France%'
              AND product_name IS NOT NULL
              AND code IS NOT NULL
              AND LENGTH(code) >= 8
              AND completeness >= 0.3
            ORDER BY completeness DESC
            LIMIT 100000
        """,
    },
}


def run_query(
    con: duckdb.DuckDBPyConnection, name: str, info: dict, source: str
) -> pd.DataFrame:
    """Execute an analytical query and return results."""
    logger.info("Running query '%s': %s", name, info["description"])

    sql = info["sql"].format(source=source)
    start = time.time()
    df = con.execute(sql).fetchdf()
    elapsed = time.time() - start

    logger.info("  -> %d rows in %.2f seconds", len(df), elapsed)
    return df


def save_results(results: dict[str, pd.DataFrame]) -> Path:
    """Save all query results."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, df in results.items():
        parquet_path = OUTPUT_DIR / f"{name}.parquet"
        csv_path = OUTPUT_DIR / f"{name}.csv"
        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)
        logger.info("Saved %s -> %s (%d rows)", name, csv_path, len(df))

    return OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Big data analytics on OFF dataset using DuckDB"
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        choices=list(ANALYTICAL_QUERIES.keys()) + ["all"],
        default=["all"],
        help="Queries to run",
    )
    parser.add_argument(
        "--list-queries", action="store_true", help="List available queries"
    )

    args = parser.parse_args()

    if args.list_queries:
        for name, info in ANALYTICAL_QUERIES.items():
            print(f"  {name}: {info['description']}")
        return

    parquet_path = get_parquet_path()
    query_names = (
        list(ANALYTICAL_QUERIES.keys()) if "all" in args.queries else args.queries
    )

    logger.info(
        "Starting DuckDB big data extraction (%d queries on %s)",
        len(query_names),
        parquet_path.name,
    )

    con = duckdb.connect()
    source = f"read_parquet('{parquet_path}')"

    results = {}
    for name in query_names:
        info = ANALYTICAL_QUERIES[name]
        try:
            df = run_query(con, name, info, source)
            results[name] = df
        except Exception as e:
            logger.error("Query '%s' failed: %s", name, e)

    con.close()

    if results:
        save_results(results)
        total_rows = sum(len(df) for df in results.values())
        logger.info(
            "Big data extraction complete: %d queries, %d total rows",
            len(results),
            total_rows,
        )
    else:
        logger.warning("No results from big data queries")


if __name__ == "__main__":
    main()
