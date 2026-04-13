"""
NutriTrack - MinIO Data Lake setup and governance configuration
Covers: C18 (Architecture), C19 (Infrastructure), C20 (Catalog), C21 (Governance)
Entry point: main()
"""

import argparse
import json
import logging
import os

from minio import Minio
from minio.commonconfig import ENABLED
from minio.lifecycleconfig import Expiration, Filter, LifecycleConfig, Rule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")

# Medallion architecture buckets
BUCKETS = {
    "bronze": "Raw data layer - as-is from sources",
    "silver": "Cleaned and validated data layer",
    "gold": "Analytics-ready, aggregated data layer",
    "backups": "Database backups and system snapshots",
}

# Access policies per group (C21 - Data Governance)
GROUP_POLICIES = {
    "app_users": {
        "description": "Application end-users: read-only access to gold analytics",
        "buckets": {"gold": "readonly"},
    },
    "nutritionists": {
        "description": "Nutritionists: read access to silver and gold",
        "buckets": {"silver": "readonly", "gold": "readonly"},
    },
    "admins": {
        "description": "Administrators: full access to all buckets",
        "buckets": {"bronze": "readwrite", "silver": "readwrite", "gold": "readwrite", "backups": "readwrite"},
    },
    "etl_service": {
        "description": "ETL pipeline service: write access to all data buckets",
        "buckets": {"bronze": "readwrite", "silver": "readwrite", "gold": "readwrite"},
    },
}


def get_client() -> Minio:
    """Create MinIO client."""
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)


def create_buckets(client: Minio):
    """Create medallion architecture buckets."""
    for bucket, description in BUCKETS.items():
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("Created bucket: %s (%s)", bucket, description)
        else:
            logger.info("Bucket already exists: %s", bucket)


def setup_lifecycle_rules(client: Minio):
    """Configure data lifecycle rules (C20 - Data lifecycle management)."""
    # Bronze: expire after 90 days
    bronze_config = LifecycleConfig(
        [
            Rule(
                ENABLED, rule_filter=Filter(prefix="api/"), expiration=Expiration(days=90), rule_id="expire-api-raw-90d"
            ),
            Rule(
                ENABLED,
                rule_filter=Filter(prefix="scraping/"),
                expiration=Expiration(days=90),
                rule_id="expire-scraping-raw-90d",
            ),
        ]
    )
    try:
        client.set_bucket_lifecycle("bronze", bronze_config)
        logger.info("Bronze lifecycle rules set (90-day expiration)")
    except Exception as e:
        logger.warning("Could not set bronze lifecycle: %s", e)

    # Backups: expire after 30 days
    backup_config = LifecycleConfig(
        [
            Rule(
                ENABLED,
                rule_filter=Filter(prefix="daily/"),
                expiration=Expiration(days=30),
                rule_id="expire-daily-backups-30d",
            )
        ]
    )
    try:
        client.set_bucket_lifecycle("backups", backup_config)
        logger.info("Backup lifecycle rules set (30-day expiration)")
    except Exception as e:
        logger.warning("Could not set backup lifecycle: %s", e)


def generate_bucket_policy(bucket: str, access: str) -> dict:
    """Generate a MinIO bucket policy JSON."""
    if access == "readonly":
        actions = ["s3:GetObject", "s3:ListBucket"]
    elif access == "readwrite":
        actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    else:
        actions = ["s3:GetObject"]

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": actions,
                "Resource": [f"arn:aws:s3:::{bucket}/*", f"arn:aws:s3:::{bucket}"],
            }
        ],
    }


