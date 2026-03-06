"""
NutriTrack - Database backup script
Covers: C16 - DW maintenance (scheduled backups)
Entry point: main()
"""

import argparse
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("NUTRITRACK_DB_HOST", "localhost")
DB_PORT = os.getenv("NUTRITRACK_DB_PORT", "5432")
DB_NAME = os.getenv("NUTRITRACK_DB_NAME", "nutritrack")
DB_USER = os.getenv("NUTRITRACK_DB_USER", "postgres")
DB_PASSWORD = os.getenv("NUTRITRACK_DB_PASSWORD", "postgres")

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "data/backups"))

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")


def run_pg_dump(backup_type: str = "full", schemas: list[str] | None = None) -> Path | None:
    """Run pg_dump to create a database backup."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"nutritrack_{backup_type}_{timestamp}.sql.gz"
    backup_path = BACKUP_DIR / filename

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    cmd = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "--format=custom",
        "--compress=6",
        f"--file={backup_path}",
    ]

    if schemas:
        for schema in schemas:
            cmd.extend(["--schema", schema])

    if backup_type == "data_only":
        cmd.append("--data-only")
    elif backup_type == "schema_only":
        cmd.append("--schema-only")

    try:
        logger.info("Running backup: %s", " ".join(cmd))
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info("Backup created: %s (%.2f MB)", backup_path, size_mb)
            return backup_path
        else:
            logger.error("Backup failed: %s", result.stderr)
            return None

    except FileNotFoundError:
        logger.error("pg_dump not found. Install PostgreSQL client tools.")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Backup timed out after 300 seconds")
        return None


def upload_to_minio(backup_path: Path) -> bool:
    """Upload backup to MinIO backups bucket."""
    try:
        from minio import Minio
        client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

        date_prefix = datetime.now().strftime("%Y/%m/%d")
        object_name = f"{date_prefix}/{backup_path.name}"

        client.fput_object("backups", object_name, str(backup_path))
        logger.info("Uploaded to MinIO: backups/%s", object_name)
        return True

    except Exception as e:
        logger.error("MinIO upload failed: %s", e)
        return False


def cleanup_old_backups(keep_days: int = 7):
    """Remove local backups older than keep_days."""
    if not BACKUP_DIR.exists():
        return

    cutoff = time.time() - (keep_days * 86400)
    removed = 0

    for f in BACKUP_DIR.glob("nutritrack_*.sql.gz"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1

    if removed:
        logger.info("Cleaned up %d old local backups", removed)


def main():
    parser = argparse.ArgumentParser(description="NutriTrack database backup")
    parser.add_argument(
        "--type",
        choices=["full", "app_only", "dw_only", "schema_only", "data_only"],
        default="full",
        help="Backup type",
    )
    parser.add_argument("--upload", action="store_true", help="Upload to MinIO")
    parser.add_argument("--cleanup", type=int, default=7, help="Remove local backups older than N days")

    args = parser.parse_args()

    schemas = None
    if args.type == "app_only":
        schemas = ["app"]
    elif args.type == "dw_only":
        schemas = ["dw"]

    backup_type = args.type if args.type in ("full", "schema_only", "data_only") else "full"
    backup_path = run_pg_dump(backup_type, schemas)

    if backup_path:
        if args.upload:
            upload_to_minio(backup_path)
        cleanup_old_backups(args.cleanup)
        logger.info("Backup process complete")
    else:
        logger.error("Backup failed")
        exit(1)


if __name__ == "__main__":
    main()
