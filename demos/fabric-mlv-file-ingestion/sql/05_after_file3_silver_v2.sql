-- 05_after_file3_silver_v2.sql  - run once bronze shows attribute_b (after the file_003 refresh).
-- Point of the step: bronze evolves automatically (DYNAMIC); silver is an explicit contract you
-- change deliberately. "To modify the definition ... use the CREATE OR REPLACE command":
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#update-a-materialized-lake-view
-- OR REPLACE can't be combined with IF NOT EXISTS (Arguments table, same page).
-- UNVERIFIED: whether replacing silver while gold.value_by_segment depends on it keeps the lineage
-- intact without recreating gold. If gold errors on its next run, DROP gold.value_by_segment
-- and re-run 03_gold_value_by_segment.sql.

CREATE OR REPLACE MATERIALIZED LAKE VIEW silver.table_a_clean
(
    CONSTRAINT id_not_null         CHECK (id IS NOT NULL)              ON MISMATCH DROP,
    CONSTRAINT non_negative_value  CHECK (value >= 0)                  ON MISMATCH DROP,
    CONSTRAINT known_segment       CHECK (segment IN ('A', 'B', 'C'))  ON MISMATCH DROP
)
COMMENT "Silver v2: adds attribute_b (introduced in file_003)"
TBLPROPERTIES (delta.enableChangeDataFeed=true)
AS SELECT
    CAST(id AS INT)                AS id,
    segment,
    attribute_a,
    CAST(value AS DECIMAL(10,2))   AS value,
    attribute_b,
    __filepath__                   AS source_file
FROM bronze.table_a;

-- New gold view that only makes sense once the column exists.
CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS gold.value_by_attribute_b
COMMENT "Gold: row count and total value by attribute_b"
AS SELECT
    COALESCE(attribute_b, '(none)') AS attribute_b,
    COUNT(*)                        AS row_count,
    SUM(value)                      AS total_value
FROM silver.table_a_clean
GROUP BY COALESCE(attribute_b, '(none)');

SELECT * FROM gold.value_by_attribute_b ORDER BY attribute_b;
