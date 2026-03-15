"""
NutriTrack - Extract data from PostgreSQL operational database
Source type: Database (C8, C9)
Demonstrates SQL extraction with joins, filters, aggregations, and optimization.
Entry point: main()
Dependencies: psycopg2, sqlalchemy, pandas
"""

import argparse
import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Database connection
DB_HOST = os.getenv("NUTRITRACK_DB_HOST", "localhost")
DB_PORT = os.getenv("NUTRITRACK_DB_PORT", "5432")
DB_NAME = os.getenv("NUTRITRACK_DB_NAME", "nutritrack")
DB_USER = os.getenv("NUTRITRACK_DB_USER", "nutritrack")
DB_PASSWORD = os.getenv("NUTRITRACK_DB_PASSWORD", "nutritrack")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/raw/database"))


# =============================================================
# SQL Queries (C9 - documented with optimization choices)
# =============================================================

QUERIES = {
    "products_with_brands": {
        "description": "Extract products with brand and category info using JOINs",
        "optimization": "Uses indexes on brand_id and category_id for efficient joins",
        "sql": """
            SELECT
                p.barcode,
                p.product_name,
                p.generic_name,
                b.brand_name,
                b.parent_company,
                c.category_name,
                c.level AS category_level,
                p.energy_kcal,
                p.fat_g,
                p.saturated_fat_g,
                p.carbohydrates_g,
                p.sugars_g,
                p.fiber_g,
                p.proteins_g,
                p.salt_g,
                p.nutriscore_grade,
                p.nutriscore_score,
                p.nova_group,
                p.ecoscore_grade,
                p.completeness_score,
                p.countries,
                p.data_source,
                p.updated_at
            FROM app.products p
            LEFT JOIN app.brands b ON p.brand_id = b.brand_id
            LEFT JOIN app.categories c ON p.category_id = c.category_id
            WHERE p.product_name IS NOT NULL
            ORDER BY p.completeness_score DESC NULLS LAST
        """,
    },
    "category_nutrition_stats": {
        "description": "Aggregate nutritional statistics per category",
        "optimization": "GROUP BY with aggregate functions; HAVING filters after aggregation",
        "sql": """
            SELECT
                c.category_name,
                COUNT(*) AS product_count,
                ROUND(AVG(p.energy_kcal), 1) AS avg_energy_kcal,
                ROUND(AVG(p.proteins_g), 1) AS avg_proteins_g,
                ROUND(AVG(p.fat_g), 1) AS avg_fat_g,
                ROUND(AVG(p.sugars_g), 1) AS avg_sugars_g,
                ROUND(AVG(p.fiber_g), 1) AS avg_fiber_g,
                ROUND(AVG(p.salt_g), 2) AS avg_salt_g,
                MODE() WITHIN GROUP (ORDER BY p.nutriscore_grade) AS most_common_nutriscore,
                ROUND(AVG(p.nova_group), 1) AS avg_nova_group
            FROM app.products p
            JOIN app.categories c ON p.category_id = c.category_id
            WHERE p.energy_kcal IS NOT NULL
            GROUP BY c.category_name
            HAVING COUNT(*) >= 5
            ORDER BY product_count DESC
        """,
    },
    "brand_quality_ranking": {
        "description": "Rank brands by average Nutri-Score using window functions",
        "optimization": "Window function RANK() avoids subquery; CTE for readability",
        "sql": """
            WITH brand_stats AS (
                SELECT
                    b.brand_name,
                    COUNT(*) AS product_count,
                    ROUND(AVG(p.nutriscore_score), 2) AS avg_nutriscore_score,
                    SUM(CASE WHEN p.nutriscore_grade IN ('A', 'B') THEN 1 ELSE 0 END) AS healthy_count,
                    SUM(CASE WHEN p.nutriscore_grade IN ('D', 'E') THEN 1 ELSE 0 END) AS unhealthy_count,
                    RANK() OVER (ORDER BY AVG(p.nutriscore_score) ASC) AS quality_rank
                FROM app.products p
                JOIN app.brands b ON p.brand_id = b.brand_id
                WHERE p.nutriscore_score IS NOT NULL
                GROUP BY b.brand_name
                HAVING COUNT(*) >= 10
            )
            SELECT
                quality_rank,
                brand_name,
                product_count,
                avg_nutriscore_score,
                healthy_count,
                unhealthy_count,
                ROUND(healthy_count * 100.0 / product_count, 1) AS pct_healthy
            FROM brand_stats
            ORDER BY quality_rank
            LIMIT 50
        """,
    },
    "nutriscore_distribution": {
        "description": "Nutri-Score grade distribution across all products",
        "optimization": "Simple GROUP BY on indexed column nutriscore_grade",
        "sql": """
            SELECT
                p.nutriscore_grade,
                COUNT(*) AS count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage,
                ROUND(AVG(p.energy_kcal), 0) AS avg_kcal,
                ROUND(AVG(p.sugars_g), 1) AS avg_sugars,
                ROUND(AVG(p.salt_g), 2) AS avg_salt,
                ROUND(AVG(p.fiber_g), 1) AS avg_fiber
            FROM app.products p
            WHERE p.nutriscore_grade IS NOT NULL
            GROUP BY p.nutriscore_grade
            ORDER BY p.nutriscore_grade
        """,
    },
    "user_meal_summary": {
        "description": "User daily meal summaries with macro breakdown",
        "optimization": "Composite index on (user_id, meal_date) for fast range scan",
        "sql": """
            SELECT
                u.username,
                m.meal_date,
                m.meal_type,
                COUNT(mi.meal_item_id) AS items_count,
                ROUND(SUM(mi.energy_kcal), 0) AS total_kcal,
                ROUND(SUM(mi.proteins_g), 1) AS total_proteins,
                ROUND(SUM(mi.carbohydrates_g), 1) AS total_carbs,
                ROUND(SUM(mi.fat_g), 1) AS total_fat,
                ROUND(SUM(mi.fiber_g), 1) AS total_fiber,
                -- Macro ratios (calories from each macro)
                ROUND(SUM(mi.proteins_g) * 4 / NULLIF(SUM(mi.energy_kcal), 0) * 100, 1) AS protein_pct,
                ROUND(SUM(mi.carbohydrates_g) * 4 / NULLIF(SUM(mi.energy_kcal), 0) * 100, 1) AS carbs_pct,
                ROUND(SUM(mi.fat_g) * 9 / NULLIF(SUM(mi.energy_kcal), 0) * 100, 1) AS fat_pct
            FROM app.users u
            JOIN app.meals m ON u.user_id = m.user_id
            JOIN app.meal_items mi ON m.meal_id = mi.meal_id
            WHERE u.is_active = TRUE
            GROUP BY u.username, m.meal_date, m.meal_type
            ORDER BY m.meal_date DESC, u.username, m.meal_type
        """,
    },
}


