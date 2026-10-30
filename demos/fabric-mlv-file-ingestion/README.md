# Fabric demo: file data ingestion with Materialized Lake Views (Preview)

**Platform:** Microsoft Fabric (lakehouse, Spark SQL) · **Date:** 30 Oct 2026 · **Status:** see *Tested* below

A ready-to-run kit that builds a full **files → bronze → silver → gold** medallion in a Fabric lakehouse
using only Spark SQL materialized lake views (MLVs). No pipeline, no Copy job, no notebook loader for bronze.

Built 30 Oct 2026 against these sources (read that day):
- Blog: [File Data Ingestion with Materialized Lake Views in Microsoft Fabric (Preview)](https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/file-data-ingestion-with-materialized-lake-views-in-microsoft-fabric-preview/5367801)
- [Overview of materialized lake views](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view)
- [Spark SQL reference for MLVs](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view) (incl. *Ingest files with `USING OneLake_Files`*)
- [Get started](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/get-started-with-materialized-lake-views) · [Data quality](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/data-quality) · [Refresh](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/refresh-materialized-lake-view) · [Schedule / ad-hoc run](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/schedule-lineage-run) · [Lineage](https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/view-lineage)

Tested in Fabric demo_ws on <date>

The syntax is taken from the docs above, and the expected numbers come from a local DuckDB emulation. Read *Doc uncertainties* before a live demo.

## What it shows

| # | Capability | Where |
|---|---|---|
| 1 | Bronze in one statement: `USING OneLake_Files` on a folder of CSVs | `sql/01_bronze_table_a.sql` |
| 2 | `refresh_mode = APPEND_ONLY`: a new file in the folder gets picked up on the next refresh | steps 5–6 |
| 3 | `schema_mode = DYNAMIC`: file_003 adds `attribute_b`, bronze gains the column, older rows get NULL | step 7 |
| 4 | `__filepath__`: row counts reconciled to each source file | `sql/04_inspect.sql` (a, b) |
| 5 | Silver data quality: `CONSTRAINT … ON MISMATCH DROP` removes bad rows; lineage shows dropped counts | `sql/02_silver_table_a_clean.sql` |
| 6 | Gold aggregate refreshed in dependency order | `sql/03_gold_value_by_segment.sql` |
| 7 | Lineage from the source-folder node to gold, plus files processed and rows added per run | Manage → lineage |
| 8 | Deliberate contract change: silver v2 adds the new column, and a new gold view uses it | `sql/05_after_file3_silver_v2.sql` |

All data is generic: one entity, `table_a`, with columns `id`, `segment` (A, B, C), `attribute_a` and `value`, plus `attribute_b` from file_003 on.

Object names match what already exists in Fabric `demo_ws`: lakehouse `demo_mlv_lh` (schema-enabled), `bronze.table_a`, MLV `silver.table_a_clean` and MLV `gold.value_by_segment`.

## Quick run: self-contained notebook

`fabric/notebooks/table_a_files_notebook.txt` is one paste-ready script (PySpark and `%%sql` cells, separated by `# =====` lines). The same cells are in `fabric/notebooks/table_a_files_notebook.ipynb` for *Import → Notebook*. Attach the notebook to `demo_mlv_lh` and run top to bottom. It needs no uploads and no edits:

1. Writes `file_001.csv` (7 rows) into `Files/mlv_demo/table_a_files/`, with the workspace and lakehouse names read from the notebook context.
2. Creates `bronze.table_a_files` (`USING OneLake_Files`, DYNAMIC, APPEND_ONLY), `silver.table_a_files_clean` (three `ON MISMATCH DROP` rules) and `gold.value_by_segment_files`.
3. Writes `file_002.csv` (4 rows) into the same folder and refreshes bronze, silver and gold in order.
4. Ends with `SELECT segment, row_count, total_value FROM gold.value_by_segment_files ORDER BY segment`.

These are new names, so nothing already in the lakehouse is touched. An optional schedule note and the cleanup statements are in the NOTE block near the end.

**Expected output of the last cell:**

| segment | row_count | total_value |
|---|---|---|
| A | 3 | 42.00 |
| B | 3 | 28.00 |
| C | 2 | 55.00 |

Along the way: after file_001, gold shows A 2 / 30.00, B 2 / 20.00, C 1 / 30.00. After file_002, rows per file are file_001.csv 7 bronze / 5 silver / 2 dropped (NULL `id`, negative `value`) and file_002.csv 4 / 3 / 1 dropped (segment `X`).

If the bronze cell rejects `${demo.table_a_files_path}`, replace it with the path printed by the first cell.

## Contents

```
data/        file_001.csv (40 rows), file_002.csv (35), file_003.csv (30, + attribute_b)
scripts/     generate_batches.py   – deterministic generator (seed 20261030)
             validate_csvs.py      – header/row/type checks
             expected_outputs.py   – DuckDB emulation -> expected/
             build_notebook.py     – builds both .ipynb files
sql/         00..06, 99 – one file per step of the full kit, every statement cites its doc page
fabric/notebooks/table_a_files_notebook.txt / .ipynb
             – self-contained quick run (new object names, see above)
fabric/notebooks/mlv_file_ingestion_demo.ipynb
             – the full kit as %%sql (Spark SQL) cells, for Import notebook
expected/    EXPECTED.md + per-step CSVs (rows per file, dropped rows, gold)
WRITEUP.md   blog-ready write-up
NOTES.md     technical notes and expected numbers
```

