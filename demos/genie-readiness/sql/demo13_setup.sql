-- =====================================================================================
-- genie-readiness (post 13): paste-ready setup for catalog demo_dbx, schema demo13
--
-- Run in the Databricks SQL editor on a SQL warehouse (tested target: Azure Databricks
-- Premium, Unity Catalog, Serverless Starter Warehouse). Paste the whole script and use
-- "Run all". Safe to re-run: it drops and recreates the two demo tables only.
--
-- Creates:
--   demo_dbx.demo13.dim_a   one row per segment, PRIMARY KEY (segment_id)
--   demo_dbx.demo13.fact_a  one row per id, PRIMARY KEY (id),
--                           FOREIGN KEY (segment_id) REFERENCES dim_a (segment_id)
-- PK/FK constraints in Unity Catalog are informational: they are not enforced on write,
-- but Catalog Explorer shows them and Genie reads them as the declared relationship.
--
-- Expected result of the last query:
--   segment | attribute_a | row_count | total_value
--   A       | a1          | 3         | 42.00
--   B       | a2          | 3         | 28.00
--   C       | a1          | 2         | 55.00
-- =====================================================================================

CREATE SCHEMA IF NOT EXISTS demo_dbx.demo13
  COMMENT 'Demo schema for post 13 (Genie readiness). Generic sample data only.';

-- Drop the fact first: it holds the foreign key that points at dim_a.
DROP TABLE IF EXISTS demo_dbx.demo13.fact_a;
DROP TABLE IF EXISTS demo_dbx.demo13.dim_a;

CREATE TABLE demo_dbx.demo13.dim_a (
  segment_id  INT     NOT NULL COMMENT 'Surrogate key of the segment. Referenced by fact_a.segment_id.',
  segment     STRING  NOT NULL COMMENT 'Segment code: A, B or C. Use this column when a question names a segment.',
  attribute_a STRING  NOT NULL COMMENT 'Attribute of the segment: a1 or a2. Segments A and C are a1, segment B is a2.',
  CONSTRAINT dim_a_pk PRIMARY KEY (segment_id)
)
COMMENT 'Grain: one row per segment. Dimension describing each segment (code and attribute_a).';

CREATE TABLE demo_dbx.demo13.fact_a (
  id          INT            NOT NULL COMMENT 'Unique identifier of the row. Primary key of fact_a.',
  segment_id  INT            NOT NULL COMMENT 'Segment of the row. Foreign key to dim_a.segment_id (1 = A, 2 = B, 3 = C); join to dim_a for the segment code and attribute_a.',
  value       DECIMAL(10,2)  NOT NULL COMMENT 'Measured value of the row, two decimals, never negative. Sum it for totals.',
  CONSTRAINT fact_a_pk PRIMARY KEY (id),
  CONSTRAINT fact_a_dim_a_fk FOREIGN KEY (segment_id) REFERENCES demo_dbx.demo13.dim_a (segment_id)
)
COMMENT 'Grain: one row per id. Each row has exactly one segment (segment_id -> dim_a) and one value. Total value = SUM(value); row count = COUNT(*).';

INSERT INTO demo_dbx.demo13.dim_a (segment_id, segment, attribute_a) VALUES
  (1, 'A', 'a1'),
  (2, 'B', 'a2'),
  (3, 'C', 'a1');

INSERT INTO demo_dbx.demo13.fact_a (id, segment_id, value) VALUES
  (1, 1, 10.00),
  (2, 1, 20.00),
  (3, 2, 15.00),
  (4, 2,  5.00),
  (5, 3, 30.00),
  (6, 1, 12.00),
  (7, 2,  8.00),
  (8, 3, 25.00);

-- Check 1: the declared keys. Expected 3 rows: dim_a_pk PRIMARY KEY, fact_a_pk PRIMARY KEY,
-- fact_a_dim_a_fk FOREIGN KEY.
SELECT table_name, constraint_name, constraint_type
FROM demo_dbx.information_schema.table_constraints
WHERE table_schema = 'demo13'
ORDER BY table_name, constraint_type DESC, constraint_name;

-- Check 2 (final): the join along the declared key. Expected:
--   A | a1 | 3 | 42.00
--   B | a2 | 3 | 28.00
--   C | a1 | 2 | 55.00
SELECT d.segment,
       d.attribute_a,
       COUNT(*)      AS row_count,
       SUM(f.value)  AS total_value
FROM demo_dbx.demo13.fact_a AS f
JOIN demo_dbx.demo13.dim_a  AS d
  ON f.segment_id = d.segment_id
GROUP BY d.segment, d.attribute_a
ORDER BY d.segment;
