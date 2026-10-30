# Notes: dabs-dev-vs-prod

## Documented behaviour

- `mode: development` prefixes resource names with `[dev ${workspace.current_user.short_name}]` and pauses schedules and triggers ([Databricks docs: bundle deployment modes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/deployment-modes)). As tested below, a schedule set to `UNPAUSED` explicitly stays active.
- `mode: production` validates that `run_as` / permissions are set and does not change names or schedules.
- A notebook task with no compute settings runs on serverless jobs compute. `environment_key` is not accepted on notebook tasks (it is for Python script, wheel and dbt tasks).

## Tested in an Azure Databricks Premium workspace (Oct 30, 2026)
- Serverless compute for workflows was disabled there, so the first deploy failed with "Serverless compute for workflows is not enabled in the workspace". Adding `existing_cluster_id` to the task fixed it.
- Dev mode added the `[dev <user>]` prefix and a dev tag as expected. It did not pause the schedule, because the YAML sets `pause_status: UNPAUSED` explicitly.
- Bundle-managed jobs lock the Pause button in the UI. Change `pause_status` in the YAML and redeploy instead.
- With no `run_as` set, prod runs as the deploying user. For real prod, set `run_as` to a service principal.
- Deployed to both `dev` and `prod`. The Jobs list showed `[dev <user>] demo_daily_job` and `demo_daily_job` side by side (shot p50-01).
- After the shot, both jobs were paused. The YAML in this repo still has `pause_status: UNPAUSED`, so set it to `PAUSED` before any redeploy.