To regenerate locally: `python3 scripts/generate_batches.py && python3 scripts/validate_csvs.py && python3 scripts/expected_outputs.py && python3 scripts/build_notebook.py` (`expected_outputs.py` needs `pip install duckdb` for the emulation only).

## Prerequisites

- A workspace on **Fabric capacity** or a **Fabric trial** ("A workspace with a Fabric-enabled capacity", from Get started).
- A **lakehouse with Lakehouse schemas enabled** on **Fabric Runtime 1.3** (Get started prerequisites). This kit uses `demo_mlv_lh` in `demo_ws`; any scratch lakehouse works.
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

## Step-by-step run of the full kit (about 20–30 minutes)

> Upload **one file at a time**. If you upload all three files before step 3, the CREATE ingests everything at once and the incremental story is lost.
> The full kit uses the `demo_ws` names (`bronze.table_a`, `silver.table_a_clean`, `gold.value_by_segment`). Where those already exist, `IF NOT EXISTS` leaves them as they are; use the quick run above for a fresh set.

1. **Create the folder.** In the lakehouse explorer, under **Files**, create `mlv_demo/table_a/`.
2. **Upload file 1.** Upload `data/file_001.csv` into `Files/mlv_demo/table_a/`.
3. **Import the notebook.** In the workspace, go to *Import → Notebook → From this computer* and pick `fabric/notebooks/mlv_file_ingestion_demo.ipynb`. Attach it to the lakehouse. In the bronze cell, replace `<workspace>` and `<lakehouse>`, or paste the folder's **Copy ABFS path** (folder `…` menu) and keep the trailing `/`.
   Alternative: open *Materialized lake views → New → New notebook → Create with Spark SQL* and paste the `sql/` files in order.
4. **Create the views.** Run sections **0 → 3** (schemas, bronze, silver, gold), then section **4 (Inspect)**. Cell 4(e) will error because `attribute_b` doesn't exist yet. That's expected.
   → Compare with *After file_001* below.
5. **Open the lineage.** In the lakehouse, go to **Materialized lake views → Manage** (select the refresh icon if the graph is empty). You should see `source folder → bronze.table_a → silver.table_a_clean → gold.value_by_segment`.
6. **Upload file 2, then refresh.** Upload `file_002.csv` to the same folder. In the lineage toolbar, select **Run** → name it `after-file-002` → *Refresh with dependant lineage* (selecting gold pulls in its upstream views) → **Run**. You can also create a schedule and select **Run** next to it. Watch it in **Recent runs**.
   Notebook fallback: run the *Refresh between files* cells (`REFRESH … FULL` in dependency order).
   Then re-run section 4 and compare with *After file_002*.
7. **Upload file 3, then refresh** the same way (run name `after-file-003`). Re-run section 4. This time 4(d) `DESCRIBE` should list **`attribute_b`**, and 4(e) should work.
8. **Evolve silver.** Run section **5**. `CREATE OR REPLACE` silver v2 adds `attribute_b`, then `gold.value_by_attribute_b` is created. If gold doesn't update automatically, run the lineage again. Lineage now has two gold leaves.
9. **Optional:** create a time-based schedule (Manage schedules → New schedule) to show hands-off refresh. Upload a copy of a file under a new name to see it get picked up. Note that this changes the expected numbers.

## What to look for in the lineage view

- **Source folder node** (the first node). Select it to see the OneLake path and the files discovered in the folder: 1, then 2, then 3.
- **bronze.table_a node.** Its details show format `csv`, schema mode `DYNAMIC` and refresh mode `APPEND_ONLY`.
- **Recent runs → drill into a run → select bronze.** You'll see **Files processed** and **Rows added**. With APPEND_ONLY, a run after file 2 should show **1 file / 35 rows**, and after file 3 **1 file / 30 rows**. Files processed counts what *that run* ingested, not what's in the folder, and a run with no new files reports 0. If you used the notebook `FULL` fallback, bronze reprocesses the whole folder, so expect 2 files / 75 rows, then 3 files / 105 rows.
- **silver.table_a_clean node.** Shows the **dropped-records count** from the `ON MISMATCH DROP` constraints. Expect 2 after the first refresh. Later runs show either the per-run count (3, then 2) or the cumulative count (5, then 7), depending on whether the run was incremental or full. The docs don't say which is displayed (uncertainty #4).
- The **CDF banner**: Fabric may suggest *Activate CDF* for views that could refresh incrementally. That's fine to accept in a demo.

## Expected outputs per step (full kit)

Computed by `scripts/expected_outputs.py`. Full tables are in `expected/`. In Fabric, `__filepath__` holds the full OneLake path, so the inspect queries strip it down to the file name.