def setup_access_policies(client: Minio):
    """Document and apply access policies per group (C21)."""
    logger.info("Access policy documentation:")
    for group, config in GROUP_POLICIES.items():
        logger.info("  Group: %s - %s", group, config["description"])
        for bucket, access in config["buckets"].items():
            logger.info("    %s: %s", bucket, access)

    # Set gold bucket as publicly readable (for app users)
    try:
        policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": ["arn:aws:s3:::gold/*"],
                    }
                ],
            }
        )
        client.set_bucket_policy("gold", policy)
        logger.info("Gold bucket: public read access enabled")
    except Exception as e:
        logger.warning("Could not set gold policy: %s", e)


def upload_initial_catalog(client: Minio):
    """Upload initial data catalog metadata (C20)."""
    from io import BytesIO

    catalog = {
        "catalog_version": "2.0",
        "project": "NutriTrack",
        "description": "Fitness Nutrition Tracker Data Catalog",
        "architecture_principle": (
            "The DW and the Lake answer different questions for different people. "
            "The DW serves BI analysts with normalized star schema (fast SQL JOINs). "
            "The Lake serves data scientists with flat files (pd.read_parquet() and go)."
        ),
        "layers": {
            "bronze": {
                "description": "Raw data as ingested from sources — immutable archive",
                "datasets": {
                    "api/": "Open Food Facts API extractions (JSON)",
                    "parquet/": "OFF Parquet export extractions",
                    "scraping/": "Nutritional guidelines web scraping",
                    "duckdb/": "DuckDB analytical query results",
                },
                "metadata": {
                    "_manifests/": "Ingestion manifests (file counts per date)",
                    "_lineage/": "Source lineage: availability, file sizes, row counts before processing",
                },
                "retention": "90 days",
                "update_frequency": "daily",
            },
            "silver": {
                "description": "Cleaned, validated, and deduplicated data",
                "datasets": {
                    "products/": "Cleaned product dataset (Parquet, CSV)",
                },
                "metadata": {
                    "_quality/": "Data quality reports: completeness scores, null rates, cleaning decisions",
                    "_reports/": "Cleaning execution reports",
                },
                "retention": "1 year",
                "update_frequency": "daily",
            },
            "gold": {
                "description": "Denormalized, ML-ready, and metadata datasets for data scientists — NOT DW copies",
                "datasets": {
                    "product_wide_denormalized/": "Flat table: every product + brand + category inlined (no JOINs needed)",
                    "data_quality_report/": "Column-level completeness, null rates, anomaly flags",
                    "source_comparison/": "Cross-source analysis: row counts, overlap, unique products per source",
                    "daily_snapshots/": "Full catalog as one dated file — time-travel without SCD",
                    "ml_nutrition_features/": "Scaled/encoded feature matrix ready for ML training",
                },
                "consumers": "Data scientists, ML engineers, data stewards",
                "retention": "indefinite",
                "update_frequency": "daily",
            },
        },
        "governance": {
            "rgpd": {
                "personal_data": "No personal data in data lake (user data stays in PostgreSQL only)",
                "data_registry": "RGPD data registry maintained in app.rgpd_data_registry table",
                "deletion_procedures": "Lifecycle rules auto-delete expired raw data",
            },
            "access_groups": GROUP_POLICIES,
        },
        "lineage": {
            "bronze -> silver": "etl_aggregate_clean (clean_data): deduplication, format normalization, validation",
            "silver -> gold": "etl_datalake_ingest (publish_to_gold): reads silver Parquet, builds denormalized + quality + ML datasets (NO PostgreSQL)",
            "cleaned data -> postgres (app)": "etl_aggregate_clean (load_to_database): load cleaned data into operational database",
            "postgres (app) -> postgres (dw)": "etl_load_warehouse: star schema ETL with SCD (reads app + user data, distinct from gold layer)",
            "parallel_fork": "etl_datalake_ingest and etl_load_warehouse both run at 05:00, independently consuming etl_aggregate_clean output",
        },
    }

    catalog_bytes = json.dumps(catalog, indent=2).encode()
    for bucket in ["bronze", "silver", "gold"]:
        client.put_object(
            bucket,
            "_catalog/metadata.json",
            BytesIO(catalog_bytes),
            len(catalog_bytes),
            content_type="application/json",
        )
    logger.info("Data catalog metadata uploaded to all buckets")


def check_storage_status(client: Minio):
    """Monitor storage status (C20 - monitoring)."""
    logger.info("Storage status:")
    for bucket in BUCKETS:
        if client.bucket_exists(bucket):
            objects = list(client.list_objects(bucket, recursive=True))
            total_size = sum(obj.size for obj in objects if obj.size)
            logger.info(
                "  %s: %d objects, %.2f MB",
                bucket,
                len(objects),
                total_size / (1024 * 1024),
            )


def main():
    parser = argparse.ArgumentParser(description="Setup MinIO Data Lake for NutriTrack")
    parser.add_argument("--create-buckets", action="store_true", help="Create medallion buckets")
    parser.add_argument("--setup-lifecycle", action="store_true", help="Configure lifecycle rules")
    parser.add_argument("--setup-access", action="store_true", help="Configure access policies")
    parser.add_argument("--upload-catalog", action="store_true", help="Upload data catalog")
    parser.add_argument("--check-status", action="store_true", help="Check storage status")
    parser.add_argument("--all", action="store_true", help="Run all setup steps")

    args = parser.parse_args()
    run_all = args.all or not any(
        [
            args.create_buckets,
            args.setup_lifecycle,
            args.setup_access,
            args.upload_catalog,
            args.check_status,
        ]
    )

    client = get_client()

    if run_all or args.create_buckets:
        create_buckets(client)
    if run_all or args.setup_lifecycle:
        setup_lifecycle_rules(client)
    if run_all or args.setup_access:
        setup_access_policies(client)
    if run_all or args.upload_catalog:
        upload_initial_catalog(client)
    if run_all or args.check_status:
        check_storage_status(client)

    logger.info("MinIO Data Lake setup complete")


if __name__ == "__main__":
    main()
