# dabs-dev-vs-prod

**Platform:** Azure Databricks (Premium) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 50 (shots p50-01, p50-02, p50-03)

One Databricks Asset Bundle with one job, `demo_daily_job`, deployed to two targets. The Jobs list shows what the target mode changes (p50-01). The prod target runs as a service principal and sets job permissions (p50-02), and the service principal gets data grants on its own catalog only (p50-03).

## Status

Deployed to both targets in an Azure Databricks Premium workspace on Oct 30, 2026, with prod running as the deploying user. Serverless compute for workflows was off in that workspace, so the deploy needed `existing_cluster_id` on the task. Both jobs were paused after the shot. Since `b41c3c5` the repo YAML ships `pause_status: PAUSED`.

The prod `run_as` service principal and the `permissions` block were added afterwards. Tested in Azure Databricks workspace demo-dbx2 on Oct 30, 2026: dev and prod validated and deployed, prod runs as the service principal `agent-sp`, one dev run and one prod run succeeded, and both schedules stayed PAUSED. Details in `NOTES.md`.

## What it shows

| Target | Mode | Job name in the Jobs list | Runs as | Schedule (as shipped) |
|---|---|---|---|---|
| `dev` (default) | `development` | `[dev <user>] demo_daily_job` | the deploying user | Paused |
| `prod` | `production` | `demo_daily_job` | service principal `${var.prod_sp_app_id}` | Paused |

- Same YAML, two behaviours: development mode prefixes the name with `[dev <user>]` and adds a dev tag; production mode keeps the name as written. Dev mode pauses schedules by default, but when tested it did **not** pause one set to `UNPAUSED` explicitly. Set `pause_status: UNPAUSED` to see a live schedule, and set it back afterwards.
- Prod deploys to a shared root path (`/Workspace/Shared/.bundle/demo/...`). Dev deploys under the user's own home folder.
- The schedule is a quartz cron for 03:00 on 1 January (`0 0 3 1 1 ?`, Europe/Oslo), so even an active schedule won't fire during a demo session.

### Prod: deploy identity vs run identity (p50-02)

```yaml
targets:
  prod:
    mode: production
    permissions:
      - level: CAN_MANAGE
        user_name: ${workspace.current_user.userName}   # the deploying user
      - level: CAN_VIEW
        group_name: analysts
      - level: CAN_RUN
        group_name: demo_runners
    run_as:
      service_principal_name: ${var.prod_sp_app_id}     # passed at deploy time
```

- **Deploy identity**: whoever runs `databricks bundle deploy`. Gets CAN_MANAGE on the job.
- **Run identity**: the service principal in `run_as`. The job's "Run as" field shows it.
- **Job permissions are not data grants.** `analysts` with CAN_VIEW can see the job and its runs, nothing more. What the service principal can read and write is granted in Unity Catalog: `sql/grants_run_sp.sql` gives USE CATALOG, USE SCHEMA, SELECT and MODIFY on its own catalog only (p50-03).
- The application ID is **never committed**. `prod_sp_app_id` has no default; prod deploy and validate fail until you pass it.

## Prerequisites

- An Azure Databricks workspace. With serverless compute for workflows enabled, the notebook task needs no cluster settings. Without it, deploy fails with "Serverless compute for workflows is not enabled in the workspace"; set `existing_cluster_id` on the task (see the comments in `databricks/resources/demo_daily_job.yml`, and step 3 below).
- Databricks CLI with bundle support. Locally: a profile for the workspace. In the workspace web terminal: nothing, it is preinstalled and signed in as you.
- For prod:
  - A service principal in the workspace, and its **application ID**.
  - **The deployer needs the Service Principal User role on that service principal** (account console or workspace admin settings: Service principals > the SP > Permissions > grant `Service principal: User`). Without it, the prod deploy fails because you can't set another identity as the job's run_as.
  - Groups named `analysts` and `demo_runners` in the workspace (or change `group_name`). An unknown group fails the deploy. In an identity-federated workspace, create them as **account** groups and assign them to the workspace; a workspace-local group works for job permissions but not for Unity Catalog grants or `is_account_group_member`.
  - The service principal must be assigned to the workspace **and** have the `Workspace access` entitlement. Without the entitlement, the prod run fails with "does not have access to Databricks Workspace".
  - For runs (not for deploy): the service principal needs CAN ATTACH TO / CAN RESTART on the cluster if you use `existing_cluster_id`, and the grants in `sql/grants_run_sp.sql` for any data it touches.

## How to run (local CLI)

```bash
cd databricks
databricks bundle validate -t dev  --profile <your-profile>
databricks bundle deploy   -t dev  --profile <your-profile>
databricks bundle validate -t prod --profile <your-profile> --var="prod_sp_app_id=<application id>"
databricks bundle deploy   -t prod --profile <your-profile> --var="prod_sp_app_id=<application id>"
databricks jobs list --profile <your-profile> --output json   # names, schedule pause_status
```

