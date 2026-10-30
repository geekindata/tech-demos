# Shot and clip list: Fabric SQL database mirroring lag

Screens to capture in a separate pass. The trial workspace on the Fabric trial capacity (64 CU). Nothing here needs load running; for a live clip, rerun one short burst (see README, "Rerun one burst").

## Shots

1. Replication monitor. Open the source database in the trial workspace, then "Replication" (Monitor replication). Capture: status Running, table dbo.table_a, Rows replicated, Last completed. Crop out tenant and user names.
2. Workspace view. Trial workspace item list showing the source database (SQL database), its SQL analytics endpoint, the helper lakehouse and the three notebooks. Blur workspace and item names. Capacity badge showing the trial.
3. Lag chart. results/lag_chart.png full frame. Optional close crop on the per rate boxplot.
4. Data appearing. SQL analytics endpoint query editor, query:
   SELECT TOP 20 id, segment, attribute_a, updated_at AS committed_utc, SYSUTCDATETIME() AS now_utc, DATEDIFF(second, updated_at, SYSUTCDATETIME()) AS age_s FROM dbo.table_a WHERE id >= 9000000000 ORDER BY id DESC;
   Shows the marker rows (id 9000000000 and up) that the lag is measured on.
5. Source vs endpoint count. Same COUNT(*) on the SQL database and on the SQL analytics endpoint side by side.
6. DMV output on the source: SELECT * FROM sys.dm_change_feed_log_scan_sessions; and SELECT * FROM sys.dm_change_feed_errors; (empty).
7. Capacity Metrics app. Compute page, filter to the trial capacity, item view for the trial workspace, time window of the run. Capture CU (s) per item and operation.
8. Notebook run history for the workload notebook (Monitor hub) showing the completed run and its duration.

## Clips (screen recording)

A. Data appearing: from the box run scripts/film_run.sh 100 300 (100 rows/s, 300 s burst). Wait 1 to 2 minutes for the notebook session, then keep the endpoint query from shot 4 on screen and re-run it every 10 s. Markers surface in batches about every 2.5 to 5.5 minutes, so a 300 s burst makes sure at least one batch lands on camera; age_s shows each marker's lag. Run the same query on the SQL database (source) side for the instant comparison.
B. Replication monitor refresh, about 20 s: Rows replicated counter changing while a burst runs.
C. Chart reveal, about 10 s: slow push in on results/lag_chart.png.

Stop the burst after the clips (the job ends by itself after run_s seconds).