**After file_001 (CREATE)**: bronze 40, silver 38, **dropped 2**, with 4 data columns + `__filepath__`.

| file | bronze | silver | dropped | why dropped |
|---|---|---|---|---|
| file_001.csv | 40 | 38 | 2 | NULL id; id 1040 value −12.50 |

gold.value_by_segment: A 13 / 657.50 · B 11 / 522.50 · C 14 / 705.00 *(row_count / total_value)*

**After file_002 + refresh**: bronze 75, silver 70, **dropped 5**.

| file | bronze | silver | dropped | why dropped |
|---|---|---|---|---|
| file_001.csv | 40 | 38 | 2 | (as above) |
| file_002.csv | 35 | 32 | 3 | NULL id; id 2033 value −37.50; id 2034 segment X |

gold: A 27 / 1 313.00 · B 24 / 1 013.50 · C 19 / 982.50

**After file_003 + refresh**: bronze 105, silver 98, **dropped 7**. Bronze now has **`attribute_b`** (6 columns including `__filepath__`).

| file | bronze | silver | dropped | rows with attribute_b | why dropped |
|---|---|---|---|---|---|
| file_001.csv | 40 | 38 | 2 | 0 (NULL, column didn't exist) | |
| file_002.csv | 35 | 32 | 3 | 0 | |
| file_003.csv | 30 | 28 | 2 | 17 (13 empty → NULL) | id 3029 segment X; id 3030 value −20.00 |

gold.value_by_segment: A 37 / 1 619.00 · B 33 / 1 642.50 · C 28 / 1 369.50 (total 98 rows, 4 631.00)

**After step 8 (silver v2)**: gold.value_by_attribute_b: `(none)` 82 / 4 001.00 · b1 8 / 399.00 · b2 2 / 121.00 · b3 6 / 110.00. Silver still has 98 rows, and gold.value_by_segment is unchanged.

Gold totals stay correct no matter which refresh strategy Fabric picks. Optimal refresh only changes how much work a run does, not the result.

## Doc uncertainties (verify live before presenting)

1. **`__filepath__` without `AS SELECT`.** The Spark SQL reference example says "Each row also gets a `__filepath__` column", and the blog runs `GROUP BY __filepath__` on a bronze view defined without `AS SELECT`. The overview, though, says to *project* `__filepath__` "when you need per-row file traceability". If `__filepath__` isn't present on bronze, add `AS SELECT id, …, __filepath__` to bronze. That pins the column list, so DYNAMIC may then not surface `attribute_b`. **Unverified**, and so is how DYNAMIC interacts with an explicit projection. Also unverified: reading `__filepath__` from a *downstream* table-based MLV (silver).
2. **Replacing silver while gold depends on it** (step 8). `CREATE OR REPLACE` is the documented way to change a definition, but the docs don't say whether dependents survive a replace. Fallback: drop the gold views, replace silver, recreate gold.
3. **Inferred types.** The default of `inferSchema` for OneLake_Files isn't documented. The kit casts explicitly in silver, so either default works.
4. **Dropped-count display** in lineage after incremental vs full runs. The docs only say "The lineage view shows the count of dropped records."
5. **Path forms.** Only the `abfss://<Workspace>@onelake.dfs.fabric.microsoft.com/<Lakehouse>.Lakehouse/Files/…/` name form appears in the docs. The GUID form (`abfss://<workspaceId>@onelake.dfs.fabric.microsoft.com/<lakehouseId>/Files/…`) is standard OneLake but not shown for this feature. The Copy ABFS path from the UI is the safest choice.
6. **Notebook refresh without `FULL`.** Only `REFRESH MATERIALIZED LAKE VIEW … FULL` is documented, so the kit doesn't use a bare `REFRESH`. Whether a notebook `REFRESH` cascades to dependents isn't stated, so the fallback refreshes each view explicitly in order.
7. **`COMMENT` on a file-ingesting view.** It's in the documented syntax block (between `OPTIONS` and `TBLPROPERTIES`) but not in the bronze example. Delete it if the parser complains.
8. **Runtime.** Get started says Runtime 1.3. The data-quality page mentions Runtime 2.0 for column-level checks, which this kit doesn't use. Whether file ingestion needs a particular runtime isn't stated.

## Cost and cleanup

**Cost:** runs on an existing Fabric capacity (an F2 is enough) or a Fabric trial. A run takes about 20–30 minutes of capacity time; there is no other billable resource. **Pause the capacity when you're done.**

**Cleanup:** keep the scratch workspace and lakehouse (repo convention). For the quick run, use the cleanup statements in the NOTE block of `table_a_files_notebook.txt`, then delete `Files/mlv_demo/table_a_files/`. For the full kit, `sql/99_cleanup.sql` drops gold, then silver, then bronze; those names match the existing `demo_ws` objects, so only run it if you mean to remove them. Delete any schedule you created (*Manage schedules* → trash icon). Don't modify the `_mlv_system` schema while the lakehouse is still in use.

Finally, pause the Fabric capacity (Azure portal → the Fabric capacity → Pause) unless something else needs it.
