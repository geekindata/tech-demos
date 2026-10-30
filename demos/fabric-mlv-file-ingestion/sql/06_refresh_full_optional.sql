-- 06_refresh_full_optional.sql - notebook fallback if you can't use the lineage "Run" button.
-- Documented syntax: REFRESH MATERIALIZED LAKE VIEW [workspace.lakehouse.schema].MLV_Identifier FULL
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view#run-a-one-time-full-refresh-with-sql
-- and for file views "REFRESH MATERIALIZED LAKE VIEW <bronze view> FULL;" (blog + Spark SQL reference tip).
-- Docs recommend lineage/scheduled refresh for ongoing runs ("don't orchestrate ... from a notebook").
-- A notebook refresh does NOT cascade; run in dependency order yourself.
-- FULL on bronze reprocesses the current folder as a snapshot, so no duplicate rows.

REFRESH MATERIALIZED LAKE VIEW bronze.table_a FULL;
REFRESH MATERIALIZED LAKE VIEW silver.table_a_clean FULL;
REFRESH MATERIALIZED LAKE VIEW gold.value_by_segment FULL;
-- after step 05 only:
-- REFRESH MATERIALIZED LAKE VIEW gold.value_by_attribute_b FULL;
