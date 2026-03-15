-- =============================================================
-- Migration 001: ETL Activity Log & DW RGPD Registry
-- Covers: C16 - Activity logging with alert/error categories
-- =============================================================

\c nutritrack;

-- ETL Activity Log: structured logging for monitoring & alerting
CREATE TABLE IF NOT EXISTS app.etl_activity_log (
    log_id SERIAL PRIMARY KEY,
    log_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_category VARCHAR(20) NOT NULL CHECK (alert_category IN ('CRITICAL', 'WARNING', 'INFO')),
    dag_id VARCHAR(100) NOT NULL,
    task_id VARCHAR(100),
    run_id VARCHAR(250),
    execution_date TIMESTAMP,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'task_failure', 'task_success', 'task_retry',
        'sla_miss', 'dag_failure', 'dag_success',
        'backup_success', 'backup_failure',
        'data_quality_alert', 'maintenance'
    )),
    message TEXT NOT NULL,
    details JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP
);

CREATE INDEX idx_etl_log_timestamp ON app.etl_activity_log(log_timestamp DESC);
CREATE INDEX idx_etl_log_category ON app.etl_activity_log(alert_category);
CREATE INDEX idx_etl_log_dag ON app.etl_activity_log(dag_id);
CREATE INDEX idx_etl_log_event ON app.etl_activity_log(event_type);

-- Add DW-specific entries to RGPD registry
INSERT INTO app.rgpd_data_registry (
    data_category, data_description, legal_basis, retention_period,
    data_subjects, processing_purpose, recipients, security_measures
) VALUES
(
    'Data warehouse analytics',
    'Aggregated nutrition statistics, product market analysis (no personal identifiers)',
    'Legitimate interest (Art. 6.1.f GDPR)',
    'Indefinite (aggregated, non-personal data)',
    'None (aggregated data)',
    'Business intelligence and nutrition trend analysis',
    'Analysts via Superset dashboards, nutritionist_role',
    'Access restricted to authorized roles, pseudonymized user data via SHA-256 hash'
),
(
    'DW user dimension',
    'Pseudonymized user profiles: SHA-256 hashed user_id, age_group, activity_level, dietary_goal',
    'Legitimate interest (Art. 6.1.f GDPR)',
    '3 years after last activity',
    'App users (pseudonymized)',
    'Aggregated nutrition behavior analysis per demographic segment',
    'Analysts via Superset dashboards',
    'User IDs hashed with SHA-256, no reversible mapping stored, SCD Type 2 for history'
),
(
    'ETL activity logs',
    'Pipeline execution logs: DAG names, task IDs, timestamps, error messages',
    'Legitimate interest (Art. 6.1.f GDPR)',
    '1 year',
    'None (system operational data)',
    'Pipeline monitoring, SLA tracking, incident investigation',
    'Data engineers, admin_role',
    'No personal data in logs, access restricted to admin/engineering roles'
),
(
    'Database backups',
    'Full and partial PostgreSQL backups stored in MinIO',
    'Legitimate interest (Art. 6.1.f GDPR)',
    '30 days (local), 90 days (MinIO)',
    'All data subjects present in database',
    'Disaster recovery, business continuity',
    'admin_role only',
    'Encrypted at rest in MinIO, access restricted to admin role, automated cleanup'
);

-- Grant access to the activity log
GRANT SELECT ON app.etl_activity_log TO admin_role, nutritionist_role;
GRANT SELECT, INSERT ON app.etl_activity_log TO etl_service;
GRANT ALL ON app.etl_activity_log TO nutritrack;
GRANT USAGE, SELECT ON SEQUENCE app.etl_activity_log_log_id_seq TO etl_service, nutritrack;
