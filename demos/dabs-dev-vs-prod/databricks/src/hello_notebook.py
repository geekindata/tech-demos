# Databricks notebook source
# Trivial task for the dev-vs-prod bundle demo: prints which target deployed it.

# COMMAND ----------

dbutils.widgets.text("catalog", "main")
dbutils.widgets.text("schema", "demo_schema")
dbutils.widgets.text("target", "dev")

# COMMAND ----------

print(f"Hello from the {dbutils.widgets.get('target')} target "
      f"({dbutils.widgets.get('catalog')}.{dbutils.widgets.get('schema')})")
