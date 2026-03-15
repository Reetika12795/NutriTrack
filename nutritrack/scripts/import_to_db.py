"""
NutriTrack - Import cleaned data into PostgreSQL operational database
Covers: C11 - Database import script
Entry point: main()
Dependencies: psycopg2, sqlalchemy, pandas
"""

import argparse
import logging
import os
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("NUTRITRACK_DB_HOST", "localhost")
DB_PORT = os.getenv("NUTRITRACK_DB_PORT", "5432")
DB_NAME = os.getenv("NUTRITRACK_DB_NAME", "nutritrack")
DB_USER = os.getenv("NUTRITRACK_DB_USER", "nutritrack")
DB_PASSWORD = os.getenv("NUTRITRACK_DB_PASSWORD", "nutritrack")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

CLEANED_DATA_DIR = Path(os.getenv("CLEANED_DATA_DIR", "data/cleaned"))
BATCH_SIZE = 5000


def get_engine():
    """Create SQLAlchemy engine."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset."""
    parquet_path = CLEANED_DATA_DIR / "products_cleaned.parquet"
    csv_path = CLEANED_DATA_DIR / "products_cleaned.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        logger.info("Loaded %d products from %s", len(df), parquet_path)
        return df

    if csv_path.exists():
        df = pd.read_csv(csv_path, low_memory=False)
        logger.info("Loaded %d products from %s", len(df), csv_path)
        return df

    raise FileNotFoundError(f"No cleaned data found in {CLEANED_DATA_DIR}. Run aggregate_clean.py first.")


def import_brands(engine, df: pd.DataFrame) -> dict[str, int]:
    """Import unique brands and return a name -> id mapping."""
    brands = df["brand_name"].dropna().unique()
    logger.info("Importing %d unique brands", len(brands))

    brand_map = {}
    with engine.begin() as conn:
        for brand_name in brands:
            brand_name = str(brand_name).strip()[:255]
            if not brand_name:
                continue

            result = conn.execute(
                text("""
                    INSERT INTO app.brands (brand_name)
                    VALUES (:name)
                    ON CONFLICT DO NOTHING
                    RETURNING brand_id
                """),
                {"name": brand_name},
            )
            row = result.fetchone()
            if row:
                brand_map[brand_name] = row[0]
            else:
                result = conn.execute(
                    text("SELECT brand_id FROM app.brands WHERE brand_name = :name"),
                    {"name": brand_name},
                )
                row = result.fetchone()
                if row:
                    brand_map[brand_name] = row[0]

    logger.info("Imported/mapped %d brands", len(brand_map))
    return brand_map


def import_categories(engine, df: pd.DataFrame) -> dict[str, int]:
    """Import unique categories and return a name -> id mapping."""
    categories_raw = df["category_name"].dropna().unique()
    logger.info("Processing %d unique category entries", len(categories_raw))

    category_map = {}
    with engine.begin() as conn:
        for cat_raw in categories_raw:
            # Take the first category from comma-separated lists
            cat_name = str(cat_raw).split(",")[0].strip()[:255]
            if not cat_name or cat_name in category_map:
                category_map[str(cat_raw)] = category_map.get(cat_name)
                continue

            result = conn.execute(
                text("""
                    INSERT INTO app.categories (category_name)
                    VALUES (:name)
                    ON CONFLICT DO NOTHING
                    RETURNING category_id
                """),
                {"name": cat_name},
            )
            row = result.fetchone()
            if row:
                category_map[cat_name] = row[0]
                category_map[str(cat_raw)] = row[0]
            else:
                result = conn.execute(
                    text("SELECT category_id FROM app.categories WHERE category_name = :name"),
                    {"name": cat_name},
                )
                row = result.fetchone()
                if row:
                    category_map[cat_name] = row[0]
                    category_map[str(cat_raw)] = row[0]

    unique_mapped = len(set(v for v in category_map.values() if v is not None))
    logger.info("Imported/mapped %d unique categories", unique_mapped)
    return category_map


