# Connection values for this demo. Real values live in scripts/env.local (gitignored) or the environment.
# Copy scripts/env.example to scripts/env.local and fill it in from
#   GET /v1/workspaces/{ws}/sqlDatabases   (properties.serverFqdn, properties.databaseName)
#   GET /v1/workspaces/{ws}/sqlEndpoints/{id}/connectionString
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$_here/env.local" ] && source "$_here/env.local"
: "${SRC_SERVER:?set SRC_SERVER in scripts/env.local or the environment}"
: "${SRC_DB:?set SRC_DB in scripts/env.local or the environment}"
: "${EP_SERVER:?set EP_SERVER in scripts/env.local or the environment}"
: "${EP_DB:?set EP_DB in scripts/env.local or the environment}"
: "${FABRIC_WORKSPACE:?set FABRIC_WORKSPACE in scripts/env.local or the environment}"
: "${SQL_DATABASE:?set SQL_DATABASE in scripts/env.local or the environment}"
: "${HELPER_LAKEHOUSE:?set HELPER_LAKEHOUSE in scripts/env.local or the environment}"
: "${SEED_NOTEBOOK:?set SEED_NOTEBOOK in scripts/env.local or the environment}"
: "${WORKLOAD_NOTEBOOK:?set WORKLOAD_NOTEBOOK in scripts/env.local or the environment}"
export SRC_SERVER SRC_DB EP_SERVER EP_DB FABRIC_WORKSPACE SQL_DATABASE HELPER_LAKEHOUSE SEED_NOTEBOOK WORKLOAD_NOTEBOOK
