# Notes: fabric-databricks-post51

Verified hands-on on 30 Oct 2026 while creating the post 51 scratch objects.

## Verified facts

- **Free Edition grants:** a group needs `USE SCHEMA` on the schema as well as `SELECT` on the table before it can query the table. `USE CATALOG` on the catalog is also required in general Unity Catalog terms.
- **OneLake security role names** allow letters and numbers only. Underscores are rejected, so the role is `demoreaders`, not `demo_readers`.
- **Databricks Free Edition** has serverless compute only: no compute policies and no auto-termination setting to configure. Compute governance shots need a Premium workspace.
- **Semantic models need Power BI Pro** (or a trial). With a free Power BI license you can create a lakehouse, notebook, pipeline and eventstream on an F2, but not a semantic model.
- **Compute policy:** fixing `autotermination_minutes` at 10 and `node_type_id` at Standard_DS3_v2 locks both fields on the create-compute form (see `screenshots/08b-databricks-compute-autotermination.png`).

## MLflow runs in `demo_experiment`

| Run | alpha | rmse = round(1/(1+alpha), 3) |
|---|---|---|
| alpha_0.1 | 0.1 | 0.909 |
| alpha_0.5 | 0.5 | 0.667 |
| alpha_1.0 | 1.0 | 0.5 |

## dim_table and gold_table

`dim_table`: (1, alpha, A), (2, beta, B), (3, gamma, A). `gold_table` = count per category: A 2, B 1.

## State at the end of 30 Oct 2026

F2 paused; `demo-dbx` cluster terminated and SQL warehouse stopped; Free Edition warehouse stopped and the post 51 objects removed.
