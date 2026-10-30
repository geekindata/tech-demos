# Your bronze layer is now one SQL statement: file ingestion with Fabric Materialized Lake Views

Most Fabric medallion projects I see have the same awkward first mile. Silver and gold are tidy and declarative, but getting raw files into the first Delta table still means a pipeline, a Copy job or a notebook somebody has to own. Microsoft has now put that first mile into preview: **materialized lake views (MLVs) can ingest CSV and Parquet files directly from OneLake**.

## What it is

An MLV is a Spark SQL definition that Fabric materializes as a Delta table, refreshes for you and tracks in a lineage graph. Until now an MLV had to read from tables. The new form swaps the `AS SELECT … FROM` for a source description:

```sql
CREATE MATERIALIZED LAKE VIEW bronze.raw_orders
USING OneLake_Files
OPTIONS (
    'format' = 'csv',
    'path'   = 'abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/mlv_demo/orders/',
    'header' = 'true'
)
TBLPROPERTIES (
    'schema_mode'  = 'DYNAMIC',
    'refresh_mode' = 'APPEND_ONLY'
);
```

The path can be a folder, which is read recursively, a OneLake folder shortcut, or a single file. Two table properties set the behaviour:

- **`schema_mode`**: `DYNAMIC`, the default, adds newly discovered columns and fills `NULL` where a file doesn't have them. `FIXED` pins the schema at creation and rejects drift.
- **`refresh_mode`**: `APPEND_ONLY` adds rows from new files, `FULL` reprocesses the folder as a snapshot, and `MIRROR` reflects both file additions and deletions.

Rows can carry a `__filepath__` column recording which file they came from. You can also add a FROM-less `AS SELECT` to cast, filter or project during ingestion.

## Why it simplifies bronze

The real gain isn't fewer lines of code. Bronze becomes part of the same dependency graph as everything downstream:

- **One orchestration model.** Fabric knows that silver reads bronze and bronze reads a folder, and it refreshes them in that order. There's no pipeline-then-notebook handoff to schedule and no glue to keep in step.
- **One lineage graph.** The graph starts at a source-folder node. You can select it to see the files discovered, and drill into a run to see *files processed* and *rows added*.
- **Same data quality and monitoring** as table-based MLVs: `ON MISMATCH DROP | FAIL` constraints and dropped-row counts in lineage.
- **Schema drift handled where it belongs.** Bronze absorbs a new column automatically, while silver stays an explicit contract you change on purpose.

## The demo

The kit is three small order files for an outdoor-gear retailer selling in Norway, Sweden, Denmark and Finland, plus four views.

1. **Bronze**: the statement above, pointed at `Files/mlv_demo/orders/`.
2. **Silver**: a table-based MLV over bronze that casts types, computes `line_amount` and enforces three rules with `ON MISMATCH DROP`: `order_id IS NOT NULL`, `quantity > 0` and `unit_price >= 0`. It also keeps `__filepath__` as `source_file`.
3. **Gold**: order lines, units and revenue per country.

The run goes like this:

- **Batch 1** (40 rows) is uploaded and the views are created. Bronze holds 40 rows and silver 38. One row with a missing order ID and one with a negative quantity are dropped, and the silver node in lineage shows the drop count.
- **Batch 2** (35 rows) lands in the same folder and you trigger a run from the lineage view. The run details for bronze show one file processed and 35 rows added. `GROUP BY __filepath__` reconciles 40 + 35 rows to the two files, and silver now drops five rows in total.
- **Batch 3** (30 rows) adds a `discount_code` column. After the refresh, `DESCRIBE` on bronze shows the new column. Rows from the first two files have `NULL` there, with no DDL and no pipeline change. Silver keeps working unchanged because it selects named columns.
- **Contract change.** When the business wants discount reporting, `CREATE OR REPLACE` silver to include `discount_code` and add a `gold.discount_usage` view. The lineage graph grows a second gold leaf.

Final state: 105 bronze rows, 98 silver rows and 7 dropped, each traceable to its file and rule.

## Caveats while it's in preview

- **Preview means preview.** Syntax and behaviour can change. Test on a throwaway lakehouse, not a client's production workspace.
- **Prerequisites:** Fabric capacity or trial, and a lakehouse with schemas enabled. The get-started guide lists Fabric Runtime 1.3.
- **Formats:** CSV and Parquet only.
- **Paths:** no spaces or `%20`. Community users also report that wildcards and partial file-name filters don't work, so arrange folders to match what you want ingested.
- **`FIXED` schema** fails if the folder already holds files with different schemas when you create the view.
- **Shortcuts:** managed refresh only discovers new files at the shortcut root, not in nested shortcut folders.
- **Don't orchestrate refresh from notebooks.** Use lineage runs and schedules. The minimum schedule interval is five minutes, and session-level `spark.conf` settings don't apply to scheduled refreshes.
- **Documentation gaps:** the docs are inconsistent in places, for example on whether `__filepath__` must be projected and on how many CSV options are supported. Verify before promising anything to a client.

## Where I'd use it

Use it for landing zones fed by file drops, such as ERP extracts and partner feeds, where bronze is really just "read everything in this folder". Keep pipelines for API calls, cross-cloud movement and non-SQL steps.

*Sources: Microsoft Fabric blog "File Data Ingestion with Materialized Lake Views in Microsoft Fabric (Preview)" and the Microsoft Learn MLV documentation (overview, Spark SQL reference, data quality, refresh, lineage), October 2026.*
