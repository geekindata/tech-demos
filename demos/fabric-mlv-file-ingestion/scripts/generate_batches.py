#!/usr/bin/env python3
"""Generate three small, deterministic CSV batches of orders for the Fabric MLV
file-ingestion demo.

- orders_batch_01.csv / orders_batch_02.csv: base schema (9 columns)
- orders_batch_03.csv: same columns + a new trailing column `discount_code`
  (schema drift for DYNAMIC schema mode)
- Each batch contains a few rows that should be DROPPED by the silver
  constraints: empty order_id (NULL), quantity <= 0, or negative unit_price.

Usage:  python3 scripts/generate_batches.py   (writes to ../data/)
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261030
OUT = Path(__file__).resolve().parent.parent / "data"

BASE_COLS = ["order_id", "order_date", "customer_id", "country", "channel",
             "product_sku", "product_name", "quantity", "unit_price"]

PRODUCTS = [  # sku, name, unit price (NOK)
    ("SKU-1001", "Wool hiking socks", 149.00),
    ("SKU-1002", "Insulated water bottle", 299.00),
    ("SKU-1003", "Merino base layer", 899.00),
    ("SKU-1004", "Trekking poles", 749.00),
    ("SKU-1005", "Headlamp 400lm", 399.00),
    ("SKU-1006", "Down jacket", 2499.00),
]
COUNTRIES = ["NO", "SE", "DK", "FI"]
CHANNELS = ["web", "store", "app"]
DISCOUNTS = ["", "", "", "AUTUMN10", "MEMBER15", "FREESHIP"]

# Batch spec: (file, start order number, n_good_rows, first date, n_days, bad rows)
# Bad rows: list of (kind) where kind in {"null_id", "neg_qty", "zero_qty", "neg_price"}
BATCHES = [
    ("orders_batch_01.csv", 10001, 38, date(2026, 10, 1), 7, ["null_id", "neg_qty"]),
    ("orders_batch_02.csv", 10101, 32, date(2026, 10, 8), 7, ["neg_qty", "zero_qty", "null_id"]),
    ("orders_batch_03.csv", 10201, 28, date(2026, 10, 15), 7, ["neg_price", "neg_qty"]),
]


def make_row(rng, order_no, d0, ndays):
    sku, name, price = rng.choice(PRODUCTS)
    return {
        "order_id": f"ORD-{order_no}",
        "order_date": (d0 + timedelta(days=rng.randrange(ndays))).isoformat(),
        "customer_id": f"C{rng.randint(1, 60):04d}",
        "country": rng.choice(COUNTRIES),
        "channel": rng.choice(CHANNELS),
        "product_sku": sku,
        "product_name": name,
        "quantity": rng.choice([1, 1, 1, 2, 2, 3, 4]),
        "unit_price": f"{price:.2f}",
    }


def main():
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (fname, start, n_good, d0, ndays, bad) in enumerate(BATCHES, start=1):
        cols = BASE_COLS + (["discount_code"] if i == 3 else [])
        rows, no = [], start
        for _ in range(n_good):
            r = make_row(rng, no, d0, ndays); no += 1
            rows.append(r)
        for kind in bad:
            r = make_row(rng, no, d0, ndays); no += 1
            if kind == "null_id":
                r["order_id"] = ""          # empty CSV field -> NULL
            elif kind == "neg_qty":
                r["quantity"] = -r["quantity"]
            elif kind == "zero_qty":
                r["quantity"] = 0
            elif kind == "neg_price":
                r["unit_price"] = f"-{r['unit_price']}"
            rows.append(r)
        rng.shuffle(rows)  # bad rows are not all at the bottom
        if i == 3:
            for r in rows:
                r["discount_code"] = rng.choice(DISCOUNTS)
        with open(OUT / fname, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {fname}: {len(rows)} rows ({len(bad)} expected to fail silver rules)")


if __name__ == "__main__":
    main()
