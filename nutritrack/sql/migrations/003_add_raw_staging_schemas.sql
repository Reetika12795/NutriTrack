-- Migration 003: Add raw and staging schemas for proper ELT layering
-- Data flows: raw (landing) → staging (cleaned) → app (operational) → dw (analytics)

-- Raw schema: landing zone for source data (exact copy, no transformation)
CREATE SCHEMA IF NOT EXISTS raw;
GRANT USAGE ON SCHEMA raw TO nutritrack;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT ALL ON TABLES TO nutritrack;

CREATE TABLE IF NOT EXISTS raw.products_landing (
    landing_id SERIAL PRIMARY KEY,
    barcode VARCHAR(50),
    product_name TEXT,
    brand_name VARCHAR(255),
    category_name VARCHAR(255),
    energy_kcal NUMERIC(8,2),
    fat_g NUMERIC(8,2),
    proteins_g NUMERIC(8,2),
    carbohydrates_g NUMERIC(8,2),
    sugars_g NUMERIC(8,2),
    fiber_g NUMERIC(8,2),
    salt_g NUMERIC(8,4),
    nutriscore_grade CHAR(1),
    nutriscore_score INTEGER,
    nova_group INTEGER,
    data_source VARCHAR(50),
    raw_json JSONB,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staging schema: cleaned and validated data (typed, deduplicated)
CREATE SCHEMA IF NOT EXISTS staging;
GRANT USAGE ON SCHEMA staging TO nutritrack;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO nutritrack;

CREATE TABLE IF NOT EXISTS staging.products_cleaned (
    barcode VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(500) NOT NULL,
    brand_name VARCHAR(255),
    category_name VARCHAR(255),
    energy_kcal NUMERIC(8,2),
    fat_g NUMERIC(8,2),
    saturated_fat_g NUMERIC(8,2),
    proteins_g NUMERIC(8,2),
    carbohydrates_g NUMERIC(8,2),
    sugars_g NUMERIC(8,2),
    fiber_g NUMERIC(8,2),
    salt_g NUMERIC(8,4),
    nutriscore_grade CHAR(1) CHECK (nutriscore_grade IN ('A','B','C','D','E')),
    nutriscore_score INTEGER,
    nova_group INTEGER CHECK (nova_group BETWEEN 1 AND 4),
    completeness_score NUMERIC(5,2),
    data_source VARCHAR(50),
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality checks log table
CREATE TABLE IF NOT EXISTS staging.data_quality_checks (
    check_id SERIAL PRIMARY KEY,
    check_date DATE DEFAULT CURRENT_DATE,
    pipeline_name VARCHAR(100),
    check_name VARCHAR(200),
    check_type VARCHAR(50),
    expected_value VARCHAR(200),
    actual_value VARCHAR(200),
    passed BOOLEAN,
    details TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dq_checks_date ON staging.data_quality_checks(check_date);
CREATE INDEX IF NOT EXISTS idx_dq_checks_pipeline ON staging.data_quality_checks(pipeline_name);
