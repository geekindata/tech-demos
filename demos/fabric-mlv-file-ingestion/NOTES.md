# Notes: fabric-mlv-file-ingestion

Kit built 30 Oct 2026 for the Fabric preview feature *file data ingestion with materialized lake views* (`USING OneLake_Files`).

Tested in Fabric demo_ws on <date>

The SQL follows the Microsoft Learn MLV docs and the Fabric blog as read on 30 Oct 2026. The numbers below come from a local DuckDB emulation (`scripts/expected_outputs.py` for the full kit, the same logic for the quick run). Compare them with the live results.

## Objects

- In `demo_ws`, lakehouse `demo_mlv_lh` (schema-enabled): `bronze.table_a`, MLV `silver.table_a_clean`, MLV `gold.value_by_segment`. The full kit (`sql/`, `mlv_file_ingestion_demo.ipynb`) uses these names; folder `Files/mlv_demo/table_a/`.
- The self-contained quick run (`fabric/notebooks/table_a_files_notebook.txt` / `.ipynb`) creates new objects only: `bronze.table_a_files`, `silver.table_a_files_clean`, `gold.value_by_segment_files`; folder `Files/mlv_demo/table_a_files/`.

## How it works (from WRITEUP.md)

- Bronze is one statement: `CREATE MATERIALIZED LAKE VIEW bronze.table_a USING OneLake_Files OPTIONS ('format'='csv', 'path'='<folder>', 'header'='true')`.
- `schema_mode = DYNAMIC` (default) adds new columns and fills NULL for older files; `FIXED` pins the schema at CREATE and rejects drift.
- `refresh_mode = APPEND_ONLY` adds rows from new files; `FULL` reprocesses the folder; `MIRROR` reflects additions and deletions.
- `__filepath__` records the source file per row, so row counts can be reconciled per file.
- Silver is a table-based MLV with three `ON MISMATCH DROP` constraints: `id IS NOT NULL`, `value >= 0`, `segment IN ('A','B','C')`. It keeps `__filepath__` as `source_file`.
- Gold counts rows and sums `value` per segment. Fabric refreshes bronze → silver → gold in dependency order and shows it all in one lineage graph. A notebook `REFRESH … FULL` doesn't cascade, so the notebooks refresh each view in order.
- file_003 adds `attribute_b`. Bronze absorbs it; silver stays a deliberate contract and is only changed in step 8 (silver v2 plus `gold.value_by_attribute_b`).

## Quick run: expected numbers

| After | Bronze rows | Silver rows | Dropped | gold.value_by_segment_files (row_count / total_value) |
|---|---|---|---|---|
| file_001 (CREATE) | 7 | 5 | 2 (NULL id; value −4.00) | A 2 / 30.00 · B 2 / 20.00 · C 1 / 30.00 |
| file_002 + FULL refresh | 11 | 8 | 3 (+ segment X) | A 3 / 42.00 · B 3 / 28.00 · C 2 / 55.00 |

## Full kit: expected numbers

| After | Bronze rows | Silver rows | Dropped (cumulative) |
|---|---|---|---|
| file_001 (CREATE) | 40 | 38 | 2 |
| file_002 + refresh | 75 | 70 | 5 |
| file_003 + refresh | 105 | 98 | 7 |

Per file: file_001 40 → 38, file_002 35 → 32, file_003 30 → 28.

Dropped rows: file_001 NULL `id` (A, 25.00), id 1040 value −12.50; file_002 NULL `id` (A, 60.00), id 2033 value −37.50, id 2034 segment X; file_003 id 3029 segment X, id 3030 value −20.00.

`gold.value_by_segment` (row_count / total_value):

| Segment | After file_001 | After file_002 | After file_003 |
|---|---|---|---|
| A | 13 / 657.50 | 27 / 1 313.00 | 37 / 1 619.00 |
| B | 11 / 522.50 | 24 / 1 013.50 | 33 / 1 642.50 |
| C | 14 / 705.00 | 19 / 982.50 | 28 / 1 369.50 |
| **Total** | 38 / 1 885.00 | 70 / 3 309.00 | **98 / 4 631.00** |

Bronze `attribute_b`: 0 rows populated in file_001 and file_002 (column absent, NULL), 17 of 30 in file_003.

`gold.value_by_attribute_b` after silver v2: `(none)` 82 / 4 001.00, b1 8 / 399.00, b2 2 / 121.00, b3 6 / 110.00.

In the lineage run details, APPEND_ONLY should show 1 file / 35 rows after file_002 and 1 file / 30 rows after file_003. The notebook `FULL` fallback reprocesses everything (2 files / 75 rows, then 3 files / 105 rows). Silver dropped counts: 2, then 3 per run or 5 cumulative, then 2 per run or 7 cumulative.

Full per-step tables are in `expected/EXPECTED.md` and `expected/*.csv`.

## Open questions to verify in Fabric

See *Doc uncertainties* in `README.md`. The main ones: whether `__filepath__` is present without an `AS SELECT`, whether gold survives `CREATE OR REPLACE` of silver, whether lineage shows per-run or cumulative dropped counts, and whether the `${demo.table_a_files_path}` substitution in the quick run's bronze cell is accepted (fallback: paste the printed path).
