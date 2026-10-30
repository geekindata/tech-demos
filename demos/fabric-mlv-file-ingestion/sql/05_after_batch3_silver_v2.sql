-- 05_after_batch3_silver_v2.sql  - run once bronze shows discount_code (after batch_03 refresh).
-- Point of the step: bronze evolves automatically (DYNAMIC); silver is an explicit contract you
-- change deliberately. "To modify the definition ... use the CREATE OR REPLACE command":
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#update-a-materialized-lake-view
-- OR REPLACE can't be combined with IF NOT EXISTS (Arguments table, same page).
-- UNVERIFIED: whether replacing silver while gold.sales_by_country depends on it keeps the lineage
-- intact without recreating gold. If gold errors on its next run, run 99_cleanup order for gold only
-- (DROP gold.sales_by_country) and re-run 03_gold_sales_by_country.sql.

CREATE OR REPLACE MATERIALIZED LAKE VIEW silver.orders
(
    CONSTRAINT order_id_not_null  CHECK (order_id IS NOT NULL) ON MISMATCH DROP,
    CONSTRAINT positive_quantity  CHECK (quantity > 0)        ON MISMATCH DROP,
    CONSTRAINT non_negative_price CHECK (unit_price >= 0)     ON MISMATCH DROP
)
COMMENT "Silver v2: adds discount_code (introduced in batch_03)"
TBLPROPERTIES (delta.enableChangeDataFeed=true)
AS SELECT
    order_id,
    CAST(order_date AS DATE)            AS order_date,
    customer_id,
    country,
    channel,
    product_sku,
    product_name,
    CAST(quantity AS INT)               AS quantity,
    CAST(unit_price AS DECIMAL(10,2))   AS unit_price,
    CAST(quantity AS INT) * CAST(unit_price AS DECIMAL(10,2)) AS line_amount,
    discount_code,
    __filepath__                        AS source_file
FROM bronze.raw_orders;

-- New gold view that only makes sense once the column exists.
CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS gold.discount_usage
COMMENT "Gold: order lines and revenue by discount code"
AS SELECT
    COALESCE(discount_code, '(none)') AS discount_code,
    COUNT(*)                          AS order_lines,
    SUM(line_amount)                  AS revenue_nok
FROM silver.orders
GROUP BY COALESCE(discount_code, '(none)');

SELECT * FROM gold.discount_usage ORDER BY discount_code;
