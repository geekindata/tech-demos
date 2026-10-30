# NOTES: fabric-variable-library-targets

## Where it ran

- Fabric workspace `demo_ws`, on the Fabric trial, Oct 30, 2026.
- Items: Variable Library `demo_varlib`, PySpark notebook `demo_varlib_read` (no lakehouse attached).

## Verified values

| Check | Result | Where |
|---|---|---|
| Active value set | Test | `demo_ws` |
| `getLibrary("demo_varlib").target_lakehouse` | `demo_lakehouse_test` | `demo_ws`, notebook output |
| `get("$(/**/demo_varlib/batch_size)")` | `1000` | `demo_ws`, notebook output |

Not verified in Fabric: the output with Preprod or Prod active, and importing `fabric/demo_varlib/` through Git integration.

## Technical notes

- Two ways to read a value: the library object (`getLibrary(name).<variable>`) and a variable reference string (`$(/**/<library>/<variable>)`). Both return the active value set's value.
- Value set order comes from `settings.json` (`valueSetsOrder`). Defaults live in `variables.json`; each value set file only lists overrides.
- The variable names match the batched loader demo (`fabric-batched-ingest-replay`), where `batch_size` and the target are the kind of values that change per stage.
