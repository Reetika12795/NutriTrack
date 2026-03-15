"""
Airflow DAG: Load data into the star-schema data warehouse
Schedule: Daily at 05:00 UTC (after aggregate_clean)
Covers: C13 (Star schema), C14 (DW creation), C15 (ETL), C17 (SCD)
"""

from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from airflow import DAG

default_args = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["admin@nutritrack.local"],
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _get_db_engine():
    import os

    from sqlalchemy import create_engine
    db_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('NUTRITRACK_DB_USER', 'nutritrack')}:"
        f"{os.getenv('NUTRITRACK_DB_PASSWORD', 'nutritrack')}@"
        f"{os.getenv('NUTRITRACK_DB_HOST', 'postgres')}:"
        f"{os.getenv('NUTRITRACK_DB_PORT', '5432')}/"
        f"{os.getenv('NUTRITRACK_DB_NAME', 'nutritrack')}"
    )
    return create_engine(db_url)


def load_dim_brands(**context):
    """Load brand dimension with SCD Type 1 (overwrite on correction)."""
    from sqlalchemy import text
    engine = _get_db_engine()

    with engine.begin() as conn:
        # Insert new brands
        result = conn.execute(text("""
            INSERT INTO dw.dim_brand (brand_name, parent_company)
            SELECT DISTINCT b.brand_name, b.parent_company
            FROM app.brands b
            LEFT JOIN dw.dim_brand db ON b.brand_name = db.brand_name
            WHERE db.brand_key IS NULL
        """))
        print(f"Inserted {result.rowcount} new brands")

        # SCD Type 1: update brand names that changed
        result = conn.execute(text("""
            UPDATE dw.dim_brand db
            SET brand_name = b.brand_name,
                parent_company = b.parent_company,
                last_updated = CURRENT_TIMESTAMP
            FROM app.brands b
            WHERE db.brand_name = b.brand_name
              AND (db.parent_company IS DISTINCT FROM b.parent_company)
        """))
        print(f"Updated {result.rowcount} brands (SCD Type 1)")


