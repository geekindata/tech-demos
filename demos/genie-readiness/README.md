# genie-readiness: a fact and a dimension that Genie can read without guessing

> Built 2026-10-30 · Target: Azure Databricks Premium, Unity Catalog, Serverless Starter Warehouse · Status: tested in Azure Databricks workspace demo-dbx2 (catalog `demo_dbx2`) on Oct 30, 2026

**Platform:** Azure Databricks (Premium, Unity Catalog) · **Date:** 30 Oct 2026 · **Related post:** GeekInData blog post 13, Genie readiness (shots p13-01, p13-02a to p13-02d, p13-03)

One SQL script creates a small star in `<catalog>.demo13` (set the catalog in the script's `USE CATALOG` line; tested with `demo_dbx2`). `fact_a` states its grain in the table comment, every column has a comment, and both tables carry declared keys: a PRIMARY KEY on `dim_a`, and a PRIMARY KEY plus a FOREIGN KEY to `dim_a` on `fact_a`. A Genie space, `demo13_space`, is then built on those two tables with the join declared in the space definition (its serialized config), not described in prompt text.

## What it shows

| Shot | What to capture | Produced by |
|---|---|---|
| p13-01 | Catalog Explorer → `<catalog>.demo13.fact_a` → Overview: the grain comment, the column comments (including the `segment_id` code list) and the PK / FK markers | `sql/demo13_setup.sql` |
| p13-02a | Genie space `demo13_space`: the two data sources `dim_a` and `fact_a` | Walkthrough steps 3 and 4 |
| p13-02b | Inside the space, `fact_a` shows `id` as PK and `segment_id` as FK to `dim_a` | Walkthrough step 4 |
| p13-02c | Inside the space, `dim_a` shows `segment_id` as PK | Walkthrough step 4 |
| p13-02d | Catalog Explorer → `fact_a` → Entity Relationship Diagram: the declared PK/FK from `fact_a.segment_id` to `dim_a.segment_id` that the space's join follows | `sql/demo13_setup.sql` |
| p13-03 | A Genie answer with **Show code** expanded, showing the `JOIN ... ON segment_id` it used | Walkthrough step 8 |

## What you need

| Requirement | Notes |
|---|---|
| Azure Databricks workspace, Premium tier, Unity Catalog enabled | Genie and informational PK/FK constraints need Unity Catalog |
| A catalog (`<catalog>`), with `USE CATALOG` and `CREATE SCHEMA` (or an existing `demo13` with `CREATE TABLE`) | Edit the `USE CATALOG` line at the top of the script; it then runs `CREATE SCHEMA IF NOT EXISTS demo13` |
| A SQL warehouse (the default *Serverless Starter Warehouse* works) with `CAN USE` | Pro or serverless warehouses are needed for Genie |
| Access to Genie (AI/BI) in the workspace | Space creators need `SELECT` on both tables and `CAN USE` on the warehouse |

## Quickstart (about 5 minutes)

1. Open **SQL Editor**, pick the **Serverless Starter Warehouse**.
2. Paste the whole of `sql/demo13_setup.sql`, change `USE CATALOG demo_dbx2;` to your catalog if needed, and select **Run all**.

**Expected output.** The second-to-last query (`information_schema.table_constraints`) returns 3 rows: `dim_a / dim_a_pk / PRIMARY KEY`, `fact_a / fact_a_pk / PRIMARY KEY`, `fact_a / fact_a_dim_a_fk / FOREIGN KEY`. The last query returns:

| segment | attribute_a | row_count | total_value |
|---|---|---|---|
| A | a1 | 3 | 42.00 |
| B | a2 | 3 | 28.00 |
| C | a1 | 2 | 55.00 |

`dim_a` has 3 rows and `fact_a` 8 rows (total value 125.00).

## Walkthrough

1. **Run the script** (Quickstart). → The final join result above.
2. **Check the metadata (p13-01).** Catalog Explorer → `<catalog>` → `demo13` → `fact_a`. → Overview shows the table comment beginning *Grain: one row per id*, a comment on `id`, `segment_id` and `value`, and key markers on `id` (PK) and `segment_id` (FK to `dim_a`). The same view on `dim_a` shows *Grain: one row per segment* and the PK on `segment_id`.
3. **Create the space.** Left sidebar → **Genie** → **New**. Add data sources `<catalog>.demo13.fact_a` and `<catalog>.demo13.dim_a` (only these two). Pick the **Serverless Starter Warehouse**. Name the space **`demo13_space`** → **Create**.
4. **Open the configuration.** In the space, select **Configure**. → The **Data** list shows the two tables. Table and column descriptions are taken from the Unity Catalog comments.
5. **Declare the join in the space definition.** In demo-dbx2 the join was declared through the API, as a join entry in the space's serialized config, sent with `POST /api/2.0/genie/spaces` ([Genie spaces API](https://docs.databricks.com/api/workspace/genie), [define join relationships](https://docs.databricks.com/aws/en/genie-agents/tune-quality)). This is the join entry as read back from the tested space (`serialized_space` version 2, catalog replaced with `<catalog>`):

   ```json
   "instructions": {
     "join_specs": [
       {
         "left":  { "identifier": "<catalog>.demo13.fact_a", "alias": "fact_a" },
         "right": { "identifier": "<catalog>.demo13.dim_a",  "alias": "dim_a" },
         "sql": [
           "`fact_a`.`segment_id` = `dim_a`.`segment_id`",
           "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
         ]
       }
     ]
   }
   ```

   Left `fact_a`, right `dim_a`, condition `fact_a.segment_id = dim_a.segment_id`, many to one. The docs describe a joins editor in the Genie UI (Configure → Joins, or Examples → Add → Joins in some versions), but no view showing the declared join was visible in demo-dbx2, so that UI path is untested here. The proof is p13-02a to p13-02c (tables and keys in the space), p13-02d (the PK/FK the join follows) and p13-03 (the generated SQL using the join).
6. **Add the two sample questions.** In the space **Settings** (or Configure → **Sample questions**), add:
   - `What is the total value by segment?`
   - `What is the total value for attribute_a a1?`
   → Both appear as clickable starters in a new chat.
7. **Ask question 1.** Select the first sample question. → Expected answer:

   | segment | total_value |
   |---|---|
   | A | 42.00 |
   | B | 28.00 |
   | C | 55.00 |

8. **Ask question 2 and expand the SQL (p13-03).** Select the second sample question. → Expected answer: **97.00** (segments A and C, 5 rows). Expand **Show code**: the generated SQL should join `fact_a` to `dim_a` on `segment_id` and filter `attribute_a = 'a1'`. If the SQL sums without the join, or joins on anything else, check the join entry from step 5 in the space definition.

## How it works

- Informational PRIMARY KEY and FOREIGN KEY constraints in Unity Catalog are not enforced on write. They document the relationship for tools, and Genie respects them ([constraints](https://learn.microsoft.com/en-us/azure/databricks/tables/constraints), [Genie best practices](https://www.databricks.com/blog/data-dialogue-best-practices-guide-building-high-performing-genie-spaces)).
- Joins declared in the space ([define join relationships](https://docs.databricks.com/aws/en/genie-agents/tune-quality)) count as knowledge-store snippets and tell Genie the condition and cardinality, so it doesn't infer a join from column names.
- The grain comment says what one row is, which is what stops a COUNT or SUM from being double-counted after a join.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `CREATE SCHEMA` permission error | No `CREATE SCHEMA` on `<catalog>` | Ask for the grant, or create `demo13` once as an admin and rerun |
| PRIMARY KEY error about nullable columns | Key columns must be `NOT NULL` | Keep the `NOT NULL` in the script |
| `DROP TABLE dim_a` fails on rerun | An FK still references it | Run the script top to bottom: it drops `fact_a` first |
| Genie can't see the tables | Missing `SELECT` / `USE SCHEMA` for the space user | Grant them on `<catalog>.demo13` |

## Cost and cleanup

- Cost: a few minutes of the Serverless Starter Warehouse (a 2X-Small serverless warehouse), well under 1 DBU. Genie questions run on the same warehouse.
- After the shots, **stop the warehouse** (SQL Warehouses → Stop) or leave its auto-stop on.
- Keep the schema and the space for re-shoots (repo convention). To remove them: delete `demo13_space` in Genie, then `DROP TABLE <catalog>.demo13.fact_a; DROP TABLE <catalog>.demo13.dim_a; DROP SCHEMA <catalog>.demo13;`.

## Tested in demo-dbx2 (Oct 30, 2026)

- Script run on the Starter Warehouse (2X-Small) with catalog `demo_dbx2`: 3 constraints, join result A a1 3 / 42.00, B a2 3 / 28.00, C a1 2 / 55.00.
- `demo13_space` created with `POST /api/2.0/genie/spaces` (the two tables, one join, the two sample questions). Asked "What is the total value for attribute_a a1?": 97.00, with an INNER JOIN on `segment_id` in the generated SQL. The test conversation was deleted afterwards.

## Limitations and unverified behaviour

- The join was declared and read back through the API only. The Genie UI may expose a joins editor (Configure → Joins, or Examples → Add → Joins) in some versions, but it was not visible in demo-dbx2, so no screenshot shows the join in the space UI. Where sample questions live in the UI also differs between doc versions.
- In demo-dbx2, Genie added a join from the declared FK on its own when the space was created by API, next to the declared one. Keep exactly one join `fact_a.segment_id = dim_a.segment_id`, many to one, and remove any duplicate from the space definition (it shows up with an alias such as `dim_a_2`). The read-back of the tested space lists one join.
- Genie output is generated, so the wording and column aliases of answers vary. The numbers above don't.

## Files

```
sql/demo13_setup.sql   paste-ready script: schema, dim_a, fact_a, keys, rows, checks
tests/test_smoke.py    offline check: sqlglot parse + DuckDB replay of the expected results
NOTES.md               handoff notes
```

Local check: `pip install sqlglot duckdb pytest && pytest -q tests/`.
