#!/usr/bin/env python3
"""Build fabric/notebooks/mlv_file_ingestion_demo.ipynb from sql/*.sql.
Each SQL statement becomes its own %%sql cell (Spark SQL) so it can be run step by step."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql"

def md(text): return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}
def sql(text): return {"cell_type": "code", "metadata": {"microsoft": {"language": "sparksql"}},
                       "execution_count": None, "outputs": [],
                       "source": ("%%sql\n" + text.strip("\n")).splitlines(True)}

def statements(path):
    chunks = re.split(r";[ \t]*(?:--[^\n]*)?\n", path.read_text())
    cells, pending = [], ""
    for c in chunks:
        if any(l.strip() and not l.strip().startswith("--") for l in c.splitlines()):
            cells.append((pending + c).strip("\n") + ";"); pending = ""
        elif c.strip():
            if cells: cells[-1] += "\n" + c.strip("\n")
            else: pending += c
    return cells

STEPS = [
    ("## 0. Setup\nAttach this notebook to a **schema-enabled lakehouse** (Fabric Runtime 1.3). "
     "Before running anything, find/replace `<workspace>` and `<lakehouse>` in the bronze cell, or paste "
     "the ABFS path of `Files/mlv_demo/orders/` (Lakehouse explorer > folder `...` > Copy ABFS path). "
     "Upload **only `orders_batch_01.csv`** to `Files/mlv_demo/orders/` first.", "00_setup_schemas.sql"),
    ("## 1. Bronze: file-ingesting MLV (`USING OneLake_Files`, DYNAMIC, APPEND_ONLY)", "01_bronze_raw_orders.sql"),
    ("## 2. Silver: typed + validated (`CONSTRAINT ... ON MISMATCH DROP`)", "02_silver_orders.sql"),
    ("## 3. Gold: aggregate", "03_gold_sales_by_country.sql"),
    ("## 4. Inspect (re-run this section after every refresh)\n"
     "Expected numbers per step are in `expected/EXPECTED.md`. Cell (e) only returns `discount_code` "
     "after batch 3; before that it errors with an unresolved column, which is expected.", "04_inspect.sql"),
    ("## Refresh between batches\nUpload the next batch to the same folder, then refresh. Preferred: "
     "Lakehouse > **Materialized lake views > Manage > Run** (ad-hoc, *Refresh with dependant lineage*) so "
     "the run shows *files processed / rows added*. Notebook fallback below (FULL, in dependency order). "
     "Then re-run section 4.", "06_refresh_full_optional.sql"),
    ("## 5. After batch 3: evolve silver deliberately + new gold view", "05_after_batch3_silver_v2.sql"),
    ("## 99. Cleanup (run only when done)", "99_cleanup.sql"),
]

cells = [md("# Fabric MLV file ingestion demo: files → bronze → silver → gold\n"
            "Spark SQL cells. Run top to bottom, following README.md for the upload/refresh order. "
            "Every statement cites the Microsoft Learn page or blog it was taken from.")]
for title, f in STEPS:
    cells.append(md(title))
    cells += [sql(s) for s in statements(SQL / f)]

nb = {"nbformat": 4, "nbformat_minor": 5,
      "metadata": {"kernel_info": {"name": "synapse_pyspark"},
                   "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark"},
                   "language_info": {"name": "python"},
                   "microsoft": {"language": "python", "language_group": "synapse_pyspark"}},
      "cells": cells}
out = ROOT / "fabric" / "notebooks" / "mlv_file_ingestion_demo.ipynb"
out.write_text(json.dumps(nb, indent=1))
print(f"wrote {out} with {len(cells)} cells")
