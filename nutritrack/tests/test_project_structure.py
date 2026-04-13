"""Tests validating project file structure and configuration integrity.

Ensures all expected directories, configuration files, Dockerfiles,
and SQL schemas are present and well-formed.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SQL_DIR = PROJECT_ROOT / "sql"


class TestProjectDirectories:
    """Verify the expected directory layout exists."""

    def test_api_directory_exists(self):
        assert (PROJECT_ROOT / "api").is_dir()

    def test_app_directory_exists(self):
        assert (PROJECT_ROOT / "app").is_dir()

    def test_airflow_directory_exists(self):
        assert (PROJECT_ROOT / "airflow").is_dir()

    def test_airflow_dags_directory_exists(self):
        assert (PROJECT_ROOT / "airflow" / "dags").is_dir()

    def test_scripts_directory_exists(self):
        assert (PROJECT_ROOT / "scripts").is_dir()

    def test_sql_directory_exists(self):
        assert (PROJECT_ROOT / "sql").is_dir()

    def test_monitoring_directory_exists(self):
        assert (PROJECT_ROOT / "monitoring").is_dir()

    def test_tests_directory_exists(self):
        assert (PROJECT_ROOT / "tests").is_dir()


class TestDockerfiles:
    """Verify each service has a valid Dockerfile."""

    def test_api_dockerfile_exists(self):
        assert (PROJECT_ROOT / "api" / "Dockerfile").is_file()

    def test_app_dockerfile_exists(self):
        assert (PROJECT_ROOT / "app" / "Dockerfile").is_file()

    def test_airflow_dockerfile_exists(self):
        assert (PROJECT_ROOT / "airflow" / "Dockerfile").is_file()

    def test_docker_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").is_file()

    def test_api_dockerfile_has_from(self):
        content = (PROJECT_ROOT / "api" / "Dockerfile").read_text()
        assert content.strip().startswith("FROM ")

    def test_app_dockerfile_has_from(self):
        content = (PROJECT_ROOT / "app" / "Dockerfile").read_text()
        assert content.strip().startswith("FROM ")


class TestRequirements:
    """Verify Python requirement files are present and non-empty."""

    def test_root_requirements_exists(self):
        path = PROJECT_ROOT / "requirements.txt"
        assert path.is_file()
        assert path.stat().st_size > 0

    def test_dev_requirements_exists(self):
        path = PROJECT_ROOT / "requirements-dev.txt"
        assert path.is_file()
        assert path.stat().st_size > 0

    def test_api_requirements_exists(self):
        path = PROJECT_ROOT / "api" / "requirements.txt"
        assert path.is_file()
        assert path.stat().st_size > 0

    def test_dev_requirements_has_pytest(self):
        content = (PROJECT_ROOT / "requirements-dev.txt").read_text()
        assert "pytest" in content

    def test_dev_requirements_has_ruff(self):
        content = (PROJECT_ROOT / "requirements-dev.txt").read_text()
        assert "ruff" in content


class TestPyprojectToml:
    """Verify pyproject.toml has expected tool configurations."""

    def test_file_exists(self):
        assert (PROJECT_ROOT / "pyproject.toml").is_file()

    def test_has_ruff_config(self):
        content = (PROJECT_ROOT / "pyproject.toml").read_text()
        assert "[tool.ruff]" in content

    def test_has_pytest_config(self):
        content = (PROJECT_ROOT / "pyproject.toml").read_text()
        assert "[tool.pytest" in content


class TestSQLMigrations:
    """Verify SQL migration files are present and well-structured."""

    def test_init_directory_exists(self):
        assert (SQL_DIR / "init").is_dir()

    def test_migrations_directory_exists(self):
        assert (SQL_DIR / "migrations").is_dir()

    def test_operational_schema_is_first(self):
        """Operational schema should be numbered 01."""
        assert (SQL_DIR / "init" / "01_schema_operational.sql").is_file()

    def test_warehouse_schema_is_second(self):
        """Warehouse schema should be numbered 02."""
        assert (SQL_DIR / "init" / "02_schema_warehouse.sql").is_file()

    def test_scd_procedures_exist(self):
        """SCD (Slowly Changing Dimension) procedures for C17."""
        assert (SQL_DIR / "scd_procedures.sql").is_file()

    def test_analytical_queries_exist(self):
        """Analytical queries file should exist."""
        assert (SQL_DIR / "queries" / "analytical_queries.sql").is_file()

    def test_etl_activity_log_migration(self):
        """ETL activity log migration for C16."""
        assert (SQL_DIR / "migrations" / "001_add_etl_activity_log.sql").is_file()

    def test_init_databases_script(self):
        """Database initialization script should create required databases."""
        content = (SQL_DIR / "init" / "00_init_databases.sql").read_text()
        assert "CREATE" in content.upper()


class TestETLScripts:
    """Verify ETL scripts are present for each extraction method."""

    def test_api_extraction_exists(self):
        assert (PROJECT_ROOT / "scripts" / "extract_off_api.py").is_file()

    def test_scraping_extraction_exists(self):
        assert (PROJECT_ROOT / "scripts" / "extract_scraping.py").is_file()

    def test_parquet_extraction_exists(self):
        assert (PROJECT_ROOT / "scripts" / "extract_off_parquet.py").is_file()

    def test_duckdb_extraction_exists(self):
        assert (PROJECT_ROOT / "scripts" / "extract_duckdb.py").is_file()

    def test_db_extraction_exists(self):
        assert (PROJECT_ROOT / "scripts" / "extract_from_db.py").is_file()

    def test_aggregate_clean_exists(self):
        assert (PROJECT_ROOT / "scripts" / "aggregate_clean.py").is_file()

    def test_import_to_db_exists(self):
        assert (PROJECT_ROOT / "scripts" / "import_to_db.py").is_file()

    def test_backup_database_exists(self):
        assert (PROJECT_ROOT / "scripts" / "backup_database.py").is_file()


class TestAirflowDags:
    """Verify Airflow DAGs are present."""

    def test_dags_directory_has_python_files(self):
        dags_dir = PROJECT_ROOT / "airflow" / "dags"
        dag_files = list(dags_dir.glob("*.py"))
        assert len(dag_files) > 0, "No DAG files found in airflow/dags/"

    def test_etl_load_warehouse_dag(self):
        assert (PROJECT_ROOT / "airflow" / "dags" / "etl_load_warehouse.py").is_file()

    def test_etl_extract_api_dag(self):
        assert (PROJECT_ROOT / "airflow" / "dags" / "etl_extract_off_api.py").is_file()
