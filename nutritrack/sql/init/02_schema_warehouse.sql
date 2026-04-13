-- =============================================================
-- NutriTrack Data Warehouse Schema (Star Schema)
-- Database: nutritrack | Schema: dw
-- Covers: C13 (Star schema modeling), C14 (DW creation)
-- Approach: Bottom-up (datamarts first, then combine)
-- =============================================================

\c nutritrack;

CREATE SCHEMA IF NOT EXISTS dw;
SET search_path TO dw, public;

-- =============================================================
-- DIMENSION TABLES
-- =============================================================

-- Time dimension (pre-populated)
CREATE TABLE dw.dim_time (
    time_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- Product dimension
CREATE TABLE dw.dim_product (
    product_key SERIAL PRIMARY KEY,
    barcode VARCHAR(20) NOT NULL,
    product_name VARCHAR(500),
    generic_name VARCHAR(500),
    quantity VARCHAR(100),
    packaging VARCHAR(255),
    ingredients_text TEXT,
    completeness_score NUMERIC(5,2),
    -- SCD Type 2 fields (C17 - Kimball dimension variations)
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT TRUE,
    -- Source tracking
    source_product_id INTEGER,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_product_barcode ON dw.dim_product(barcode);
CREATE INDEX idx_dim_product_current ON dw.dim_product(is_current) WHERE is_current = TRUE;

-- Brand dimension (SCD Type 1 for name corrections)
CREATE TABLE dw.dim_brand (
    brand_key SERIAL PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL,
    parent_company VARCHAR(255),
    -- SCD Type 1: overwrite on correction, track last update
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_brand_name ON dw.dim_brand(brand_name);

-- Category dimension (hierarchical)
CREATE TABLE dw.dim_category (
    category_key SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL,
    parent_category VARCHAR(255),
    category_level INTEGER DEFAULT 1,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Country dimension (SCD Type 3 for expansion)
CREATE TABLE dw.dim_country (
    country_key SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10),
    region VARCHAR(100),
    continent VARCHAR(50),
    -- SCD Type 3: previous value column for country list changes
    previous_country_list VARCHAR(500),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User dimension (anonymized for analytics)
CREATE TABLE dw.dim_user (
    user_key SERIAL PRIMARY KEY,
    user_hash VARCHAR(64) NOT NULL,  -- hashed user_id for pseudonymization
    age_group VARCHAR(20),
    activity_level VARCHAR(20),
    dietary_goal VARCHAR(30),
    registration_date DATE,
    -- SCD Type 2 for profile changes
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT TRUE,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_user_hash ON dw.dim_user(user_hash);
CREATE INDEX idx_dim_user_current ON dw.dim_user(is_current) WHERE is_current = TRUE;

-- Nutriscore dimension (for tracking score methodology changes)
CREATE TABLE dw.dim_nutriscore (
    nutriscore_key SERIAL PRIMARY KEY,
    nutriscore_grade CHAR(1) NOT NULL,
    grade_description VARCHAR(100),
    color_code VARCHAR(7),
    score_range_min INTEGER,
    score_range_max INTEGER
);

INSERT INTO dw.dim_nutriscore (nutriscore_grade, grade_description, color_code, score_range_min, score_range_max) VALUES
('A', 'Excellent nutritional quality', '#038141', -15, -1),
('B', 'Good nutritional quality', '#85BB2F', 0, 2),
('C', 'Average nutritional quality', '#FECB02', 3, 10),
('D', 'Poor nutritional quality', '#EE8100', 11, 18),
('E', 'Bad nutritional quality', '#E63E11', 19, 40);

-- =============================================================
-- FACT TABLES
-- =============================================================

-- Fact: Daily nutrition tracking (per user, per day)
CREATE TABLE dw.fact_daily_nutrition (
    daily_nutrition_id SERIAL PRIMARY KEY,
    user_key INTEGER NOT NULL REFERENCES dw.dim_user(user_key),
    time_key INTEGER NOT NULL REFERENCES dw.dim_time(time_key),
    product_key INTEGER NOT NULL REFERENCES dw.dim_product(product_key),
    category_key INTEGER REFERENCES dw.dim_category(category_key),
    brand_key INTEGER REFERENCES dw.dim_brand(brand_key),
    -- Measures
    meal_type VARCHAR(20),
    quantity_g NUMERIC(8,2),
    energy_kcal NUMERIC(8,2),
    fat_g NUMERIC(8,2),
    saturated_fat_g NUMERIC(8,2),
    carbohydrates_g NUMERIC(8,2),
    sugars_g NUMERIC(8,2),
    proteins_g NUMERIC(8,2),
    fiber_g NUMERIC(8,2),
    salt_g NUMERIC(8,4),
    nutriscore_score INTEGER,
    nova_group INTEGER,
    -- Metadata
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fact_nutrition_user_time ON dw.fact_daily_nutrition(user_key, time_key);
CREATE INDEX idx_fact_nutrition_time ON dw.fact_daily_nutrition(time_key);
CREATE INDEX idx_fact_nutrition_product ON dw.fact_daily_nutrition(product_key);

-- Fact: Product market analysis
CREATE TABLE dw.fact_product_market (
    product_market_id SERIAL PRIMARY KEY,
    product_key INTEGER NOT NULL REFERENCES dw.dim_product(product_key),
    brand_key INTEGER REFERENCES dw.dim_brand(brand_key),
    category_key INTEGER REFERENCES dw.dim_category(category_key),
    country_key INTEGER REFERENCES dw.dim_country(country_key),
    time_key INTEGER NOT NULL REFERENCES dw.dim_time(time_key),
    -- Measures
    nutriscore_grade CHAR(1),
    nutriscore_score INTEGER,
    nova_group INTEGER,
    ecoscore_grade CHAR(1),
    completeness_score NUMERIC(5,2),
    energy_kcal_per_100g NUMERIC(8,2),
    fat_per_100g NUMERIC(8,2),
    sugars_per_100g NUMERIC(8,2),
    salt_per_100g NUMERIC(8,4),
    fiber_per_100g NUMERIC(8,2),
    proteins_per_100g NUMERIC(8,2),
    -- Metadata
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fact_market_product ON dw.fact_product_market(product_key);
CREATE INDEX idx_fact_market_time ON dw.fact_product_market(time_key);
CREATE INDEX idx_fact_market_category ON dw.fact_product_market(category_key);
CREATE INDEX idx_fact_market_brand ON dw.fact_product_market(brand_key);

-- =============================================================
-- POPULATE TIME DIMENSION (2020-2030)
-- =============================================================

INSERT INTO dw.dim_time (time_key, full_date, day_of_week, day_name, day_of_month, day_of_year, week_of_year, month, month_name, quarter, year, is_weekend)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS time_key,
    d AS full_date,
    EXTRACT(DOW FROM d)::INTEGER AS day_of_week,
    TO_CHAR(d, 'Day') AS day_name,
    EXTRACT(DAY FROM d)::INTEGER AS day_of_month,
    EXTRACT(DOY FROM d)::INTEGER AS day_of_year,
    EXTRACT(WEEK FROM d)::INTEGER AS week_of_year,
    EXTRACT(MONTH FROM d)::INTEGER AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(QUARTER FROM d)::INTEGER AS quarter,
    EXTRACT(YEAR FROM d)::INTEGER AS year,
    EXTRACT(DOW FROM d) IN (0, 6) AS is_weekend
FROM generate_series('2020-01-01'::date, '2030-12-31'::date, '1 day'::interval) AS d;

-- =============================================================
-- SCD PROCEDURES (C17 - Kimball dimension variations)
-- =============================================================

-- SCD Type 1: Brand name correction (overwrite)
CREATE OR REPLACE FUNCTION dw.scd_type1_update_brand(
    p_brand_key INTEGER,
    p_new_brand_name VARCHAR(255)
)
RETURNS VOID AS $$
BEGIN
    UPDATE dw.dim_brand
    SET brand_name = p_new_brand_name,
        last_updated = CURRENT_TIMESTAMP
    WHERE brand_key = p_brand_key;
END;
$$ LANGUAGE plpgsql;

-- SCD Type 2: Product change (new row with history)
CREATE OR REPLACE FUNCTION dw.scd_type2_update_product(
    p_barcode VARCHAR(20),
    p_product_name VARCHAR(500),
    p_generic_name VARCHAR(500),
    p_quantity VARCHAR(100),
    p_packaging VARCHAR(255),
    p_ingredients_text TEXT,
    p_completeness_score NUMERIC(5,2),
    p_source_product_id INTEGER
)
RETURNS VOID AS $$
BEGIN
    -- Close the current record
    UPDATE dw.dim_product
    SET end_date = CURRENT_DATE - 1,
        is_current = FALSE
    WHERE barcode = p_barcode
      AND is_current = TRUE;

    -- Insert new current record
    INSERT INTO dw.dim_product (
        barcode, product_name, generic_name, quantity, packaging,
        ingredients_text, completeness_score, effective_date, end_date,
        is_current, source_product_id
    ) VALUES (
        p_barcode, p_product_name, p_generic_name, p_quantity, p_packaging,
        p_ingredients_text, p_completeness_score, CURRENT_DATE, '9999-12-31',
        TRUE, p_source_product_id
    );
END;
$$ LANGUAGE plpgsql;

-- SCD Type 3: Country expansion (add column for previous value)
CREATE OR REPLACE FUNCTION dw.scd_type3_update_country(
    p_country_key INTEGER,
    p_new_country_name VARCHAR(100)
)
RETURNS VOID AS $$
BEGIN
    UPDATE dw.dim_country
    SET previous_country_list = country_name,
        country_name = p_new_country_name
    WHERE country_key = p_country_key;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- ANALYTICAL VIEWS (Datamarts)
-- =============================================================

-- Datamart: User daily nutrition summary
CREATE OR REPLACE VIEW dw.dm_user_daily_nutrition AS
SELECT
    u.user_hash,
    u.age_group,
    u.activity_level,
    u.dietary_goal,
    t.full_date,
    t.day_name,
    t.month_name,
    t.year,
    f.meal_type,
    SUM(f.energy_kcal) AS total_kcal,
    SUM(f.fat_g) AS total_fat_g,
    SUM(f.carbohydrates_g) AS total_carbs_g,
    SUM(f.proteins_g) AS total_proteins_g,
    SUM(f.fiber_g) AS total_fiber_g,
    SUM(f.salt_g) AS total_salt_g,
    AVG(f.nutriscore_score) AS avg_nutriscore,
    AVG(f.nova_group) AS avg_nova_group,
    COUNT(*) AS items_count
FROM dw.fact_daily_nutrition f
JOIN dw.dim_user u ON f.user_key = u.user_key AND u.is_current = TRUE
JOIN dw.dim_time t ON f.time_key = t.time_key
GROUP BY u.user_hash, u.age_group, u.activity_level, u.dietary_goal,
         t.full_date, t.day_name, t.month_name, t.year, f.meal_type;

-- Datamart: Product market overview by category
CREATE OR REPLACE VIEW dw.dm_product_market_by_category AS
SELECT
    c.category_name,
    c.parent_category,
    ns.nutriscore_grade,
    ns.grade_description,
    COUNT(*) AS product_count,
    AVG(f.energy_kcal_per_100g) AS avg_kcal,
    AVG(f.sugars_per_100g) AS avg_sugars,
    AVG(f.salt_per_100g) AS avg_salt,
    AVG(f.fiber_per_100g) AS avg_fiber,
    AVG(f.proteins_per_100g) AS avg_proteins,
    AVG(f.completeness_score) AS avg_completeness
FROM dw.fact_product_market f
JOIN dw.dim_category c ON f.category_key = c.category_key
JOIN dw.dim_nutriscore ns ON f.nutriscore_grade = ns.nutriscore_grade
JOIN dw.dim_product p ON f.product_key = p.product_key AND p.is_current = TRUE
GROUP BY c.category_name, c.parent_category, ns.nutriscore_grade, ns.grade_description;

-- Datamart: Brand nutrition quality ranking
CREATE OR REPLACE VIEW dw.dm_brand_quality_ranking AS
SELECT
    b.brand_name,
    b.parent_company,
    COUNT(*) AS product_count,
    AVG(f.nutriscore_score) AS avg_nutriscore_score,
    MODE() WITHIN GROUP (ORDER BY f.nutriscore_grade) AS most_common_grade,
    AVG(f.nova_group) AS avg_nova_group,
    AVG(f.completeness_score) AS avg_completeness
FROM dw.fact_product_market f
JOIN dw.dim_brand b ON f.brand_key = b.brand_key
JOIN dw.dim_product p ON f.product_key = p.product_key AND p.is_current = TRUE
GROUP BY b.brand_name, b.parent_company
HAVING COUNT(*) >= 5;

-- =============================================================
-- GRANTS (C21 - Data Governance)
-- =============================================================

GRANT USAGE ON SCHEMA dw TO nutritrack, app_readonly, nutritionist_role, admin_role, etl_service;

-- app_readonly: no access to warehouse
-- nutritionist_role: read access to analytical views only
GRANT SELECT ON dw.dm_user_daily_nutrition, dw.dm_product_market_by_category, dw.dm_brand_quality_ranking TO nutritionist_role;
GRANT SELECT ON dw.dim_time, dw.dim_nutriscore TO nutritionist_role;

-- admin_role: full access to warehouse
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dw TO admin_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA dw TO admin_role;

-- etl_service: write access for ETL loading
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dw TO etl_service;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA dw TO etl_service;

-- nutritrack: full access
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dw TO nutritrack;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA dw TO nutritrack;
