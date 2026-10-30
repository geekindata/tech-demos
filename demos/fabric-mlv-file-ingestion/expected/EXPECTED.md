# Expected outputs (computed locally with DuckDB emulation)

Bronze = all rows of all files uploaded so far (DYNAMIC schema = union by column name).
Silver = bronze rows passing all three constraints. Gold = SUMs/COUNTs over silver.


## After file_001.csv is uploaded and the lineage is refreshed

**Bronze columns:** `id`, `segment`, `attribute_a`, `value`, `__filepath__`

**Rows per file (bronze vs silver):**

| file | bronze_rows | silver_rows | dropped_rows |
|---|---|---|---|
| file_001.csv | 40 | 38 | 2 |

**Totals:** bronze = 40, silver = 38, dropped = 2

**Rows dropped by silver constraints:**

| file | id | segment | value | violated_constraint |
|---|---|---|---|---|
| file_001.csv |  | A | 25.00 | id_not_null |
| file_001.csv | 1040 | A | -12.50 | non_negative_value |

**gold.value_by_segment:**

| segment | row_count | total_value |
|---|---|---|
| A | 13 | 657.50 |
| B | 11 | 522.50 |
| C | 14 | 705.00 |


## After file_002.csv is uploaded and the lineage is refreshed

**Bronze columns:** `id`, `segment`, `attribute_a`, `value`, `__filepath__`

**Rows per file (bronze vs silver):**

| file | bronze_rows | silver_rows | dropped_rows |
|---|---|---|---|
| file_001.csv | 40 | 38 | 2 |
| file_002.csv | 35 | 32 | 3 |

**Totals:** bronze = 75, silver = 70, dropped = 5

**Rows dropped by silver constraints:**

| file | id | segment | value | violated_constraint |
|---|---|---|---|---|
| file_001.csv |  | A | 25.00 | id_not_null |
| file_001.csv | 1040 | A | -12.50 | non_negative_value |
| file_002.csv |  | A | 60.00 | id_not_null |
| file_002.csv | 2034 | X | 40.00 | known_segment |
| file_002.csv | 2033 | A | -37.50 | non_negative_value |

**gold.value_by_segment:**

| segment | row_count | total_value |
|---|---|---|
| A | 27 | 1313.00 |
| B | 24 | 1013.50 |
| C | 19 | 982.50 |


## After file_003.csv is uploaded and the lineage is refreshed

**Bronze columns:** `id`, `segment`, `attribute_a`, `value`, `attribute_b`, `__filepath__`

**Rows per file (bronze vs silver):**

| file | bronze_rows | silver_rows | dropped_rows |
|---|---|---|---|
| file_001.csv | 40 | 38 | 2 |
| file_002.csv | 35 | 32 | 3 |
| file_003.csv | 30 | 28 | 2 |

**Totals:** bronze = 105, silver = 98, dropped = 7

**Rows dropped by silver constraints:**

| file | id | segment | value | violated_constraint |
|---|---|---|---|---|
| file_001.csv |  | A | 25.00 | id_not_null |
| file_001.csv | 1040 | A | -12.50 | non_negative_value |
| file_002.csv |  | A | 60.00 | id_not_null |
| file_002.csv | 2034 | X | 40.00 | known_segment |
| file_002.csv | 2033 | A | -37.50 | non_negative_value |
| file_003.csv | 3029 | X | 25.00 | known_segment |
| file_003.csv | 3030 | B | -20.00 | non_negative_value |

**gold.value_by_segment:**

| segment | row_count | total_value |
|---|---|---|
| A | 37 | 1619.00 |
| B | 33 | 1642.50 |
| C | 28 | 1369.50 |

**gold.value_by_attribute_b (after silver v2 adds attribute_b):**

| attribute_b | row_count | total_value |
|---|---|---|
| (none) | 82 | 4001.00 |
| b1 | 8 | 399.00 |
| b2 | 2 | 121.00 |
| b3 | 6 | 110.00 |

**bronze attribute_b population per file** (files 1-2 predate the column, so NULL; empty values in file 3 are also NULL):

| file | rows | rows_with_attribute_b |
|---|---|---|
| file_001.csv | 40 | 0 |
| file_002.csv | 35 | 0 |
| file_003.csv | 30 | 17 |

