-- =============================================================
-- NutriTrack Operational Schema (MPD - Modele Physique de Donnees)
-- Database: nutritrack | Schema: app
-- Covers: C11 - RGPD-compliant database creation
-- =============================================================

\c nutritrack;

CREATE SCHEMA IF NOT EXISTS app;
SET search_path TO app, public;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================
-- TABLES
-- =============================================================

-- Categories (hierarchical)
CREATE TABLE app.categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL UNIQUE,
    parent_category_id INTEGER REFERENCES app.categories(category_id),
    level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_parent ON app.categories(parent_category_id);
CREATE INDEX idx_categories_name ON app.categories(category_name);

-- Brands
CREATE TABLE app.brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL UNIQUE,
    parent_company VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_brands_name ON app.brands(brand_name);

-- Products (from Open Food Facts)
CREATE TABLE app.products (
    product_id SERIAL PRIMARY KEY,
    barcode VARCHAR(20) UNIQUE NOT NULL,
    product_name VARCHAR(500),
    generic_name VARCHAR(500),
    quantity VARCHAR(100),
    packaging VARCHAR(255),
    brand_id INTEGER REFERENCES app.brands(brand_id),
    category_id INTEGER REFERENCES app.categories(category_id),
    -- Nutrition per 100g
    energy_kcal NUMERIC(8,2),
    energy_kj NUMERIC(8,2),
    fat_g NUMERIC(8,2),
    saturated_fat_g NUMERIC(8,2),
    carbohydrates_g NUMERIC(8,2),
    sugars_g NUMERIC(8,2),
    fiber_g NUMERIC(8,2),
    proteins_g NUMERIC(8,2),
    salt_g NUMERIC(8,4),
    sodium_g NUMERIC(8,4),
    -- Scores
    nutriscore_grade CHAR(1),
    nutriscore_score INTEGER,
    nova_group INTEGER CHECK (nova_group BETWEEN 1 AND 4),
    ecoscore_grade CHAR(1),
    -- Metadata
    countries VARCHAR(500),
    ingredients_text TEXT,
    allergens TEXT,
    traces TEXT,
    image_url VARCHAR(1000),
    off_url VARCHAR(500),
    completeness_score NUMERIC(5,2),
    -- Source tracking
    data_source VARCHAR(50) DEFAULT 'open_food_facts',
    last_modified_off TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_barcode ON app.products(barcode);
CREATE INDEX idx_products_name ON app.products USING gin(to_tsvector('french', product_name));
CREATE INDEX idx_products_brand ON app.products(brand_id);
CREATE INDEX idx_products_category ON app.products(category_id);
CREATE INDEX idx_products_nutriscore ON app.products(nutriscore_grade);
CREATE INDEX idx_products_nova ON app.products(nova_group);

-- Users (RGPD-compliant: minimal personal data, consent tracking)
CREATE TABLE app.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'nutritionist', 'admin')),
    -- Profile (optional, with consent)
    age_group VARCHAR(20),
    activity_level VARCHAR(20) CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
    dietary_goal VARCHAR(30) CHECK (dietary_goal IN ('lose_weight', 'maintain', 'gain_muscle', 'eat_healthier')),
    -- RGPD consent tracking
    consent_data_processing BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP,
    data_retention_until DATE,
    -- Account management
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON app.users(email);
CREATE INDEX idx_users_username ON app.users(username);

