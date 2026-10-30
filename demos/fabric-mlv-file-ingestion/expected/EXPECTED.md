# Expected outputs (computed locally with DuckDB emulation)

Bronze = all rows of all files uploaded so far (DYNAMIC schema = union by column name).
Silver = bronze rows passing all three constraints. Gold = SUMs/COUNTs over silver.


## After batch 01 is uploaded and the lineage is refreshed

**Bronze columns:** `order_id`, `order_date`, `customer_id`, `country`, `channel`, `product_sku`, `product_name`, `quantity`, `unit_price`, `__filepath__`

**Rows per file (bronze vs silver):**

| file | bronze_rows | silver_rows | dropped_rows |
|---|---|---|---|
| orders_batch_01.csv | 40 | 38 | 2 |

**Totals:** bronze = 40, silver = 38, dropped = 2

**Rows dropped by silver constraints:**

| file | order_id | quantity | unit_price | violated_constraint |
|---|---|---|---|---|
| orders_batch_01.csv |  | 1 | 399.00 | order_id_not_null |
| orders_batch_01.csv | ORD-10040 | -1 | 749.00 | positive_quantity |

**gold.sales_by_country:**

| country | order_lines | units | revenue_nok |
|---|---|---|---|
| DK | 11 | 22 | 18328.00 |
| FI | 6 | 11 | 10339.00 |
| NO | 9 | 15 | 6935.00 |
| SE | 12 | 21 | 13329.00 |


## After batch 02 is uploaded and the lineage is refreshed

**Bronze columns:** `order_id`, `order_date`, `customer_id`, `country`, `channel`, `product_sku`, `product_name`, `quantity`, `unit_price`, `__filepath__`

**Rows per file (bronze vs silver):**

| file | bronze_rows | silver_rows | dropped_rows |
|---|---|---|---|
| orders_batch_01.csv | 40 | 38 | 2 |
| orders_batch_02.csv | 35 | 32 | 3 |

**Totals:** bronze = 75, silver = 70, dropped = 5

**Rows dropped by silver constraints:**

| file | order_id | quantity | unit_price | violated_constraint |
|---|---|---|---|---|
| orders_batch_01.csv |  | 1 | 399.00 | order_id_not_null |
| orders_batch_01.csv | ORD-10040 | -1 | 749.00 | positive_quantity |
| orders_batch_02.csv |  | 3 | 149.00 | order_id_not_null |
| orders_batch_02.csv | ORD-10133 | -2 | 299.00 | positive_quantity |
| orders_batch_02.csv | ORD-10134 | 0 | 399.00 | positive_quantity |

**gold.sales_by_country:**

| country | order_lines | units | revenue_nok |
|---|---|---|---|
| DK | 19 | 36 | 34464.00 |
| FI | 12 | 17 | 16183.00 |
| NO | 17 | 34 | 13916.00 |
| SE | 22 | 37 | 26713.00 |


## After batch 03 is uploaded and the lineage is refreshed

**Bronze columns:** `order_id`, `order_date`, `customer_id`, `country`, `channel`, `product_sku`, `product_name`, `quantity`, `unit_price`, `discount_code`, `__filepath__`

**Rows per file (bronze vs silver):**

| file | bronze_rows | silver_rows | dropped_rows |
|---|---|---|---|
| orders_batch_01.csv | 40 | 38 | 2 |
| orders_batch_02.csv | 35 | 32 | 3 |
| orders_batch_03.csv | 30 | 28 | 2 |

**Totals:** bronze = 105, silver = 98, dropped = 7

**Rows dropped by silver constraints:**

| file | order_id | quantity | unit_price | violated_constraint |
|---|---|---|---|---|
| orders_batch_01.csv |  | 1 | 399.00 | order_id_not_null |
| orders_batch_01.csv | ORD-10040 | -1 | 749.00 | positive_quantity |
| orders_batch_02.csv |  | 3 | 149.00 | order_id_not_null |
| orders_batch_02.csv | ORD-10133 | -2 | 299.00 | positive_quantity |
| orders_batch_02.csv | ORD-10134 | 0 | 399.00 | positive_quantity |
| orders_batch_03.csv | ORD-10229 | 1 | -149.00 | non_negative_price |
| orders_batch_03.csv | ORD-10230 | -4 | 299.00 | positive_quantity |

**gold.sales_by_country:**

| country | order_lines | units | revenue_nok |
|---|---|---|---|
| DK | 25 | 45 | 41705.00 |
| FI | 19 | 29 | 27221.00 |
| NO | 21 | 45 | 30855.00 |
| SE | 33 | 57 | 37943.00 |

**gold.discount_usage (after silver v2 adds discount_code):**

| discount_code | order_lines | revenue_nok |
|---|---|---|
| (none) | 81 | 117352.00 |
| AUTUMN10 | 5 | 10192.00 |
| FREESHIP | 7 | 4938.00 |
| MEMBER15 | 5 | 5242.00 |

**bronze discount_code population per file** (batches 1-2 predate the column, so NULL; empty values in batch 3 are also NULL):

| file | rows | rows_with_code |
|---|---|---|
| orders_batch_01.csv | 40 | 0 |
| orders_batch_02.csv | 35 | 0 |
| orders_batch_03.csv | 30 | 19 |

