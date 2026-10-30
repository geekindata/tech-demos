"""Build the Fabric Python notebooks for the mirroring lag test (no secrets inside).
mirror_seed.ipynb     : create dbo.table_a, seed 1,000,000 rows, time the initial snapshot to the SQL analytics endpoint
mirror_workload.ipynb : seeded insert/update/delete bursts at given rates with heartbeat markers, poll the endpoint, log lag
mirror_cold.ipynb     : single markers after a long idle gap (cold probes)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent)); import nbutil
NB = pathlib.Path(__file__).resolve().parent.parent / 'notebooks'

PARAMS = '''# Parameters (overridden by the RunNotebook job)
src_server = ""      # serverFqdn of mirror_src_db (from GET /sqlDatabases)
src_db = ""          # databaseName of mirror_src_db
ep_server = ""       # SQL analytics endpoint host (GET /sqlEndpoints/{id}/connectionString)
ep_db = "mirror_src_db"
seed = 42
job = "workload"
rates = "10,100,1000"   # rows/s, run order is interleaved per repeat
repeats = 3
run_s = 150             # burst length per run
gap_s = 60              # idle between runs
marker_every_s = 10
poll_s = 2
tail_timeout_s = 600
idle_s = 600            # cold probes only
n_probes = 3            # cold probes only
'''

COMMON = '''import json, struct, time, datetime, random, os, traceback, statistics
import pyodbc, notebookutils
OUT = f"/lakehouse/default/Files/mirror_lag/{job}"
os.makedirs(OUT, exist_ok=True)
def utcnow(): return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
def conn(server, db):
    t = notebookutils.credentials.getToken("https://database.windows.net/")
    b = t.encode("utf-16-le"); ts = struct.pack(f"<I{len(b)}s", len(b), b)
    return pyodbc.connect(f"Driver={{ODBC Driver 18 for SQL Server}};Server={server};Database={db};Encrypt=yes;",
                          attrs_before={1256: ts}, autocommit=True)
def save(name, obj):
    with open(f"{OUT}/{name}", "w") as f:
        json.dump(obj, f, indent=1, default=str)
def offset_src(c, n=5):
    """seconds to add to the source clock to get notebook UTC (min-RTT sample)"""
    best = None
    for _ in range(n):
        t0 = time.time(); s = c.execute("SELECT SYSUTCDATETIME()").fetchone()[0]; t1 = time.time()
        rtt = t1 - t0; off = (t0 + t1) / 2 - s.replace(tzinfo=datetime.timezone.utc).timestamp()
        if best is None or rtt < best[0]: best = (rtt, off)
    return {"rtt_s": round(best[0], 4), "offset_s": round(best[1], 4)}
MARK_BASE = 9_000_000_000
def put_marker(src, mid, tag):
    r = src.execute("SET NOCOUNT ON; INSERT INTO dbo.table_a(id, segment, attribute_a, value, updated_at) "
                    "OUTPUT inserted.updated_at VALUES (?, 'M', ?, 0, SYSUTCDATETIME());", mid, tag).fetchone()
    return r[0]
def replication_dmvs(src):
    res = {}
    for q in ["SELECT TOP 30 * FROM sys.dm_change_feed_log_scan_sessions ORDER BY start_time DESC",
              "SELECT TOP 30 * FROM sys.dm_change_feed_errors ORDER BY entry_time DESC"]:
        try:
            cur = src.execute(q); cols = [d[0] for d in cur.description]
            res[q] = [dict(zip(cols, [str(v) for v in row])) for row in cur.fetchall()]
        except Exception as e:
            res[q] = "ERROR: " + str(e)
    return res
'''

SEED = '''log = {"job": job, "seed": seed}
src = conn(src_server, src_db); ep = conn(ep_server, ep_db)
log["offset"] = offset_src(src)
src.execute("""IF OBJECT_ID('dbo.table_a') IS NULL
CREATE TABLE dbo.table_a (
  id bigint NOT NULL CONSTRAINT pk_table_a PRIMARY KEY CLUSTERED,
  segment char(1) NOT NULL,
  attribute_a varchar(12) NOT NULL,
  value decimal(18,2) NOT NULL,
  updated_at datetime2(6) NOT NULL)""")
n_have = src.execute("SELECT COUNT_BIG(*) FROM dbo.table_a").fetchone()[0]
log["rows_before"] = n_have
t0 = utcnow(); log["seed_start_utc"] = t0
# deterministic seed rows: CHECKSUM of (id, seed) drives every column, so reruns give identical data
for lo in range(1, 1_000_001, 250_000):
    src.execute(f"""SET NOCOUNT ON;
