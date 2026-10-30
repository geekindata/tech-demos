# Fabric SQL database mirroring lag (trial series, experiment 1)

How long does a change committed in a Fabric SQL database take to become queryable on its auto mirrored SQL analytics endpoint, at about 10, 100 and 1,000 changed rows per second?

## Environment (as run on 2026-10-30)

| Item | Value |
|---|---|
| Capacity | Fabric trial, SKU FTL64 (64 CU), region North Europe, id `<capacity-id>` |
| Workspace | demo_mirror_ws (`<workspace-id>`) |
| Source | Fabric SQL database mirror_src_db (`<sql-database-id>`), collation SQL_Latin1_General_CP1_CI_AS |
| Source engine | Microsoft SQL Azure (RTM) 12.0.2000.8, build Sep 17 2026 |
| Target | SQL analytics endpoint mirror_src_db (`<sql-endpoint-id>`) over the OneLake Delta mirror |
| Endpoint engine | Microsoft Azure SQL Data Warehouse (RTM) 12.0.2000.8, build Oct 20 2026 |
| Driver host | Fabric Python notebook (non Spark), Python 3.11.15, pyodbc with ODBC Driver 18 for SQL Server, Entra token from notebookutils |
| Helper lakehouse | mirror_lab_lh (run logs in Files/mirror_lag/) |
| Notebooks | mirror_seed, mirror_workload, mirror_probe (connectivity check) |
| Cost | Trial capacity only. No Azure resources, no tenant changes, zero spend |

## Method

1. Table: dbo.table_a (id bigint PK, segment char(1), attribute_a varchar(12), value decimal(18,2), updated_at datetime2(6)).
2. Seed (notebook mirror_seed, seed 42): 1,000,000 deterministic rows from GENERATE_SERIES in 4 batches of 250k. Then poll the endpoint COUNT(*) every 5 s to time the initial snapshot.
3. Workload (notebook mirror_workload, seed 42): 9 runs, interleaved 10, 100, 1000, 10, 100, 1000, 10, 100, 1000 rows/s. Each run is a 150 s burst, one transaction per 1 s tick, mix 40% insert, 40% update (random contiguous range in ids 1 to 500000), 20% delete (walking down from the top of ids 500001 to 1000000). 60 s idle between runs.
4. Lag probe: every 10 s plus once at the end of each burst, insert a marker row (id 9000000000 and up, segment 'M', updated_at = SYSUTCDATETIME() on the source). A second thread polls the endpoint every 2 s for new marker ids; each poll has a unique predicate so it is never served from a result cache. Lag = first poll that sees the marker minus its source commit time, corrected for the measured clock offset between the two servers (under 4 ms).
5. After each run: wait until the endpoint COUNT(*) equals the source COUNT(*) (count convergence).
6. Replication health: sys.dm_change_feed_log_scan_sessions (TOP 30, which covers the tail of run 7 plus runs 8 and 9) and sys.dm_change_feed_errors on the source, saved as raw/raw_dmvs.json.
7. After the night, read only: scripts/fetch_delta_log.py lists the mirrored table's _delta_log through the OneLake DFS API and downloads the commit files for the measured window; scripts/delta_commits.py writes results/delta_commits.csv and matches each marker to the first Delta commit that contains it.
8. scripts/make_results.py pulls the JSON logs from OneLake and writes results/results.csv, results/markers.csv and results/lag_chart.png. No number is typed in by hand.

## Results (real runs, 2026-10-30, 20:55 to 21:52 Oslo time, UTC+1)

Lag = source commit to visible on the SQL analytics endpoint, in seconds, 17 markers per run, all 153 markers seen. p95 is true nearest rank (ceil(0.95 n)); with 17 markers per run that equals the run max.

| Rate | Run 1 median / p95 | Run 2 median / p95 | Run 3 median / p95 | All 51 markers median / p95 | Min | Max |
|---|---|---|---|---|---|---|
| 10 rows/s | 218.4 / 296.4 | 156.0 / 234.0 | 112.0 / 178.0 | 158.0 / 276.4 | 32.0 | 296.4 |
| 100 rows/s | 184.0 / 264.0 | 104.6 / 204.6 | 110.0 / 180.0 | 130.0 / 244.0 | 18.0 | 264.0 |
| 1000 rows/s | 98.0 / 214.0 | 102.0 / 212.0 | 100.0 / 184.0 | 100.0 / 212.0 | 20.0 | 214.0 |

Headline figures are the pooled ones (all 3 runs, 51 markers per rate). Slowest of all 153 markers: 296.4 s.

