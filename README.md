# tech-demos

Runnable demos behind GeekInData posts: Microsoft Fabric, Azure Databricks and Databricks Free Edition.
Each demo is self-contained under `demos/<slug>/` and states what it costs and how to clean it up.

## Demo index

| Slug | Platform | Description | Date |
|---|---|---|---|
| [fabric-data-agent-baseline](demos/fabric-data-agent-baseline/) | Microsoft Fabric | Data agent baseline: 20 fixed questions over one lakehouse, accuracy, latency and CU before the Nov 2 to 10 NL2SQL update (n=1) | 2026-10-30 |
| [fabric-variable-library-targets](demos/fabric-variable-library-targets/) | Microsoft Fabric | Variable Library with Test, Preprod and Prod value sets, read from a notebook (post 31) | 2026-10-30 |
| [fabric-batched-ingest-replay](demos/fabric-batched-ingest-replay/) | Microsoft Fabric | Batched loader with one retry per batch, a run log and a replay list after a failed batch (post 30) | 2026-10-30 |
| [genie-readiness](demos/genie-readiness/) | Azure Databricks | Fact and dimension with grain and column comments, PK/FK constraints and a Genie space with a declared join (post 13) | 2026-10-30 |
| [fabric-mlv-file-ingestion](demos/fabric-mlv-file-ingestion/) | Microsoft Fabric | Files → bronze → silver → gold with materialized lake views (`USING OneLake_Files`, preview), generic `table_a` data, plus a self-contained notebook | 2026-10-30 |
| [fabric-databricks-post51](demos/fabric-databricks-post51/) | Fabric + Azure Databricks | Scratch objects and screenshots for blog post 51, *Fabric or Databricks? How I Decide* | 2026-10-30 |

## How to use this repo

1. Pick a demo from the index and open `demos/<slug>/README.md`. It lists what the demo shows, prerequisites, how to run it, and cost and cleanup.
2. `NOTES.md` in the same folder holds technical notes and the numbers that were verified (and where, for example locally or in Fabric).
3. Fabric items in `fabric/` are for that demo's workspace only: either Git-synced items (connect a scratch workspace to the folder) or notebook source to paste into a Fabric notebook. Each demo's README says which.
4. Databricks code in `databricks/` is an Asset Bundle: `databricks bundle validate -t dev` and `databricks bundle deploy -t dev`, using your own CLI profile. No host is stored in the repo.
5. Always pause the Fabric capacity and stop or terminate Databricks compute after a run.

Conventions for adding a demo are in [docs/conventions.md](docs/conventions.md).

## Branch and PR flow

- `main` is the published state. It only changes through a reviewed pull request.
- `dev` is the working branch. New demos and edits land on `dev` first (or on a short-lived branch off `dev`).
- Open a PR from `dev` to `main` when a demo is complete. The PR template checklist must be ticked: no secrets or IDs, README and NOTES updated, cost and cleanup stated.
- After review, merge to `main` and add the demo's row to the index above.
