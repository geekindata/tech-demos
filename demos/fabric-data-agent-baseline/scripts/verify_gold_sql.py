"""Run each gold_sql (T-SQL) on the agent_lakehouse SQL endpoint and compare with the DuckDB gold_answer in questions.csv."""
import csv, os, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
os.environ.setdefault('AZ_BIN', '/home/box/tools/azcli/bin/az')
import fab, tsql
here = pathlib.Path(__file__).resolve().parent.parent
ws = open(here / 'scripts/agent_ws_id').read().strip()
lh = [i for i in fab.call('GET', f'/workspaces/{ws}/lakehouses')[1]['value'] if i['displayName'] == 'agent_lakehouse'][0]
server = lh['properties']['sqlEndpointProperties']['connectionString']
c = tsql.connect(server, 'agent_lakehouse'); cur = c.cursor()
def fmt(rows, cols):
    if len(rows) == 1 and len(cols) == 1: return str(rows[0][0])
    return '; '.join(', '.join(f'{k}={v}' for k, v in zip(cols, r)) for r in rows)
for t in ['region', 'nation', 'supplier', 'customer', 'part', 'orders', 'lineitem']:
    cur.execute(f'SELECT COUNT(*) FROM {t}'); print(t, cur.fetchone()[0])
ok = 0
for r in csv.DictReader(open(here / 'questions.csv')):
    t0 = time.time(); cur.execute(r['gold_sql']); cols = [d[0] for d in cur.description]
    got = fmt([tuple(x) for x in cur.fetchall()], cols); same = got == r['gold_answer']; ok += same
    print(r['q_id'], 'MATCH' if same else 'DIFF', round(time.time() - t0, 1), '' if same else f'\n  sql={got}\n  duck={r["gold_answer"]}')
print('matches', ok, '/ 20')
