# fabric-variable-library-targets: one notebook, three targets, picked by a Variable Library

**Platform:** Microsoft Fabric (Variable Library, PySpark notebook) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 31 (shot p31-01)

Tested in Fabric workspace `demo_ws` on the Fabric trial on Oct 30, 2026.

A Variable Library item, `demo_varlib`, holds two variables (`target_lakehouse`, `batch_size`) and three value sets (`Test`, `Preprod`, `Prod`). A notebook, `demo_varlib_read`, reads the values of the **active** value set. The notebook code never changes between stages; only the active value set does.

## What it shows

| # | Capability | Where |
|---|---|---|
| 1 | A Variable Library with a default value per variable and one value set per stage | `fabric/demo_varlib/` |
| 2 | Reading a variable through the library object: `notebookutils.variableLibrary.getLibrary("demo_varlib").target_lakehouse` | `fabric/notebooks/demo_varlib_read.py` |
| 3 | Reading a variable by reference: `notebookutils.variableLibrary.get("$(/**/demo_varlib/batch_size)")` | `fabric/notebooks/demo_varlib_read.py` |
| 4 | Switching the active value set changes what the notebook gets, with no code edit | Run step 4 |

## Contents

```
fabric/demo_varlib/settings.json           value set order: Test, Preprod, Prod
fabric/demo_varlib/variables.json          variables and their default values
fabric/demo_varlib/valueSets/*.json        Test, Preprod and Prod overrides
fabric/notebooks/demo_varlib_read.py       notebook cell, paste into a PySpark notebook
NOTES.md                                   technical notes and verified values
```

The values used:

| Variable | Type | Default | Test | Preprod | Prod |
|---|---|---|---|---|---|
| `target_lakehouse` | String | `demo_lakehouse_dev` | `demo_lakehouse_test` | `demo_lakehouse_preprod` | `demo_lakehouse_prod` |
| `batch_size` | Integer | 500 | 1000 | 2000 | 5000 |

The lakehouse names are only string values. The demo reads them; it does not need lakehouses with those names to exist.

## Prerequisites

- A workspace on a **Fabric trial** or a **Fabric capacity** (an F2 is enough). Tested on the Fabric trial.
- Contributor (or higher) on the workspace, so you can create items.
- Variable libraries available in your tenant. If *Variable library* is missing from *New item*, ask your Fabric admin.

## Setup

1. In the workspace, select **New item** > **Variable library**. Name it `demo_varlib`.
2. Add the two variables from the table above, with their types and default values.
3. Add three value sets in this order: `Test`, `Preprod`, `Prod`, and fill in the values from the table.
4. Set **Test** as the active value set and **Save**.

The JSON files in `fabric/demo_varlib/` mirror the item definition format (the same files a Git-connected workspace stores for a Variable Library). In `demo_ws` the item was built in the UI as above; importing these files through Git integration was not tested.

## Run

1. In the same workspace, create a PySpark notebook named `demo_varlib_read`. No lakehouse needs to be attached.
2. Paste `fabric/notebooks/demo_varlib_read.py` into one cell.
3. Run the cell.
4. Optional: in `demo_varlib`, make **Prod** the active value set, save, and run the cell again. Set **Test** back as active afterwards.

## Expected output

With **Test** active (verified in `demo_ws`):

```
target_lakehouse = demo_lakehouse_test
batch_size       = 1000
```

With **Prod** active, the same cell should print `demo_lakehouse_prod` and `5000` (not run in `demo_ws`).

## Caveats

- The notebook reads the value set that is active in the workspace where it runs. In a deployment pipeline, each stage workspace has its own active value set, so the same notebook picks up different values per stage.
- The first run starts a Spark session, which takes a short while on a trial or F2.
- In the value set files the overrides are stored as strings (`"1000"`), as in the definition files; the variable type (`Integer`) is set in `variables.json`.

## Cost and cleanup

**Cost:** free on the Fabric trial. On a paid capacity (an F2 is enough) one run is a few minutes of capacity time; there is no other billable resource. **Pause the capacity when you're done.**

**Cleanup:** keep the scratch workspace and both items (repo convention). Stop the notebook session (*Stop session*) after the run. If you switched the active value set, set it back to **Test**. On a paid capacity, pause it in the Azure portal.

Docs (read Oct 30, 2026): [Variable libraries overview](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview) · [NotebookUtils variable library utilities](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities)
