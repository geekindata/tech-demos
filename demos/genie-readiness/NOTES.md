# genie-readiness technical notes
Date: 2026-10-30 · Tool: Azure Databricks AI/BI Genie, Unity Catalog informational constraints · Source: [Genie: tune quality / joins](https://docs.databricks.com/aws/en/genie-agents/tune-quality), [Genie: instructions](https://learn.microsoft.com/en-us/azure/databricks/genie/add-instructions)

Tested in Azure Databricks workspace demo-dbx2, catalog `demo_dbx2`, on Oct 30, 2026 (Premium, Unity Catalog, Starter Warehouse at 2X-Small).

## One-line takeaway
Grain in the table comment, a comment per column, and declared PK/FK plus a join in the space give Genie the join instead of leaving it to guess.

## What the demo shows
1. `sql/demo13_setup.sql` creates `<catalog>.demo13.dim_a` (3 rows) and `fact_a` (8 rows) with comments and keys → final join returns A a1 3 / 42.00, B a2 3 / 28.00, C a1 2 / 55.00.
2. `information_schema.table_constraints` lists 3 constraints: `dim_a_pk`, `fact_a_pk`, `fact_a_dim_a_fk`.
3. Genie space `demo13_space` on the two tables with join `fact_a.segment_id = dim_a.segment_id` (many to one).
4. Sample question "What is the total value by segment?" → A 42.00, B 28.00, C 55.00.
5. Sample question "What is the total value for attribute_a a1?" → 97.00 (needs the join: `attribute_a` lives only in `dim_a`).

## Key numbers
| Metric | Value | Status |
|---|---|---|
| Statements in the script | 9 (parsed with sqlglot 30.26, Databricks dialect) | mirrored |
| dim_a / fact_a rows | 3 / 8 | verified (demo-dbx2) |
| Final join | A 3 / 42.00 · B 3 / 28.00 · C 2 / 55.00 | verified (demo-dbx2) |
| Total value, all rows | 125.00 | verified (demo-dbx2) |
| Answer to sample question 2 | 97.00 | verified in Genie (demo-dbx2) |

## Setup facts
- Runtime: Databricks SQL on the Serverless Starter Warehouse. No cluster, no bundle.
- Cost: minutes of a 2X-Small serverless warehouse. Stop it after.
- Time end to end: about 10 minutes including the Genie space.

## Gotchas and limitations
- PK/FK in Unity Catalog are informational (not enforced). Key columns must be `NOT NULL`.
- The FK means `dim_a` can't be dropped first. The script drops `fact_a` first.
- Genie UI names for joins and sample questions differ between doc versions (Configure → Joins vs Configure → Examples → Add → Joins).
- Join relationships and table descriptions count toward the space's 200 knowledge-store snippets; sample SQL toward 100 instructions.

## Visual moments
- p13-01: Catalog Explorer, `fact_a` Overview: grain comment, column comments, PK/FK markers.
- p13-02: `demo13_space` Configure: two tables and the one declared join.
- p13-03: answer to "What is the total value for attribute_a a1?" with Show code expanded, the JOIN on `segment_id` visible.

## Settled in demo-dbx2
- Genie does add a join from the FK by itself (seen when creating the space by API, alias `dim_a_2`), next to the declared one. Remove the duplicate so one join remains.
- The space can be created by API: `POST /api/2.0/genie/spaces` with `serialized_space` version 2 (tables, join, sample questions) and the warehouse ID passed at runtime, never committed.
- Exact UI menu path for sample questions still to confirm during the shots.

## Links
- https://learn.microsoft.com/en-us/azure/databricks/tables/constraints
- https://docs.databricks.com/aws/en/genie-agents/tune-quality
- https://learn.microsoft.com/en-us/azure/databricks/genie/add-instructions
- https://www.databricks.com/blog/data-dialogue-best-practices-guide-building-high-performing-genie-spaces
