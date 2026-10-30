# p30-01: demo batched load over table_a style data, one batch fails on purpose.
# Runs in a Fabric PySpark notebook (writes dbo.table_a_batched in the default lakehouse)
# and locally without Spark (dry run, counts only).
import random, time

try:
    spark  # noqa: F821  (present in Fabric notebooks)
    HAS_SPARK = True
except NameError:
    HAS_SPARK = False

ENTITY = "table_a"
TARGET = "dbo.table_a_batched"
BATCH_KEYS = ["batch_01", "batch_02", "batch_03", "batch_04", "batch_05"]
FAIL_BATCH = "batch_03"          # the one batch that fails on purpose
MAX_ATTEMPTS = 2                 # retry once, then record the failure

random.seed(42)

def make_rows(batch_key, n):
    seg = ["A", "B", "C"]
    return [(f"{batch_key}-{i:04d}", seg[i % 3], f"a{i % 5 + 1}", round(random.uniform(1, 100), 2))
            for i in range(n)]

class SchemaMismatchError(Exception):
    pass

def load_batch(batch_key, rows):
    if batch_key == FAIL_BATCH:
        # Simulated bad file: value column arrives as text in this batch
        raise SchemaMismatchError("column value: expected DOUBLE, found STRING")
    if HAS_SPARK:
        df = spark.createDataFrame(rows, "id string, segment string, attribute_a string, value double")  # noqa: F821
        df.write.mode("append").saveAsTable(TARGET)
    return len(rows)

log = []
for bk in BATCH_KEYS:
    rows = make_rows(bk, random.randint(800, 1200))
    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.time()
        try:
            written = load_batch(bk, rows)
            log.append((ENTITY, bk, attempt, len(rows), written, round(time.time() - t0, 2), ""))
            break
        except Exception as e:  # record and retry once
            log.append((ENTITY, bk, attempt, len(rows), 0, round(time.time() - t0, 2), type(e).__name__))

cols = ["entity", "batch_key", "attempt", "rows_in", "rows_written", "duration_s", "error_class"]
if HAS_SPARK:
    display(spark.createDataFrame(log, cols))  # noqa: F821
else:
    w = [max(len(str(r[i])) for r in log + [tuple(cols)]) for i in range(len(cols))]
    print("  ".join(c.ljust(w[i]) for i, c in enumerate(cols)))
    for r in log:
        print("  ".join(str(v).ljust(w[i]) for i, v in enumerate(r)))

failed = sorted({r[1] for r in log if r[6]} - {r[1] for r in log if not r[6]})
print(f"\nBatches loaded: {len(BATCH_KEYS) - len(failed)} of {len(BATCH_KEYS)}. Replay from: {failed}")
