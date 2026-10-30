# Notes: dabs-dev-vs-prod

## Documented behaviour (not yet verified hands-on)

The bundle has not been deployed yet: on 30 Oct 2026 the box had no CLI authentication for the Azure Databricks workspace. Fill in this section after the first deploy.

- `mode: development` prefixes resource names with `[dev ${workspace.current_user.short_name}]` and pauses schedules and triggers ([Databricks docs: bundle deployment modes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/deployment-modes)).
- `mode: production` validates that `run_as` / permissions are set and does not change names or schedules.
- A notebook task with no compute settings runs on serverless jobs compute. `environment_key` is not accepted on notebook tasks (it is for Python script, wheel and dbt tasks).

## To verify after deploy

- [ ] `databricks jobs list` shows `[dev <user>] demo_daily_job` with schedule `PAUSED`.
- [ ] `databricks jobs list` shows `demo_daily_job` (prod) with schedule `UNPAUSED`.
- [ ] Job ids noted here (no host or workspace id).
