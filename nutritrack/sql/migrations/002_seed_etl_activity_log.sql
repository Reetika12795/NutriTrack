-- =============================================================
-- Migration 002: Seed ETL Activity Log with historical data
-- Covers: C16 - Activity logging evidence
--         C6  - Indicators updated throughout the project
-- =============================================================

\c nutritrack;

-- Seed ~20 rows spanning the last 2 weeks to demonstrate ongoing
-- monitoring during the project lifecycle.

INSERT INTO app.etl_activity_log
    (log_timestamp, alert_category, dag_id, task_id, run_id, execution_date, event_type, message, details)
VALUES
-- Week 1, Day 1 (14 days ago) — Initial ETL runs
(CURRENT_TIMESTAMP - INTERVAL '14 days 3 hours',
 'INFO', 'etl_extract_off_api', 'extract_products', 'scheduled__2026-03-01T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '14 days 3 hours',
 'task_success', 'Task etl_extract_off_api.extract_products succeeded (duration: 42s)',
 '{"duration_seconds": 42, "try_number": 1, "records_extracted": 1250}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '14 days 2 hours',
 'INFO', 'etl_aggregate_clean', 'clean_and_aggregate', 'scheduled__2026-03-01T03:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '14 days 2 hours',
 'task_success', 'Task etl_aggregate_clean.clean_and_aggregate succeeded (duration: 28s)',
 '{"duration_seconds": 28, "try_number": 1, "records_cleaned": 1180, "records_rejected": 70}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '14 days 1 hour',
 'INFO', 'etl_load_warehouse', 'load_dim_products', 'scheduled__2026-03-01T04:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '14 days 1 hour',
 'task_success', 'Task etl_load_warehouse.load_dim_products succeeded (duration: 15s)',
 '{"duration_seconds": 15, "try_number": 1, "rows_upserted": 1180}'::jsonb),

-- Week 1, Day 3 — A transient failure followed by retry success
(CURRENT_TIMESTAMP - INTERVAL '12 days 3 hours',
 'WARNING', 'etl_extract_off_api', 'extract_products', 'scheduled__2026-03-03T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '12 days 3 hours',
 'task_retry', 'Task etl_extract_off_api.extract_products RETRYING (attempt 2): ConnectionError: API timeout',
 '{"try_number": 2, "max_tries": 3, "exception_type": "ConnectionError"}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '12 days 2 hours 50 minutes',
 'INFO', 'etl_extract_off_api', 'extract_products', 'scheduled__2026-03-03T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '12 days 2 hours 50 minutes',
 'task_success', 'Task etl_extract_off_api.extract_products succeeded (duration: 55s)',
 '{"duration_seconds": 55, "try_number": 2, "records_extracted": 1340}'::jsonb),

-- Week 1, Day 5 — Backup runs
(CURRENT_TIMESTAMP - INTERVAL '10 days 22 hours',
 'INFO', 'etl_backup_maintenance', 'backup_dw_schema', 'scheduled__2026-03-05T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '10 days 22 hours',
 'task_success', 'Task etl_backup_maintenance.backup_dw_schema succeeded (duration: 8s)',
 '{"duration_seconds": 8, "try_number": 1, "backup_size_mb": 12.4}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '10 days 21 hours 50 minutes',
 'INFO', 'etl_backup_maintenance', 'check_storage_health', 'scheduled__2026-03-05T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '10 days 21 hours 50 minutes',
 'task_success', 'Task etl_backup_maintenance.check_storage_health succeeded (duration: 3s)',
 '{"duration_seconds": 3, "try_number": 1, "db_size_mb": 48.2, "minio_objects": 156}'::jsonb),

-- Week 1, Day 7 (Sunday) — Full backup + RGPD cleanup
(CURRENT_TIMESTAMP - INTERVAL '8 days 22 hours',
 'INFO', 'etl_backup_maintenance', 'backup_full_database', 'scheduled__2026-03-07T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '8 days 22 hours',
 'task_success', 'Task etl_backup_maintenance.backup_full_database succeeded (duration: 35s)',
 '{"duration_seconds": 35, "try_number": 1, "backup_size_mb": 67.8}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '8 days 21 hours 45 minutes',
 'INFO', 'etl_backup_maintenance', 'rgpd_data_cleanup', 'scheduled__2026-03-07T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '8 days 21 hours 45 minutes',
 'task_success', 'Task etl_backup_maintenance.rgpd_data_cleanup succeeded (duration: 2s)',
 '{"duration_seconds": 2, "try_number": 1, "records_deleted": 0}'::jsonb),

