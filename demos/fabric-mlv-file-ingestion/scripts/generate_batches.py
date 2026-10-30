#!/usr/bin/env python3
"""Generate three small, deterministic CSV files of generic demo rows for the
Fabric MLV file-ingestion demo.

- file_001.csv / file_002.csv: base schema (id, segment, attribute_a, value)
- file_003.csv: same columns + a new trailing column `attribute_b`
  (schema drift for DYNAMIC schema mode)
- Each file contains a few rows that the silver constraints should DROP:
  empty id (NULL), negative value, or a segment outside A/B/C.

Usage:  python3 scripts/generate_batches.py   (writes to ../data/)
"""
import csv
import random
from pathlib import Path

SEED = 20261030
OUT = Path(__file__).resolve().parent.parent / "data"

BASE_COLS = ["id", "segment", "attribute_a", "value"]
SEGMENTS = ["A", "B", "C"]
ATTR_A = ["a1", "a2", "a3"]
ATTR_B = ["", "", "b1", "b2", "b3"]
VALUES = [10.00, 12.50, 20.00, 25.00, 40.00, 55.50]

# (file, first id, n_good_rows, bad row kinds) with kind in {"null_id", "neg_value", "bad_segment"}
FILES = [
    ("file_001.csv", 1001, 38, ["null_id", "neg_value"]),
    ("file_002.csv", 2001, 32, ["neg_value", "bad_segment", "null_id"]),
    ("file_003.csv", 3001, 28, ["bad_segment", "neg_value"]),
]


def make_row(rng, i):
    return {"id": str(i), "segment": rng.choice(SEGMENTS),
            "attribute_a": rng.choice(ATTR_A),
            "value": f"{rng.choice(VALUES) * rng.choice([1, 1, 2, 3]):.2f}"}


def main():
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    for n, (fname, start, n_good, bad) in enumerate(FILES, start=1):
        cols = BASE_COLS + (["attribute_b"] if n == 3 else [])
        rows, i = [], start
        for _ in range(n_good):
            rows.append(make_row(rng, i)); i += 1
        for kind in bad:
            r = make_row(rng, i); i += 1
            if kind == "null_id":
                r["id"] = ""                 # empty CSV field -> NULL
            elif kind == "neg_value":
                r["value"] = f"-{r['value']}"
            elif kind == "bad_segment":
                r["segment"] = "X"
            rows.append(r)
        rng.shuffle(rows)  # bad rows are not all at the bottom
        if n == 3:
            for r in rows:
                r["attribute_b"] = rng.choice(ATTR_B)
        with open(OUT / fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {fname}: {len(rows)} rows ({len(bad)} expected to fail silver rules)")


if __name__ == "__main__":
    main()
