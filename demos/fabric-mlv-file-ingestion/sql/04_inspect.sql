-- 04_inspect.sql  - run after every refresh. Plain SELECTs against MLVs (they query like Delta tables:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view )

-- (a) Rows per source file. Query taken from the blog ("reconcile row counts back to individual source files"):
--   https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801
--   and the GROUP BY __filepath__ tip on the lineage page:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/view-lineage#interpret-file-processing-metrics
SELECT __filepath__, COUNT(*) AS rows
FROM bronze.raw_orders
GROUP BY __filepath__;

-- (b) Bronze vs silver per file = dropped rows per file. __filepath__ is a full OneLake path;
--   element_at(split(...)) is a standard Spark SQL built-in used only for readability.
SELECT element_at(split(b.__filepath__, '/'), -1) AS file,
       b.bronze_rows,
       COALESCE(s.silver_rows, 0)                 AS silver_rows,
       b.bronze_rows - COALESCE(s.silver_rows, 0) AS dropped_rows
FROM (SELECT __filepath__, COUNT(*) AS bronze_rows FROM bronze.raw_orders GROUP BY __filepath__) b
LEFT JOIN (SELECT source_file, COUNT(*) AS silver_rows FROM silver.orders GROUP BY source_file) s
  ON s.source_file = b.__filepath__
ORDER BY file;

-- (c) Which bronze rows the silver constraints dropped (mirrors the three CHECK conditions).
SELECT element_at(split(__filepath__, '/'), -1) AS file, order_id, quantity, unit_price,
       CASE WHEN order_id IS NULL THEN 'order_id_not_null'
            WHEN CAST(quantity AS INT) <= 0 THEN 'positive_quantity'
            ELSE 'non_negative_price' END AS violated_constraint
FROM bronze.raw_orders
WHERE order_id IS NULL
   OR CAST(quantity AS INT) <= 0
   OR CAST(unit_price AS DECIMAL(10,2)) < 0
ORDER BY file, violated_constraint;

-- (d) Schema of bronze: after batch_03, discount_code should appear (DYNAMIC schema mode).
--   DESCRIBE on an MLV is standard Spark SQL on a Delta table; not shown explicitly in MLV docs.
DESCRIBE TABLE bronze.raw_orders;

-- (e) After batch_03 only: discount_code population per file (NULL for files that predate the column).
SELECT element_at(split(__filepath__, '/'), -1) AS file,
       COUNT(*) AS rows, COUNT(discount_code) AS rows_with_code
FROM bronze.raw_orders
GROUP BY __filepath__
ORDER BY file;

-- (f) Gold
SELECT * FROM gold.sales_by_country ORDER BY country;
