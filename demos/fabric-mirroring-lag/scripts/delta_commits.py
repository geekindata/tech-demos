"""Parse downloaded _delta_log commit JSONs (raw/delta_log/) of the mirrored dbo.table_a and match them
to the lag markers. Read only; the download is done with scripts/ops.py style OneLake DFS GETs.
commitInfo from this replicator carries no timestamp field, so the commit time is the commit file's
OneLake lastModified (1 s resolution) and, as a cross check, the newest add.modificationTime (ms)."""
import json, csv, glob, os, datetime as d, statistics as st
UTC = d.timezone.utc; OSLO = d.timezone(d.timedelta(hours=1))
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
listing = {n: d.datetime.fromisoformat(t) for n, t, _ in json.load(open(f'{root}/raw/delta_log/_listing.json'))}
P = lambda s: d.datetime.fromisoformat(s).replace(tzinfo=UTC)
runs = [r for r in csv.DictReader(open(f'{root}/results/results.csv')) if r['start_utc'] and r['warm_or_cold'] == 'warm']
runs.sort(key=lambda r: r['start_utc'])
win = [(P(r['start_utc']), P(r['start_utc']) + d.timedelta(seconds=150), i + 1, int(r['run_no']), r['variant'].split('_')[0]) for i, r in enumerate(runs)]
seed = [r for r in csv.DictReader(open(f'{root}/results/results.csv')) if r['warm_or_cold'] == 'cold'][0]
def which(t):
    for a, b, i, n, rate in win:
        if a - d.timedelta(seconds=1) <= t <= b + d.timedelta(seconds=1): return i, n, rate
    return '', '', ('seed' if t < win[0][0] else 'idle_gap')
out = []
for f in sorted(glob.glob(f'{root}/raw/delta_log/0*.json')):
    n = os.path.basename(f); acts = [json.loads(l) for l in open(f) if l.strip()]
    ci = next((a['commitInfo'] for a in acts if 'commitInfo' in a), {})
    adds = [a['add'] for a in acts if 'add' in a]; rem = {a['remove']['path'] for a in acts if 'remove' in a}
    new = [a for a in adds if a['path'] not in rem]
    st_ = [json.loads(a['stats']) for a in new if a.get('stats')]
    upd = [s['maxValues'].get('updated_at') for s in st_ if s.get('maxValues', {}).get('updated_at')]
    mx = max(upd) if upd else ''
    mod = max((a['modificationTime'] for a in adds), default=None)
    t = listing[n].astimezone(UTC)
    ts = ci.get('timestamp'); tci = d.datetime.fromtimestamp(ts / 1000, UTC) if ts else None
    src_hi = P(mx) if mx else None
    ri, rn, rate = which(src_hi) if src_hi else ('', '', '')
    out.append(dict(version=int(n.split('.')[0]), commit_utc=(tci or t).strftime('%Y-%m-%d %H:%M:%S'),
        commit_oslo=(tci or t).astimezone(OSLO).strftime('%Y-%m-%d %H:%M:%S'), time_source='commitInfo.timestamp' if tci else 'file_lastModified',
        max_add_modificationTime_utc=d.datetime.fromtimestamp(mod / 1000, UTC).strftime('%H:%M:%S.%f')[:-3] if mod else '',
        operation=ci.get('operation', ''), new_file_rows=sum(s.get('numRecords', 0) for s in st_),
        numOutputRows=(ci.get('operationMetrics') or {}).get('numOutputRows', ''), files_added=len(adds), files_removed=len(rem),
        src_max_updated_at_utc=mx[:23], run_idx=ri, run_no=rn, rate=rate, _t=(tci or t), _src=src_hi))
out.sort(key=lambda r: r['version'])
# markers: first Delta commit whose newest source change time >= marker commit time
mk = list(csv.DictReader(open(f'{root}/results/markers.csv')))
for m in mk:
    c = P(m['commit_src_utc']); hit = next((r for r in out if r['_src'] and r['_src'] >= c - d.timedelta(milliseconds=5)), None)
    m['delta_utc'] = hit['_t'] if hit else None; m['delta_version'] = hit['version'] if hit else ''
seen = {}
for m in mk: seen.setdefault(m['seen_utc'], []).append(m)
for r in out:
    r['markers_first_in_delta'] = sum(1 for m in mk if m['delta_version'] == r['version'])
with open(f'{root}/results/delta_commits.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, [k for k in out[0] if not k.startswith('_')]); w.writeheader()
    for r in out: w.writerow({k: v for k, v in r.items() if not k.startswith('_')})
# summary
ws = [r for r in out if r['_t'] >= win[0][0] and r['_t'] <= win[-1][1] + d.timedelta(seconds=330)]
gaps = [(b['_t'] - a['_t']).total_seconds() for a, b in zip(ws, ws[1:]) if a['run_idx'] and a['run_idx'] == b['run_idx'] and b['operation'] == 'Merge']
print('commits per run', {i: sum(1 for r in out if r['run_idx'] == i) for i in range(1, 10)})
c2d = [(m['delta_utc'] - P(m['commit_src_utc'])).total_seconds() for m in mk if m['delta_utc']]
d2e = [(P(m['seen_utc']) - m['delta_utc']).total_seconds() for m in mk if m['delta_utc']]
lag = [float(m['lag_s']) for m in mk if m['delta_utc']]
q = lambda v: (round(min(v), 1), round(st.median(v), 1), round(sorted(v)[-(-95 * len(v) // 100) - 1], 1), round(max(v), 1))
print('commits in file', len(out), 'versions', out[0]['version'], out[-1]['version'])
print('in-burst Merge gaps n', len(gaps), 'min/median/p95/max', q(gaps))
print('markers matched', len(c2d), 'of', len(mk))
print('commit->delta min/med/p95/max', q(c2d)); print('delta->endpoint', q(d2e))
print('share of lag after delta median', round(st.median([b / l for b, l in zip(d2e, lag)]) * 100, 1), '%')
print('ops', {o: sum(1 for r in out if r['operation'] == o) for o in {r['operation'] for r in out}})
neg = [x for x in d2e if x < 0]; print('negative delta->endpoint', len(neg))
# endpoint batches (seen_utc clusters <= 10 s apart) vs Delta commits landed since the previous batch
sv = sorted({P(m['seen_utc']) for m in mk}); cl = [[sv[0]]]
for s in sv[1:]: (cl[-1].append(s) if (s - cl[-1][-1]).total_seconds() <= 10 else cl.append([s]))
prev, per = None, []
for c in cl:
    per.append(sum(1 for r in out if r['_t'] <= c[0] and (prev is None or r['_t'] > prev))); prev = c[0]
bg = [(b[0] - a[0]).total_seconds() for a, b in zip(cl, cl[1:])]
print('endpoint batches', len(cl), 'gap min/median/max', round(min(bg), 1), round(st.median(bg), 1), round(max(bg), 1),
      '| Delta commits per batch after the first: min/median/max', min(per[1:]), st.median(per[1:]), max(per[1:]))
