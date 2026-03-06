#!/bin/bash
set -e

echo "=== Superset initialization ==="

# Upgrade metadata DB schema
superset db upgrade

# Create admin user (idempotent — skips if exists)
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@nutritrack.local \
    --password admin || true

# Initialize Superset (roles, permissions)
superset init

# Register NutriTrack DW datasource (idempotent — updates if exists)
superset set-database-uri \
    --database_name "NutriTrack DW" \
    --uri "postgresql+psycopg2://superset:superset@postgres:5432/nutritrack" \
    || true

echo "=== Superset initialization complete ==="

# Start the webserver
exec superset run -h 0.0.0.0 -p 8088 --with-threads
