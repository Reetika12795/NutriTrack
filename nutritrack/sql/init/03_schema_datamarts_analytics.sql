-- =============================================================
-- NutriTrack Analytics Datamarts for Superset Dashboards
-- Database: nutritrack | Schema: dw
-- Covers: C13 (Analytical query optimization), C14 (Analyst access)
-- =============================================================

\c nutritrack;
SET search_path TO dw, public;

-- =============================================================
-- VIEW: Nutri-Score distribution by category
-- Purpose: Product Market Analysis dashboard
-- Shows count and percentage of each Nutri-Score grade per category
-- =============================================================
CREATE OR REPLACE VIEW dw.dm_nutriscore_distribution AS
SELECT
    c.category_name,
    c.parent_category,
    ns.nutriscore_grade,
    ns.grade_description,
    ns.color_code,
    COUNT(*) AS product_count,
    ROUND(
        100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY c.category_name), 0),
        1
    ) AS pct_of_category,
    AVG(f.energy_kcal_per_100g) AS avg_kcal,
    AVG(f.sugars_per_100g) AS avg_sugars,
    AVG(f.salt_per_100g) AS avg_salt,
    AVG(f.proteins_per_100g) AS avg_proteins
FROM dw.fact_product_market f
JOIN dw.dim_category c ON f.category_key = c.category_key
JOIN dw.dim_nutriscore ns ON f.nutriscore_grade = ns.nutriscore_grade
JOIN dw.dim_product p ON f.product_key = p.product_key AND p.is_current = TRUE
GROUP BY c.category_name, c.parent_category,
         ns.nutriscore_grade, ns.grade_description, ns.color_code;

-- =============================================================
-- VIEW: Nutrition trends (anonymized daily aggregates)
-- Purpose: User Nutrition Trends dashboard
-- Aggregated at day/age_group/goal level — no individual user data
-- =============================================================
CREATE OR REPLACE VIEW dw.dm_nutrition_trends AS
SELECT
    t.full_date,
    t.day_name,
    t.month_name,
    t.quarter,
    t.year,
    t.is_weekend,
    u.age_group,
    u.dietary_goal,
    COUNT(DISTINCT u.user_hash) AS active_users,
    SUM(f.energy_kcal) AS total_kcal,
    AVG(f.energy_kcal) AS avg_kcal_per_item,
    SUM(f.proteins_g) AS total_proteins_g,
    SUM(f.fat_g) AS total_fat_g,
    SUM(f.carbohydrates_g) AS total_carbs_g,
    SUM(f.fiber_g) AS total_fiber_g,
    AVG(f.nutriscore_score) AS avg_nutriscore,
    COUNT(*) AS meal_items_count,
    -- 7-day moving average of caloric intake
    AVG(SUM(f.energy_kcal)) OVER (
        PARTITION BY u.age_group, u.dietary_goal
        ORDER BY t.full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS kcal_7day_moving_avg
FROM dw.fact_daily_nutrition f
JOIN dw.dim_user u ON f.user_key = u.user_key AND u.is_current = TRUE
JOIN dw.dim_time t ON f.time_key = t.time_key
GROUP BY t.full_date, t.day_name, t.month_name, t.quarter, t.year, t.is_weekend,
         u.age_group, u.dietary_goal;

-- =============================================================
-- VIEW: DW health and data completeness metrics
-- Purpose: DW Health & Data Quality dashboard
-- Shows record counts, load timestamps, completeness per table
-- =============================================================
CREATE OR REPLACE VIEW dw.dm_dw_health AS
SELECT
    'dim_product' AS table_name,
    'dimension' AS table_type,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE is_current = TRUE) AS active_rows,
    MAX(loaded_at) AS last_loaded_at,
    ROUND(AVG(CASE WHEN product_name IS NOT NULL THEN 1 ELSE 0 END) * 100, 1) AS name_completeness_pct,
    ROUND(AVG(completeness_score) * 100, 1) AS avg_completeness_pct
FROM dw.dim_product

UNION ALL

SELECT
    'dim_brand',
    'dimension',
    COUNT(*),
    COUNT(*),
    MAX(loaded_at),
    ROUND(AVG(CASE WHEN brand_name IS NOT NULL THEN 1 ELSE 0 END) * 100, 1),
    NULL
FROM dw.dim_brand

UNION ALL

SELECT
    'dim_category',
    'dimension',
    COUNT(*),
    COUNT(*),
    MAX(loaded_at),
    ROUND(AVG(CASE WHEN category_name IS NOT NULL THEN 1 ELSE 0 END) * 100, 1),
    NULL
FROM dw.dim_category

UNION ALL

SELECT
    'dim_country',
    'dimension',
    COUNT(*),
    COUNT(*),
    MAX(loaded_at),
    ROUND(AVG(CASE WHEN country_name IS NOT NULL THEN 1 ELSE 0 END) * 100, 1),
    NULL
FROM dw.dim_country

UNION ALL

SELECT
    'dim_user',
    'dimension',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_current = TRUE),
    MAX(loaded_at),
    ROUND(AVG(CASE WHEN user_hash IS NOT NULL THEN 1 ELSE 0 END) * 100, 1),
    NULL
FROM dw.dim_user

UNION ALL

SELECT
    'dim_nutriscore',
    'dimension',
    COUNT(*),
    COUNT(*),
    NULL,
    100.0,
    NULL
FROM dw.dim_nutriscore

UNION ALL

SELECT
    'dim_time',
    'dimension',
    COUNT(*),
    COUNT(*),
    NULL,
    100.0,
    NULL
FROM dw.dim_time

UNION ALL

SELECT
    'fact_daily_nutrition',
    'fact',
    COUNT(*),
    COUNT(*),
    MAX(loaded_at),
    ROUND(AVG(CASE WHEN energy_kcal IS NOT NULL THEN 1 ELSE 0 END) * 100, 1),
    NULL
FROM dw.fact_daily_nutrition

UNION ALL

SELECT
    'fact_product_market',
    'fact',
    COUNT(*),
    COUNT(*),
    MAX(loaded_at),
    ROUND(AVG(CASE WHEN nutriscore_grade IS NOT NULL THEN 1 ELSE 0 END) * 100, 1),
    ROUND(AVG(completeness_score) * 100, 1)
FROM dw.fact_product_market;

-- =============================================================
-- GRANTS for new views
-- =============================================================
GRANT SELECT ON dw.dm_nutriscore_distribution TO nutritionist_role;
GRANT SELECT ON dw.dm_nutrition_trends TO nutritionist_role;
GRANT SELECT ON dw.dm_dw_health TO admin_role;
GRANT SELECT ON dw.dm_nutriscore_distribution, dw.dm_nutrition_trends, dw.dm_dw_health TO superset;
