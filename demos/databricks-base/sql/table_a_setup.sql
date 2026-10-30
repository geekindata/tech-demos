-- databricks-base: the shared demo table the Unity Catalog demos expect.
--
-- Creates <catalog>.demo.table_a (id, segment, attribute_a, value) with 6 rows, a row
-- filter (segment_a_only) and a column mask (mask_attribute), and grants read access to
-- the account group `analysts` and to the agent service principal.
--
-- The catalog name appears on the USE CATALOG line and the two GRANT ... ON CATALOG lines.
-- Change all three to your catalog.
-- Replace <agent-sp application id> with the service principal's application ID (keep the
-- backticks), or drop the two agent-sp lines. Don't commit the filled-in ID.
--
-- `analysts` must be an account group assigned to the workspace: is_account_group_member()
-- and Unity Catalog grants don't see workspace-local groups.
-- The emails in attribute_a are fake example.com addresses.
--
-- Tested on the Serverless Starter Warehouse in demo-dbx2 (Oct 30, 2026).

USE CATALOG demo_dbx2;

CREATE SCHEMA IF NOT EXISTS demo
  COMMENT 'Demo schema for the Unity Catalog demos. Generic sample data only.';

CREATE OR REPLACE TABLE demo.table_a (id INT, segment STRING, attribute_a STRING, value INT);

INSERT INTO demo.table_a VALUES
  (1, 'A', 'user1@example.com', 10),
  (2, 'B', 'user2@example.com', 20),
  (3, 'C', 'user3@example.com', 30),
  (4, 'A', 'user4@example.com', 15),
  (5, 'B', 'user5@example.com', 25),
  (6, 'C', 'user6@example.com', 35);

-- Members of analysts see every row; everyone else sees segment A only.
CREATE OR REPLACE FUNCTION demo.segment_a_only(segment STRING)
  RETURN is_account_group_member('analysts') OR segment = 'A';

-- Members of analysts see attribute_a in clear text; everyone else sees ***.
CREATE OR REPLACE FUNCTION demo.mask_attribute(v STRING)
  RETURN CASE WHEN is_account_group_member('analysts') THEN v ELSE '***' END;

ALTER TABLE demo.table_a SET ROW FILTER demo.segment_a_only ON (segment);

ALTER TABLE demo.table_a ALTER COLUMN attribute_a SET MASK demo.mask_attribute;

GRANT USE CATALOG ON CATALOG demo_dbx2 TO `analysts`;

GRANT USE SCHEMA, SELECT ON SCHEMA demo TO `analysts`;

GRANT USE CATALOG ON CATALOG demo_dbx2 TO `<agent-sp application id>`;

GRANT USE SCHEMA, SELECT ON SCHEMA demo TO `<agent-sp application id>`;

-- Check: as a user outside analysts this returns 2 rows (segment A) with attribute_a = ***.
SELECT * FROM demo.table_a ORDER BY id;
