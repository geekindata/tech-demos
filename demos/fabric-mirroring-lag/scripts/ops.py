"""Box-side ops for the mirroring lag demo: upload/run Fabric notebooks, read OneLake files.
Token comes from the Azure CLI and is never printed."""
import sys, json, base64, time, subprocess, urllib.request, urllib.error, os
AZ = os.environ.get('AZ_BIN', '/home/box/tools/azcli/bin/az')
def _load_env_local():
    # Fill os.environ from scripts/env.local (gitignored) for anything not already set.
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.local')
    if os.path.exists(f):
        for line in open(f):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env_local()
def env(name):
    v = os.environ.get(name)
    if not v: sys.exit(f'set {name} in scripts/env.local or the environment (see scripts/env.example)')
    return v
WS_NAME = os.environ.get('FABRIC_WORKSPACE', ''); LH_NAME = os.environ.get('HELPER_LAKEHOUSE', '')
_T = {}
def tok(res='https://api.fabric.microsoft.com'):
    if res not in _T:
        _T[res] = subprocess.run([AZ, 'account', 'get-access-token', '--resource', res, '--query', 'accessToken', '-o', 'tsv'],
                                 capture_output=True, text=True, check=True).stdout.strip()
    return _T[res]
def call(method, path, body=None):
    url = path if path.startswith('http') else 'https://api.fabric.microsoft.com/v1' + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
        headers={'Authorization': 'Bearer ' + tok(), 'Content-Type': 'application/json', 'x-ms-fabric-skill': 'sqldb-cli'})
    try:
        with urllib.request.urlopen(r) as resp:
            t = resp.read().decode(); return resp.status, (json.loads(t) if t else None), dict(resp.headers)
    except urllib.error.HTTPError as e:
        t = e.read().decode()
        try: j = json.loads(t)
        except Exception: j = t
        return e.code, j, dict(e.headers)
def ws():
    env('FABRIC_WORKSPACE'); s, j, _ = call('GET', '/workspaces'); return [w for w in j['value'] if w['displayName'] == WS_NAME][0]['id']
def item(typ, name):
    s, j, _ = call('GET', f'/workspaces/{ws()}/items?type={typ}')
    m = [x for x in j['value'] if x['displayName'] == name]; return m[0]['id'] if m else None
def upsert(name, path):
    nb = json.load(open(path)); W = ws(); L = item('Lakehouse', env('HELPER_LAKEHOUSE'))
    nb['metadata'].setdefault('dependencies', {})['lakehouse'] = {'default_lakehouse': L, 'default_lakehouse_name': LH_NAME, 'default_lakehouse_workspace_id': W}
    d = {'format': 'ipynb', 'parts': [{'path': 'notebook-content.ipynb', 'payload': base64.b64encode(json.dumps(nb).encode()).decode(), 'payloadType': 'InlineBase64'}]}
    i = item('Notebook', name)
    if i: s, j, h = call('POST', f'/workspaces/{W}/notebooks/{i}/updateDefinition', {'definition': d})
    else: s, j, h = call('POST', f'/workspaces/{W}/notebooks', {'displayName': name, 'definition': d})
    print('upsert', s, j if s >= 400 else '')
    loc = h.get('Location')
    while s == 202 and loc:
        time.sleep(5); s2, j2, _ = call('GET', loc)
        if isinstance(j2, dict) and j2.get('status') in ('Succeeded', 'Failed'): print(j2.get('status')); break
    return item('Notebook', name)
def run(name, params):
    W = ws(); i = item('Notebook', name)
    body = {'executionData': {'parameters': {k: {'value': str(v), 'type': t} for k, (v, t) in params.items()}}}
    s, j, h = call('POST', f'/workspaces/{W}/items/{i}/jobs/instances?jobType=RunNotebook', body)
    print('run', s, j if s >= 400 else ''); return h.get('Location')
def get_file(rel):
    url = f"https://onelake.dfs.fabric.microsoft.com/{env('FABRIC_WORKSPACE')}/{env('HELPER_LAKEHOUSE')}.Lakehouse/Files/{rel}"
    r = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok('https://storage.azure.com'), 'x-ms-version': '2023-11-03'})
    return urllib.request.urlopen(r).read().decode()
if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'upsert': print(upsert(sys.argv[2], sys.argv[3]))
    elif c == 'run': print(run(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}))
    elif c == 'status': s, j, _ = call('GET', sys.argv[2]); print(json.dumps(j, indent=1))
    elif c == 'get': sys.stdout.write(get_file(sys.argv[2]))