def load_dim_categories(**context):
    """Load category dimension."""
    from sqlalchemy import text
    engine = _get_db_engine()

    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO dw.dim_category (category_name, parent_category, category_level)
            SELECT DISTINCT
                c.category_name,
                pc.category_name AS parent_category,
                c.level
            FROM app.categories c
            LEFT JOIN app.categories pc ON c.parent_category_id = pc.category_id
            LEFT JOIN dw.dim_category dc ON c.category_name = dc.category_name
            WHERE dc.category_key IS NULL
        """))
        print(f"Inserted {result.rowcount} new categories")


def load_dim_products(**context):
    """Load product dimension with SCD Type 2 (historical tracking)."""
    from sqlalchemy import text
    engine = _get_db_engine()

    with engine.begin() as conn:
        # Insert new products (not yet in dimension)
        result = conn.execute(text("""
            INSERT INTO dw.dim_product (
                barcode, product_name, generic_name, quantity, packaging,
                ingredients_text, completeness_score, source_product_id
            )
            SELECT
                p.barcode, p.product_name, p.generic_name, p.quantity, p.packaging,
                p.ingredients_text, p.completeness_score, p.product_id
            FROM app.products p
            LEFT JOIN dw.dim_product dp ON p.barcode = dp.barcode AND dp.is_current = TRUE
            WHERE dp.product_key IS NULL
        """))
        new_count = result.rowcount
        print(f"Inserted {new_count} new products")

        # SCD Type 2: detect changes and create historical records
        result = conn.execute(text("""
            WITH changed_products AS (
                SELECT p.barcode, p.product_name, p.generic_name, p.quantity,
                       p.packaging, p.ingredients_text, p.completeness_score, p.product_id
                FROM app.products p
                JOIN dw.dim_product dp ON p.barcode = dp.barcode AND dp.is_current = TRUE
                WHERE p.product_name IS DISTINCT FROM dp.product_name
                   OR p.ingredients_text IS DISTINCT FROM dp.ingredients_text
                   OR p.completeness_score IS DISTINCT FROM dp.completeness_score
            )
            UPDATE dw.dim_product dp
            SET end_date = CURRENT_DATE - 1, is_current = FALSE
            FROM changed_products cp
            WHERE dp.barcode = cp.barcode AND dp.is_current = TRUE
            RETURNING dp.barcode
        """))
        changed_barcodes = result.fetchall()
        print(f"Closed {len(changed_barcodes)} product records (SCD Type 2)")

        # Insert new current versions for changed products
        if changed_barcodes:
            result = conn.execute(text("""
                INSERT INTO dw.dim_product (
                    barcode, product_name, generic_name, quantity, packaging,
                    ingredients_text, completeness_score, effective_date,
                    is_current, source_product_id
                )
                SELECT
                    p.barcode, p.product_name, p.generic_name, p.quantity, p.packaging,
                    p.ingredients_text, p.completeness_score, CURRENT_DATE,
                    TRUE, p.product_id
                FROM app.products p
                WHERE p.barcode IN (
                    SELECT dp.barcode FROM dw.dim_product dp
                    WHERE dp.is_current = FALSE
                    AND dp.end_date = CURRENT_DATE - 1
                )
                AND NOT EXISTS (
                    SELECT 1 FROM dw.dim_product dp2
                    WHERE dp2.barcode = p.barcode AND dp2.is_current = TRUE
                )
            """))
            print(f"Inserted {result.rowcount} updated product records (SCD Type 2)")


def load_dim_users(**context):
    """Load user dimension (anonymized) with SCD Type 2."""
    from sqlalchemy import text
    engine = _get_db_engine()

    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO dw.dim_user (user_hash, age_group, activity_level, dietary_goal, registration_date)
            SELECT
                encode(digest(u.user_id::text, 'sha256'), 'hex') AS user_hash,
                u.age_group, u.activity_level, u.dietary_goal,
                u.created_at::date
            FROM app.users u
            LEFT JOIN dw.dim_user du
                ON encode(digest(u.user_id::text, 'sha256'), 'hex') = du.user_hash
                AND du.is_current = TRUE
            WHERE du.user_key IS NULL
              AND u.is_active = TRUE
        """))
        print(f"Inserted {result.rowcount} new users into dimension")


def load_fact_product_market(**context):
    """Load product market analysis fact table."""
    from sqlalchemy import text
    engine = _get_db_engine()

    with engine.begin() as conn:
        today_key = datetime.now().strftime("%Y%m%d")

        result = conn.execute(text("""
            INSERT INTO dw.fact_product_market (
                product_key, brand_key, category_key, country_key, time_key,
                nutriscore_grade, nutriscore_score, nova_group, ecoscore_grade,
                completeness_score, energy_kcal_per_100g, fat_per_100g,
                sugars_per_100g, salt_per_100g, fiber_per_100g, proteins_per_100g
            )
            SELECT
                dp.product_key,
                db.brand_key,
                dc.category_key,
                dco.country_key,
                CAST(:time_key AS INTEGER),
                p.nutriscore_grade,
                p.nutriscore_score,
                p.nova_group,
                p.ecoscore_grade,
                p.completeness_score,
                p.energy_kcal,
                p.fat_g,
                p.sugars_g,
                p.salt_g,
                p.fiber_g,
                p.proteins_g
            FROM app.products p
            JOIN dw.dim_product dp ON p.barcode = dp.barcode AND dp.is_current = TRUE
            LEFT JOIN app.brands b ON p.brand_id = b.brand_id
            LEFT JOIN dw.dim_brand db ON b.brand_name = db.brand_name
            LEFT JOIN app.categories c ON p.category_id = c.category_id
            LEFT JOIN dw.dim_category dc ON c.category_name = dc.category_name
            LEFT JOIN dw.dim_country dco ON p.countries LIKE '%' || dco.country_name || '%'
            WHERE NOT EXISTS (
                SELECT 1 FROM dw.fact_product_market fpm
                WHERE fpm.product_key = dp.product_key
                  AND fpm.time_key = CAST(:time_key AS INTEGER)
            )
        """), {"time_key": today_key})
        print(f"Loaded {result.rowcount} product market facts")


