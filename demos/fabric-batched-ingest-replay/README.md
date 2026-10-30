# fabric-batched-ingest-replay: a batched loader that logs every attempt and tells you what to replay

**Platform:** Microsoft Fabric (lakehouse, PySpark notebook) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 30 (shot p30-01)

Tested in Fabric workspace `demo_ws` on the Fabric trial on Oct 30, 2026.

A notebook, `demo_batched_load`, loads five batches of generic `table_a` rows into `dbo.table_a_batched`. One batch, `batch_03`, fails on purpose with a `SchemaMismatchError` (its `value` column arrives as text). The loader retries once, records every attempt in a run log, keeps going with the other batches and ends with the list of batches to replay.

## What it shows

| # | Capability | Where |
|---|---|---|
| 1 | Loading in batches, one append per batch | `load_batch()` |
| 2 | One retry per batch, then record the failure and move on | the `MAX_ATTEMPTS` loop |
| 3 | A run log with entity, batch key, attempt, rows in, rows written, duration and error class | the displayed table |
| 4 | A replay list: batches with no successful attempt | last line of output |

Data is generic: entity `table_a` with columns `id`, `segment` (A, B, C), `attribute_a` (a1 to a5) and `value`, generated in the notebook with a fixed seed (42).

## Contents

```
fabric/notebooks/demo_batched_load.py   notebook cell, paste into a PySpark notebook (also runs locally as a dry run)
NOTES.md                                technical notes and verified values
```

## Prerequisites

- A workspace on a **Fabric trial** or a **Fabric capacity** (an F2 is enough). Tested on the Fabric trial.
- A lakehouse to attach as the notebook's default lakehouse. `demo_ws` used `demo_mlv_lh` (schema-enabled, so the table lands in `dbo`). Any scratch lakehouse works; with schemas off, change `TARGET` to `table_a_batched`.
- Contributor (or higher) on the workspace.

## Setup

1. In the workspace, create a PySpark notebook named `demo_batched_load`.
2. Attach your lakehouse as the default lakehouse.
3. Paste `fabric/notebooks/demo_batched_load.py` into one cell.

## Run

Run the cell once. To try it without Fabric: `python3 fabric/notebooks/demo_batched_load.py` runs a dry run with no Spark and prints the same log and summary (nothing is written).

## Expected output

The run log has 6 rows, because `batch_03` is tried twice:

| entity | batch_key | attempt | rows_in | rows_written | error_class |
|---|---|---|---|---|---|
| table_a | batch_01 | 1 | 1127 | 1127 | |
| table_a | batch_02 | 1 | 1155 | 1155 | |
| table_a | batch_03 | 1 | 1001 | 0 | SchemaMismatchError |
| table_a | batch_03 | 2 | 1001 | 0 | SchemaMismatchError |
| table_a | batch_04 | 1 | 990 | 990 | |
| table_a | batch_05 | 1 | 946 | 946 | |

`duration_s` depends on the run. The last line is:

```
Batches loaded: 4 of 5. Replay from: ['batch_03']
```

After one run, `dbo.table_a_batched` should hold 4 218 rows (the four loaded batches).

## Caveats

- The failure is simulated: `load_batch()` raises `SchemaMismatchError` for `batch_03` before writing anything. It stands in for a file whose `value` column arrives as text.
- Each run appends. Running the cell again adds the same rows again; drop the table first (see cleanup) for a clean re-run.
- The replay list is printed, not stored. In a real loader you would write the run log to a table and drive the replay from it.

## Cost and cleanup

**Cost:** free on the Fabric trial. On a paid capacity (an F2 is enough) one run is a few minutes of capacity time; there is no other billable resource. **Pause the capacity when you're done.**

**Cleanup:** keep the scratch workspace, lakehouse and notebook (repo convention). Stop the notebook session after the run. To reset the demo table, run `DROP TABLE IF EXISTS dbo.table_a_batched` in a Spark SQL cell. On a paid capacity, pause it in the Azure portal.
