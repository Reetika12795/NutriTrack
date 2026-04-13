-- =============================================================
-- NutriTrack Analytical SQL Queries
-- Covers: C9 - SQL extraction queries from DBMS
-- Documents: selection/filtering/join choices and query optimizations
-- =============================================================

-- =============================================================
-- QUERY 1: Daily nutrition summary per user with RDA percentage
-- Optimization: Uses composite index on (user_id, meal_date)
-- Join strategy: INNER JOIN ensures only valid linked data
-- =============================================================
SELECT
    u.username,
    m.meal_date,
    COUNT(DISTINCT m.meal_id) AS meals_count,
    SUM(mi.energy_kcal) AS total_kcal,
    SUM(mi.proteins_g) AS total_proteins_g,
    SUM(mi.carbohydrates_g) AS total_carbs_g,
    SUM(mi.fat_g) AS total_fat_g,
    SUM(mi.fiber_g) AS total_fiber_g,
    -- RDA percentage (based on 2000 kcal diet)
    ROUND(SUM(mi.energy_kcal) / 2000.0 * 100, 1) AS pct_rda_energy,
    ROUND(SUM(mi.proteins_g) / 50.0 * 100, 1) AS pct_rda_proteins,
    ROUND(SUM(mi.fiber_g) / 25.0 * 100, 1) AS pct_rda_fiber
FROM app.users u
JOIN app.meals m ON u.user_id = m.user_id
JOIN app.meal_items mi ON m.meal_id = mi.meal_id
WHERE m.meal_date = CURRENT_DATE
  AND u.is_active = TRUE
GROUP BY u.username, m.meal_date
ORDER BY total_kcal DESC;

-- EXPLAIN ANALYZE notes:
-- Index idx_meals_user_date enables fast lookup on (user_id, meal_date)
-- Aggregate pushdown reduces rows before final sort


-- =============================================================
-- QUERY 2: Product search with full-text search and Nutri-Score filter
-- Optimization: GIN index on to_tsvector for text search
-- Filter strategy: WHERE clause filters before aggregation
-- =============================================================
SELECT
    p.barcode,
    p.product_name,
    b.brand_name,
    c.category_name,
    p.nutriscore_grade,
    p.nova_group,
    p.energy_kcal,
    p.proteins_g,
    p.fat_g,
    p.carbohydrates_g,
    p.fiber_g,
    ts_rank(to_tsvector('french', p.product_name), plainto_tsquery('french', 'chocolat noir')) AS relevance
FROM app.products p
LEFT JOIN app.brands b ON p.brand_id = b.brand_id
LEFT JOIN app.categories c ON p.category_id = c.category_id
WHERE to_tsvector('french', p.product_name) @@ plainto_tsquery('french', 'chocolat noir')
  AND p.nutriscore_grade IN ('A', 'B', 'C')
ORDER BY relevance DESC, p.nutriscore_grade ASC
LIMIT 20;

-- EXPLAIN ANALYZE notes:
-- GIN index idx_products_name used for full-text search
-- LEFT JOINs on brands/categories allow products without brand/category
-- LIMIT applied after sort to get best matches first


-- =============================================================
-- QUERY 3: Healthier alternatives in the same category
-- Optimization: Window function avoids self-join
-- Strategy: Partition by category, rank by nutriscore
-- =============================================================
WITH product_ranking AS (
    SELECT
        p.product_id,
        p.barcode,
        p.product_name,
        b.brand_name,
        c.category_name,
        p.nutriscore_grade,
        p.nutriscore_score,
        p.energy_kcal,
        p.nova_group,
        ROW_NUMBER() OVER (
            PARTITION BY p.category_id
            ORDER BY p.nutriscore_score ASC, p.nova_group ASC
        ) AS rank_in_category,
        COUNT(*) OVER (PARTITION BY p.category_id) AS category_product_count
    FROM app.products p
    LEFT JOIN app.brands b ON p.brand_id = b.brand_id
    LEFT JOIN app.categories c ON p.category_id = c.category_id
    WHERE p.category_id = (
        SELECT category_id FROM app.products WHERE barcode = '3017620422003'
    )
    AND p.nutriscore_score IS NOT NULL
)
SELECT *
FROM product_ranking
WHERE rank_in_category <= 5
ORDER BY nutriscore_score ASC;

-- EXPLAIN ANALYZE notes:
-- Window function avoids expensive self-join
-- Subquery on barcode uses unique index for constant-time lookup
-- PARTITION BY category_id groups products within same category


