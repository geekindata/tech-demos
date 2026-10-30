# Conventions

## Layout

Each demo lives in `demos/<slug>/`. The slug is short, lowercase and hyphenated, with **no date in the folder name**. The date goes in the demo's README or NOTES.

```
demos/<slug>/
  README.md      what it shows, prerequisites, how to run, cost and cleanup
  NOTES.md       technical notes and verified numbers (say where each was verified)
  fabric/        Git-synced Fabric items for this demo's workspace only
  databricks/    databricks.yml, resources/, src/
  data/          small sample CSVs only
  screenshots/   cropped, anonymised PNGs, with a README.md caption per file
```

Only include the folders a demo needs. Extra subfolders such as `sql/`, `scripts/` or `expected/` are fine when they make the demo easier to follow.

## Environments, cost and cleanup

- Demos run in scratch environments (a scratch Fabric workspace, a scratch Databricks workspace or schema).
- Scratch environments are **kept, not deleted**, so demos can be re-run and re-shot.
- Compute is **always paused or stopped after use**: pause the Fabric capacity, terminate clusters, stop SQL warehouses, and make sure no jobs are running.
- Every README states the expected cost and the cleanup steps.

## What never goes in the repo

- Secrets, keys, tokens, passwords or connection strings.
- Tenant, subscription, workspace, capacity or object IDs (GUIDs).
- Email addresses or personal names from the environment.
- Environment URLs: workspace hosts, portal links, OneLake paths with real names. Use placeholders such as `<workspace>` and `<lakehouse>`. Links to public documentation are fine.
- Large or real data. `data/` holds small, generated sample CSVs only.

Screenshots are cropped to the relevant panel and have names, emails, IDs and URLs removed or blurred before they are committed. Raw captures stay out of the repo (`raw/` is git-ignored).

## Databricks bundles

- `databricks.yml` defines at least a `dev` target and never hard-codes a host. Use a CLI profile or a variable.
- Catalog and schema names are parameters, not literals.

## Pull requests

Work on `dev`, then open a PR to `main`. The PR template checklist applies to every PR.
