#!/usr/bin/env python3
"""Build the two Fabric notebooks:
- fabric/notebooks/mlv_file_ingestion_demo.ipynb from sql/*.sql (step-by-step kit, one %%sql cell per statement)
- fabric/notebooks/table_a_files_notebook.ipynb from table_a_files_notebook.txt (self-contained run)"""
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
     "the ABFS path of `Files/mlv_demo/table_a/` (Lakehouse explorer > folder `...` > Copy ABFS path). "
     "Upload **only `file_001.csv`** to `Files/mlv_demo/table_a/` first.", "00_setup_schemas.sql"),
    ("## 1. Bronze: file-ingesting MLV (`USING OneLake_Files`, DYNAMIC, APPEND_ONLY)", "01_bronze_table_a.sql"),
    ("## 2. Silver: typed + validated (`CONSTRAINT ... ON MISMATCH DROP`)", "02_silver_table_a_clean.sql"),
    ("## 3. Gold: aggregate", "03_gold_value_by_segment.sql"),
    ("## 4. Inspect (re-run this section after every refresh)\n"
     "Expected numbers per step are in `expected/EXPECTED.md`. Cell (e) only returns `attribute_b` "
     "after file_003; before that it errors with an unresolved column, which is expected.", "04_inspect.sql"),
    ("## Refresh between files\nUpload the next file to the same folder, then refresh. Preferred: "
     "Lakehouse > **Materialized lake views > Manage > Run** (ad-hoc, *Refresh with dependant lineage*) so "
     "the run shows *files processed / rows added*. Notebook fallback below (FULL, in dependency order). "
     "Then re-run section 4.", "06_refresh_full_optional.sql"),
    ("## 5. After file_003: evolve silver deliberately + new gold view", "05_after_file3_silver_v2.sql"),
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
out.write_text(json.dumps(nb, indent=1) + "\n")
print(f"wrote {out} with {len(cells)} cells")

# Self-contained notebook: split the paste-ready text on its "# ===== CELL" separators.
src = (ROOT / "fabric" / "notebooks" / "table_a_files_notebook.txt").read_text()
parts = re.split(r"(?m)^# ===== (CELL|NOTE)[^\n]*\n", src)
cells2 = [md("# Fabric MLV file ingestion: self-contained run\n"
             "Attach to the schema-enabled lakehouse, run top to bottom. Source: `table_a_files_notebook.txt`.")]
for kind, body in zip(parts[1::2], parts[2::2]):
    body = body.strip("\n")
    if kind == "NOTE":
        cells2.append(md("\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.splitlines())))
    elif body.startswith("%%sql"):
        cells2.append({"cell_type": "code", "metadata": {"microsoft": {"language": "sparksql"}},
                       "execution_count": None, "outputs": [], "source": body.splitlines(True)})
    else:
        cells2.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                       "source": body.splitlines(True)})
nb2 = dict(nb, cells=cells2)
out2 = ROOT / "fabric" / "notebooks" / "table_a_files_notebook.ipynb"
out2.write_text(json.dumps(nb2, indent=1) + "\n")
print(f"wrote {out2} with {len(cells2)} cells")
