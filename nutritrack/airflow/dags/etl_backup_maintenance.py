"""
Airflow DAG: Scheduled backups and maintenance tasks
Schedule: Daily at 02:00 UTC (before ETL pipelines)
Covers: C16 - Scheduled full/partial backups, maintenance procedures

Backup strategy:
  - Daily: Partial backup of dw schema only (incremental, fast)
  - Weekly (Sunday): Full database backup (all schemas)
  - Both uploaded to MinIO backups bucket
  - Local backups cleaned up after 7 days
"""

from __future__ import annotations

from datetime import datetime, timedelta

from alerting import ALERTING_DEFAULT_ARGS, sla_miss_callback

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    **ALERTING_DEFAULT_ARGS,
    "retry_delay": timedelta(minutes=10),
}


def run_dw_backup(**context):
    """Daily partial backup: data warehouse schema only."""
    import sys

    sys.path.insert(0, "/opt/airflow/scripts")
    from backup_database import cleanup_old_backups, run_pg_dump, upload_to_minio

    backup_path = run_pg_dump(backup_type="full", schemas=["dw"])
    if backup_path:
        upload_to_minio(backup_path)
        cleanup_old_backups(keep_days=7)
        print(f"DW backup completed: {backup_path}")
    else:
        raise RuntimeError("DW backup failed — see backup_database.py logs")


def run_full_backup(**context):
    """Weekly full backup: all schemas."""
    import sys

    sys.path.insert(0, "/opt/airflow/scripts")
    from backup_database import cleanup_old_backups, run_pg_dump, upload_to_minio

    backup_path = run_pg_dump(backup_type="full")
    if backup_path:
        upload_to_minio(backup_path)
        cleanup_old_backups(keep_days=7)
        print(f"Full backup completed: {backup_path}")
    else:
        raise RuntimeError("Full backup failed — see backup_database.py logs")


def run_rgpd_cleanup(**context):
    """Run RGPD data cleanup: delete expired user data."""
    import os

    from sqlalchemy import create_engine, text

    db_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('NUTRITRACK_DB_USER', 'nutritrack')}:"
        f"{os.getenv('NUTRITRACK_DB_PASSWORD', 'nutritrack')}@"
        f"{os.getenv('NUTRITRACK_DB_HOST', 'postgres')}:"
        f"{os.getenv('NUTRITRACK_DB_PORT', '5432')}/"
        f"{os.getenv('NUTRITRACK_DB_NAME', 'nutritrack')}"
    )
    engine = create_engine(db_url)

    with engine.begin() as conn:
        result = conn.execute(text("SELECT app.rgpd_cleanup_expired_data()"))
        deleted = result.scalar()
        print(f"RGPD cleanup: {deleted} records affected")


def check_storage_health(**context):
    """Check PostgreSQL and MinIO storage health metrics."""
    import os

    from sqlalchemy import create_engine, text

    db_url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('NUTRITRACK_DB_USER', 'nutritrack')}:"
        f"{os.getenv('NUTRITRACK_DB_PASSWORD', 'nutritrack')}@"
        f"{os.getenv('NUTRITRACK_DB_HOST', 'postgres')}:"
        f"{os.getenv('NUTRITRACK_DB_PORT', '5432')}/"
        f"{os.getenv('NUTRITRACK_DB_NAME', 'nutritrack')}"
    )
    engine = create_engine(db_url)

    # Check database sizes
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT
                schemaname,
                COUNT(*) AS table_count,
                pg_size_pretty(SUM(pg_total_relation_size(schemaname || '.' || tablename))) AS total_size
            FROM pg_tables
            WHERE schemaname IN ('app', 'dw')
            GROUP BY schemaname
        """)
        )
        for row in result:
            print(f"Schema {row[0]}: {row[1]} tables, {row[2]} total size")

        # Check row counts for key tables
        for table in ["app.products", "dw.dim_product", "dw.fact_product_market", "dw.fact_daily_nutrition"]:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count} rows")

    # Check MinIO bucket sizes
    try:
        from minio import Minio

        client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=False,
        )
        for bucket in ["bronze", "silver", "gold", "backups"]:
            objects = list(client.list_objects(bucket, recursive=True))
            total_size = sum(obj.size for obj in objects)
            print(f"MinIO {bucket}: {len(objects)} objects, {total_size / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"MinIO health check failed: {e}")


with DAG(
    "etl_backup_maintenance",
    default_args=default_args,
    description="Scheduled backups, RGPD cleanup, and storage health checks (C16)",
    schedule_interval="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["backup", "maintenance", "rgpd", "c16"],
    sla_miss_callback=sla_miss_callback,
) as dag:
    # Daily DW backup
    dw_backup = PythonOperator(
        task_id="backup_dw_schema",
        python_callable=run_dw_backup,
        sla=timedelta(minutes=30),
    )

    # Weekly full backup (only runs on Sundays)
    full_backup = PythonOperator(
        task_id="backup_full_database",
        python_callable=run_full_backup,
        sla=timedelta(hours=1),
    )

    # Weekly RGPD cleanup (Sundays)
    rgpd_cleanup = PythonOperator(
        task_id="rgpd_data_cleanup",
        python_callable=run_rgpd_cleanup,
        sla=timedelta(minutes=10),
    )

    # Daily storage health check
    storage_check = PythonOperator(
        task_id="check_storage_health",
        python_callable=check_storage_health,
        sla=timedelta(minutes=5),
    )

    # DW backup runs daily; full backup + RGPD cleanup run after DW backup
    dw_backup >> full_backup >> rgpd_cleanup
    dw_backup >> storage_check
