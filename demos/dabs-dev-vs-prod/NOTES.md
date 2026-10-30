# Notes: dabs-dev-vs-prod

**Takeaway:** the identity that deploys a job and the identity that runs it are different things; put the run identity in the bundle as a service principal and keep its ID out of the repo.

## Documented behaviour

- `mode: development` prefixes resource names with `[dev ${workspace.current_user.short_name}]` and pauses schedules and triggers ([Databricks docs: bundle deployment modes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/deployment-modes)). As tested below, a schedule set to `UNPAUSED` explicitly stays active. (verified)
- `mode: production` validates that `run_as` / permissions are set and does not change names or schedules. (mirrored from docs)
- `run_as` accepts `user_name` or `service_principal_name` (the application ID). Setting a service principal requires the deployer to have the Service Principal User role on it. (mirrored from docs; not yet run here)
- Target `permissions` use `user_name`, `group_name` or `service_principal_name`, with levels such as CAN_VIEW, CAN_MANAGE_RUN and CAN_MANAGE; for jobs, the "Can Run" UI level is CAN_MANAGE_RUN. (mirrored from docs)
- Variables without a default must be passed: `--var="name=value"` or `BUNDLE_VAR_name`. (mirrored from docs)
- A notebook task with no compute settings runs on serverless jobs compute. `environment_key` is not accepted on notebook tasks. (verified)
- The workspace web terminal has the latest CLI preinstalled and authenticated as the current user; config profiles are not used there. Needs DBR 15.0+ and no PrivateLink. (mirrored from docs)

## Tested in an Azure Databricks Premium workspace (Oct 30, 2026)

- Serverless compute for workflows was disabled there, so the first deploy failed with "Serverless compute for workflows is not enabled in the workspace". Adding `existing_cluster_id` to the task fixed it.
- Dev mode added the `[dev <user>]` prefix and a dev tag as expected. It did not pause the schedule, because the YAML then set `pause_status: UNPAUSED` explicitly.
- Bundle-managed jobs lock the Pause button in the UI. Change `pause_status` in the YAML and redeploy instead.
- At that point prod had `run_as: user_name` = the deploying user. The Jobs list showed `[dev <user>] demo_daily_job` and `demo_daily_job` side by side (shot p50-01).
- After the shot, both jobs were paused. Since `b41c3c5` the repo YAML ships `pause_status: PAUSED`.

## Changed after the test (not yet deployed)

- Prod `run_as` is now `service_principal_name: ${var.prod_sp_app_id}`; the variable has no default and dev sets a dummy value it never uses.
- Prod `permissions`: CAN_MANAGE for the deploying user, CAN_VIEW for group `analysts`.
- `sql/grants_run_sp.sql`: USE CATALOG, USE SCHEMA, SELECT, MODIFY on the prod catalog only.
- Tested in Azure Databricks on <date>.

## Visual moments

- p50-02: job details with **Run as** = the service principal (mask the ID), then the Permissions dialog with you on Can Manage and `analysts` on Can View.
- p50-03: Catalog Explorer > the prod catalog > Permissions, showing the service principal with the four privileges and nothing on other catalogs.

## Open questions

- p50-02 in the shot audit expects groups on CAN_VIEW **and** CAN_RUN. The bundle has CAN_VIEW only, as asked. Add a CAN_MANAGE_RUN group entry if the shot needs it.
- Does the service principal need CAN ATTACH TO on the cluster when the workspace has serverless off? Expected yes for runs, not for deploy.

## Links

- Deployment modes: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/deployment-modes
- run_as: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as
- Bundle permissions: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/permissions
- Web terminal: https://learn.microsoft.com/en-us/azure/databricks/compute/web-terminal
