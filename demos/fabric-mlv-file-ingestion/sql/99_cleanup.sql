-- 99_cleanup.sql - drop downstream first. Syntax: DROP MATERIALIZED LAKE VIEW MLV_Identifier;
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#delete-a-materialized-lake-view
-- Also delete any refresh schedule you created (Manage schedules > trash icon):
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/schedule-lineage-run#manage-schedules
-- Do not touch the _mlv_system schema (overview page, "Don't alter the _mlv_system schema").
-- These names match the objects already in demo_ws (demo_mlv_lh), so this also drops those.

DROP MATERIALIZED LAKE VIEW gold.value_by_attribute_b;   -- only exists if you ran step 05
DROP MATERIALIZED LAKE VIEW gold.value_by_segment;
DROP MATERIALIZED LAKE VIEW silver.table_a_clean;
DROP MATERIALIZED LAKE VIEW bronze.table_a;
-- Optional, if the schemas were created only for this demo (standard Spark SQL, not from MLV docs):
-- DROP SCHEMA gold; DROP SCHEMA silver; DROP SCHEMA bronze;
-- Finally delete the Files/mlv_demo/table_a folder in the Lakehouse explorer.
