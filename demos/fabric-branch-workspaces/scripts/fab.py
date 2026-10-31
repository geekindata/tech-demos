"""Minimal Fabric REST helper. Token from az per process, never printed.
Workspace names come from env.local (gitignored), see env.example."""
import json, os, subprocess, time, urllib.request, urllib.error
AZ = "/home/box/tools/azcli/bin/az"
_t = None
def tok():
    global _t
    if not _t:
        _t = subprocess.run([AZ, "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
                             "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True).stdout.strip()
    return _t
def call(path, method="GET", body=None, raw=False):
    url = path if path.startswith("http") else "https://api.fabric.microsoft.com/v1/" + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok(), "Content-Type": "application/json"},
                               method=method, data=data)
    try:
        resp = urllib.request.urlopen(r)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()[:800]
    b = resp.read()
    return resp.status, dict(resp.headers), (json.loads(b) if b else None)
def lro(path, method="POST", body=None):
    s, h, b = call(path, method, body)
    if s != 202:
        return s, b
    loc = h.get("Location"); 
    for _ in range(120):
        time.sleep(int(h.get("Retry-After", 3)) if False else 3)
        s2, h2, b2 = call(loc)
        st = (b2 or {}).get("status") if isinstance(b2, dict) else None
        if st in ("Succeeded", "Failed", "Cancelled"):
            if st == "Succeeded":
                s3, _, b3 = call(loc + "/result")
                return (s3, b3) if s3 == 200 else (200, b2)
            return 500, b2
    return 408, None
def ws_id(name):
    s, _, b = call("workspaces")
    return [w for w in b["value"] if w["displayName"] == name][0]["id"]
def env(key):
    """Read a setting from env.local next to scripts/ (or the process environment)."""
    if key in os.environ: return os.environ[key]
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "env.local")
    for line in open(p):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == key: return v.strip()
    raise KeyError(key + " missing in env.local (copy env.example)")
MAIN_WS = lambda: env("MAIN_WS")
FEATURE_WS = lambda: env("FEATURE_WS")
