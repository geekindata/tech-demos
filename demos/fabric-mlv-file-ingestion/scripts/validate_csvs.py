#!/usr/bin/env python3
"""Sanity-check the generated CSV batches: header, consistent column count per
row, unique non-null order_ids, parseable dates/numbers, and the expected
number of rule-breaking rows. Exits non-zero on any problem."""
import csv, sys
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = ["order_id", "order_date", "customer_id", "country", "channel",
        "product_sku", "product_name", "quantity", "unit_price"]
EXPECT = {"orders_batch_01.csv": (BASE, 40, 2),
          "orders_batch_02.csv": (BASE, 35, 3),
          "orders_batch_03.csv": (BASE + ["discount_code"], 30, 2)}
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
        d = dict(zip(cols, r))
        date.fromisoformat(d["order_date"]); q = int(d["quantity"]); p = float(d["unit_price"])
        if d["order_id"]:
            if d["order_id"] in seen: errors.append(f"{name}:{i} duplicate {d['order_id']}")
            seen.add(d["order_id"])
        if not d["order_id"] or q <= 0 or p < 0: bad += 1
    if bad != n_bad: errors.append(f"{name}: {bad} bad rows, expected {n_bad}")
    print(f"{name}: {len(rows)} rows, {len(cols)} cols, {bad} rule-breaking rows")
if errors:
    print("FAIL"); print("\n".join(errors)); sys.exit(1)
print("OK: all batches valid")
