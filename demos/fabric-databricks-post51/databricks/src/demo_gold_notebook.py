# Databricks notebook source
# Writes gold_table: row count per category from dim_table.
# Catalog and schema are notebook parameters (bundle variables catalog / schema).

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "demo_schema")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

df = spark.table(f"{catalog}.{schema}.dim_table").groupBy("category").count()
df.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.gold_table")
display(spark.table(f"{catalog}.{schema}.gold_table"))
