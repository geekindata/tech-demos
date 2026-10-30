# Notes: fabric-mlv-file-ingestion

Kit built 30 Oct 2026 for the Fabric preview feature *file data ingestion with materialized lake views* (`USING OneLake_Files`).

> **Status: not yet run in Fabric.** The SQL follows the Microsoft Learn MLV docs and the Fabric blog as read on 30 Oct 2026. Every number below comes from a local DuckDB emulation (`scripts/expected_outputs.py`), not from a Fabric run. Update this file with the live results after the first run in Fabric.

## How it works (from WRITEUP.md)

- Bronze is one statement: `CREATE MATERIALIZED LAKE VIEW bronze.raw_orders USING OneLake_Files OPTIONS ('format'='csv', 'path'='<folder>', 'header'='true')`.
- `schema_mode = DYNAMIC` (default) adds new columns and fills NULL for older files; `FIXED` pins the schema at CREATE and rejects drift.
- `refresh_mode = APPEND_ONLY` adds rows from new files; `FULL` reprocesses the folder; `MIRROR` reflects additions and deletions.
- `__filepath__` records the source file per row, so row counts can be reconciled per file.
- Silver is a table-based MLV with three `ON MISMATCH DROP` constraints: `order_id IS NOT NULL`, `quantity > 0`, `unit_price >= 0`. It keeps `__filepath__` as `source_file`.
- Gold aggregates order lines, units and revenue per country. Fabric refreshes bronze → silver → gold in dependency order and shows it all in one lineage graph.
- Batch 3 adds `discount_code`. Bronze absorbs it; silver stays a deliberate contract and is only changed in step 8 (silver v2 plus `gold.discount_usage`).

## Expected numbers (local emulation)

| After | Bronze rows | Silver rows | Dropped (cumulative) |
|---|---|---|---|
| Batch 01 (CREATE) | 40 | 38 | 2 |
| Batch 02 + refresh | 75 | 70 | 5 |
| Batch 03 + refresh | 105 | 98 | 7 |

Per file: batch 01 40 → 38, batch 02 35 → 32, batch 03 30 → 28.

Dropped rows: batch 01 NULL `order_id`, ORD-10040 qty −1; batch 02 NULL `order_id`, ORD-10133 qty −2, ORD-10134 qty 0; batch 03 ORD-10229 price −149.00, ORD-10230 qty −4.

`gold.sales_by_country` after batch 03 (order_lines / units / revenue_nok):

| Country | Lines | Units | Revenue NOK |
|---|---|---|---|
| DK | 25 | 45 | 41 705.00 |
| FI | 19 | 29 | 27 221.00 |
| NO | 21 | 45 | 30 855.00 |
| SE | 33 | 57 | 37 943.00 |
| **Total** | **98** | **176** | **137 724.00** |

`gold.discount_usage` after silver v2: `(none)` 81 / 117 352.00, AUTUMN10 5 / 10 192.00, FREESHIP 7 / 4 938.00, MEMBER15 5 / 5 242.00.

In the lineage run details, APPEND_ONLY should show 1 file / 35 rows after batch 02 and 1 file / 30 rows after batch 03. The notebook `FULL` fallback reprocesses everything (2 files / 75 rows, then 3 files / 105 rows).

Full per-step tables are in `expected/EXPECTED.md` and `expected/*.csv`.

## Open questions to verify in Fabric

See *Doc uncertainties* in `README.md`. The main ones: whether `__filepath__` is present without an `AS SELECT`, whether gold survives `CREATE OR REPLACE` of silver, and whether lineage shows per-run or cumulative dropped counts.
