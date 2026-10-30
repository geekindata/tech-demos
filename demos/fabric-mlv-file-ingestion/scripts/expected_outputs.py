#!/usr/bin/env python3
"""Emulate bronze/silver/gold logic locally with DuckDB to compute the expected
results after each step of the demo. This is an approximation of Fabric's
behaviour (DYNAMIC schema ~ union_by_name, ON MISMATCH DROP ~ WHERE filter);
it is NOT Fabric. Writes expected/*.csv and expected/EXPECTED.md.
Requires: pip install duckdb
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "expected"
OUT.mkdir(exist_ok=True)
FILES = ["orders_batch_01.csv", "orders_batch_02.csv", "orders_batch_03.csv"]

SILVER_RULES = """
    order_id IS NOT NULL AND CAST(quantity AS INT) > 0
    AND CAST(unit_price AS DECIMAL(10,2)) >= 0
"""

md = ["# Expected outputs (computed locally with DuckDB emulation)\n",
      "Bronze = all rows of all files uploaded so far (DYNAMIC schema = union by column name).",
      "Silver = bronze rows passing all three constraints. Gold = SUMs/COUNTs over silver.\n"]

def table_md(rel):
    cols = rel.columns
    rows = rel.fetchall()
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    return "\n".join(out)

for step in (1, 2, 3):
    con = duckdb.connect()
    paths = [str(DATA / f) for f in FILES[:step]]
    con.execute(f"""
        CREATE TABLE bronze AS
        SELECT * REPLACE (parse_filename(filename) AS filename)
        FROM read_csv({paths}, header=true, union_by_name=true, filename=true, all_varchar=true)
    """)
    con.execute("ALTER TABLE bronze RENAME COLUMN filename TO __filepath__")
    con.execute(f"""
        CREATE TABLE silver AS SELECT
          order_id, CAST(order_date AS DATE) AS order_date, customer_id, country, channel,
          product_sku, product_name, CAST(quantity AS INT) AS quantity,
          CAST(unit_price AS DECIMAL(10,2)) AS unit_price,
          CAST(quantity AS INT) * CAST(unit_price AS DECIMAL(10,2)) AS line_amount,
          {"discount_code," if step == 3 else ""}
          __filepath__ AS source_file
        FROM bronze WHERE {SILVER_RULES}
    """)
    md.append(f"\n## After batch {step:02d} is uploaded and the lineage is refreshed\n")
    md.append("**Bronze columns:** `" + "`, `".join(c for c in con.table("bronze").columns) + "`\n")

    per_file = con.sql(f"""
        SELECT b.__filepath__ AS file, b.bronze_rows, COALESCE(s.silver_rows,0) AS silver_rows,
               b.bronze_rows - COALESCE(s.silver_rows,0) AS dropped_rows
        FROM (SELECT __filepath__, COUNT(*) bronze_rows FROM bronze GROUP BY 1) b
        LEFT JOIN (SELECT source_file, COUNT(*) silver_rows FROM silver GROUP BY 1) s
          ON s.source_file = b.__filepath__
        ORDER BY 1""")
    per_file.write_csv(str(OUT / f"step{step}_rows_per_file.csv"))
    md.append("**Rows per file (bronze vs silver):**\n\n" + table_md(per_file) + "\n")

    totals = con.sql("""SELECT (SELECT COUNT(*) FROM bronze) AS bronze_rows,
                               (SELECT COUNT(*) FROM silver) AS silver_rows""").fetchall()[0]
    md.append(f"**Totals:** bronze = {totals[0]}, silver = {totals[1]}, dropped = {totals[0]-totals[1]}\n")

    dropped = con.sql(f"""
        SELECT __filepath__ AS file, order_id, quantity, unit_price,
          CASE WHEN order_id IS NULL THEN 'order_id_not_null'
               WHEN CAST(quantity AS INT) <= 0 THEN 'positive_quantity'
               ELSE 'non_negative_price' END AS violated_constraint
        FROM bronze WHERE NOT ({SILVER_RULES}) OR order_id IS NULL
        ORDER BY 1, 5""")
    dropped.write_csv(str(OUT / f"step{step}_dropped_rows.csv"))
    md.append("**Rows dropped by silver constraints:**\n\n" + table_md(dropped) + "\n")

    gold = con.sql("""
        SELECT country, COUNT(*) AS order_lines, SUM(quantity) AS units,
               SUM(line_amount) AS revenue_nok
        FROM silver GROUP BY country ORDER BY country""")
    gold.write_csv(str(OUT / f"step{step}_gold_sales_by_country.csv"))
    md.append("**gold.sales_by_country:**\n\n" + table_md(gold) + "\n")

    if step == 3:
        disc = con.sql("""SELECT COALESCE(discount_code,'(none)') AS discount_code,
               COUNT(*) AS order_lines, SUM(line_amount) AS revenue_nok
               FROM silver GROUP BY 1 ORDER BY 1""")
        disc.write_csv(str(OUT / "step3_gold_discount_usage.csv"))
        md.append("**gold.discount_usage (after silver v2 adds discount_code):**\n\n" + table_md(disc) + "\n")
        nulls = con.sql("""SELECT __filepath__ AS file, COUNT(*) AS rows,
               COUNT(discount_code) AS rows_with_code FROM bronze GROUP BY 1 ORDER BY 1""")
        md.append("**bronze discount_code population per file** (batches 1-2 predate the column, so NULL; "
                  "empty values in batch 3 are also NULL):\n\n" + table_md(nulls) + "\n")
    con.close()

(OUT / "EXPECTED.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
