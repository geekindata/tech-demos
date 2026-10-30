# Databricks notebook source
# Logs three MLflow runs (alpha 0.1, 0.5, 1.0) with a toy rmse metric.
# The experiment is a parameter: an absolute workspace path, or empty to use the notebook's own experiment.

# COMMAND ----------

import mlflow

dbutils.widgets.text("experiment_name", "")
experiment_name = dbutils.widgets.get("experiment_name").strip()
if experiment_name:
    mlflow.set_experiment(experiment_name)

# COMMAND ----------

for a in [0.1, 0.5, 1.0]:
    with mlflow.start_run(run_name=f"alpha_{a}"):
        mlflow.log_param("alpha", a)
        mlflow.log_metric("rmse", round(1 / (1 + a), 3))
