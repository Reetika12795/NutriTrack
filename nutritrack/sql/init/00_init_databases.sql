-- =============================================================
-- NutriTrack Database Initialization
-- Creates databases and roles for the project
-- Runs as postgres superuser on the default postgres DB
-- =============================================================

-- Create databases
CREATE DATABASE nutritrack;
CREATE DATABASE airflow;

-- Create roles for different access levels (C21 - Data Governance)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nutritrack') THEN
        CREATE ROLE nutritrack WITH LOGIN PASSWORD 'nutritrack';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airflow') THEN
        CREATE ROLE airflow WITH LOGIN PASSWORD 'airflow';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly') THEN
        CREATE ROLE app_readonly WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nutritionist_role') THEN
        CREATE ROLE nutritionist_role WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin_role') THEN
        CREATE ROLE admin_role WITH NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'etl_service') THEN
        CREATE ROLE etl_service WITH LOGIN PASSWORD 'etl_service';
    END IF;
END
$$;

-- Grant database access
GRANT ALL PRIVILEGES ON DATABASE nutritrack TO nutritrack;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
GRANT CONNECT ON DATABASE nutritrack TO app_readonly;
GRANT CONNECT ON DATABASE nutritrack TO nutritionist_role;
GRANT CONNECT ON DATABASE nutritrack TO admin_role;
GRANT CONNECT ON DATABASE nutritrack TO etl_service;

-- PostgreSQL 15+ requires explicit GRANT on public schema for non-owners
\c airflow;
GRANT ALL ON SCHEMA public TO airflow;

\c nutritrack;
GRANT ALL ON SCHEMA public TO nutritrack;
