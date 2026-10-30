"""Read CU-s per item kind and item for one capacity and date from the Capacity Metrics semantic model (read-only).
Usage: metrics_cu.py <capacity_id> <yyyy-mm-dd>   Token from the Azure CLI, never printed."""
import json, os, subprocess, sys, urllib.request, urllib.error
AZ = '/home/box/tools/azcli/bin/az'; from envcfg import env; DS = env('METRICS_MODEL_ID')   # Capacity Metrics semantic model id, set locally
def tok():
    return subprocess.run([AZ, 'account', 'get-access-token', '--resource', 'https://analysis.windows.net/powerbi/api',
                           '--query', 'accessToken', '-o', 'tsv'], capture_output=True, text=True, check=True).stdout.strip()
def dax(q):
    r = urllib.request.Request(f'https://api.powerbi.com/v1.0/myorg/datasets/{DS}/executeQueries', method='POST',
        data=json.dumps({'queries': [{'query': q}], 'serializerSettings': {'includeNulls': True}}).encode(),
        headers={'Authorization': 'Bearer ' + tok(), 'Content-Type': 'application/json'})
    try: return json.loads(urllib.request.urlopen(r).read().decode('utf-8-sig'))['results'][0]['tables'][0]['rows']
    except urllib.error.HTTPError as e: sys.exit(f'DAX error {e.code}: {e.read().decode()[:800]}')
# Best effort: on Oct 30 2026 this model returned 0 for every item (Metrics data lag or refresh), so ask.py's
# token based CU estimate is the primary guard and this is a cross-check only.
cap, day = sys.argv[1].upper(), sys.argv[2]
y, m, d = map(int, day.split('-'))
rows = dax(f"""EVALUATE SUMMARIZECOLUMNS(Items[Item kind], Items[Item name],
 TREATAS({{"{cap}"}}, Capacities[Capacity Id]), TREATAS({{DATE({y},{m},{d})}}, Dates[Date]),
 "cu_s", [Total CU (Item detail)])""")
tot = 0
for r in sorted(rows, key=lambda r: -(r['[cu_s]'] or 0)):
    v = r['[cu_s]'] or 0; tot += v
    if v: print(f"{r['Items[Item kind]']:<24} {r['Items[Item name]']:<40} {v:12.1f} CU-s")
print(f'total {tot:.1f} CU-s = {tot/3600:.2f} CU-h')
