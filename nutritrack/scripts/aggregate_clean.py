"""
NutriTrack - Data aggregation and cleaning pipeline
Covers: C10 - Data aggregation from different sources
Merges data from all 5 extraction sources, removes corruption,
homogenizes formats, and produces a single clean dataset.
Entry point: main()
Dependencies: pandas, pathlib
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", "data/raw"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/cleaned"))

# Standard column mapping across sources
STANDARD_COLUMNS = {
    "code": "barcode",
    "product_name": "product_name",
    "generic_name": "generic_name",
    "quantity": "quantity",
    "packaging": "packaging",
    "brands": "brand_name",
    "brand_name": "brand_name",
    "categories": "category_name",
    "category_name": "category_name",
    "countries": "countries",
    "energy-kcal_100g": "energy_kcal",
    "energy_kcal": "energy_kcal",
    "energy-kj_100g": "energy_kj",
    "energy_kj": "energy_kj",
    "fat_100g": "fat_g",
    "fat_g": "fat_g",
    "saturated-fat_100g": "saturated_fat_g",
    "saturated_fat_g": "saturated_fat_g",
    "carbohydrates_100g": "carbohydrates_g",
    "carbohydrates_g": "carbohydrates_g",
    "sugars_100g": "sugars_g",
    "sugars_g": "sugars_g",
    "fiber_100g": "fiber_g",
    "fiber_g": "fiber_g",
    "proteins_100g": "proteins_g",
    "proteins_g": "proteins_g",
    "salt_100g": "salt_g",
    "salt_g": "salt_g",
    "sodium_100g": "sodium_g",
    "sodium_g": "sodium_g",
    "nutriscore_grade": "nutriscore_grade",
    "nutriscore_score": "nutriscore_score",
    "nova_group": "nova_group",
    "ecoscore_grade": "ecoscore_grade",
    "ingredients_text": "ingredients_text",
    "allergens": "allergens",
    "traces": "traces",
    "image_url": "image_url",
    "url": "off_url",
    "off_url": "off_url",
    "completeness": "completeness_score",
    "completeness_score": "completeness_score",
    "last_modified_t": "last_modified_t",
}


def load_api_data() -> pd.DataFrame:
    """Load data extracted from the OFF REST API."""
    api_dir = RAW_DATA_DIR / "api"
    if not api_dir.exists():
        logger.warning("No API data directory found at %s", api_dir)
        return pd.DataFrame()

    dfs = []
    for json_file in api_dir.glob("*.json"):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        products = data.get("products", [])
        if products:
            df = pd.DataFrame(products)
            df["data_source"] = "api"
            dfs.append(df)
            logger.info("Loaded %d products from %s", len(df), json_file.name)

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_parquet_data() -> pd.DataFrame:
    """Load data extracted from the OFF Parquet/CSV export."""
    parquet_dir = RAW_DATA_DIR / "parquet"
    if not parquet_dir.exists():
        logger.warning("No Parquet data directory found at %s", parquet_dir)
        return pd.DataFrame()

    dfs = []
    for file in parquet_dir.glob("*.parquet"):
        df = pd.read_parquet(file)
        df["data_source"] = "parquet"
        dfs.append(df)
        logger.info("Loaded %d products from %s", len(df), file.name)

    for file in parquet_dir.glob("*.csv"):
        df = pd.read_csv(file, low_memory=False)
        df["data_source"] = "parquet"
        dfs.append(df)
        logger.info("Loaded %d products from %s", len(df), file.name)

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def load_duckdb_data() -> pd.DataFrame:
    """Load data extracted by DuckDB analytical queries."""
    duckdb_dir = RAW_DATA_DIR / "duckdb"
    if not duckdb_dir.exists():
        logger.warning("No DuckDB data directory found at %s", duckdb_dir)
        return pd.DataFrame()

    # Look for the main product import file
    import_file = duckdb_dir / "france_products_for_import.parquet"
    if import_file.exists():
        df = pd.read_parquet(import_file)
        df["data_source"] = "duckdb"
        logger.info("Loaded %d products from DuckDB export", len(df))
        return df

    import_csv = duckdb_dir / "france_products_for_import.csv"
    if import_csv.exists():
        df = pd.read_csv(import_csv, low_memory=False)
        df["data_source"] = "duckdb"
        logger.info("Loaded %d products from DuckDB CSV export", len(df))
        return df

    return pd.DataFrame()


def load_db_data() -> pd.DataFrame:
    """Load data extracted from PostgreSQL database."""
    db_dir = RAW_DATA_DIR / "database"
    if not db_dir.exists():
        logger.warning("No database data directory found at %s", db_dir)
        return pd.DataFrame()

    products_file = db_dir / "products_with_brands.csv"
    if products_file.exists():
        df = pd.read_csv(products_file, low_memory=False)
        df["data_source"] = "database"
        logger.info("Loaded %d products from DB export", len(df))
        return df

    return pd.DataFrame()


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to standard names."""
    rename_map = {col: STANDARD_COLUMNS[col] for col in df.columns if col in STANDARD_COLUMNS}
    df = df.rename(columns=rename_map)

    # Keep only standard columns that exist
    standard_cols = list(set(STANDARD_COLUMNS.values()))
    existing_cols = [c for c in standard_cols if c in df.columns]
    if "data_source" in df.columns:
        existing_cols.append("data_source")

    return df[existing_cols]


