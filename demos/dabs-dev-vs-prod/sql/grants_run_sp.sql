-- dabs-dev-vs-prod (post 50, shot p50-03): minimal data grants for the prod run identity.
-- Job permissions (CAN_VIEW, CAN_MANAGE in databricks.yml) are not data grants. What the
-- service principal can read or write is granted here, in Unity Catalog, on its own catalog only.
--
-- Run in the SQL editor as the catalog owner (or a user with MANAGE on the catalog).
-- Replace <prod_catalog> with the demo prod catalog and <application id> with the service
-- principal's application ID (keep the backticks). Don't commit the filled-in values.

GRANT USE CATALOG ON CATALOG <prod_catalog> TO `<application id>`;
GRANT USE SCHEMA  ON CATALOG <prod_catalog> TO `<application id>`;
GRANT SELECT      ON CATALOG <prod_catalog> TO `<application id>`;
GRANT MODIFY      ON CATALOG <prod_catalog> TO `<application id>`;

-- Check (this is what the Permissions tab in Catalog Explorer shows):
SHOW GRANTS `<application id>` ON CATALOG <prod_catalog>;
