# fabric-databricks-post51

**Platform:** Microsoft Fabric + Azure Databricks (Premium) · **Date:** 30 Oct 2026 · **Related post:** blog post 51, *Fabric or Databricks? How I Decide*

Scratch objects created to take the screenshots for post 51. The post compares how the two platforms handle Git, workspace items, gold tables, security, compute governance and ML tracking. This folder records what exists, so the shots can be re-taken.

## What it shows

### Microsoft Fabric: scratch workspace `demo_ws` on an F2 capacity

| Item | Type | Notes |
|---|---|---|
| `demo_lakehouse` | Lakehouse | Holds `dim_table` (3 rows, written by `demo_notebook`) |
| `demo_notebook` | Notebook | Source in `fabric/notebooks/demo_notebook.py` (plain notebook source to paste into a Fabric notebook, not Fabric Git-sync format) |
| `demo_pipeline` | Data pipeline | Empty, shown in the item list |
| `demo_eventstream` | Eventstream | No source added |
| `demoreaders` | OneLake security role on `demo_lakehouse` | Read access |

Also shown: workspace Git integration settings, capacity settings with assigned workspaces, and Manage permissions on an item.

### Azure Databricks: Premium scratch workspace `demo-dbx`

| Object | Type | Notes |
|---|---|---|
| `demo_policy` | Compute policy | `autotermination_minutes` fixed at 10, `node_type_id` fixed at Standard_DS3_v2, an Azure-only VM type (`databricks/resources/demo_policy.json`; see `resources/README.md` for AWS/GCP) |
| `demo_cluster` | Single-node all-purpose cluster | Created under `demo_policy` |
| `demo_mlflow` | Notebook | `databricks/src/demo_mlflow.py` (experiment path is the `experiment_name` parameter) |
| `demo_experiment` | MLflow experiment | 3 runs, alpha 0.1, 0.5 and 1.0 |

### Databricks Free Edition

In a Databricks Free Edition workspace, `workspace.demo_schema` with `dim_table` and `gold_table`, the notebook `demo_gold_notebook` (`databricks/src/demo_gold_notebook.py`) and a `bundle-examples` Git folder were created for shots 03b, 07a and 09a. They were removed afterwards to keep that workspace clean. Re-create them with the bundle (`demo_gold_job` seeds `dim_table`, then writes `gold_table`) if needed (Azure Databricks `demo-dbx` is the preferred place for new Databricks demos).

## Prerequisites

- A Fabric capacity (an F2 is enough) and a workspace assigned to it. OneLake security must be enabled on the lakehouse.
- An Azure Databricks Premium workspace (compute policies need Premium) with Unity Catalog, and a Databricks CLI profile for it.

## How to run

**Fabric:** create a lakehouse and a new notebook, paste the code from `fabric/notebooks/demo_notebook.py` into a cell (it is notebook source, not a Git-synced Fabric item), attach it to the lakehouse and run it. Add a pipeline and an eventstream from *New item*, and a OneLake security role from the lakehouse's *Manage OneLake security*.

**Databricks:**

```bash
cd databricks
databricks bundle validate -t dev --profile <your-profile>
databricks bundle deploy   -t dev --profile <your-profile> --var="catalog=<catalog>" --var="schema=<schema>"
```

Create the policy from `resources/demo_policy.json` (Compute → Policies → Create, JSON view, or `databricks cluster-policies create --json @resources/demo_policy.json`). Both jobs run on serverless (notebook tasks with no cluster settings). `demo_gold_job` runs `seed_dim` (creates `dim_table` from inline values) and then `write_gold`. `demo_mlflow_job` logs the three runs to `--var="experiment_name=/Users/<you>/demo_experiment"` (the default). Run them with `databricks bundle run -t dev demo_gold_job` and `databricks bundle run -t dev demo_mlflow_job`.

## Cost and cleanup

- **Fabric:** the F2 bills per hour while running. **Pause it after every session** (Azure portal → the Fabric capacity → Pause) and confirm on a fresh page load that it shows *Paused*.
- **Azure Databricks:** the workspace itself costs almost nothing; you pay for running compute. **Terminate `demo_cluster`** (the policy auto-terminates it after 10 idle minutes anyway), **stop any SQL warehouse**, and check that no job runs are active. To remove the bundle's jobs and files: `databricks bundle destroy -t dev --profile <your-profile>` (tables and the experiment created by the runs are not removed by destroy).
- Scratch environments are kept, not deleted, per the repo conventions. Leave `demo_ws` and `demo-dbx` in place with all compute paused or stopped.

## Limitations

- **No semantic model.** The account has a free Power BI license, and creating a semantic model (including Direct Lake) needs Power BI Pro or a trial. Shot 7b was skipped and the item list has no semantic model.
- The OneLake security role view in 10a doesn't show members.
- 13b shows the eventstream editor, because the Real-Time hub page wouldn't load.
- Databricks Free Edition has no compute policies or auto-termination settings, so 8b was taken in Azure Databricks Premium.
