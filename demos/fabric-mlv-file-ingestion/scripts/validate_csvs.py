#!/usr/bin/env python3
"""Sanity-check the generated CSV files: header, consistent column count per
row, unique non-null ids, parseable numbers, and the expected number of
rule-breaking rows. Exits non-zero on any problem."""
import csv, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = ["id", "segment", "attribute_a", "value"]
EXPECT = {"file_001.csv": (BASE, 40, 2),
          "file_002.csv": (BASE, 35, 3),
          "file_003.csv": (BASE + ["attribute_b"], 30, 2)}
errors, seen = [], set()
for name, (cols, n_rows, n_bad) in EXPECT.items():
    raw = (DATA / name).read_bytes()
    if b"\r" in raw: errors.append(f"{name}: CRLF line endings")
    with open(DATA / name, newline="", encoding="utf-8") as f:
        rd = csv.reader(f); header = next(rd); rows = list(rd)
    if header != cols: errors.append(f"{name}: header {header}")
    if len(rows) != n_rows: errors.append(f"{name}: {len(rows)} rows, expected {n_rows}")
    bad = 0
    for i, r in enumerate(rows, 2):
        if len(r) != len(cols): errors.append(f"{name}:{i} has {len(r)} fields"); continue
        d = dict(zip(cols, r)); v = float(d["value"])
        if d["id"]:
            if d["id"] in seen: errors.append(f"{name}:{i} duplicate id {d['id']}")
            seen.add(d["id"])
        if not d["id"] or v < 0 or d["segment"] not in ("A", "B", "C"): bad += 1
    if bad != n_bad: errors.append(f"{name}: {bad} bad rows, expected {n_bad}")
    print(f"{name}: {len(rows)} rows, {len(cols)} cols, {bad} rule-breaking rows")
if errors:
    print("FAIL"); print("\n".join(errors)); sys.exit(1)
print("OK: all files valid")
