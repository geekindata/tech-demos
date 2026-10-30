-- 03_gold_sales_by_country.sql
-- Gold aggregate, same shape as the blog's gold.daily_sales example (SUM ... GROUP BY):
--   https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801
-- IF NOT EXISTS + AS SELECT ... GROUP BY form: Get Started page
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/get-started-with-materialized-lake-views
-- Only SUM/COUNT are used: they "support incremental refresh without the partitioning requirement"
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view#sql-constructs-supported-by-incremental-refresh

CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS gold.sales_by_country
COMMENT "Gold: order lines, units and revenue (NOK) per country"
AS SELECT
    country,
    COUNT(*)          AS order_lines,
    SUM(quantity)     AS units,
    SUM(line_amount)  AS revenue_nok
FROM silver.orders
GROUP BY country;
