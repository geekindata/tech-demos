# Fabric demo: file data ingestion with Materialized Lake Views (Preview)

**Platform:** Microsoft Fabric (lakehouse, Spark SQL) · **Date:** 30 Oct 2026 · **Status:** not yet run in Fabric

A ready-to-run kit that builds a full **files → bronze → silver → gold** medallion in a Fabric lakehouse
using only Spark SQL materialized lake views (MLVs). No pipeline, no Copy job, no notebook loader for bronze.

Built 30 Oct 2026 against these sources (read that day):
- Blog: [File Data Ingestion with Materialized Lake Views in Microsoft Fabric (Preview)](https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801)
- [Overview of materialized lake views](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view)
- [Spark SQL reference for MLVs](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view) (incl. *Ingest files with `USING OneLake_Files`*)
- [Get started](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/get-started-with-materialized-lake-views) · [Data quality](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/data-quality) · [Refresh](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view) · [Schedule / ad-hoc run](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/schedule-lineage-run) · [Lineage](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/view-lineage)

The kit has **not** been run in a Fabric tenant. The syntax is taken from the docs above, and the expected
numbers come from a local DuckDB emulation. Read *Doc uncertainties* before a live demo.

## What it shows

| # | Capability | Where |
|---|---|---|
| 1 | Bronze in one statement: `USING OneLake_Files` on a folder of CSVs | `sql/01_bronze_raw_orders.sql` |
| 2 | `refresh_mode = APPEND_ONLY`: a new file in the folder gets picked up on the next refresh | steps 5–6 |
| 3 | `schema_mode = DYNAMIC`: batch 3 adds `discount_code`, bronze gains the column, older rows get NULL | step 8 |
| 4 | `__filepath__`: row counts reconciled to each source file | `sql/04_inspect.sql` (a, b) |
| 5 | Silver data quality: `CONSTRAINT … ON MISMATCH DROP` removes bad rows; lineage shows dropped counts | `sql/02_silver_orders.sql` |
| 6 | Gold aggregate refreshed in dependency order | `sql/03_gold_sales_by_country.sql` |
| 7 | Lineage from the source-folder node to gold, plus files processed and rows added per run | Manage → lineage |
| 8 | Deliberate contract change: silver v2 adds the new column, and a new gold view uses it | `sql/05_after_batch3_silver_v2.sql` |

## Contents

```
data/        orders_batch_01.csv (40 rows), orders_batch_02.csv (35), orders_batch_03.csv (30, + discount_code)
scripts/     generate_batches.py   – deterministic generator (seed 20261030)
             validate_csvs.py      – header/row/type checks
             expected_outputs.py   – DuckDB emulation -> expected/
             build_notebook.py     – builds the .ipynb from sql/
sql/         00..06, 99 – one file per step, every statement cites its doc page
fabric/notebooks/mlv_file_ingestion_demo.ipynb
             – same SQL as %%sql (Spark SQL) cells, for Import notebook
expected/    EXPECTED.md + per-step CSVs (rows per file, dropped rows, gold)
WRITEUP.md   blog-ready write-up
NOTES.md     technical notes and verified (locally emulated) numbers
```

To regenerate locally: `python3 scripts/generate_batches.py && python3 scripts/validate_csvs.py && python3 scripts/expected_outputs.py && python3 scripts/build_notebook.py` (the last two need `pip install duckdb` for the emulation only).

## Prerequisites

