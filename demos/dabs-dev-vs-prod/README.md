# dabs-dev-vs-prod

**Platform:** Azure Databricks (Premium) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 50 (shot p50-01)

One Databricks Asset Bundle with one job, `demo_daily_job`, deployed to two targets. The Jobs list then shows what the target mode changes.

## Status

Deployed to both targets in an Azure Databricks Premium workspace on Oct 30, 2026. Serverless compute for workflows was off in that workspace, so the task uses `existing_cluster_id`. Both jobs have since been paused. Details in `NOTES.md`.

## What it shows

| Target | Mode | Job name in the Jobs list | Schedule |
|---|---|---|---|
| `dev` (default) | `development` | `[dev <user>] demo_daily_job` | **Active** as deployed: dev mode pauses schedules by default, but not one set to `UNPAUSED` explicitly in the YAML |
| `prod` | `production` | `demo_daily_job` | **Active** (as configured: `UNPAUSED`) |

- Same YAML, two behaviours: development mode prefixes the name with `[dev <user>]` and adds a dev tag; production mode keeps the name as written. Neither changed the schedule here, because it is set to `UNPAUSED` explicitly.
- Prod deploys to a shared root path (`/Workspace/Shared/.bundle/demo/...`) and runs as the deploying user. Dev deploys under the user's own home folder.
- The schedule is a quartz cron for 03:00 on 1 January (`0 0 3 1 1 ?`, Europe/Oslo), so the active prod schedule won't fire during a demo session.

## Prerequisites

- An Azure Databricks workspace. With serverless compute for workflows enabled, the notebook task needs no cluster settings. Without it, deploy fails with "Serverless compute for workflows is not enabled in the workspace"; set `existing_cluster_id` on the task (see the comments in `databricks/resources/demo_daily_job.yml`).
- Databricks CLI with bundle support and a profile for the workspace.

## How to run

```bash
cd databricks
databricks bundle validate -t dev  --profile <your-profile>
databricks bundle deploy   -t dev  --profile <your-profile>
databricks bundle deploy   -t prod --profile <your-profile>
databricks jobs list --profile <your-profile> --output json   # check names and schedule pause_status
```

Deploying does not run the job. To run it once on purpose: `databricks bundle run -t dev demo_daily_job`.

## Cost and cleanup

- Deploying costs nothing. A run of the trivial notebook on serverless costs a few cents.
- **After the screenshot, pause the schedules**: set `pause_status: PAUSED` and redeploy. Bundle-managed jobs lock the Pause button in the UI, so the YAML is the way. Both deployed jobs are paused now. The repo YAML still says `UNPAUSED` (that is what the shot shows), so switch it to `PAUSED` before redeploying.
- To remove both jobs: `databricks bundle destroy -t dev` and `databricks bundle destroy -t prod`.
- Check that no job runs are active.
