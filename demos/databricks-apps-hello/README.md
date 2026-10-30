# databricks-apps-hello

**Platform:** Azure Databricks (Premium) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 4 (shot p4-02)

A minimal Streamlit "hello" app, `demo-app`, deployed as a Databricks App so its details page can be shown: status *Running*, app URL, compute size, the app's service principal and the source code path.

## Status

Deployed in an Azure Databricks Premium workspace on Oct 30, 2026. The app reached *Running*, the details page was captured, and the app was then stopped. Details in `NOTES.md`.

## What it shows

- `app/app.py`: one page with a title and the app name read from `DATABRICKS_APP_NAME`.
- `app/app.yaml`: the start command (`streamlit run app.py`).
- `app/requirements.txt`: `streamlit`.

## Prerequisites

- An Azure Databricks workspace in a region where Databricks Apps is available, with Apps enabled.
- Databricks CLI with a profile for the workspace (`databricks apps list` should work).

## How to run

```bash
databricks apps create demo-app --compute-size MEDIUM --profile <your-profile>   # smallest size
databricks workspace import-dir app /Workspace/Users/<you>/apps/demo-app --overwrite --profile <your-profile>
databricks apps deploy demo-app --source-code-path /Workspace/Users/<you>/apps/demo-app --profile <your-profile>
databricks apps get demo-app --profile <your-profile>
```

## Cost and cleanup

- **Apps bill while they run**, whether or not anyone uses them. Stop it right after the screenshot: `databricks apps stop demo-app`.
- Keep the stopped app for re-shoots. To remove it entirely: `databricks apps delete demo-app`.
