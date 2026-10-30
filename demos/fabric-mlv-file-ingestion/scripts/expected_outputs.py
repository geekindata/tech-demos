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
FILES = ["file_001.csv", "file_002.csv", "file_003.csv"]

SILVER_RULES = """
    id IS NOT NULL AND CAST(value AS DECIMAL(10,2)) >= 0 AND segment IN ('A','B','C')
"""

md = ["# Expected outputs (computed locally with DuckDB emulation)\n",
      "Bronze = all rows of all files uploaded so far (DYNAMIC schema = union by column name).",
      "Silver = bronze rows passing all three constraints. Gold = SUMs/COUNTs over silver.\n"]


def table_md(rel):
    cols, rows = rel.columns, rel.fetchall()
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
          CAST(id AS INT) AS id, segment, attribute_a,
          CAST(value AS DECIMAL(10,2)) AS value,
          {"attribute_b," if step == 3 else ""}
          __filepath__ AS source_file
        FROM bronze WHERE {SILVER_RULES}
    """)
    md.append(f"\n## After file_{step:03d}.csv is uploaded and the lineage is refreshed\n")
    md.append("**Bronze columns:** `" + "`, `".join(con.table("bronze").columns) + "`\n")

    per_file = con.sql("""
        SELECT b.__filepath__ AS file, b.bronze_rows, COALESCE(s.silver_rows,0) AS silver_rows,
               b.bronze_rows - COALESCE(s.silver_rows,0) AS dropped_rows
        FROM (SELECT __filepath__, COUNT(*) bronze_rows FROM bronze GROUP BY 1) b
        LEFT JOIN (SELECT source_file, COUNT(*) silver_rows FROM silver GROUP BY 1) s
          ON s.source_file = b.__filepath__
        ORDER BY 1""")
    per_file.write_csv(str(OUT / f"step{step}_rows_per_file.csv"))
    md.append("**Rows per file (bronze vs silver):**\n\n" + table_md(per_file) + "\n")

    totals = con.sql("""SELECT (SELECT COUNT(*) FROM bronze), (SELECT COUNT(*) FROM silver)""").fetchall()[0]
    md.append(f"**Totals:** bronze = {totals[0]}, silver = {totals[1]}, dropped = {totals[0]-totals[1]}\n")

    dropped = con.sql(f"""
        SELECT __filepath__ AS file, id, segment, value,
          CASE WHEN id IS NULL THEN 'id_not_null'
               WHEN CAST(value AS DECIMAL(10,2)) < 0 THEN 'non_negative_value'
               ELSE 'known_segment' END AS violated_constraint
        FROM bronze WHERE NOT ({SILVER_RULES}) OR id IS NULL
        ORDER BY 1, 5, 2""")
    dropped.write_csv(str(OUT / f"step{step}_dropped_rows.csv"))
    md.append("**Rows dropped by silver constraints:**\n\n" + table_md(dropped) + "\n")

    gold = con.sql("""
        SELECT segment, COUNT(*) AS row_count, SUM(value) AS total_value
        FROM silver GROUP BY segment ORDER BY segment""")
    gold.write_csv(str(OUT / f"step{step}_gold_value_by_segment.csv"))
    md.append("**gold.value_by_segment:**\n\n" + table_md(gold) + "\n")

    if step == 3:
        b = con.sql("""SELECT COALESCE(attribute_b,'(none)') AS attribute_b,
               COUNT(*) AS row_count, SUM(value) AS total_value
               FROM silver GROUP BY 1 ORDER BY 1""")
        b.write_csv(str(OUT / "step3_gold_value_by_attribute_b.csv"))
        md.append("**gold.value_by_attribute_b (after silver v2 adds attribute_b):**\n\n" + table_md(b) + "\n")
        nulls = con.sql("""SELECT __filepath__ AS file, COUNT(*) AS rows,
               COUNT(attribute_b) AS rows_with_attribute_b FROM bronze GROUP BY 1 ORDER BY 1""")
        md.append("**bronze attribute_b population per file** (files 1-2 predate the column, so NULL; "
                  "empty values in file 3 are also NULL):\n\n" + table_md(nulls) + "\n")
    con.close()

(OUT / "EXPECTED.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