* Initial snapshot: 1,000,000 rows inserted in 5.5 s, in the mirrored Delta table (ReplaceTable commit) about 46 s after the seed commit, full count visible on the endpoint 125.3 s after the seed commit.
* Achieved rates: 10.1, 100.6 to 100.7, 1006.4 to 1006.5 rows/s, zero late ticks, zero poll errors.
* Count convergence after each burst: 88 s to 216 s.
* Replication health (DMV sample of runs 7 to 9 only: 30 scan sessions, 21:36 to 21:49 Oslo): every scan session Done, error_count 0, rows_left_to_publish 0, sys.dm_change_feed_errors empty, sessions every 15 s with reported latency median 0 s, max 15 s.
* Shape: new markers surface on the endpoint in 15 batches (distinct seen times clustered within 10 s), 150.8 s to 329.1 s apart, median 187.8 s. That produces the sawtooth on the right of the chart.
* Where the time goes (results/delta_commits.csv, 102 commits, versions 0 to 101, read through the OneLake DFS API at `https://onelake.dfs.fabric.microsoft.com/<workspace-id>/<sql-database-id>/Tables/dbo/table_a/_delta_log/`, the mirrored Delta table of the SQL database item itself, no shortcut): during every burst the replicator committed to the mirrored Delta table every 12 to 16 s (median 15.0 s, 89 in-burst gaps, 11 to 12 commits per run). Each marker was in Delta 7.4 to 28.9 s after its source commit (median 18.5 s, p95 27.3 s). From Delta to visible on the endpoint took 2.8 to 278.6 s (median 116.3 s, p95 218.6 s), a median 86% of each marker's lag. Each endpoint batch picked up 1 to 11 Delta commits at once (median 6.5). So the 150 to 330 s batching sits between the Delta table and the SQL analytics endpoint, not in replication.
* Which metadata sync the endpoint used is not confirmed: a one off read only check found the new sync objects (sys.dm_db_external_tables_log_status, sys.sp_dw_refresh_ext_table) on the endpoint, but the DMV listed zero tables (results/sync_check.json, NOTES.md).
* Rate trend: in each of the 3 rounds the median fell from 10 to 100 to 1000 rows/s, but the order inside every round was always 10, 100, 1000 and each run's markers fall into only 1 to 3 batches, so treat it as an observation, not a cause.
* CU: any CU in the mirroring window is harness cost (the endpoint polls, the notebook sessions and the SQL database workload), not replication cost. Mirroring a Fabric SQL database to OneLake has no compute cost ([Learn FAQ](https://learn.microsoft.com/en-us/fabric/database/sql/mirroring-faq#what-are-the-costs-associated-with-mirroring)). The Capacity Metrics model query returned no rows at report time; see NOTES.md.

## Rerun from scratch

All commands from the box, folder /workspace/demos/fabric-mirroring-lag.

```bash
export PATH=/home/box/tools/azcli/bin:$PATH        # az login already done; tokens are fetched in scripts/ops.py, never printed
python3 scripts/build_notebooks.py                  # writes notebooks/*.ipynb
python3 scripts/ops.py upsert mirror_seed notebooks/mirror_seed.ipynb
python3 scripts/ops.py upsert mirror_workload notebooks/mirror_workload.ipynb
cp scripts/env.example scripts/env.local            # fill in from the REST calls listed in scripts/env.sh
source scripts/env.sh
python3 scripts/ops.py run mirror_seed "{\"src_server\":[\"$SRC_SERVER\",\"string\"],\"src_db\":[\"$SRC_DB\",\"string\"],\"ep_server\":[\"$EP_SERVER\",\"string\"],\"job\":[\"seed\",\"string\"]}"
python3 scripts/ops.py run mirror_workload "{\"src_server\":[\"$SRC_SERVER\",\"string\"],\"src_db\":[\"$SRC_DB\",\"string\"],\"ep_server\":[\"$EP_SERVER\",\"string\"],\"job\":[\"workload\",\"string\"]}"
python3 scripts/ops.py status <Location URL printed by run>
/workspace/.venv-mirror/bin/python scripts/make_results.py   # needs matplotlib (venv); --offline rebuilds from raw/
python3 scripts/fetch_delta_log.py 2026-10-30T19:54 2026-10-30T20:54   # read only, about 100 small OneLake reads
python3 scripts/delta_commits.py
```

The workload job takes about 55 minutes and stops by itself. The seed is idempotent only on an empty table; drop dbo.table_a first for a clean rerun.

## Rerun one burst (for filming)

```bash
scripts/film_run.sh 100 180     # rate rows/s, burst seconds; logs to Files/mirror_lag/film_<UTC time>/
python3 scripts/ops.py status "$(cat /tmp/film_loc)"
```

Same code path as the measured runs (mirror_workload with rates=100, repeats=1, gap_s=0). The notebook session needs about 1 to 2 minutes to start. The job stops by itself after the burst plus the tail wait for the last marker.

## Files

* results/results.csv: experiment, variant, run_no, warm_or_cold, start_utc, duration_s, cu_s, rows, notes. duration_s is the lag in seconds (median marker lag for run rows).
* results/markers.csv: every marker with commit time, seen time and lag.
* results/delta_commits.csv: one row per mirrored Delta commit in the window: version, commit time UTC and Oslo (from the commit file's OneLake lastModified, because the replicator's commitInfo has no timestamp field), operation, new_file_rows (numRecords of newly added files; numOutputRows is not written by this replicator), files added and removed, newest source updated_at in the commit, run_idx, run_no and rate, and how many markers first appear in that commit.
* results/lag_summary.csv: numeric median, p95, min, max and mean per rate, per run and pooled.
* results/lag_chart.png: per rate boxplot and per marker timeline.
* raw/ (not in the repo): JSON logs exactly as written by the notebooks, the downloaded _delta_log files and the screen clips. Rebuild with make_results.py and fetch_delta_log.py.
* NOTES.md: caveats. SHOTS.md: shot and clip list.
* scripts/: ops.py (Fabric REST and OneLake helper), build_notebooks.py, nbutil.py, build_probe.py, metrics_dax.py, make_results.py, fetch_delta_log.py, delta_commits.py, film_run.sh, env.sh and env.example (copy to env.local, which is gitignored).

## lag_summary.csv
results/lag_summary.csv has numeric median_s, p95_s, min_s, max_s and mean_s columns per rate, per run (scope single_run) and pooled over all 3 runs (scope all_runs_pooled, 51 markers). p95 is true nearest rank (ceil(0.95 n)), the same method as make_results.py, so pooled p95 is 276.4 / 244.0 / 212.0 s. Headline numbers in posts and videos use the pooled rows. results.csv keeps the fairness-brief columns unchanged.
