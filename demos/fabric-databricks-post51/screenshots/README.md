# Screenshots: post 51

Cropped and anonymised on 30 Oct 2026. Names, emails, owners and other workspace names are blurred or covered with solid boxes; no URLs or IDs are visible. Raw captures are not in the repo.

| File | Caption |
|---|---|
| `03a-fabric-git-integration.png` | Fabric workspace settings, Git integration tab: choosing Azure DevOps or GitHub as the Git provider (repo and branch not yet connected in this capture). |
| `03b-databricks-git-folder.png` | Databricks Free Edition: a Git folder (`bundle-examples`) on branch `main` in the workspace; the owner column is blurred. |
| `04a-fabric-workspace-items.png` | Fabric `demo_ws` item list: eventstream, lakehouse with its SQL analytics endpoint, notebook and pipeline (no semantic model, see README). |
| `07a-databricks-notebook-gold.png` | Databricks Free Edition notebook on serverless writing `gold_table` from `dim_table` grouped by category. |
| `08a-fabric-capacity-workspaces.png` | Fabric capacity settings with "Workspaces assigned to this capacity" expanded; capacity name hidden by the crop and other workspace names covered with solid boxes. |
| `08b-alt-databricks-compute-policy.png` | Azure Databricks `demo_policy` definition: `autotermination_minutes` fixed at 10 and `node_type_id` fixed at Standard_DS3_v2. |
| `08b-databricks-compute-autotermination.png` | Azure Databricks create-compute form for `demo_cluster` under `demo_policy`: single node, node type and 10-minute auto-termination locked by the policy. |
| `09a-unity-catalog-grants.png` | Unity Catalog Permissions tab on `workspace.demo_schema.dim_table` (Free Edition) with a SELECT grant to All account users. |
| `09b-fabric-item-permissions.png` | Fabric Manage permissions on `demo_lakehouse`: direct access with workspace role and item permissions (user name, avatar and email covered with solid boxes). |
| `10a-fabric-onelake-security-role.png` | OneLake security role `demoreaders` on `demo_lakehouse`: Read, Grant, with the `dbo` schema as data in role. |
| `13a-databricks-mlflow-runs.png` | Azure Databricks MLflow experiment `demo_experiment` with three runs (alpha 0.1, 0.5, 1.0) and their rmse. |
| `13b-fabric-eventstream.png` | Fabric eventstream editor start page for `demo_eventstream` (no source added yet). |
