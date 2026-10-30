-- 04_inspect.sql  - run after every refresh. Plain SELECTs against MLVs (they query like Delta tables:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view )

-- (a) Rows per source file. Query taken from the blog ("reconcile row counts back to individual source files"):
--   https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801
--   and the GROUP BY __filepath__ tip on the lineage page:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/view-lineage#interpret-file-processing-metrics
SELECT __filepath__, COUNT(*) AS rows
FROM bronze.table_a
GROUP BY __filepath__;

-- (b) Bronze vs silver per file = dropped rows per file. __filepath__ is a full OneLake path;
--   element_at(split(...)) is a standard Spark SQL built-in used only for readability.
SELECT element_at(split(b.__filepath__, '/'), -1) AS file,
       b.bronze_rows,
       COALESCE(s.silver_rows, 0)                 AS silver_rows,
       b.bronze_rows - COALESCE(s.silver_rows, 0) AS dropped_rows
FROM (SELECT __filepath__, COUNT(*) AS bronze_rows FROM bronze.table_a GROUP BY __filepath__) b
LEFT JOIN (SELECT source_file, COUNT(*) AS silver_rows FROM silver.table_a_clean GROUP BY source_file) s
  ON s.source_file = b.__filepath__
ORDER BY file;

-- (c) Which bronze rows the silver constraints dropped (mirrors the three CHECK conditions).
SELECT element_at(split(__filepath__, '/'), -1) AS file, id, segment, value,
       CASE WHEN id IS NULL THEN 'id_not_null'
            WHEN CAST(value AS DECIMAL(10,2)) < 0 THEN 'non_negative_value'
            ELSE 'known_segment' END AS violated_constraint
FROM bronze.table_a
WHERE id IS NULL
   OR CAST(value AS DECIMAL(10,2)) < 0
   OR segment NOT IN ('A', 'B', 'C')
ORDER BY file, violated_constraint;

-- (d) Schema of bronze: after file_003, attribute_b should appear (DYNAMIC schema mode).
--   DESCRIBE on an MLV is standard Spark SQL on a Delta table; not shown explicitly in MLV docs.
DESCRIBE TABLE bronze.table_a;

-- (e) After file_003 only: attribute_b population per file (NULL for files that predate the column).
SELECT element_at(split(__filepath__, '/'), -1) AS file,
       COUNT(*) AS rows, COUNT(attribute_b) AS rows_with_attribute_b
FROM bronze.table_a
GROUP BY __filepath__
ORDER BY file;

-- (f) Gold
SELECT * FROM gold.value_by_segment ORDER BY segment;