- A workspace on **Fabric capacity** or a **Fabric trial** ("A workspace with a Fabric-enabled capacity", from Get started).
- A **lakehouse with Lakehouse schemas enabled** on **Fabric Runtime 1.3** (Get started prerequisites). Use a new, throwaway lakehouse, for example `MlvDemoLH`.
- Contributor (or higher) on the workspace, so you can create items and run schedules.
- **No spaces** in the workspace or lakehouse names used in the ABFS path. The docs say "Source paths containing a raw space or `%20` aren't currently accepted." If the workspace name has spaces, use the GUID form of the path (see uncertainty #5).
- Schema names must not be all uppercase. This kit uses `bronze`, `silver` and `gold`.

### Preview limitations worth saying out loud (from the docs and blog)
- Only CSV and Parquet. A folder is ingested recursively, or you can target a single file.
- `FIXED` schema fails if the folder already holds files with different schemas at CREATE time.
- Folder shortcut sources: managed refresh only discovers new files at the shortcut root, not in nested shortcut folders.
- Don't set the Spark CSV `mode` option, because Fabric manages malformed rows. Use `columnNameOfCorruptRecord` to capture them instead.
- The blog says CSV parsing supports `header` and `delimiter`, with more on the roadmap, but the Spark SQL reference now lists many more options. This kit uses only `format`, `path` and `header`.
- Refresh schedules have a 5-minute minimum interval. Notebook-session `spark.conf.set` settings don't apply to scheduled refreshes.
- Community comment, not docs: wildcards and partial file-name filters in `path` don't work.

## Step-by-step run (about 20–30 minutes)

> Upload **one batch at a time**. If you upload all three files before step 3, the CREATE ingests everything at once and the incremental story is lost.

1. **Create the folder.** In the lakehouse explorer, under **Files**, create `mlv_demo/orders/`.
2. **Upload batch 1.** Upload `data/orders_batch_01.csv` into `Files/mlv_demo/orders/`.
3. **Import the notebook.** In the workspace, go to *Import → Notebook → From this computer* and pick `fabric/notebooks/mlv_file_ingestion_demo.ipynb`. Attach it to the lakehouse. In the bronze cell, replace `<workspace>` and `<lakehouse>`, or paste the folder's **Copy ABFS path** (folder `…` menu) and keep the trailing `/`.
   Alternative: open *Materialized lake views → New → New notebook → Create with Spark SQL* and paste the `sql/` files in order.
4. **Create the views.** Run sections **0 → 3** (schemas, bronze, silver, gold), then section **4 (Inspect)**. Cell 4(e) will error because `discount_code` doesn't exist yet. That's expected.
   → Compare with *After batch 01* below.
5. **Open the lineage.** In the lakehouse, go to **Materialized lake views → Manage** (select the refresh icon if the graph is empty). You should see `source folder → bronze.raw_orders → silver.orders → gold.sales_by_country`.
6. **Upload batch 2, then refresh.** Upload `orders_batch_02.csv` to the same folder. In the lineage toolbar, select **Run** → name it `after-batch-02` → *Refresh with dependant lineage* (selecting gold pulls in its upstream views) → **Run**. You can also create a schedule and select **Run** next to it. Watch it in **Recent runs**.
   Notebook fallback: run the *Refresh between batches* cells (`REFRESH … FULL` in dependency order).
   Then re-run section 4 and compare with *After batch 02*.
7. **Upload batch 3, then refresh** the same way (run name `after-batch-03`). Re-run section 4. This time 4(d) `DESCRIBE` should list **`discount_code`**, and 4(e) should work.
8. **Evolve silver.** Run section **5**. `CREATE OR REPLACE` silver v2 adds `discount_code`, then `gold.discount_usage` is created. If gold doesn't update automatically, run the lineage again. Lineage now has two gold leaves.
9. **Optional:** create a time-based schedule (Manage schedules → New schedule) to show hands-off refresh. Upload a copy of a batch under a new name to see it get picked up. Note that this changes the expected numbers.

## What to look for in the lineage view

- **Source folder node** (the first node). Select it to see the OneLake path and the files discovered in the folder: 1, then 2, then 3.
- **bronze.raw_orders node.** Its details show format `csv`, schema mode `DYNAMIC` and refresh mode `APPEND_ONLY`.
- **Recent runs → drill into a run → select bronze.** You'll see **Files processed** and **Rows added**. With APPEND_ONLY, a run after batch 2 should show **1 file / 35 rows**, and after batch 3 **1 file / 30 rows**. Files processed counts what *that run* ingested, not what's in the folder, and a run with no new files reports 0. If you used the notebook `FULL` fallback, bronze reprocesses the whole folder, so expect 2 files / 75 rows, then 3 files / 105 rows.
- **silver.orders node.** Shows the **dropped-records count** from the `ON MISMATCH DROP` constraints. Expect 2 after the first refresh. Later runs show either the per-run count (3, then 2) or the cumulative count (5, then 7), depending on whether the run was incremental or full. The docs don't say which is displayed (uncertainty #4).
- The **CDF banner**: Fabric may suggest *Activate CDF* for views that could refresh incrementally. That's fine to accept in a demo.

## Expected outputs per step

Computed by `scripts/expected_outputs.py`. Full tables are in `expected/`. In Fabric, `__filepath__` holds the full OneLake path, so the inspect queries strip it down to the file name.

**After batch 01 (CREATE)**: bronze 40, silver 38, **dropped 2**, with 9 data columns + `__filepath__`.

| file | bronze | silver | dropped | why dropped |
|---|---|---|---|---|
| orders_batch_01.csv | 40 | 38 | 2 | NULL order_id; ORD-10040 qty −1 |

gold.sales_by_country: DK 11 / 22 / 18 328.00 · FI 6 / 11 / 10 339.00 · NO 9 / 15 / 6 935.00 · SE 12 / 21 / 13 329.00 *(order_lines / units / revenue_nok)*

**After batch 02 + refresh**: bronze 75, silver 70, **dropped 5**.

| file | bronze | silver | dropped | why dropped |
|---|---|---|---|---|
| orders_batch_01.csv | 40 | 38 | 2 | (as above) |
| orders_batch_02.csv | 35 | 32 | 3 | NULL order_id; ORD-10133 qty −2; ORD-10134 qty 0 |

gold: DK 19 / 36 / 34 464.00 · FI 12 / 17 / 16 183.00 · NO 17 / 34 / 13 916.00 · SE 22 / 37 / 26 713.00

**After batch 03 + refresh**: bronze 105, silver 98, **dropped 7**. Bronze now has **`discount_code`** (11 columns including `__filepath__`).

| file | bronze | silver | dropped | rows with discount_code | why dropped |
|---|---|---|---|---|---|
| orders_batch_01.csv | 40 | 38 | 2 | 0 (NULL, column didn't exist) | |
| orders_batch_02.csv | 35 | 32 | 3 | 0 | |
| orders_batch_03.csv | 30 | 28 | 2 | 19 (11 empty → NULL) | ORD-10229 price −149.00; ORD-10230 qty −4 |

gold.sales_by_country: DK 25 / 45 / 41 705.00 · FI 19 / 29 / 27 221.00 · NO 21 / 45 / 30 855.00 · SE 33 / 57 / 37 943.00 (total 98 lines, 137 724.00 NOK)

**After step 8 (silver v2)**: gold.discount_usage: `(none)` 81 / 117 352.00 · AUTUMN10 5 / 10 192.00 · FREESHIP 7 / 4 938.00 · MEMBER15 5 / 5 242.00. Silver still has 98 rows, and gold.sales_by_country is unchanged.

Gold totals stay correct no matter which refresh strategy Fabric picks. Optimal refresh only changes how much work a run does, not the result.

## Doc uncertainties (verify live before presenting)

1. **`__filepath__` without `AS SELECT`.** The Spark SQL reference example says "Each row also gets a `__filepath__` column", and the blog runs `GROUP BY __filepath__` on a bronze view defined without `AS SELECT`. The overview, though, says to *project* `__filepath__` "when you need per-row file traceability". If `__filepath__` isn't present on bronze, add `AS SELECT order_id, …, __filepath__` to bronze. That pins the column list, so DYNAMIC may then not surface `discount_code`. **Unverified**, and so is how DYNAMIC interacts with an explicit projection. Also unverified: reading `__filepath__` from a *downstream* table-based MLV (silver).
2. **Replacing silver while gold depends on it** (step 8). `CREATE OR REPLACE` is the documented way to change a definition, but the docs don't say whether dependents survive a replace. Fallback: drop the gold views, replace silver, recreate gold.
3. **Inferred types.** The default of `inferSchema` for OneLake_Files isn't documented. The kit casts explicitly in silver, so either default works.
4. **Dropped-count display** in lineage after incremental vs full runs. The docs only say "The lineage view shows the count of dropped records."
5. **Path forms.** Only the `abfss://<Workspace>@onelake.dfs.fabric.microsoft.com/<Lakehouse>.Lakehouse/Files/…/` name form appears in the docs. The GUID form (`abfss://<workspaceId>@onelake.dfs.fabric.microsoft.com/<lakehouseId>/Files/…`) is standard OneLake but not shown for this feature. The Copy ABFS path from the UI is the safest choice.
6. **Notebook refresh without `FULL`.** Only `REFRESH MATERIALIZED LAKE VIEW … FULL` is documented, so the kit doesn't use a bare `REFRESH`. Whether a notebook `REFRESH` cascades to dependents isn't stated, so the fallback refreshes each view explicitly in order.
7. **`COMMENT` on a file-ingesting view.** It's in the documented syntax block (between `OPTIONS` and `TBLPROPERTIES`) but not in the bronze example. Delete it if the parser complains.
8. **Runtime.** Get started says Runtime 1.3. The data-quality page mentions Runtime 2.0 for column-level checks, which this kit doesn't use. Whether file ingestion needs a particular runtime isn't stated.

## Cost and cleanup

**Cost:** runs on an existing Fabric capacity (an F2 is enough) or a Fabric trial. A run takes about 20–30 minutes of capacity time; there is no other billable resource. **Pause the capacity when you're done.**

**Cleanup:** keep the scratch workspace (repo convention), but remove the demo objects:


Run section **99** (`sql/99_cleanup.sql`), which drops gold, then silver, then bronze. Delete any schedule you created (*Manage schedules* → trash icon), then delete `Files/mlv_demo/` in the explorer. Simplest of all is to delete the throwaway lakehouse. Don't modify the `_mlv_system` schema while the lakehouse is still in use.

Finally, pause the Fabric capacity (Azure portal → the Fabric capacity → Pause) unless something else needs it.
