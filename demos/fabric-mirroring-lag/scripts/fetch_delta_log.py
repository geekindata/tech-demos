"""Read only: list the mirrored dbo.table_a _delta_log of source_db through the OneLake DFS API and
download the commit JSONs whose lastModified falls in a UTC window, into raw/delta_log/ (gitignored).
Usage: python3 scripts/fetch_delta_log.py 2026-10-30T19:54 2026-10-30T20:54
Path: https://onelake.dfs.fabric.microsoft.com/<workspace-id>/<sql-database-id>/Tables/dbo/table_a/_delta_log/
Ids are looked up by REST at run time; the storage token comes from the Azure CLI and is never printed."""
import sys, os, json, urllib.request, urllib.parse, email.utils, datetime as d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ops
lo, hi = (d.datetime.fromisoformat(a).replace(tzinfo=d.timezone.utc) for a in sys.argv[1:3])
W = ops.ws(); S = ops.item('SQLDatabase', 'source_db')
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'raw', 'delta_log'); os.makedirs(out, exist_ok=True)
H = lambda: {'Authorization': 'Bearer ' + ops.tok('https://storage.azure.com'), 'x-ms-version': '2023-11-03'}
base = f'https://onelake.dfs.fabric.microsoft.com/{W}'; log = f'{S}/Tables/dbo/table_a/_delta_log'
paths, cont = [], None
while True:
    q = {'resource': 'filesystem', 'directory': log, 'recursive': 'false'}
    if cont: q['continuation'] = cont
    with urllib.request.urlopen(urllib.request.Request(base + '?' + urllib.parse.urlencode(q), headers=H())) as r:
        paths += json.loads(r.read())['paths']; cont = r.headers.get('x-ms-continuation')
    if not cont: break
fs = sorted((p['name'].split('/')[-1], email.utils.parsedate_to_datetime(p['lastModified']), int(p.get('contentLength', 0))) for p in paths)
json.dump([(n, t.isoformat(), z) for n, t, z in fs], open(os.path.join(out, '_listing.json'), 'w'))
sel = [n for n, t, _ in fs if n.endswith('.json') and lo <= t <= hi]
for n in sel:
    open(os.path.join(out, n), 'wb').write(urllib.request.urlopen(urllib.request.Request(f'{base}/{log}/{n}', headers=H())).read())
print(f'listed {len(fs)} entries, downloaded {len(sel)} commit files')