def load_fact_daily_nutrition(**context):
    """Load daily nutrition fact table from meal tracking data."""
    from sqlalchemy import text
    engine = _get_db_engine()

    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO dw.fact_daily_nutrition (
                user_key, time_key, product_key, category_key, brand_key,
                meal_type, quantity_g, energy_kcal, fat_g, saturated_fat_g,
                carbohydrates_g, sugars_g, proteins_g, fiber_g, salt_g,
                nutriscore_score, nova_group
            )
            SELECT
                du.user_key,
                TO_CHAR(m.meal_date, 'YYYYMMDD')::INTEGER AS time_key,
                dp.product_key,
                dc.category_key,
                db.brand_key,
                m.meal_type,
                mi.quantity_g,
                mi.energy_kcal,
                mi.fat_g,
                NULL AS saturated_fat_g,
                mi.carbohydrates_g,
                NULL AS sugars_g,
                mi.proteins_g,
                mi.fiber_g,
                mi.salt_g,
                p.nutriscore_score,
                p.nova_group
            FROM app.meal_items mi
            JOIN app.meals m ON mi.meal_id = m.meal_id
            JOIN app.products p ON mi.product_id = p.product_id
            JOIN dw.dim_user du
                ON encode(digest(m.user_id::text, 'sha256'), 'hex') = du.user_hash
                AND du.is_current = TRUE
            JOIN dw.dim_product dp ON p.barcode = dp.barcode AND dp.is_current = TRUE
            LEFT JOIN app.brands b ON p.brand_id = b.brand_id
            LEFT JOIN dw.dim_brand db ON b.brand_name = db.brand_name
            LEFT JOIN app.categories c ON p.category_id = c.category_id
            LEFT JOIN dw.dim_category dc ON c.category_name = dc.category_name
            WHERE m.meal_date = CURRENT_DATE - 1
              AND NOT EXISTS (
                  SELECT 1 FROM dw.fact_daily_nutrition fdn
                  WHERE fdn.user_key = du.user_key
                    AND fdn.time_key = TO_CHAR(m.meal_date, 'YYYYMMDD')::INTEGER
                    AND fdn.product_key = dp.product_key
                    AND fdn.meal_type = m.meal_type
              )
        """))
        print(f"Loaded {result.rowcount} daily nutrition facts")


with DAG(
    "etl_load_warehouse",
    default_args=default_args,
    description="Load operational data into star-schema data warehouse (ETL)",
    schedule_interval="0 5 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["warehouse", "etl", "star-schema", "scd"],
) as dag:

    # Wait for etl_aggregate_clean to finish loading data into PostgreSQL app schema
    wait_for_app_load = ExternalTaskSensor(
        task_id="wait_for_aggregate_clean",
        external_dag_id="etl_aggregate_clean",
        external_task_id="load_to_database",
        execution_delta=timedelta(hours=1),  # this DAG runs at 05:00, aggregate_clean at 04:00
        timeout=3600,
        poke_interval=60,
        mode="reschedule",
    )

    dims_brands = PythonOperator(task_id="load_dim_brands", python_callable=load_dim_brands)
    dims_categories = PythonOperator(task_id="load_dim_categories", python_callable=load_dim_categories)
    dims_products = PythonOperator(task_id="load_dim_products", python_callable=load_dim_products)
    dims_users = PythonOperator(task_id="load_dim_users", python_callable=load_dim_users)
    fact_market = PythonOperator(task_id="load_fact_product_market", python_callable=load_fact_product_market)
    fact_nutrition = PythonOperator(task_id="load_fact_daily_nutrition", python_callable=load_fact_daily_nutrition)

    # Sensor must pass before dimensions load; dimensions must load before facts
    wait_for_app_load >> [dims_brands, dims_categories, dims_products, dims_users]
    [dims_brands, dims_categories, dims_products, dims_users] >> fact_market
    [dims_brands, dims_categories, dims_products, dims_users] >> fact_nutrition