def clean_barcode(barcode) -> str | None:
    """Validate and clean a barcode."""
    if pd.isna(barcode):
        return None
    barcode = str(barcode).strip()
    # Remove non-numeric characters
    barcode = re.sub(r"[^0-9]", "", barcode)
    # Must be at least 8 digits
    if len(barcode) < 8 or len(barcode) > 14:
        return None
    return barcode


def convert_kj_to_kcal(kj_value) -> float | None:
    """Convert kilojoules to kilocalories (1 kcal = 4.184 kJ)."""
    if pd.isna(kj_value):
        return None
    try:
        return round(float(kj_value) / 4.184, 2)
    except (ValueError, TypeError):
        return None


def clean_text(text) -> str | None:
    """Clean and normalize text fields."""
    if pd.isna(text):
        return None
    text = str(text).strip()
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    return text if text else None


def clean_nutriscore(grade) -> str | None:
    """Normalize Nutri-Score grade to single uppercase letter."""
    if pd.isna(grade):
        return None
    grade = str(grade).strip().upper()
    if grade in ("A", "B", "C", "D", "E"):
        return grade
    return None


def clean_nova_group(nova) -> int | None:
    """Validate NOVA group (1-4)."""
    if pd.isna(nova):
        return None
    try:
        nova = int(float(nova))
        if 1 <= nova <= 4:
            return nova
    except (ValueError, TypeError):
        pass
    return None


def clean_numeric(value, min_val: float = 0, max_val: float = 10000) -> float | None:
    """Clean and validate a numeric nutritional value."""
    if pd.isna(value):
        return None
    try:
        val = float(value)
        if min_val <= val <= max_val:
            return round(val, 2)
    except (ValueError, TypeError):
        pass
    return None


