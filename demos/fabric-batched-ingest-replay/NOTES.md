# NOTES: fabric-batched-ingest-replay

## Where it ran

- Fabric workspace `demo_ws`, on the Fabric trial, Oct 30, 2026.
- Notebook `demo_batched_load`, default lakehouse `demo_mlv_lh` (schema-enabled), target `dbo.table_a_batched`.
- Local dry run (Python 3, no Spark) on Oct 30, 2026, for the row counts.

## Verified values

| Check | Result | Where |
|---|---|---|
| Final line | `Batches loaded: 4 of 5. Replay from: ['batch_03']` | `demo_ws`, notebook output, and local dry run |
| `batch_03` attempts | 2, both `SchemaMismatchError` | `demo_ws`, notebook output, and local dry run |
| Rows in per batch | 1127, 1155, 1001, 990, 946 | local dry run (same seed, so the same counts in Fabric) |
| Rows written | 4 218 (batches 01, 02, 04, 05) | local dry run |

## Technical notes

- The rows are generated with `random.seed(42)` before any Spark call, so the batch sizes are the same in Fabric and locally.
- `MAX_ATTEMPTS = 2` means one retry. A schema mismatch fails the same way on retry, which is the point: retries help transient errors, not bad data, so the batch goes on the replay list.
- The replay list is the set of batch keys with a failed attempt and no successful one.
- `batch_size` and the target table are good candidates for a Variable Library, see `fabric-variable-library-targets`.
