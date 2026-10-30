# Notes and caveats: Fabric SQL database mirroring lag

Measured on a 64-CU Fabric trial; not a statement about paid F64 or production SLAs. One region, one evening (2026-10-30, Oslo time UTC+1), one database, one table. Another job was building a TPC-H dataset on the same trial capacity at the same time, so noisy neighbour effects cannot be ruled out.

## What the number means

* Lag here is end to end: source commit, change feed capture, Delta write to OneLake, then the SQL analytics endpoint picking up the new Delta version. It is not the OneLake write time alone. A reader of the Delta files directly (Spark, Direct Lake) may see changes earlier.
* The source change feed DMV sample (TOP 30 scan sessions, which covers only the tail of run 7 plus runs 8 and 9, 21:36 to 21:49 Oslo) shows sessions every 15 s with latency 0 s to 15 s and no errors. The DMV latency column is scan end minus the commit time it processed, so it covers capture and publish to the OneLake landing zone, not the Delta commit.
* Markers became visible on the endpoint in 15 batches (the 20 distinct seen times cluster into 15 within 10 s; some batches span two consecutive 2 s polls), 150.8 s to 329.1 s apart, median 187.8 s. A marker's lag therefore depends mostly on where it lands inside that cycle, which is why each run shows a sawtooth from about 20 s up to about 300 s.
* Delta commits (results/delta_commits.csv). Path read, read only, through the OneLake DFS API: `https://onelake.dfs.fabric.microsoft.com/<workspace>/<item>/Tables/dbo/table_a/_delta_log/`, the mirrored table of the SQL database item (no shortcut, no Spark). 1 directory listing and 102 commit file GETs (versions 0 to 101, 19:56 to 21:49 Oslo, about 434 KB). The replicator (engineInfo Microsoft-Trident-WL-Replicator) writes no commitInfo timestamp, so commit time is the commit file's OneLake lastModified (1 s resolution); the newest add.modificationTime agrees within 1 s. numOutputRows is not written either, so the CSV gives new_file_rows from the add stats.
  * During every burst the replicator committed a Merge every 14 to 16 s (median 15.0 s over 88 in-burst Merge to Merge gaps; the one 12 s gap follows an Optimize commit; 11 or 12 commits per run, 98 Merge, 2 Optimize, 1 Write, 1 ReplaceTable in total).
  * Each of the 153 markers was matched to the first commit whose newest source updated_at reaches the marker's commit time. Source commit to Delta: 7.4 to 28.9 s, median 18.5 s, p95 27.3 s. Delta to visible on the endpoint: 2.8 to 278.6 s, median 116.3 s, p95 218.6 s, a median 86% of each marker's lag (median of per marker shares, 153 markers; in medians, 116 s of about 135 s). Each endpoint batch picked up 1 to 11 Delta commits at once (median 6.5).
  * Seed: the 1M row ReplaceTable commit landed about 46 s after the seed commit; the endpoint showed the full count at 125.3 s.
  * Finding: commits arrive every 15 s, not every 150 to 330 s, so the batching is not in replication. It sits between the Delta table and the SQL analytics endpoint (the endpoint's metadata sync). Learn's SQL analytics endpoint page says the lakehouse to endpoint lag is normally under one minute (https://learn.microsoft.com/en-us/fabric/data-warehouse/sql-analytics-endpoint-performance); here it was a median 116 s with 150 to 330 s cycles. A Direct Lake or Spark reader of the Delta table would have seen changes within about 30 s.
* Higher change rates showed lower median lag (10 rows/s 158 s, 100 rows/s 130 s, 1000 rows/s 100 s over all markers; pooled nearest rank p95 276.4 / 244.0 / 212.0 s). With only 3 runs per rate and a batch cycle of several minutes, treat this as an observation, not a cause. The order inside every round was always 10, 100, 1000, so rate is confounded with position in the round, and each run's 17 markers fall into only 1 to 3 endpoint batches, so the effective sample is the batch count, not 51 per rate. Run 1 of each rate was the slowest, so a warm up effect after the initial snapshot is mixed in.
* These values are for querying through the SQL analytics endpoint in this setup only; check them against current Microsoft documentation before quoting a general figure.

## Which metadata sync the endpoint uses

One read only check, run once on 2026-10-30 at 22:17 Oslo time in a Fabric Python notebook (notebooks/sync_check.ipynb in the trial workspace, 16 s session), against the SQL analytics endpoint of the source database:
`SELECT OBJECT_ID('sys.dm_db_external_tables_log_status') AS dmv_log_status, OBJECT_ID('sys.sp_dw_refresh_ext_table') AS sp_refresh`, then `SELECT TOP 5 * FROM sys.dm_db_external_tables_log_status`.

* Both objects exist (non NULL object ids). Learn says they are available only on endpoints that use the new metadata sync (preview) (https://learn.microsoft.com/en-us/fabric/data-engineering/sql-analytics-endpoint-metadata-sync).
* The DMV returned columns object_id, latest_log_version, latest_checkpoint_version, latest_checksum_version, last_update_time_utc, is_blocked, but zero rows, so it lists no table, dbo.table_a included.
* Reading: object existence is not evidence, since these objects are likely in every endpoint's catalog. Learn says the DMV reports the latest metadata sync only when the new version is in use (https://learn.microsoft.com/en-us/fabric/data-engineering/sql-analytics-endpoint-metadata-sync), so zero rows for an actively updating mirrored table points to legacy sync. The timing points the same way: new sync promises changes within seconds, while 2 s polls saw a median of 116 s from Delta to the endpoint. Wording: consistent with legacy sync, not confirmed. A stronger probe (DMV right after a heartbeat write, optionally one sp_dw_refresh_ext_table call, which is a refresh action) is queued for a gap between benchmark blocks. The raw result is results/sync_check.json.

## Measurement limits

* p95 is true nearest rank, ceil(0.95 n). With 17 markers per run that is the run max. An earlier draft used rank round(0.95 n), one rank lower (266.4 / 234.0 / 202.0 s pooled); those values are superseded.
* Poll interval 2 s, so each lag value has about 2 s resolution (plus the poll query time, median 0.12 s).
* Marker commit times come from the source server clock (SYSUTCDATETIME), seen times from the endpoint server clock. The offset between the two was measured from the lowest round trip sample and was under 4 ms; it is applied to every value.
* The poll query carries a unique predicate per poll to avoid result set caching.
* Initial snapshot lag (125 s for 1M rows) includes the endpoint discovering a brand new table; until then it returned error 208 Invalid object name 'dbo.table_a'.
* The optional idle (cold) probe, a single marker after 10 minutes without changes, was built (notebooks/cold_probe.ipynb) but not run, to finish the series sooner. The only cold row in results.csv is the initial snapshot.

## CU

* All CU in the mirroring window is harness cost: the SQL database workload (the inserts, updates and deletes and the marker writes), the SQL analytics endpoint (the 2 s polls) and the notebook sessions. It is not replication cost. Learn's FAQ says: "There is no compute cost for mirroring data from Fabric SQL database to Fabric OneLake" (https://learn.microsoft.com/en-us/fabric/database/sql/mirroring-faq#what-are-the-costs-associated-with-mirroring, checked 2026-10-30). Mirroring storage is free up to a capacity based limit.
* cu_s is blank in results.csv. The Capacity Metrics semantic model was queried read only through executeQueries (scripts/metrics_dax.py). After a model refresh the Items table listed 62 items, but 'Metrics By Item Operation And Hour' returned no rows at all, including when filtered to the trial capacity id. Capture CU from the Metrics app UI instead (see SHOTS.md, shot 7), window 20:50 to 22:00 Oslo time, the trial workspace, items: the source database (SQL database and endpoint) and the workload notebook.

## Things that failed on the way (exact errors)

* No TDS from the box to Fabric SQL. mssql-python 1.16.0 with an access token, and with ActiveDirectoryDefault: "OperationalError: Driver Error: General error; DDBC Error: [Microsoft]Protocol error in TDS stream". go-sqlcmd v1.10.0 with ActiveDirectoryAzCli: "invalid packet size, it is longer than buffer size". Port 1433 was reachable. Fix: all SQL runs inside Fabric Python notebooks.
* mssql-python rejects the keyword "Connection Timeout" (unknown keyword).
* First probe notebook ended with System_Cancelled_Session_Statements_Failed; writing logs to /lakehouse/default/Files with error capture fixed it.
* Mirroring status REST: POST mirroredDatabases/{sqlDbId}/getMirroringStatus and getTablesMirroringStatus returned 404 ItemNotFound; sqlDatabases/{id}/getMirroringStatus returned 404 EntityNotFound. These calls exist only for mirrored database items, not for the built in mirroring of a Fabric SQL database. Replication health was taken from the source DMVs instead, and the portal Replication monitor is a screenshot item.
* Matplotlib 3.10 renamed boxplot labels to tick_labels; fixed in make_results.py.
* Job status reads NotStarted for 1 to 2 minutes while the notebook session starts.

## State left behind

* The source database and dbo.table_a stay in place (about 1.0M rows plus marker rows). No load is running: the workload job completed at 21:52 Oslo time, and a 30 s smoke test of scripts/film_run.sh (100 rows/s, job film_20261030T205559, started 21:56, completed 21:59 Oslo time, 103.3 rows/s, 5 of 5 markers seen, median lag 166 s) is also finished. The smoke test is not part of results.csv.
* The paid F2 capacity was not used.
