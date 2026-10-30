-- 02_silver_table_a_clean.sql  (v1 - created after file_001, before attribute_b exists)
-- Table-based MLV on top of the file-ingesting bronze view.
-- CREATE ... (CONSTRAINT name CHECK (cond) ON MISMATCH DROP) ... COMMENT ... TBLPROPERTIES ... AS SELECT
--   clause order from the Syntax block:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#syntax
-- ON MISMATCH DROP "silently removes the row"; default is FAIL; "The lineage view shows the count of
--   dropped records":
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/data-quality
-- Constraints use only deterministic built-ins so incremental refresh stays possible:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view#sql-constructs-supported-by-incremental-refresh
-- TBLPROPERTIES (delta.enableChangeDataFeed=true) at create time is documented on the refresh page
--   ("You can enable CDF at creation time"); it lets gold (which reads silver) refresh incrementally.
-- Selecting __filepath__ from bronze downstream: UNVERIFIED in docs (see README uncertainties #1).
-- CASTs are defensive: the default of 'inferSchema' for OneLake_Files is not documented (uncertainty #3).

CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS silver.table_a_clean
(
    CONSTRAINT id_not_null         CHECK (id IS NOT NULL)              ON MISMATCH DROP,
    CONSTRAINT non_negative_value  CHECK (value >= 0)                  ON MISMATCH DROP,
    CONSTRAINT known_segment       CHECK (segment IN ('A', 'B', 'C'))  ON MISMATCH DROP
)
COMMENT "Silver: typed, validated table_a rows (rows breaking a rule are dropped)"
TBLPROPERTIES (delta.enableChangeDataFeed=true)
AS SELECT
    CAST(id AS INT)                AS id,
    segment,
    attribute_a,
    CAST(value AS DECIMAL(10,2))   AS value,
    __filepath__                   AS source_file
FROM bronze.table_a;
