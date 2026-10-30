-- 06_refresh_full_optional.sql - notebook fallback if you can't use the lineage "Run" button.
-- Documented syntax: REFRESH MATERIALIZED LAKE VIEW [workspace.lakehouse.schema].MLV_Identifier FULL
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view#run-a-one-time-full-refresh-with-sql
-- and for file views "REFRESH MATERIALIZED LAKE VIEW bronze.raw_orders FULL;" (blog + Spark SQL reference tip).
-- Docs recommend lineage/scheduled refresh for ongoing runs ("don't orchestrate ... from a notebook").
-- A notebook refresh does NOT cascade; run in dependency order yourself.
-- FULL on bronze reprocesses the current folder as a snapshot, so no duplicate rows.

REFRESH MATERIALIZED LAKE VIEW bronze.raw_orders FULL;
REFRESH MATERIALIZED LAKE VIEW silver.orders FULL;
REFRESH MATERIALIZED LAKE VIEW gold.sales_by_country FULL;
-- after step 05 only:
-- REFRESH MATERIALIZED LAKE VIEW gold.discount_usage FULL;
