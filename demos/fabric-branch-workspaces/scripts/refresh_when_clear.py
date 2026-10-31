"""Step 2: one tiny refresh of demo_model, only when no notebook in the MIRROR_WS workspace (env.local) is InProgress."""
import json, subprocess, sys, time, datetime, urllib.request, urllib.error
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); import fab
LOG = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "results", "refresh_log.txt")
def log(m):
    open(LOG, "a").write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S Oslo ") + m + "\n")
def busy():
    fab._t = None
    m = fab.ws_id(fab.env("MIRROR_WS"))
    for it in fab.call(f"workspaces/{m}/items?type=Notebook")[2]["value"]:
        j = fab.call(f"workspaces/{m}/items/{it['id']}/jobs/instances")[2] or {}
        if any(x["status"] in ("InProgress", "NotStarted") for x in j.get("value", [])):
            return it["displayName"]
    return None
def pbi(path, method="GET", body=None):
    t = subprocess.run([fab.AZ, "account", "get-access-token", "--resource", "https://analysis.windows.net/powerbi/api",
                        "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True).stdout.strip()
    r = urllib.request.Request("https://api.powerbi.com/v1.0/myorg/" + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + t, "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(r); b = resp.read(); return resp.status, (json.loads(b) if b else None)
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:300]
deadline = time.time() + float(sys.argv[1] if len(sys.argv) > 1 else 4) * 3600
log("watcher start")
while True:
    b = busy()
    if not b: break
    if time.time() > deadline: log(f"gave up, {b} still running; refresh NOT done"); sys.exit(1)
    time.sleep(120)
W = fab.ws_id(MAIN_WS())
mid = [i for i in fab.call(f"workspaces/{W}/items?type=SemanticModel")[2]["value"] if i["displayName"] == "demo_model"][0]["id"]
if busy(): log("lag run started at the last moment, retry later"); sys.exit(1)
s, b = pbi(f"groups/{W}/datasets/{mid}/refreshes", "POST", {"notifyOption": "NoNotification"})
log(f"refresh POST {s}")
for _ in range(60):
    time.sleep(10)
    s, b = pbi(f"groups/{W}/datasets/{mid}/refreshes?$top=1")
    r = b["value"][0] if s == 200 and b.get("value") else {}
    if r.get("status") in ("Completed", "Failed", "Disabled"):
        log(f"refresh {r['status']} start {r.get('startTime')} end {r.get('endTime')} (UTC)")
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        open(fab.env("CU_LEDGER"), "a").write(
            f"{now},{now[:10]},,,,,60.0,est_pending_metrics,demo_model,branch_ws_step2_refresh_{r['status']},{(r.get('startTime') or '')[:19]}Z,{(r.get('endTime') or '')[:19]}Z,5\n")
        break
log("watcher end")