def aggregate_and_clean(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Main aggregation and cleaning pipeline.
    Merges all sources, deduplicates, cleans, and normalizes.
    """
    logger.info("Starting aggregation from %d sources", len(dfs))

    # Standardize columns across all sources
    standardized = []
    for df in dfs:
        if not df.empty:
            std_df = standardize_columns(df)
            standardized.append(std_df)
            logger.info(
                "Standardized: %d rows, %d columns (source: %s)",
                len(std_df),
                len(std_df.columns),
                std_df["data_source"].iloc[0] if "data_source" in std_df.columns else "unknown",
            )

    if not standardized:
        logger.warning("No data to aggregate")
        return pd.DataFrame()

    # Concatenate all sources
    merged = pd.concat(standardized, ignore_index=True)
    logger.info("Merged dataset: %d rows", len(merged))
    initial_count = len(merged)

    # --- CLEANING PIPELINE ---

    # 1. Clean barcodes
    merged["barcode"] = merged["barcode"].apply(clean_barcode)
    merged = merged.dropna(subset=["barcode"])
    logger.info("After barcode cleaning: %d rows (removed %d)", len(merged), initial_count - len(merged))

    # 2. Clean text fields
    for col in [
        "product_name",
        "generic_name",
        "brand_name",
        "category_name",
        "ingredients_text",
        "allergens",
        "traces",
        "packaging",
        "quantity",
    ]:
        if col in merged.columns:
            merged[col] = merged[col].apply(clean_text)

    # 3. Remove entries without product name
    merged = merged.dropna(subset=["product_name"])
    logger.info("After name filter: %d rows", len(merged))

    # 4. Format homogenization: energy conversion (kJ -> kcal)
    if "energy_kj" in merged.columns:
        # Fill missing kcal from kJ conversion
        mask = merged["energy_kcal"].isna() & merged["energy_kj"].notna()
        merged.loc[mask, "energy_kcal"] = merged.loc[mask, "energy_kj"].apply(convert_kj_to_kcal)
        logger.info("Converted %d kJ values to kcal", mask.sum())

    # 5. Clean numeric nutrition values
    numeric_ranges = {
        "energy_kcal": (0, 1000),
        "energy_kj": (0, 4200),
        "fat_g": (0, 100),
        "saturated_fat_g": (0, 100),
        "carbohydrates_g": (0, 100),
        "sugars_g": (0, 100),
        "fiber_g": (0, 100),
        "proteins_g": (0, 100),
        "salt_g": (0, 100),
        "sodium_g": (0, 40),
    }
    for col, (min_v, max_v) in numeric_ranges.items():
        if col in merged.columns:
            merged[col] = merged[col].apply(lambda x: clean_numeric(x, min_v, max_v))

    # 6. Clean scores
    if "nutriscore_grade" in merged.columns:
        merged["nutriscore_grade"] = merged["nutriscore_grade"].apply(clean_nutriscore)
    if "nova_group" in merged.columns:
        merged["nova_group"] = merged["nova_group"].apply(clean_nova_group)
    if "nutriscore_score" in merged.columns:
        merged["nutriscore_score"] = merged["nutriscore_score"].apply(lambda x: clean_numeric(x, -15, 40))
    if "completeness_score" in merged.columns:
        merged["completeness_score"] = merged["completeness_score"].apply(lambda x: clean_numeric(x, 0, 1))

    # 7. Deduplication: keep the most complete version per barcode
    merged = merged.sort_values("completeness_score", ascending=False, na_position="last")
    before_dedup = len(merged)
    merged = merged.drop_duplicates(subset=["barcode"], keep="first")
    logger.info(
        "After deduplication: %d rows (removed %d duplicates)",
        len(merged),
        before_dedup - len(merged),
    )

    # 8. Final validation
    merged = merged.reset_index(drop=True)

    return merged


def generate_cleaning_report(initial_count: int, final_df: pd.DataFrame) -> dict:
    """Generate a cleaning/quality report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "initial_records": initial_count,
        "final_records": len(final_df),
        "records_removed": initial_count - len(final_df),
        "removal_rate_pct": round((initial_count - len(final_df)) / max(initial_count, 1) * 100, 1),
        "completeness": {},
    }

    for col in final_df.columns:
        non_null = final_df[col].notna().sum()
        report["completeness"][col] = {
            "non_null": int(non_null),
            "pct": round(non_null / max(len(final_df), 1) * 100, 1),
        }

    return report


def save_results(df: pd.DataFrame, report: dict) -> Path:
    """Save cleaned dataset and quality report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save cleaned data
    parquet_path = OUTPUT_DIR / "products_cleaned.parquet"
    csv_path = OUTPUT_DIR / "products_cleaned.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    # Save quality report
    report_path = OUTPUT_DIR / "cleaning_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved cleaned data: %s (%d rows)", parquet_path, len(df))
    logger.info("Saved cleaning report: %s", report_path)

    return parquet_path


def main():
    parser = argparse.ArgumentParser(description="Aggregate and clean data from all extraction sources")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["api", "parquet", "duckdb", "database", "all"],
        default=["all"],
        help="Sources to aggregate",
    )

    args = parser.parse_args()
    use_all = "all" in args.sources

    logger.info("Starting data aggregation and cleaning pipeline")

    # Load data from each source
    source_dfs = []
    total_initial = 0

    if use_all or "api" in args.sources:
        df = load_api_data()
        if not df.empty:
            source_dfs.append(df)
            total_initial += len(df)

    if use_all or "parquet" in args.sources:
        df = load_parquet_data()
        if not df.empty:
            source_dfs.append(df)
            total_initial += len(df)

    if use_all or "duckdb" in args.sources:
        df = load_duckdb_data()
        if not df.empty:
            source_dfs.append(df)
            total_initial += len(df)

    if use_all or "database" in args.sources:
        df = load_db_data()
        if not df.empty:
            source_dfs.append(df)
            total_initial += len(df)

    if not source_dfs:
        logger.warning("No source data found. Run extraction scripts first.")
        return

    # Aggregate and clean
    cleaned_df = aggregate_and_clean(source_dfs)

    if cleaned_df.empty:
        logger.warning("Cleaning pipeline produced no results")
        return

    # Generate report and save
    report = generate_cleaning_report(total_initial, cleaned_df)
    save_results(cleaned_df, report)

    logger.info(
        "Pipeline complete: %d -> %d records (%.1f%% retained)",
        total_initial,
        len(cleaned_df),
        len(cleaned_df) / max(total_initial, 1) * 100,
    )


if __name__ == "__main__":
    main()
