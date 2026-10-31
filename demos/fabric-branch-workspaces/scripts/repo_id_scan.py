"""Scan a checked-out folder for GUIDs; flag any that equal a real tenant, workspace, item, capacity or connection id."""
import os, re, sys, json, subprocess
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
root = sys.argv[1]
G = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
real = {}
for w in call("workspaces")[2]["value"]:
    real[w["id"].lower()] = "workspace"
    if w["displayName"] in (MAIN_WS(), FEATURE_WS()):
        for i in call(f"workspaces/{w['id']}/items")[2]["value"]: real[i["id"].lower()] = "item " + i["displayName"]
for c in call("capacities")[2]["value"]: real[c["id"].lower()] = "capacity"
for c in (call("connections")[2] or {}).get("value", []): real[c["id"].lower()] = "connection"
tid = subprocess.run([AZ, "account", "show", "--query", "tenantId", "-o", "tsv"], capture_output=True, text=True).stdout.strip().lower()
real[tid] = "tenant"
kinds, bad, lid_hits = {}, [], []
for dp, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(dp, f); t = open(p, errors="replace").read()
        for ln, line in enumerate(t.splitlines(), 1):
            for m in G.finditer(line):
                g = m.group(0).lower(); ctx = line[:m.start()]
                k = "logicalId" if "logicalId" in ctx else "lineageTag" if "lineageTag" in ctx else "other GUID"
                kinds[k] = kinds.get(k, 0) + 1
                if g in real: bad.append(f"{os.path.relpath(p, root)}:{ln} {k} equals {real[g]}")
        for seg in os.path.relpath(p, root).split(os.sep):
            if re.fullmatch(r"[0-9a-f]{20}", seg): kinds["PBIR hex name"] = kinds.get("PBIR hex name", 0) + 1
print("GUIDs by type:", kinds or "none")
print("real ID matches:", bad or "none (no tenant, workspace, item, capacity or connection id found)")
sys.exit(1 if bad else 0)