INSERT INTO dbo.table_a(id, segment, attribute_a, value, updated_at)
SELECT g.value,
  CHAR(65 + ABS(CHECKSUM(g.value, {seed}, 1)) % 3),
  CONCAT('attr_', RIGHT(CONCAT('000', ABS(CHECKSUM(g.value, {seed}, 2)) % 1000), 4)),
  CAST(ABS(CHECKSUM(g.value, {seed}, 3)) % 100000 AS decimal(18,2)) / 100,
  DATEADD(second, ABS(CHECKSUM(g.value, {seed}, 4)) % 86400, CAST('2026-01-01' AS datetime2(6)))
FROM GENERATE_SERIES(CAST({lo} AS bigint), CAST({lo + 249_999} AS bigint)) g
WHERE NOT EXISTS (SELECT 1 FROM dbo.table_a t WHERE t.id = g.value);""")
t1 = utcnow(); log["seed_end_utc"] = t1; log["seed_s"] = (t1 - t0).total_seconds()
src_n = src.execute("SELECT COUNT_BIG(*) FROM dbo.table_a").fetchone()[0]; log["src_rows"] = src_n
# poll the SQL analytics endpoint until the full seed is visible
polls = []; seen = None; deadline = time.time() + 1800
while time.time() < deadline:
    ps = utcnow()
    try:
        n = ep.execute(f"SELECT COUNT_BIG(*) FROM dbo.table_a WHERE {len(polls)} = {len(polls)}").fetchone()[0]
        err = None
    except Exception as e:
        n, err = None, str(e)[:300]
    polls.append({"t": ps, "rows": n, "err": err})
    if n == src_n: seen = ps; break
    time.sleep(5)
log["first_full_visible_utc"] = seen
log["initial_snapshot_lag_s"] = (seen - t1).total_seconds() if seen else None
log["polls"] = polls[-20:]; log["n_polls"] = len(polls)
log["dmvs"] = replication_dmvs(src)
save("seed.json", log)
print(json.dumps({k: v for k, v in log.items() if k not in ("dmvs", "polls")}, default=str, indent=1))
'''

WORK = '''import threading
src = conn(src_server, src_db); ep = conn(ep_server, ep_db)
rate_list = [int(x) for x in rates.split(",")]
plan = [(r, rep + 1) for rep in range(repeats) for r in rate_list]
meta = {"job": job, "seed": seed, "plan": plan, "run_s": run_s, "gap_s": gap_s, "poll_s": poll_s,
        "marker_every_s": marker_every_s, "mix": "40% insert, 40% update, 20% delete per 1 s tick"}
runs = []; markers = []
st = src.execute("SELECT ISNULL(MAX(id),0) FROM dbo.table_a WHERE id < ?", MARK_BASE).fetchone()[0]
next_ins = max(st, 1_000_000) + 1
del_ptr = src.execute("SELECT ISNULL(MAX(id), 1000000) FROM dbo.table_a WHERE id BETWEEN 500001 AND 1000000").fetchone()[0] + 1  # deletes walk down from the top of the seed range
# continue marker ids after any earlier job
mk = src.execute("SELECT ISNULL(MAX(id), ?) FROM dbo.table_a WHERE id >= ?", MARK_BASE, MARK_BASE).fetchone()[0] + 1

def poll_until(pending, stop_evt, seen_out, poll_log):
    last_seen = 0; i = 0
    while pending or not stop_evt.is_set():
        if stop_evt.is_set() and not pending: break
        ps = utcnow(); t0 = time.time()
        try:
            rows = ep.execute(f"SELECT id FROM dbo.table_a WHERE id >= {MARK_BASE} AND id > {last_seen} AND {i} = {i}").fetchall()
            err = None
        except Exception as e:
            rows, err = [], str(e)[:300]
        qd = time.time() - t0; i += 1
        poll_log.append((ps, round(qd, 3), len(rows), err))
        for (mid,) in rows:
            if mid in pending:
                seen_out[mid] = (ps, qd); pending.discard(mid)
            last_seen = max(last_seen, mid)
        if stop_evt.is_set() and time.time() > stop_evt.deadline: break
        time.sleep(max(0, poll_s - qd))

for run_idx, (rate, rep) in enumerate(plan):
    rnd = random.Random(seed * 1000 + rate * 10 + rep)
    off = offset_src(src)
    n_ins = round(rate * 0.4); n_upd = round(rate * 0.4); n_del = rate - n_ins - n_upd
    pending = set(); seen = {}; plog = []; mtimes = {}
    stop = threading.Event(); stop.deadline = float("inf")
    th = threading.Thread(target=poll_until, args=(pending, stop, seen, plog), daemon=True); th.start()
    r0 = utcnow(); t_start = time.time(); done = {"ins": 0, "upd": 0, "del": 0}; late = 0; next_mark = 0
    tick = 0
    while True:
        target = t_start + tick
        now = time.time()
        if now - t_start >= run_s: break
        if now < target: time.sleep(target - now)
        elif now - target > 1: late += 1
        if time.time() - t_start >= next_mark:
            m_id = mk; mk += 1
            mtimes[m_id] = put_marker(src, m_id, f"r{run_idx+1}_{rate}"); pending.add(m_id); next_mark += marker_every_s
        ux = rnd.randint(1, 500_000 - n_upd)
        del_ptr -= n_del
        r = src.execute(f"""SET NOCOUNT ON; DECLARE @i int, @u int, @d int;
