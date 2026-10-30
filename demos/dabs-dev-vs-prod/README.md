# dabs-dev-vs-prod

**Platform:** Azure Databricks (Premium) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 50 (shot p50-01)

One Databricks Asset Bundle with one job, `demo_daily_job`, deployed to two targets. The Jobs list then shows what the target mode changes.

## What it shows

| Target | Mode | Job name in the Jobs list | Schedule |
|---|---|---|---|
| `dev` (default) | `development` | `[dev <user>] demo_daily_job` | **Paused** (dev mode pauses all schedules) |
| `prod` | `production` | `demo_daily_job` | **Active** (as configured: `UNPAUSED`) |

- Same YAML, two behaviours: development mode prefixes the name with `[dev <user>]` and pauses schedules; production mode keeps the name and schedule as written.
- Prod deploys to a shared root path (`/Workspace/Shared/.bundle/demo/...`) and runs as the deploying user. Dev deploys under the user's own home folder.
- The schedule is a quartz cron for 03:00 on 1 January (`0 0 3 1 1 ?`, Europe/Oslo), so the active prod schedule won't fire during a demo session.

## Prerequisites

- An Azure Databricks workspace with serverless jobs compute enabled. The notebook task has no cluster settings, so it runs on serverless.
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
- **After the screenshot, pause the prod schedule** (job → Schedules & Triggers → Pause, or set `pause_status: PAUSED` for prod and redeploy), so nothing runs on 1 January.
- To remove both jobs: `databricks bundle destroy -t dev` and `databricks bundle destroy -t prod`.
- Check that no job runs are active.
