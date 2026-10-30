# Notes: databricks-apps-hello

## Tested in an Azure Databricks Premium workspace (Oct 30, 2026)

- Deployed `demo-app` with the commands in `README.md`. Every deployment step succeeded.
- The app details page showed status **Running**, with the app URL, compute size, the app's service principal and the source code path (shot p4-02).
- The app was stopped right after the shot, so it no longer bills. It is kept, stopped, for re-shoots.
- In the related dev-vs-prod bundle test in the same workspace, serverless compute for workflows was off, so that job uses `existing_cluster_id` (see `demos/dabs-dev-vs-prod/NOTES.md`). Apps run on their own compute, so this app needed no change.