INSERT INTO dbo.table_a(id, segment, attribute_a, value, updated_at)
SELECT g.value, CHAR(65 + ABS(CHECKSUM(g.value, {seed}, 1)) % 3),
  CONCAT('attr_', RIGHT(CONCAT('000', ABS(CHECKSUM(g.value, {seed}, 2)) % 1000), 4)),
  CAST(ABS(CHECKSUM(g.value, {seed}, 3)) % 100000 AS decimal(18,2)) / 100, SYSUTCDATETIME()
FROM GENERATE_SERIES(CAST({next_ins} AS bigint), CAST({next_ins + n_ins - 1} AS bigint)) g; SET @i = @@ROWCOUNT;
UPDATE dbo.table_a SET value = value + 1, updated_at = SYSUTCDATETIME() WHERE id BETWEEN {ux} AND {ux + n_upd - 1}; SET @u = @@ROWCOUNT;
DELETE FROM dbo.table_a WHERE id BETWEEN {del_ptr} AND {del_ptr + n_del - 1}; SET @d = @@ROWCOUNT;
SELECT @i, @u, @d;""").fetchone()
        next_ins += n_ins
        done["ins"] += r[0]; done["upd"] += r[1]; done["del"] += r[2]; tick += 1
    # final marker marks the end of the burst
    m_id = mk; mk += 1; mtimes[m_id] = put_marker(src, m_id, f"r{run_idx+1}_{rate}_end"); pending.add(m_id)
    r1 = utcnow(); burst_s = time.time() - t_start
    stop.deadline = time.time() + tail_timeout_s; stop.set(); th.join(tail_timeout_s + 60)
    # convergence: endpoint row count equals source row count (covers deletes too)
    src_n = src.execute(f"SELECT COUNT_BIG(*) FROM dbo.table_a").fetchone()[0]
    conv = None; c0 = time.time(); k = 0
    while time.time() - c0 < tail_timeout_s:
        ps = utcnow(); k += 1
        n = ep.execute(f"SELECT COUNT_BIG(*) FROM dbo.table_a WHERE {k} = {k}").fetchone()[0]
        if n == src_n: conv = ps; break
        time.sleep(poll_s)
    lags = []
    for m_id, ct in sorted(mtimes.items()):
        ct_local = ct + datetime.timedelta(seconds=off["offset_s"])
        s = seen.get(m_id)
        lag = (s[0] - ct_local).total_seconds() if s else None
        markers.append({"run_no": rep, "run_idx": run_idx + 1, "rate": rate, "marker_id": m_id, "commit_src_utc": ct,
                        "seen_utc": s[0] if s else None, "lag_s": lag, "poll_query_s": s[1] if s else None,
                        "is_end_marker": m_id == max(mtimes)})
        if lag is not None: lags.append(lag)
    end_ct = mtimes[max(mtimes)] + datetime.timedelta(seconds=off["offset_s"])
    run = {"run_idx": run_idx + 1, "rate": rate, "run_no": rep, "start_utc": r0, "end_utc": r1, "burst_s": round(burst_s, 1),
           "rows_ins": done["ins"], "rows_upd": done["upd"], "rows_del": done["del"],
           "achieved_rows_per_s": round(sum(done.values()) / burst_s, 1), "late_ticks": late,
           "markers": len(mtimes), "markers_seen": len(lags),
           "lag_median_s": round(statistics.median(lags), 2) if lags else None,
           "lag_p95_s": round(sorted(lags)[max(0, int(round(0.95 * len(lags))) - 1)], 2) if lags else None,
           "lag_max_s": round(max(lags), 2) if lags else None, "lag_min_s": round(min(lags), 2) if lags else None,
           "end_marker_lag_s": round((seen[max(mtimes)][0] - end_ct).total_seconds(), 2) if max(mtimes) in seen else None,
           "count_converged_s": round((conv - end_ct).total_seconds(), 2) if conv else None,
           "src_rows_after": src_n, "polls": len(plog), "poll_errors": [p for p in plog if p[3]][:5],
           "poll_query_median_s": statistics.median([p[1] for p in plog]) if plog else None, "clock": off}
    runs.append(run); print(json.dumps(run, default=str))
    save("runs.json", {"meta": meta, "runs": runs}); save("markers.json", markers)
    time.sleep(gap_s)
save("dmvs.json", replication_dmvs(src))
print("done", len(runs))
'''

COLD = '''src = conn(src_server, src_db); ep = conn(ep_server, ep_db)
mk = src.execute("SELECT ISNULL(MAX(id), ?) FROM dbo.table_a WHERE id >= ?", MARK_BASE, MARK_BASE).fetchone()[0] + 1
probes = []
for p in range(n_probes):
    t_idle = utcnow(); time.sleep(idle_s)
    off = offset_src(src)
    ct = put_marker(src, mk, f"cold_{p+1}"); ctl = ct + datetime.timedelta(seconds=off["offset_s"])
    seen = None; i = 0; c0 = time.time()
    while time.time() - c0 < tail_timeout_s:
        ps = utcnow(); i += 1
        if ep.execute(f"SELECT COUNT(*) FROM dbo.table_a WHERE id = {mk} AND {i} = {i}").fetchone()[0]: seen = ps; break
        time.sleep(poll_s)
    probes.append({"probe": p + 1, "idle_from_utc": t_idle, "idle_s": idle_s, "marker_id": mk, "commit_src_utc": ct,
                   "seen_utc": seen, "lag_s": round((seen - ctl).total_seconds(), 2) if seen else None, "polls": i, "clock": off})
    print(json.dumps(probes[-1], default=str)); mk += 1
    save("cold.json", probes)
save("dmvs_cold.json", replication_dmvs(src))
'''
nbutil.write(str(NB / 'mirror_seed.ipynb'), [PARAMS, COMMON, SEED])
nbutil.write(str(NB / 'mirror_workload.ipynb'), [PARAMS, COMMON, WORK])
nbutil.write(str(NB / 'mirror_cold.ipynb'), [PARAMS, COMMON, COLD])
print('ok')
