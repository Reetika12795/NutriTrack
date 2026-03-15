"""
NutriTrack — Airflow alerting callbacks and SLA monitoring.
Covers: C16 - Activity logging with alert/error categories, alert system on ETL errors.

Usage in DAGs:
    from alerting import ALERTING_DEFAULT_ARGS, sla_miss_callback

    default_args = {**ALERTING_DEFAULT_ARGS, "owner": "nutritrack"}

    with DAG(..., default_args=default_args, sla_miss_callback=sla_miss_callback):
        ...
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger("nutritrack.alerting")


def _get_db_engine():
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


def _log_to_db(
    alert_category: str,
    dag_id: str,
    task_id: str | None,
    run_id: str | None,
    execution_date: datetime | None,
    event_type: str,
    message: str,
    details: dict | None = None,
):
    """Insert a structured log entry into app.etl_activity_log."""
    try:
        from sqlalchemy import text

        engine = _get_db_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO app.etl_activity_log
                    (alert_category, dag_id, task_id, run_id, execution_date,
                     event_type, message, details)
                VALUES (:cat, :dag, :task, :run, :exec_date, :evt, :msg, :det)
            """),
                {
                    "cat": alert_category,
                    "dag": dag_id,
                    "task": task_id,
                    "run": run_id,
                    "exec_date": execution_date,
                    "evt": event_type,
                    "msg": message,
                    "det": json.dumps(details) if details else None,
                },
            )
    except Exception as e:
        logger.error("Failed to log alert to DB: %s", e)


def on_failure_callback(context):
    """Called when a task fails. Logs CRITICAL alert."""
    ti = context.get("task_instance")
    dag_id = ti.dag_id if ti else context.get("dag", {}).dag_id
    task_id = ti.task_id if ti else "unknown"
    run_id = context.get("run_id", "")
    execution_date = context.get("execution_date")
    exception = context.get("exception")

    message = f"Task {dag_id}.{task_id} FAILED: {exception}"
    details = {
        "try_number": ti.try_number if ti else None,
        "max_tries": ti.max_tries if ti else None,
        "exception_type": type(exception).__name__ if exception else None,
        "log_url": ti.log_url if ti else None,
    }

    logger.critical("[CRITICAL] %s", message)
    _log_to_db("CRITICAL", dag_id, task_id, run_id, execution_date, "task_failure", message, details)


def on_success_callback(context):
    """Called when a task succeeds. Logs INFO alert."""
    ti = context.get("task_instance")
    dag_id = ti.dag_id if ti else "unknown"
    task_id = ti.task_id if ti else "unknown"
    run_id = context.get("run_id", "")
    execution_date = context.get("execution_date")
    duration = ti.duration if ti else None

    message = f"Task {dag_id}.{task_id} succeeded (duration: {duration}s)"
    details = {
        "duration_seconds": duration,
        "try_number": ti.try_number if ti else None,
    }

    logger.info("[INFO] %s", message)
    _log_to_db("INFO", dag_id, task_id, run_id, execution_date, "task_success", message, details)


def on_retry_callback(context):
    """Called when a task retries. Logs WARNING alert."""
    ti = context.get("task_instance")
    dag_id = ti.dag_id if ti else "unknown"
    task_id = ti.task_id if ti else "unknown"
    run_id = context.get("run_id", "")
    execution_date = context.get("execution_date")
    exception = context.get("exception")

    message = f"Task {dag_id}.{task_id} RETRYING (attempt {ti.try_number}): {exception}"
    details = {
        "try_number": ti.try_number if ti else None,
        "max_tries": ti.max_tries if ti else None,
        "exception_type": type(exception).__name__ if exception else None,
    }

    logger.warning("[WARNING] %s", message)
    _log_to_db("WARNING", dag_id, task_id, run_id, execution_date, "task_retry", message, details)


def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Called when an SLA is missed. Logs WARNING alert."""
    dag_id = dag.dag_id if dag else "unknown"
    missed_tasks = [str(t) for t in task_list] if task_list else []

    message = f"SLA MISS in {dag_id}: tasks {', '.join(missed_tasks)}"
    details = {
        "missed_tasks": missed_tasks,
        "blocking_tasks": [str(t) for t in blocking_task_list] if blocking_task_list else [],
        "sla_definitions": [str(s) for s in slas] if slas else [],
    }

    logger.warning("[WARNING] %s", message)
    _log_to_db("WARNING", dag_id, None, None, None, "sla_miss", message, details)


# Default args with alerting callbacks for use in all DAGs
ALERTING_DEFAULT_ARGS = {
    "owner": "nutritrack",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["admin@nutritrack.local"],
    "retries": 2,
    "on_failure_callback": on_failure_callback,
    "on_success_callback": on_success_callback,
    "on_retry_callback": on_retry_callback,
}
