-- 00_setup_schemas.sql
-- Run in a Spark SQL notebook attached to a schema-enabled lakehouse.
-- Prereq "Lakehouse with Lakehouse schemas enabled and Fabric Runtime 1.3":
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/get-started-with-materialized-lake-views
-- CREATE SCHEMA IF NOT EXISTS pattern: same Get Started page.
-- Schema names must NOT be all-uppercase (Current limitations):
--   https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view#current-limitations

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