def get_engine():
    """Create SQLAlchemy engine with connection pooling."""
    return create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


def extract_query(engine, query_name: str, query_info: dict) -> pd.DataFrame:
    """Execute a named query and return results as DataFrame."""
    logger.info("Executing query '%s': %s", query_name, query_info["description"])
    logger.info("  Optimization: %s", query_info["optimization"])

    with engine.connect() as conn:
        # Log EXPLAIN plan for documentation
        try:
            explain_result = conn.execute(text(f"EXPLAIN ANALYZE {query_info['sql']}"))
            plan = "\n".join(row[0] for row in explain_result)
            logger.debug("Query plan:\n%s", plan)
        except Exception:
            pass  # EXPLAIN may fail on some queries

        df = pd.read_sql(text(query_info["sql"]), conn)

    logger.info("  Returned %d rows, %d columns", len(df), len(df.columns))
    return df


def save_results(dataframes: dict[str, pd.DataFrame]) -> Path:
    """Save all query results to CSV files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, df in dataframes.items():
        csv_path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        logger.info("Saved %s -> %s (%d rows)", name, csv_path, len(df))

    return OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(description="Extract data from NutriTrack PostgreSQL database")
    parser.add_argument(
        "--queries",
        nargs="+",
        choices=list(QUERIES.keys()) + ["all"],
        default=["all"],
        help="Which queries to execute",
    )
    parser.add_argument(
        "--list-queries",
        action="store_true",
        help="List available queries and exit",
    )

    args = parser.parse_args()

    if args.list_queries:
        for name, info in QUERIES.items():
            print(f"  {name}: {info['description']}")
            print(f"    Optimization: {info['optimization']}")
        return

    query_names = list(QUERIES.keys()) if "all" in args.queries else args.queries

    logger.info("Starting database extraction (%d queries)", len(query_names))

    engine = get_engine()
    results = {}

    for name in query_names:
        query_info = QUERIES[name]
        try:
            df = extract_query(engine, name, query_info)
            results[name] = df
        except Exception as e:
            logger.error("Query '%s' failed: %s", name, e)

    if results:
        save_results(results)
        total_rows = sum(len(df) for df in results.values())
        logger.info(
            "Extraction complete: %d queries, %d total rows",
            len(results),
            total_rows,
        )
    else:
        logger.warning("No query results extracted")


if __name__ == "__main__":
    main()
