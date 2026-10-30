"""Run a DAX query against the Fabric Capacity Metrics semantic model (read-only, executeQueries)."""
import os, sys, json, urllib.request, urllib.error, ops
DS = os.environ.get('METRICS_DATASET_ID')  # Capacity Metrics semantic model id, set in scripts/env.local
if not DS: sys.exit('set METRICS_DATASET_ID (see scripts/env.example)')
def dax(q):
    body = json.dumps({'queries': [{'query': q}], 'serializerSettings': {'includeNulls': True}}).encode()
    r = urllib.request.Request(f'https://api.powerbi.com/v1.0/myorg/datasets/{DS}/executeQueries', data=body, method='POST',
        headers={'Authorization': 'Bearer ' + ops.tok('https://analysis.windows.net/powerbi/api'), 'Content-Type': 'application/json'})
    try:
        return json.loads(urllib.request.urlopen(r).read().decode('utf-8-sig'))['results'][0]['tables'][0]['rows']
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'body': e.read().decode()[:1500]}
if __name__ == '__main__':
    print(json.dumps(dax(sys.argv[1]), indent=1)[:int(sys.argv[2]) if len(sys.argv) > 2 else 6000])
