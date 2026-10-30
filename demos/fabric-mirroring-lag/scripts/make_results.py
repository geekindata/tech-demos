import math
"""Pull run logs from OneLake, write results/results.csv, results/markers.csv and results/lag_chart.png.
Every number comes from the notebook run logs; nothing is typed in by hand."""
import json, csv, pathlib, statistics, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import ops
R = pathlib.Path(__file__).resolve().parent.parent / 'results'; R.mkdir(exist_ok=True)
RAW = R.parent / 'raw'; RAW.mkdir(exist_ok=True)
OFFLINE = '--offline' in sys.argv   # rebuild from raw/*.json without touching OneLake
def get(rel):
    if OFFLINE:
        f = RAW / ('raw_' + {'seed.json': 'seed.json', 'runs.json': 'runs.json'}.get(rel.split('/')[-1], rel.split('/')[-1]))
        return json.load(open(f)) if f.exists() else None
    try: return json.loads(ops.get_file(rel))
    except Exception as e: print('missing', rel, e); return None
seed = get('mirror_lag/seed/seed.json'); work = get('mirror_lag/workload/runs.json')
markers = get('mirror_lag/workload/markers.json') or []; cold = get('mirror_lag/cold/cold.json') or []
cu = json.load(open(R / 'cu_by_item.json')) if (R / 'cu_by_item.json').exists() else {}
def p95(v): v = sorted(v); return v[math.ceil(0.95 * len(v)) - 1]   # true nearest rank
for name, obj in [] if OFFLINE else [('raw_seed.json', seed), ('raw_runs.json', work), ('raw_markers.json', markers), ('raw_cold.json', cold)]:
    if obj: json.dump(obj, open(RAW / name, 'w'), indent=1, default=str)
for name in [] if OFFLINE else ['mirror_lag/workload/dmvs.json', 'mirror_lag/cold/dmvs_cold.json']:
    d = get(name)
    if d is not None: json.dump(d, open(RAW / ('raw_' + name.split('/')[-1]), 'w'), indent=1)
cols = ['experiment', 'variant', 'run_no', 'warm_or_cold', 'start_utc', 'duration_s', 'cu_s', 'rows', 'notes']
rows = []
if seed:
    rows.append(['mirror_lag', 'initial_snapshot_1M', 1, 'cold', seed['seed_end_utc'], round(seed['initial_snapshot_lag_s'], 2), '',
                 seed['src_rows'], f"seed insert {seed['seed_s']:.1f}s; duration_s = seed commit end to full 1M row count visible on SQL analytics endpoint (5 s polls, new table)"])
for r in (work or {}).get('runs', []):
    n = r['rows_ins'] + r['rows_upd'] + r['rows_del']
    lv = [m['lag_s'] for m in markers if m['run_idx'] == r['run_idx'] and m['lag_s'] is not None]
    r['lag_p95_s'] = round(p95(lv), 2) if lv else r['lag_p95_s']   # notebook used round(0.95n); recompute as nearest rank
    rows.append(['mirror_lag', f"{r['rate']}_rows_per_s", r['run_no'], 'warm', r['start_utc'], r['lag_median_s'], '', n,
                 f"duration_s = median marker lag; p95 {r['lag_p95_s']}s; min {r['lag_min_s']}s; max {r['lag_max_s']}s; "
                 f"markers {r['markers_seen']}/{r['markers']}; end marker {r['end_marker_lag_s']}s; row count converged {r['count_converged_s']}s; "
                 f"achieved {r['achieved_rows_per_s']} rows/s over {r['burst_s']}s (ins {r['rows_ins']} upd {r['rows_upd']} del {r['rows_del']}); late ticks {r['late_ticks']}"])
for p in cold:
    rows.append(['mirror_lag', 'single_marker_after_idle', p['probe'], 'cold', p['commit_src_utc'], p['lag_s'], '', 1,
                 f"one marker row after {p['idle_s']}s idle; {p['polls']} polls at 2 s"])
# per-rate summary over all markers of all runs
summ = {}
for m in markers:
    if m['lag_s'] is not None: summ.setdefault(m['rate'], []).append(m['lag_s'])
for rate, v in sorted(summ.items()):
    rows.append(['mirror_lag', f"{rate}_rows_per_s_all_runs", 0, 'warm', '', round(statistics.median(v), 2), cu.get(str(rate), ''), len(v),
                 f"summary over {len(v)} markers from all runs; p95 {round(p95(v), 2)}s; min {round(min(v), 2)}s; max {round(max(v), 2)}s"])
if cu.get('total'):
    rows.append(['mirror_lag', 'cu_total_by_item', 0, '', cu.get('window', ''), '', cu['total'], '', cu.get('note', '')])
with open(R / 'results.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(cols); w.writerows(rows)
with open(R / 'markers.csv', 'w', newline='') as f:
    w = csv.writer(f); keys = ['run_idx', 'run_no', 'rate', 'marker_id', 'commit_src_utc', 'seen_utc', 'lag_s', 'poll_query_s', 'is_end_marker']
    w.writerow(keys); [w.writerow([m.get(k) for k in keys]) for m in markers]
print(f'{len(rows)} rows -> results.csv; {len(markers)} markers')
if summ:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
    rates = sorted(summ); data = [summ[r] for r in rates]
    ax[0].boxplot(data, tick_labels=[f'{r} rows/s' for r in rates], whis=(5, 95), showfliers=True)
    for i, r in enumerate(rates):
        ax[0].annotate(f"median {statistics.median(summ[r]):.1f}s\np95 {p95(summ[r]):.1f}s", (i + 1, max(summ[r]) + 8), ha='center', va='bottom', fontsize=8)
    ax[0].set_ylim(0, max(max(v) for v in data) * 1.22)
    if cold:
        cv = [p['lag_s'] for p in cold if p['lag_s'] is not None]
        ax[0].scatter([len(rates) + 1] * len(cv), cv, marker='x', color='tab:red')
        ax[0].set_xticks(list(range(1, len(rates) + 2)), [f'{r} rows/s' for r in rates] + ['after idle'])
    ax[0].set_ylabel('lag (s): source commit to visible on endpoint')
    ax[0].set_title('Lag per change rate (all markers, whiskers p5 to p95)')
    from datetime import datetime
    ts = lambda x: datetime.fromisoformat(str(x)).timestamp()
    t0 = min(ts(m['commit_src_utc']) for m in markers)
    for r in rates:
        ms = [m for m in markers if m['rate'] == r and m['lag_s'] is not None]
        ax[1].plot([(ts(m['commit_src_utc']) - t0) / 60 for m in ms], [m['lag_s'] for m in ms], '.', label=f'{r} rows/s')
    ax[1].set_xlabel('marker commit time (minutes since first workload marker)'); ax[1].set_ylabel('lag (s)')
    ax[1].set_title('Each heartbeat marker (sawtooth = changes surface in batches)'); ax[1].legend()
    fig.suptitle('Fabric SQL database to OneLake mirroring lag, 64-CU Fabric trial (North Europe)', fontsize=11)
    fig.tight_layout(); fig.savefig(R / 'lag_chart.png', dpi=130); print('chart ok')