def import_products(
    engine,
    df: pd.DataFrame,
    brand_map: dict[str, int],
    category_map: dict[str, int],
) -> int:
    """Import products in batches."""
    total_imported = 0
    total_skipped = 0

    for start in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[start : start + BATCH_SIZE]
        records = []

        for _, row in batch.iterrows():
            brand_id = brand_map.get(str(row.get("brand_name", "")).strip())
            category_id = category_map.get(str(row.get("category_name", "")))

            record = {
                "barcode": str(row["barcode"]),
                "product_name": str(row.get("product_name", ""))[:500] or None,
                "generic_name": str(row.get("generic_name", ""))[:500] if pd.notna(row.get("generic_name")) else None,
                "quantity": str(row.get("quantity", ""))[:100] if pd.notna(row.get("quantity")) else None,
                "packaging": str(row.get("packaging", ""))[:255] if pd.notna(row.get("packaging")) else None,
                "brand_id": brand_id,
                "category_id": category_id,
                "energy_kcal": float(row["energy_kcal"]) if pd.notna(row.get("energy_kcal")) else None,
                "energy_kj": float(row["energy_kj"]) if pd.notna(row.get("energy_kj")) else None,
                "fat_g": float(row["fat_g"]) if pd.notna(row.get("fat_g")) else None,
                "saturated_fat_g": float(row["saturated_fat_g"]) if pd.notna(row.get("saturated_fat_g")) else None,
                "carbohydrates_g": float(row["carbohydrates_g"]) if pd.notna(row.get("carbohydrates_g")) else None,
                "sugars_g": float(row["sugars_g"]) if pd.notna(row.get("sugars_g")) else None,
                "fiber_g": float(row["fiber_g"]) if pd.notna(row.get("fiber_g")) else None,
                "proteins_g": float(row["proteins_g"]) if pd.notna(row.get("proteins_g")) else None,
                "salt_g": float(row["salt_g"]) if pd.notna(row.get("salt_g")) else None,
                "sodium_g": float(row["sodium_g"]) if pd.notna(row.get("sodium_g")) else None,
                "nutriscore_grade": str(row["nutriscore_grade"]) if pd.notna(row.get("nutriscore_grade")) else None,
                "nutriscore_score": int(float(row["nutriscore_score"]))
                if pd.notna(row.get("nutriscore_score"))
                else None,
                "nova_group": int(float(row["nova_group"])) if pd.notna(row.get("nova_group")) else None,
                "ecoscore_grade": str(row["ecoscore_grade"])[0]
                if pd.notna(row.get("ecoscore_grade")) and str(row.get("ecoscore_grade")).strip()
                else None,
                "countries": str(row.get("countries", ""))[:500] if pd.notna(row.get("countries")) else None,
                "ingredients_text": str(row.get("ingredients_text", ""))
                if pd.notna(row.get("ingredients_text"))
                else None,
                "allergens": str(row.get("allergens", "")) if pd.notna(row.get("allergens")) else None,
                "traces": str(row.get("traces", "")) if pd.notna(row.get("traces")) else None,
                "image_url": str(row.get("image_url", ""))[:1000] if pd.notna(row.get("image_url")) else None,
                "off_url": str(row.get("off_url", ""))[:500] if pd.notna(row.get("off_url")) else None,
                "completeness_score": float(row["completeness_score"])
                if pd.notna(row.get("completeness_score"))
                else None,
                "data_source": str(row.get("data_source", "open_food_facts"))[:50],
            }
            records.append(record)

        if records:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO app.products (
                            barcode, product_name, generic_name, quantity, packaging,
                            brand_id, category_id, energy_kcal, energy_kj, fat_g,
                            saturated_fat_g, carbohydrates_g, sugars_g, fiber_g,
                            proteins_g, salt_g, sodium_g, nutriscore_grade,
                            nutriscore_score, nova_group, ecoscore_grade, countries,
                            ingredients_text, allergens, traces, image_url, off_url,
                            completeness_score, data_source
                        ) VALUES (
                            :barcode, :product_name, :generic_name, :quantity, :packaging,
                            :brand_id, :category_id, :energy_kcal, :energy_kj, :fat_g,
                            :saturated_fat_g, :carbohydrates_g, :sugars_g, :fiber_g,
                            :proteins_g, :salt_g, :sodium_g, :nutriscore_grade,
                            :nutriscore_score, :nova_group, :ecoscore_grade, :countries,
                            :ingredients_text, :allergens, :traces, :image_url, :off_url,
                            :completeness_score, :data_source
                        )
                        ON CONFLICT (barcode) DO UPDATE SET
                            product_name = EXCLUDED.product_name,
                            energy_kcal = COALESCE(EXCLUDED.energy_kcal, app.products.energy_kcal),
                            nutriscore_grade = COALESCE(EXCLUDED.nutriscore_grade, app.products.nutriscore_grade),
                            completeness_score = GREATEST(EXCLUDED.completeness_score, app.products.completeness_score),
                            updated_at = CURRENT_TIMESTAMP
                    """),
                    records,
                )
                total_imported += len(records)

        logger.info(
            "Progress: %d/%d products imported",
            min(start + BATCH_SIZE, len(df)),
            len(df),
        )

    logger.info("Total imported: %d, skipped: %d", total_imported, total_skipped)
    return total_imported


def log_extraction(engine, source_name: str, records_loaded: int, status: str):
    """Log the import operation."""
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO app.extraction_log
                    (source_name, source_type, records_extracted, records_loaded, status, completed_at)
                VALUES
                    (:source, 'import', :loaded, :loaded, :status, CURRENT_TIMESTAMP)
            """),
            {"source": source_name, "loaded": records_loaded, "status": status},
        )


def main():
    parser = argparse.ArgumentParser(description="Import cleaned data into NutriTrack PostgreSQL database")
    parser.add_argument("--dry-run", action="store_true", help="Validate data without importing")

    args = parser.parse_args()

    logger.info("Starting database import")
    start_time = time.time()

    engine = get_engine()
    df = load_cleaned_data()

    if args.dry_run:
        logger.info("DRY RUN - validating %d records", len(df))
        logger.info("Columns: %s", list(df.columns))
        logger.info("Sample:\n%s", df.head())
        return

    # Import in order: brands -> categories -> products
    brand_map = import_brands(engine, df)
    category_map = import_categories(engine, df)
    imported = import_products(engine, df, brand_map, category_map)

    elapsed = time.time() - start_time
    log_extraction(engine, "cleaned_data_import", imported, "completed")

    logger.info(
        "Import complete: %d products in %.1f seconds (%.0f records/sec)",
        imported,
        elapsed,
        imported / max(elapsed, 1),
    )


if __name__ == "__main__":
    main()
