"""
NutriTrack - Extract products from Open Food Facts Parquet/CSV export file
Source type: Data file + Big data system (C8, C9)
Uses DuckDB for efficient querying of large Parquet files (3M+ products)
Entry point: main()
Dependencies: duckdb, pandas, pathlib
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

# Open Food Facts export URLs
OFF_PARQUET_URL = "https://static.openfoodfacts.org/data/openfoodfacts-products.parquet"
OFF_CSV_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/raw/parquet"))
DATA_DIR = Path(os.getenv("DATA_DIR", "data/source"))


def get_data_path() -> Path:
    """Locate the OFF data file (Parquet or CSV)."""
    parquet_path = DATA_DIR / "openfoodfacts-products.parquet"
    csv_path = DATA_DIR / "en.openfoodfacts.org.products.csv.gz"

    if parquet_path.exists():
        logger.info("Using Parquet file: %s", parquet_path)
        return parquet_path
    if csv_path.exists():
        logger.info("Using CSV file: %s", csv_path)
        return csv_path

    logger.warning(
        "No local OFF data file found. Download from:\n"
        "  Parquet: %s\n  CSV: %s\n"
        "Place in: %s",
        OFF_PARQUET_URL,
        OFF_CSV_URL,
        DATA_DIR,
    )
    raise FileNotFoundError(f"No OFF data file found in {DATA_DIR}")


def extract_with_duckdb(
    data_path: Path,
    countries_filter: str = "France",
    nutriscore_filter: list[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Extract products from the large OFF data file using DuckDB.
    DuckDB reads Parquet/CSV efficiently without loading everything into memory.

    C9: SQL queries with selection, filtering, joins, and optimizations.
    """
    con = duckdb.connect()

    # Build the file reader expression
    ext = data_path.suffix.lower()
    if ext == ".parquet":
        file_reader = f"read_parquet('{data_path}')"
    elif data_path.name.endswith(".csv.gz") or ext == ".csv":
        file_reader = f"read_csv_auto('{data_path}', ignore_errors=true)"
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    # DuckDB SQL query with filtering and selection
    nutriscore_where = ""
    if nutriscore_filter:
        grades = ", ".join(f"'{g}'" for g in nutriscore_filter)
        nutriscore_where = f"AND nutriscore_grade IN ({grades})"

    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
    SELECT
        code AS barcode,
        product_name,
        generic_name,
        quantity,
        packaging,
        brands,
        categories,
        countries,
        -- Nutrition per 100g
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
        -- Scores
        nutriscore_grade,
        nutriscore_score,
        nova_group,
        ecoscore_grade,
        -- Metadata
        ingredients_text,
        allergens,
        traces,
        image_url,
        url AS off_url,
        completeness AS completeness_score,
        last_modified_t
    FROM {file_reader}
    WHERE code IS NOT NULL
      AND product_name IS NOT NULL
      AND LENGTH(code) >= 8
      AND countries LIKE '%{countries_filter}%'
      {nutriscore_where}
    ORDER BY completeness DESC
    {limit_clause}
    """

    logger.info("Executing DuckDB query on %s...", data_path.name)
    start_time = time.time()

    df = con.execute(query).fetchdf()

    elapsed = time.time() - start_time
    logger.info(
        "Extracted %d products in %.2f seconds", len(df), elapsed
    )

    con.close()
    return df


def get_data_statistics(data_path: Path) -> dict:
    """Get statistics about the full OFF dataset using DuckDB."""
    con = duckdb.connect()

    ext = data_path.suffix.lower()
    if ext == ".parquet":
        file_reader = f"read_parquet('{data_path}')"
    else:
        file_reader = f"read_csv_auto('{data_path}', ignore_errors=true)"

    stats_query = f"""
    SELECT
        COUNT(*) AS total_products,
        COUNT(DISTINCT brands) AS unique_brands,
        COUNT(DISTINCT categories) AS unique_categories,
        COUNT(CASE WHEN nutriscore_grade IS NOT NULL THEN 1 END) AS with_nutriscore,
        COUNT(CASE WHEN nova_group IS NOT NULL THEN 1 END) AS with_nova,
        AVG("energy-kcal_100g") AS avg_energy_kcal,
        MIN(last_modified_t) AS oldest_modification,
        MAX(last_modified_t) AS newest_modification
    FROM {file_reader}
    WHERE code IS NOT NULL
    """

    logger.info("Computing dataset statistics...")
    stats = con.execute(stats_query).fetchone()
    con.close()

    return {
        "total_products": stats[0],
        "unique_brands": stats[1],
        "unique_categories": stats[2],
        "with_nutriscore": stats[3],
        "with_nova": stats[4],
        "avg_energy_kcal": round(stats[5], 1) if stats[5] else None,
    }


def save_results(df: pd.DataFrame, filename: str) -> Path:
    """Save extracted data to Parquet and CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = OUTPUT_DIR / f"{filename}.parquet"
    csv_path = OUTPUT_DIR / f"{filename}.csv"

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    logger.info("Saved %d records to %s and %s", len(df), parquet_path, csv_path)
    return parquet_path


def main():
    parser = argparse.ArgumentParser(
        description="Extract products from OFF Parquet/CSV export using DuckDB"
    )
    parser.add_argument(
        "--countries",
        type=str,
        default="France",
        help="Filter by country",
    )
    parser.add_argument(
        "--nutriscore",
        type=str,
        nargs="+",
        help="Filter by Nutri-Score grades (e.g., A B C)",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of products")
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only print dataset statistics",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="off_parquet_extract",
        help="Output filename (without extension)",
    )

    args = parser.parse_args()

    logger.info("Starting OFF Parquet/CSV extraction with DuckDB")

    data_path = get_data_path()

    if args.stats_only:
        stats = get_data_statistics(data_path)
        for key, value in stats.items():
            logger.info("  %s: %s", key, value)
        return

    df = extract_with_duckdb(
        data_path,
        countries_filter=args.countries,
        nutriscore_filter=args.nutriscore,
        limit=args.limit,
    )

    if not df.empty:
        output_path = save_results(df, args.output)
        logger.info("Extraction complete: %d products -> %s", len(df), output_path)
    else:
        logger.warning("No products extracted")


if __name__ == "__main__":
    main()