Instead of `--var`, you can `export BUNDLE_VAR_prod_sp_app_id=<application id>` once per shell.

Deploying does not run the job. To run it once on purpose: `databricks bundle run -t dev demo_daily_job`.

## Redeploy prod from the workspace web terminal

Use the web terminal (compute > your cluster > Apps > Web Terminal, or the terminal icon in a notebook's bottom panel). It needs Databricks Runtime 15.0 or above, and the web terminal enabled by an admin. The CLI there is preinstalled and authenticated as you, so don't pass `--profile`.

```bash
# 1. Go to the bundle folder (a Git folder of this repo, pulled to the latest commit)
cd /Workspace/Users/<you>/tech-demos/demos/dabs-dev-vs-prod/databricks
databricks current-user me            # check who is deploying

# 2. Set the run identity for this shell only (not committed anywhere)
export BUNDLE_VAR_prod_sp_app_id=<application id>

# 3. Only if serverless for workflows is off: point the task at this cluster.
#    Edits the workspace copy only; don't commit it.
echo "$DB_CLUSTER_ID"                 # cluster the terminal runs on; or copy the ID from the compute page
sed -i "s/^        - task_key: hello$/&\n          existing_cluster_id: $DB_CLUSTER_ID/" resources/demo_daily_job.yml

# 4. Validate and deploy prod
databricks bundle validate -t prod
databricks bundle deploy   -t prod

# 5. Check run_as and permissions
databricks jobs list --name demo_daily_job --output json     # note the prod job_id
databricks jobs get <job_id> --output json | grep run_as
databricks jobs get-permissions <job_id> --output json
```

Expected: `validate` prints the bundle summary with no errors, `deploy` ends with `Deployment complete!`, `jobs get` shows `run_as` with the application ID, and `get-permissions` lists you (IS_OWNER), `analysts` (CAN_VIEW) and `demo_runners` (CAN_MANAGE_RUN), plus admins. In the UI, Jobs > `demo_daily_job` shows **Run as** = the service principal, and **Permissions** lists you, `analysts` (Can View) and `demo_runners` (Can Manage Run).

A `%sh` notebook cell runs on the same driver, but it does not get the web terminal's CLI sign-in, so use the web terminal for bundle commands.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `no value assigned to required variable prod_sp_app_id` | Pass `--var="prod_sp_app_id=<application id>"` or export `BUNDLE_VAR_prod_sp_app_id`. |
| Deploy fails on `run_as` / permission denied for the service principal | Grant the deployer the Service Principal User role on that SP. |
| Deploy fails on `group_name: analysts` or `demo_runners` | Create the group or change `group_name`. |
| `level: CAN_MANAGE_RUN` rejected at target level | Bundle `permissions` accept CAN_VIEW, CAN_RUN and CAN_MANAGE only. Use `CAN_RUN`; on a job it becomes CAN_MANAGE_RUN. |
| Prod run fails: "does not have access to Databricks Workspace" | Give the service principal the `Workspace access` entitlement (admin settings > Identity and access > Service principals). |
| Validate warns that `/Workspace/Shared` is writable by all users | Expected for the shared prod root path in this demo. For real use, pick a root path only the deployers can write. |
| "Serverless compute for workflows is not enabled" | Add `existing_cluster_id` (step 3 above). |
| Pause button greyed out in the UI | Bundle-managed job: change `pause_status` in the YAML and redeploy. |

## Cost and cleanup

- Deploying costs nothing. A run of the trivial notebook on serverless costs a few cents.
- The YAML ships `pause_status: PAUSED`. If you switched it to `UNPAUSED` for a shot, set it back and redeploy. Bundle-managed jobs lock the Pause button in the UI, so the YAML is the way.
- To remove both jobs: `databricks bundle destroy -t dev` and `databricks bundle destroy -t prod --var="prod_sp_app_id=<application id>"`.
- To undo the data grants, run the `GRANT` lines in `sql/grants_run_sp.sql` as `REVOKE ... FROM`.
- Check that no job runs are active.

## Limitations

- `permissions` at target level apply to every resource in the bundle and to the deployed workspace files, not only to this job.
- The audit for p50-02 shows groups on CAN_VIEW and CAN_RUN: `analysts` has CAN_VIEW and `demo_runners` has CAN_RUN. In the bundle the level is written `CAN_RUN`; the job shows it as CAN_MANAGE_RUN ("Can Manage Run" in the UI).
- The job's notebook reads no data, so the run works without the catalog grants; they are there for the post's "own catalog only" point.

## Files

- `databricks/databricks.yml`: bundle, variables, dev and prod targets.
- `databricks/resources/demo_daily_job.yml`: the job.
- `databricks/src/hello_notebook.py`: the notebook task.
- `sql/grants_run_sp.sql`: Unity Catalog grants for the run service principal (placeholders).
- `tests/test_bundle.py`: parses the YAML and checks run_as, permissions and that no IDs are committed.