-- =============================================================
-- QUERY 4: Weekly nutrition trends with moving average
-- Optimization: Window function for rolling calculation
-- Strategy: LAG/LEAD avoid multiple self-joins
-- =============================================================
WITH daily_totals AS (
    SELECT
        m.meal_date,
        SUM(mi.energy_kcal) AS daily_kcal,
        SUM(mi.proteins_g) AS daily_proteins,
        SUM(mi.carbohydrates_g) AS daily_carbs,
        SUM(mi.fat_g) AS daily_fat,
        COUNT(DISTINCT mi.product_id) AS unique_products
    FROM app.meals m
    JOIN app.meal_items mi ON m.meal_id = mi.meal_id
    WHERE m.user_id = '00000000-0000-0000-0000-000000000001'::UUID
      AND m.meal_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY m.meal_date
)
SELECT
    meal_date,
    daily_kcal,
    daily_proteins,
    daily_carbs,
    daily_fat,
    unique_products,
    -- 7-day moving average
    ROUND(AVG(daily_kcal) OVER (
        ORDER BY meal_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) AS moving_avg_kcal_7d,
    -- Day-over-day change
    daily_kcal - LAG(daily_kcal) OVER (ORDER BY meal_date) AS kcal_change,
    -- Macro ratio
    ROUND(daily_proteins * 4 / NULLIF(daily_kcal, 0) * 100, 1) AS protein_pct,
    ROUND(daily_carbs * 4 / NULLIF(daily_kcal, 0) * 100, 1) AS carbs_pct,
    ROUND(daily_fat * 9 / NULLIF(daily_kcal, 0) * 100, 1) AS fat_pct
FROM daily_totals
ORDER BY meal_date;


-- =============================================================
-- QUERY 5: Nutri-Score distribution by category (warehouse query)
-- Optimization: Uses pre-aggregated fact table
-- =============================================================
SELECT
    c.category_name,
    ns.nutriscore_grade,
    ns.grade_description,
    COUNT(*) AS product_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY c.category_name), 1) AS pct_in_category,
    ROUND(AVG(f.energy_kcal_per_100g), 0) AS avg_kcal,
    ROUND(AVG(f.sugars_per_100g), 1) AS avg_sugars,
    ROUND(AVG(f.salt_per_100g), 2) AS avg_salt
FROM dw.fact_product_market f
JOIN dw.dim_category c ON f.category_key = c.category_key
JOIN dw.dim_nutriscore ns ON f.nutriscore_grade = ns.nutriscore_grade
JOIN dw.dim_product p ON f.product_key = p.product_key AND p.is_current = TRUE
GROUP BY c.category_name, ns.nutriscore_grade, ns.grade_description
ORDER BY c.category_name, ns.nutriscore_grade;


-- =============================================================
-- QUERY 6: Brand quality comparison with NOVA analysis
-- Optimization: HAVING clause filters after aggregation
-- Strategy: CTE pre-filters to reduce main query data volume
-- =============================================================
WITH brand_stats AS (
    SELECT
        b.brand_name,
        b.parent_company,
        COUNT(*) AS product_count,
        AVG(f.nutriscore_score) AS avg_nutriscore_score,
        AVG(f.nova_group) AS avg_nova,
        SUM(CASE WHEN f.nutriscore_grade IN ('A', 'B') THEN 1 ELSE 0 END) AS good_products,
        SUM(CASE WHEN f.nutriscore_grade IN ('D', 'E') THEN 1 ELSE 0 END) AS poor_products,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.energy_kcal_per_100g) AS median_kcal
    FROM dw.fact_product_market f
    JOIN dw.dim_brand b ON f.brand_key = b.brand_key
    JOIN dw.dim_product p ON f.product_key = p.product_key AND p.is_current = TRUE
    GROUP BY b.brand_name, b.parent_company
    HAVING COUNT(*) >= 10
)
SELECT
    brand_name,
    parent_company,
    product_count,
    ROUND(avg_nutriscore_score, 1) AS avg_nutriscore,
    ROUND(avg_nova, 1) AS avg_nova_group,
    good_products,
    poor_products,
    ROUND(good_products * 100.0 / product_count, 1) AS pct_good,
    ROUND(median_kcal, 0) AS median_kcal_per_100g
FROM brand_stats
ORDER BY avg_nutriscore_score ASC
LIMIT 25;


-- =============================================================
-- QUERY 7: User meal pattern analysis (time-of-day breakdown)
-- Optimization: Extract hour from timestamp for grouping
-- =============================================================
SELECT
    u.user_hash,
    u.dietary_goal,
    t.day_name,
    f.meal_type,
    COUNT(*) AS meal_count,
    ROUND(AVG(f.energy_kcal), 0) AS avg_kcal_per_meal,
    ROUND(AVG(f.proteins_g), 1) AS avg_proteins_per_meal,
    ROUND(STDDEV(f.energy_kcal), 0) AS stddev_kcal
FROM dw.fact_daily_nutrition f
JOIN dw.dim_user u ON f.user_key = u.user_key AND u.is_current = TRUE
JOIN dw.dim_time t ON f.time_key = t.time_key
GROUP BY u.user_hash, u.dietary_goal, t.day_name, f.meal_type
ORDER BY u.user_hash, t.day_name, f.meal_type;
