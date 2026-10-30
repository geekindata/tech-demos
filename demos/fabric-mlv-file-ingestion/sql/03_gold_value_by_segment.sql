-- 03_gold_value_by_segment.sql
-- Gold aggregate, same shape as the blog's gold example (SUM ... GROUP BY):
--   https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801
-- IF NOT EXISTS + AS SELECT ... GROUP BY form: Get Started page
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/get-started-with-materialized-lake-views
-- Only SUM/COUNT are used: they "support incremental refresh without the partitioning requirement"
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view#sql-constructs-supported-by-incremental-refresh

CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS gold.value_by_segment
COMMENT "Gold: row count and total value per segment"
AS SELECT
    segment,
    COUNT(*)    AS row_count,
    SUM(value)  AS total_value
FROM silver.table_a_clean
GROUP BY segment;
