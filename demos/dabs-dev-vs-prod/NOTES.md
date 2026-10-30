# Notes: dabs-dev-vs-prod

**Takeaway:** the identity that deploys a job and the identity that runs it are different things; put the run identity in the bundle as a service principal and keep its ID out of the repo.

## Documented behaviour

- `mode: development` prefixes resource names with `[dev ${workspace.current_user.short_name}]` and pauses schedules and triggers ([Databricks docs: bundle deployment modes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/deployment-modes)). As tested below, a schedule set to `UNPAUSED` explicitly stays active. (verified)
- `mode: production` validates that `run_as` / permissions are set and does not change names or schedules. (mirrored from docs)
- `run_as` accepts `user_name` or `service_principal_name` (the application ID). Setting a service principal requires the deployer to have the Service Principal User role on it. (verified in demo-dbx2)
- Target `permissions` use `user_name`, `group_name` or `service_principal_name`, with levels CAN_VIEW, CAN_RUN and CAN_MANAGE (`CAN_MANAGE_RUN` is rejected at target level). On a job, `CAN_RUN` becomes CAN_MANAGE_RUN. (verified in demo-dbx2)
- Variables without a default must be passed: `--var="name=value"` or `BUNDLE_VAR_name`. (mirrored from docs)
- A notebook task with no compute settings runs on serverless jobs compute. `environment_key` is not accepted on notebook tasks. (verified)
- The workspace web terminal has the latest CLI preinstalled and authenticated as the current user; config profiles are not used there. Needs DBR 15.0+ and no PrivateLink. (mirrored from docs)

## Tested in an Azure Databricks Premium workspace (Oct 30, 2026)

- Serverless compute for workflows was disabled there, so the first deploy failed with "Serverless compute for workflows is not enabled in the workspace". Adding `existing_cluster_id` to the task fixed it.
- Dev mode added the `[dev <user>]` prefix and a dev tag as expected. It did not pause the schedule, because the YAML then set `pause_status: UNPAUSED` explicitly.
- Bundle-managed jobs lock the Pause button in the UI. Change `pause_status` in the YAML and redeploy instead.
- At that point prod had `run_as: user_name` = the deploying user. The Jobs list showed `[dev <user>] demo_daily_job` and `demo_daily_job` side by side (shot p50-01).
- After the shot, both jobs were paused. Since `b41c3c5` the repo YAML ships `pause_status: PAUSED`.

## Service principal version, tested in demo-dbx2 (Oct 30, 2026)

- Prod `run_as` is `service_principal_name: ${var.prod_sp_app_id}`; the variable has no default and dev sets a dummy value it never uses. Passed with `BUNDLE_VAR_prod_sp_app_id` from the shell; never committed.
- Prod `permissions`: CAN_MANAGE for the deploying user (shown as IS_OWNER), CAN_VIEW for `analysts`, CAN_RUN for `demo_runners` (shown as CAN_MANAGE_RUN).
- `sql/grants_run_sp.sql` applied on catalog `demo_dbx2`: USE CATALOG, USE SCHEMA, SELECT, MODIFY for the service principal `agent-sp`, nothing elsewhere.
- Serverless for workflows is off in demo-dbx2 too. The bundle was deployed from a temporary copy outside the repo with `existing_cluster_id` added to the task, so the repo YAML stays cluster-free. The run identity needs CAN_RESTART (or CAN ATTACH TO with the cluster already running) on that cluster.
- Identity federation: `analysts` and `demo_runners` are account groups assigned to the workspace; `agent-sp` is an account service principal assigned to the workspace. The first prod run failed with "does not have access to Databricks Workspace" until the SP got the `workspace-access` entitlement; the rerun succeeded.
- Validate warns that `/Workspace/Shared` is writable by all users (the prod root path). Fine for the demo.
- One dev run and one prod run succeeded; both schedules PAUSED afterwards.

## Visual moments

- p50-02: job details with **Run as** = the service principal (mask the ID), then the Permissions dialog with you as owner, `analysts` on Can View and `demo_runners` on Can Manage Run.
- p50-03: Catalog Explorer > the prod catalog > Permissions, showing the service principal with the four privileges and nothing on other catalogs.

## Open questions

- Settled: p50-02 now has `analysts` on CAN_VIEW and `demo_runners` on CAN_RUN.
- Settled: with serverless off, the run identity needs a cluster permission (CAN_RESTART was given in demo-dbx2); the deploy does not.

## Links

- Deployment modes: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/deployment-modes
- run_as: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as
- Bundle permissions: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/permissions
- Web terminal: https://learn.microsoft.com/en-us/azure/databricks/compute/web-terminal