-- Meals
CREATE TABLE app.meals (
    meal_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app.users(user_id) ON DELETE CASCADE,
    meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    meal_date DATE NOT NULL DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meals_user_date ON app.meals(user_id, meal_date);
CREATE INDEX idx_meals_date ON app.meals(meal_date);

-- Meal Items (products within a meal)
CREATE TABLE app.meal_items (
    meal_item_id SERIAL PRIMARY KEY,
    meal_id INTEGER NOT NULL REFERENCES app.meals(meal_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES app.products(product_id),
    quantity_g NUMERIC(8,2) NOT NULL DEFAULT 100,
    -- Computed nutrition for the quantity eaten
    energy_kcal NUMERIC(8,2),
    fat_g NUMERIC(8,2),
    carbohydrates_g NUMERIC(8,2),
    proteins_g NUMERIC(8,2),
    fiber_g NUMERIC(8,2),
    salt_g NUMERIC(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meal_items_meal ON app.meal_items(meal_id);
CREATE INDEX idx_meal_items_product ON app.meal_items(product_id);

-- Nutritional Guidelines (from scraping - RDA values)
CREATE TABLE app.nutritional_guidelines (
    guideline_id SERIAL PRIMARY KEY,
    nutrient_name VARCHAR(100) NOT NULL,
    daily_value NUMERIC(8,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    age_group VARCHAR(50),
    gender VARCHAR(20),
    source_url VARCHAR(500),
    source_name VARCHAR(200),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data extraction log (audit trail)
CREATE TABLE app.extraction_log (
    log_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    records_extracted INTEGER,
    records_loaded INTEGER,
    records_rejected INTEGER,
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- RGPD: Personal Data Registry (C11 compliance)
CREATE TABLE app.rgpd_data_registry (
    registry_id SERIAL PRIMARY KEY,
    data_category VARCHAR(100) NOT NULL,
    data_description TEXT NOT NULL,
    legal_basis VARCHAR(100) NOT NULL,
    retention_period VARCHAR(100) NOT NULL,
    data_subjects VARCHAR(100) NOT NULL,
    processing_purpose TEXT NOT NULL,
    recipients VARCHAR(255),
    transfer_outside_eu BOOLEAN DEFAULT FALSE,
    security_measures TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert RGPD registry entries
INSERT INTO app.rgpd_data_registry (data_category, data_description, legal_basis, retention_period, data_subjects, processing_purpose, recipients, security_measures) VALUES
('User account data', 'Email, username, hashed password', 'Consent (Art. 6.1.a GDPR)', '3 years after last login', 'App users', 'User authentication and account management', 'NutriTrack application', 'Password hashing (bcrypt), encrypted storage'),
('User profile data', 'Age group, activity level, dietary goal', 'Consent (Art. 6.1.a GDPR)', '3 years after last login or until consent withdrawal', 'App users', 'Personalized nutrition recommendations', 'NutriTrack application', 'Pseudonymized in analytics'),
('Meal tracking data', 'Meal logs, food consumption history', 'Consent (Art. 6.1.a GDPR)', '2 years after creation', 'App users', 'Nutrition tracking and trend analysis', 'NutriTrack application', 'Associated with user_id (UUID), deletable on request'),
('Product data', 'Food product information from Open Food Facts', 'Legitimate interest (Art. 6.1.f GDPR)', 'Indefinite (public data)', 'Open Food Facts contributors', 'Product information display and nutrition analysis', 'NutriTrack application, API consumers', 'Public data, no personal information');

-- =============================================================
-- FUNCTIONS
-- =============================================================

-- Function to compute nutrition for a meal item based on quantity
CREATE OR REPLACE FUNCTION app.compute_meal_item_nutrition()
RETURNS TRIGGER AS $$
BEGIN
    SELECT
        ROUND((p.energy_kcal * NEW.quantity_g / 100), 2),
        ROUND((p.fat_g * NEW.quantity_g / 100), 2),
        ROUND((p.carbohydrates_g * NEW.quantity_g / 100), 2),
        ROUND((p.proteins_g * NEW.quantity_g / 100), 2),
        ROUND((p.fiber_g * NEW.quantity_g / 100), 2),
        ROUND((p.salt_g * NEW.quantity_g / 100), 4)
    INTO
        NEW.energy_kcal, NEW.fat_g, NEW.carbohydrates_g,
        NEW.proteins_g, NEW.fiber_g, NEW.salt_g
    FROM app.products p
    WHERE p.product_id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_compute_meal_nutrition
    BEFORE INSERT OR UPDATE ON app.meal_items
    FOR EACH ROW
    EXECUTE FUNCTION app.compute_meal_item_nutrition();

-- Function for RGPD: auto-delete expired user data
CREATE OR REPLACE FUNCTION app.rgpd_cleanup_expired_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete meal data older than 2 years
    DELETE FROM app.meal_items
    WHERE meal_id IN (
        SELECT meal_id FROM app.meals
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '2 years'
    );

    DELETE FROM app.meals
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '2 years';

    -- Deactivate users past retention date
    UPDATE app.users
    SET is_active = FALSE
    WHERE data_retention_until < CURRENT_DATE
      AND is_active = TRUE;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- GRANTS (C21 - Data Governance)
-- =============================================================

GRANT USAGE ON SCHEMA app TO nutritrack, app_readonly, nutritionist_role, admin_role, etl_service;

-- app_readonly: read access to products only
GRANT SELECT ON app.products, app.categories, app.brands, app.nutritional_guidelines TO app_readonly;

-- nutritionist_role: read products + aggregated views (no raw user data)
GRANT SELECT ON ALL TABLES IN SCHEMA app TO nutritionist_role;
REVOKE SELECT ON app.users FROM nutritionist_role;

-- admin_role: full access
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO admin_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO admin_role;

-- etl_service: write access for data loading
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO etl_service;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO etl_service;

-- nutritrack app user: full operational access
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO nutritrack;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO nutritrack;
