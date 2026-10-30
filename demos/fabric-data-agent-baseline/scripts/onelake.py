"""OneLake DFS helper (list, download, upload). Token comes from the Azure CLI and is never printed."""
import json, os, pathlib, subprocess, sys, urllib.request, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import fab
AZ = '/home/box/tools/azcli/bin/az'
HOST = 'https://onelake.dfs.fabric.microsoft.com'
_T = None
def tok():
    global _T
    _T = _T or subprocess.run([AZ, 'account', 'get-access-token', '--resource', 'https://storage.azure.com',
                               '--query', 'accessToken', '-o', 'tsv'], capture_output=True, text=True, check=True).stdout.strip()
    return _T
def req(method, url, data=None, extra=None):
    h = {'Authorization': 'Bearer ' + tok(), 'x-ms-version': '2023-11-03'}; h.update(extra or {})
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(r) as resp: return resp.status, resp.read()
def ws_id(name): return [w for w in fab.call('GET', '/workspaces')[1]['value'] if w['displayName'] == name][0]['id']
def lh_id(ws, name):
    m = [i for i in fab.call('GET', f'/workspaces/{ws}/lakehouses')[1]['value'] if i['displayName'] == name]
    return m[0]['id'] if m else None
def ls(ws, path, recursive=True):
    out, cont = [], None
    while True:
        u = f'{HOST}/{ws}?resource=filesystem&recursive={str(recursive).lower()}&directory={urllib.parse.quote(path)}'
        if cont: u += '&continuation=' + urllib.parse.quote(cont)
        h = {'Authorization': 'Bearer ' + tok(), 'x-ms-version': '2023-11-03'}
        with urllib.request.urlopen(urllib.request.Request(u, headers=h)) as resp:
            j = json.load(resp); cont = resp.headers.get('x-ms-continuation')
        out += j.get('paths', [])
        if not cont: return out
def download(ws, remote, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    _, b = req('GET', f'{HOST}/{ws}/{urllib.parse.quote(remote)}'); open(local, 'wb').write(b); return len(b)
def upload(ws, remote, local):
    b = open(local, 'rb').read(); u = f'{HOST}/{ws}/{urllib.parse.quote(remote)}'
    req('PUT', u + '?resource=file', b'', {'Content-Length': '0'})
    if b: req('PATCH', u + '?action=append&position=0', b, {'Content-Length': str(len(b))})
    req('PATCH', u + f'?action=flush&position={len(b)}', b'', {'Content-Length': '0'})
    return len(b)
