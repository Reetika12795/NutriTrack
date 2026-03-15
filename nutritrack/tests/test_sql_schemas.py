"""Tests for SQL schema files — validates syntax and structural expectations."""

from pathlib import Path

SQL_DIR = Path(__file__).parent.parent / "sql"


def _read_sql(filename: str) -> str:
    """Read a SQL file from the sql/ directory tree."""
    for sql_file in SQL_DIR.rglob(filename):
        return sql_file.read_text(encoding="utf-8")
    raise FileNotFoundError(f"{filename} not found under {SQL_DIR}")


class TestOperationalSchema:
    def test_file_exists(self):
        assert (SQL_DIR / "init" / "01_schema_operational.sql").exists()

    def test_creates_app_schema(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "CREATE SCHEMA IF NOT EXISTS app" in sql

    def test_creates_products_table(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "CREATE TABLE app.products" in sql

    def test_creates_users_table(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "CREATE TABLE app.users" in sql

    def test_creates_meals_table(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "CREATE TABLE app.meals" in sql

    def test_creates_rgpd_registry(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "rgpd_data_registry" in sql

    def test_barcode_unique_constraint(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "UNIQUE" in sql
        assert "barcode" in sql

    def test_role_check_constraint(self):
        sql = _read_sql("01_schema_operational.sql")
        assert "'user'" in sql
        assert "'nutritionist'" in sql
        assert "'admin'" in sql


class TestWarehouseSchema:
    def test_file_exists(self):
        assert (SQL_DIR / "init" / "02_schema_warehouse.sql").exists()

    def test_creates_dw_schema(self):
        sql = _read_sql("02_schema_warehouse.sql")
        assert "CREATE SCHEMA IF NOT EXISTS dw" in sql

    def test_creates_dim_time(self):
        sql = _read_sql("02_schema_warehouse.sql")
        assert "CREATE TABLE dw.dim_time" in sql

    def test_creates_dim_product(self):
        sql = _read_sql("02_schema_warehouse.sql")
        assert "CREATE TABLE dw.dim_product" in sql

    def test_creates_fact_daily_nutrition(self):
        sql = _read_sql("02_schema_warehouse.sql")
        assert "CREATE TABLE dw.fact_daily_nutrition" in sql

    def test_creates_fact_product_market(self):
        sql = _read_sql("02_schema_warehouse.sql")
        assert "CREATE TABLE dw.fact_product_market" in sql

    def test_scd_type2_product_fields(self):
        """SCD Type 2 requires effective_date, end_date, is_current."""
        sql = _read_sql("02_schema_warehouse.sql")
        assert "effective_date" in sql
        assert "end_date" in sql
        assert "is_current" in sql

    def test_star_schema_foreign_keys(self):
        """Fact tables reference dimension tables."""
        sql = _read_sql("02_schema_warehouse.sql")
        assert "REFERENCES dw.dim_user" in sql
        assert "REFERENCES dw.dim_time" in sql
        assert "REFERENCES dw.dim_product" in sql

    def test_grants_exist(self):
        sql = _read_sql("02_schema_warehouse.sql")
        assert "GRANT" in sql
        assert "etl_service" in sql
