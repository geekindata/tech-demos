# databricks-base: the shared demo table for the Unity Catalog demos

**Platform:** Azure Databricks (Premium, Unity Catalog) · **Date:** 30 Oct 2026 · **Status:** tested in workspace demo-dbx2, catalog `demo_dbx2`, on Oct 30, 2026

One SQL script, `sql/table_a_setup.sql`, creates `<catalog>.demo.table_a` with neutral sample data (id, segment, attribute_a, value), a row filter and a column mask, and grants read access to the account group `analysts` and to the agent service principal.

## What you need

| Requirement | Notes |
|---|---|
| A Unity Catalog catalog with `CREATE SCHEMA` | Change the catalog name on the `USE CATALOG` line and the two `GRANT ... ON CATALOG` lines |
| An **account** group `analysts`, assigned to the workspace | `is_account_group_member()` and UC grants don't see workspace-local groups |
| The application ID of the agent service principal (optional) | Paste it into the two agent-sp `GRANT` lines at run time; don't commit it |
| A SQL warehouse (2X-Small is enough) | |

## Run

Paste the script into the SQL editor and select **Run all**.

**Expected output** for a user outside `analysts`: 2 rows, ids 1 and 4, segment A, `attribute_a` shown as `***`. Members of `analysts` see all 6 rows (A 10, B 20, C 30, A 15, B 25, C 35) with the attribute in clear text.

## Cleanup

Stop the warehouse. Keep the schema for re-shoots. To remove it: `DROP SCHEMA <catalog>.demo CASCADE;`.
