-- 01_bronze_table_a.sql
-- Bronze: ingest every CSV in Files/mlv_demo/table_a/ straight into a materialized lake view.
-- Syntax copied from the "Ingest files with USING OneLake_Files" example:
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#ingest-files-with-using-onelake_files
-- and the announcement blog (same statement, DYNAMIC + APPEND_ONLY):
--   https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801
--
-- Replace <workspace> and <lakehouse> (in demo_ws: demo_ws and demo_mlv_lh), or paste the folder's
--   "Copy ABFS path" from the Lakehouse explorer.
-- Path rules (Spark SQL reference): trailing slash for a folder; no raw spaces or %20 in the path.
-- schema_mode DYNAMIC: "adds newly discovered columns and writes NULL when a file doesn't contain an
--   established column" (TBLPROPERTIES reference). This is what makes file_003's attribute_b appear.
-- refresh_mode APPEND_ONLY: "adds rows from new files" (TBLPROPERTIES reference).
-- No AS SELECT here on purpose: projecting a fixed column list would hide new columns.
-- The doc example states "Each row also gets a __filepath__ column" for this exact form, and the blog's
--   GROUP BY __filepath__ query runs against it. (See README "Doc uncertainties" #1.)
-- Do NOT set the Spark CSV 'mode' option: "Fabric manages malformed-row handling" (OPTIONS reference).

CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS bronze.table_a
USING OneLake_Files
OPTIONS (
    'format' = 'csv',
    'path'   = 'abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/mlv_demo/table_a/',
    'header' = 'true'
)
COMMENT "Bronze: raw table_a CSVs ingested from OneLake Files (demo)"
TBLPROPERTIES (
    'schema_mode'  = 'DYNAMIC',
    'refresh_mode' = 'APPEND_ONLY'
);
