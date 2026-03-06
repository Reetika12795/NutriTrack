-- =============================================================
-- SCD (Slowly Changing Dimensions) Procedures
-- Covers: C17 - Kimball dimension variations
-- =============================================================

-- =============================================================
-- SCD TYPE 1: Overwrite (Brand name corrections)
-- Use case: A brand name has a typo, we correct it everywhere
-- Example: "Dannon" -> "Danone"
-- =============================================================

-- Example usage:
-- SELECT dw.scd_type1_update_brand(42, 'Danone');

-- Batch SCD Type 1: correct multiple brands from a correction table
CREATE OR REPLACE FUNCTION dw.scd_type1_batch_brand_corrections(
    p_corrections JSONB
)
RETURNS INTEGER AS $$
DECLARE
    correction RECORD;
    update_count INTEGER := 0;
BEGIN
    FOR correction IN
        SELECT * FROM jsonb_to_recordset(p_corrections)
        AS x(brand_key INTEGER, new_brand_name VARCHAR(255))
    LOOP
        PERFORM dw.scd_type1_update_brand(correction.brand_key, correction.new_brand_name);
        update_count := update_count + 1;
    END LOOP;

    RETURN update_count;
END;
$$ LANGUAGE plpgsql;


-- =============================================================
-- SCD TYPE 2: Historical tracking (Product Nutri-Score changes)
-- Use case: A product is reformulated, its Nutri-Score changes from D to B
-- We keep both versions with effective dates
-- =============================================================

-- View to see product history
CREATE OR REPLACE VIEW dw.v_product_history AS
SELECT
    barcode,
    product_name,
    effective_date,
    end_date,
    is_current,
    completeness_score,
    CASE
        WHEN is_current THEN 'Current version'
        ELSE 'Historical version (ended ' || end_date::TEXT || ')'
    END AS version_status
FROM dw.dim_product
ORDER BY barcode, effective_date DESC;

-- Function to check for product changes and apply SCD Type 2
CREATE OR REPLACE FUNCTION dw.scd_type2_check_and_update_products()
RETURNS TABLE(barcode VARCHAR, change_type TEXT) AS $$
DECLARE
    src RECORD;
    existing RECORD;
BEGIN
    -- Compare current warehouse products with operational DB
    FOR src IN
        SELECT
            p.barcode,
            p.product_name,
            p.generic_name,
            p.quantity,
            p.packaging,
            p.ingredients_text,
            p.completeness_score,
            p.product_id
        FROM app.products p
    LOOP
        -- Check if product exists in dimension
        SELECT * INTO existing
        FROM dw.dim_product dp
        WHERE dp.barcode = src.barcode AND dp.is_current = TRUE;

        IF NOT FOUND THEN
            -- New product: insert
            INSERT INTO dw.dim_product (
                barcode, product_name, generic_name, quantity, packaging,
                ingredients_text, completeness_score, source_product_id
            ) VALUES (
                src.barcode, src.product_name, src.generic_name, src.quantity,
                src.packaging, src.ingredients_text, src.completeness_score,
                src.product_id
            );
            barcode := src.barcode;
            change_type := 'NEW';
            RETURN NEXT;

        ELSIF existing.product_name IS DISTINCT FROM src.product_name
           OR existing.ingredients_text IS DISTINCT FROM src.ingredients_text
           OR existing.completeness_score IS DISTINCT FROM src.completeness_score
        THEN
            -- Changed product: apply SCD Type 2
            PERFORM dw.scd_type2_update_product(
                src.barcode, src.product_name, src.generic_name,
                src.quantity, src.packaging, src.ingredients_text,
                src.completeness_score, src.product_id
            );
            barcode := src.barcode;
            change_type := 'UPDATED';
            RETURN NEXT;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;


-- =============================================================
-- SCD TYPE 3: Add column (Country expansion)
-- Use case: A product was sold in "France" and now expands to "France, Belgium"
-- We keep the previous value in an adjacent column
-- =============================================================

-- Example usage:
-- SELECT dw.scd_type3_update_country(1, 'France, Belgium, Luxembourg');
-- This stores the old value in previous_country_list


-- =============================================================
-- DEMONSTRATION QUERIES
-- =============================================================

-- Show SCD Type 2 in action: products that changed over time
-- SELECT * FROM dw.v_product_history WHERE barcode = '3017620422003';

-- Show brand corrections (SCD Type 1)
-- SELECT brand_key, brand_name, last_updated FROM dw.dim_brand WHERE last_updated > loaded_at;

-- Show country expansions (SCD Type 3)
-- SELECT country_key, country_name, previous_country_list FROM dw.dim_country WHERE previous_country_list IS NOT NULL;
