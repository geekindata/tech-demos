# Notes: databricks-apps-hello

## Status on 30 Oct 2026

Not deployed yet: the box had no CLI authentication for the Azure Databricks workspace, so Apps availability (`databricks apps list`) could not be checked.

## To verify after deploy

- [ ] `databricks apps list` works (Apps enabled in the workspace/region).
- [ ] Smallest compute size accepted by `apps create` (documented as `MEDIUM`; `LARGE` is the other option).
- [ ] Details page shows Running, URL, compute size, service principal and source code path.
- [ ] App stopped after the shot.