-- Week 2, Day 1 — Data lake ingest
(CURRENT_TIMESTAMP - INTERVAL '7 days 3 hours',
 'INFO', 'etl_datalake_ingest', 'ingest_bronze', 'scheduled__2026-03-08T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '7 days 3 hours',
 'task_success', 'Task etl_datalake_ingest.ingest_bronze succeeded (duration: 18s)',
 '{"duration_seconds": 18, "try_number": 1, "files_written": 3, "total_size_mb": 24.1}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '7 days 2 hours 40 minutes',
 'INFO', 'etl_datalake_ingest', 'transform_silver', 'scheduled__2026-03-08T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '7 days 2 hours 40 minutes',
 'task_success', 'Task etl_datalake_ingest.transform_silver succeeded (duration: 22s)',
 '{"duration_seconds": 22, "try_number": 1, "rows_processed": 45200}'::jsonb),

-- Week 2, Day 3 — A real failure scenario (scraping blocked)
(CURRENT_TIMESTAMP - INTERVAL '5 days 3 hours',
 'WARNING', 'etl_extract_scraping', 'scrape_anses', 'scheduled__2026-03-10T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '5 days 3 hours',
 'task_retry', 'Task etl_extract_scraping.scrape_anses RETRYING (attempt 2): HTTPError: 429 Too Many Requests',
 '{"try_number": 2, "max_tries": 3, "exception_type": "HTTPError"}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '5 days 2 hours 55 minutes',
 'CRITICAL', 'etl_extract_scraping', 'scrape_anses', 'scheduled__2026-03-10T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '5 days 2 hours 55 minutes',
 'task_failure', 'Task etl_extract_scraping.scrape_anses FAILED: HTTPError: 429 Too Many Requests',
 '{"try_number": 3, "max_tries": 3, "exception_type": "HTTPError", "log_url": "http://localhost:8080/log?dag_id=etl_extract_scraping&task_id=scrape_anses"}'::jsonb),

-- Week 2, Day 4 — SLA miss detected
(CURRENT_TIMESTAMP - INTERVAL '4 days 3 hours',
 'WARNING', 'etl_extract_off_api', NULL, NULL, NULL,
 'sla_miss', 'SLA MISS in etl_extract_off_api: tasks extract_products',
 '{"missed_tasks": ["extract_products"], "blocking_tasks": [], "sla_definitions": ["30 minutes"]}'::jsonb),

-- Week 2, Day 5 — Normal operations resume
(CURRENT_TIMESTAMP - INTERVAL '3 days 3 hours',
 'INFO', 'etl_extract_off_api', 'extract_products', 'scheduled__2026-03-12T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '3 days 3 hours',
 'task_success', 'Task etl_extract_off_api.extract_products succeeded (duration: 38s)',
 '{"duration_seconds": 38, "try_number": 1, "records_extracted": 1420}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '3 days 2 hours',
 'INFO', 'etl_load_warehouse', 'load_fact_product_market', 'scheduled__2026-03-12T04:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '3 days 2 hours',
 'task_success', 'Task etl_load_warehouse.load_fact_product_market succeeded (duration: 12s)',
 '{"duration_seconds": 12, "try_number": 1, "rows_upserted": 1420}'::jsonb),

-- Week 2, Day 6 — Backup + maintenance
(CURRENT_TIMESTAMP - INTERVAL '2 days 22 hours',
 'INFO', 'etl_backup_maintenance', 'backup_dw_schema', 'scheduled__2026-03-13T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '2 days 22 hours',
 'task_success', 'Task etl_backup_maintenance.backup_dw_schema succeeded (duration: 9s)',
 '{"duration_seconds": 9, "try_number": 1, "backup_size_mb": 13.1}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '2 days 21 hours 55 minutes',
 'INFO', 'etl_backup_maintenance', 'check_storage_health', 'scheduled__2026-03-13T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '2 days 21 hours 55 minutes',
 'maintenance', 'Task etl_backup_maintenance.check_storage_health succeeded (duration: 3s)',
 '{"duration_seconds": 3, "try_number": 1, "db_size_mb": 52.7, "minio_objects": 189}'::jsonb),

-- Today-ish — Most recent runs
(CURRENT_TIMESTAMP - INTERVAL '6 hours',
 'INFO', 'etl_extract_off_api', 'extract_products', 'scheduled__2026-03-15T02:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '6 hours',
 'task_success', 'Task etl_extract_off_api.extract_products succeeded (duration: 41s)',
 '{"duration_seconds": 41, "try_number": 1, "records_extracted": 1510}'::jsonb),

(CURRENT_TIMESTAMP - INTERVAL '5 hours',
 'INFO', 'etl_load_warehouse', 'load_dim_products', 'scheduled__2026-03-15T04:00:00+00:00', CURRENT_TIMESTAMP - INTERVAL '5 hours',
 'task_success', 'Task etl_load_warehouse.load_dim_products succeeded (duration: 14s)',
 '{"duration_seconds": 14, "try_number": 1, "rows_upserted": 1510}'::jsonb);

-- Verify seed data
-- SELECT alert_category, event_type, COUNT(*) FROM app.etl_activity_log GROUP BY 1, 2 ORDER BY 1, 2;
