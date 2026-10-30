-- 02_silver_orders.sql  (v1 - created after batch_01, before discount_code exists)
-- Table-based MLV on top of the file-ingesting bronze view.
-- CREATE ... (CONSTRAINT name CHECK (cond) ON MISMATCH DROP) ... COMMENT ... TBLPROPERTIES ... AS SELECT
--   clause order from the Syntax block:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#syntax
-- Multiple constraints, comma-separated, are shown in the same Syntax block.
-- ON MISMATCH DROP "silently removes the row"; default is FAIL; "The lineage view shows the count of
--   dropped records":
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/data-quality
-- Constraints use only deterministic built-ins so incremental refresh stays possible:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view#sql-constructs-supported-by-incremental-refresh
-- TBLPROPERTIES (delta.enableChangeDataFeed=true) at create time is documented on the refresh page
--   ("You can enable CDF at creation time"); it lets gold (which reads silver) refresh incrementally.
-- Selecting __filepath__ from bronze downstream: UNVERIFIED in docs (see README uncertainties #1).
-- CASTs are defensive: the default of 'inferSchema' for OneLake_Files is not documented (uncertainty #3).

CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS silver.orders
(
    CONSTRAINT order_id_not_null  CHECK (order_id IS NOT NULL) ON MISMATCH DROP,
    CONSTRAINT positive_quantity  CHECK (quantity > 0)        ON MISMATCH DROP,
    CONSTRAINT non_negative_price CHECK (unit_price >= 0)     ON MISMATCH DROP
)
COMMENT "Silver: typed, validated orders (rows breaking a rule are dropped)"
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
    __filepath__                        AS source_file
FROM bronze.raw_orders;
