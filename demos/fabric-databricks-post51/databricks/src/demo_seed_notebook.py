# Databricks notebook source
# Seeds dim_table with three inline rows so demo_gold_notebook has input.
# Catalog and schema are notebook parameters (bundle variables catalog / schema).

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "demo_schema")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.{schema}.dim_table AS
SELECT * FROM VALUES
  (1, 'alpha', 'A'),
  (2, 'beta',  'B'),
  (3, 'gamma', 'A')
AS t(id, name, category)
""")
display(spark.table(f"{catalog}.{schema}.dim_table"))
