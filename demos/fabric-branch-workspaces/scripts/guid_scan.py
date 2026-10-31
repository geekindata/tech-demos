"""Step 3: getDefinition for every item in a workspace (default: the main workspace), then classify every GUID and 32 hex name."""
import json, base64, re, os, sys, datetime
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
LABEL = sys.argv[1] if len(sys.argv) > 1 else "main"  # main or feature
WSN = MAIN_WS() if LABEL == "main" else FEATURE_WS(); W = ws_id(WSN)
items = [i for i in call(f"workspaces/{W}/items")[2]["value"] if i["type"] != "SQLEndpoint"]
G = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
H = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{20,32}(?![0-9a-fA-F])")
mask = lambda g: "********-" + g[-4:]
known = {W.lower(): "workspace id"}
s, _, me = call("workspaces/" + W)
if me.get("capacityId"): known[me["capacityId"].lower()] = "capacity id"
for i in items: known[i["id"].lower()] = f"item id of {i['displayName']}"
out = {"scanned_local": datetime.datetime.now().strftime("%Y-%m-%d %H:%M Oslo"), "items": []}
for it in items:
    q = "?format=TMDL" if it["type"] == "SemanticModel" else ""
    s, b = lro(f"workspaces/{W}/items/{it['id']}/getDefinition{q}")
    rec = {"item": it["displayName"], "type": it["type"], "getDefinition": s, "parts": [], "findings": []}
    if s != 200: rec["error"] = str(b)[:300]; out["items"].append(rec); continue
    base = f"defs/{it['displayName']}.{it['type']}"
    for p in b["definition"]["parts"]:
        txt = base64.b64decode(p["payload"]).decode("utf-8", "replace")
        fp = os.path.join(base, p["path"]); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, "w").write(txt)
        rec["parts"].append(p["path"])
        for ln, line in enumerate(txt.splitlines(), 1):
            for m in G.finditer(line):
                g = m.group(0).lower(); ctx = line[:m.start()]
                if p["path"].endswith(".platform") and "logicalId" in ctx: kind = "logicalId"
                elif "lineageTag" in ctx: kind = "lineageTag"
                elif g in known: kind = "known id: " + known[g]
                else: kind = "other GUID"
                rec["findings"].append({"part": p["path"], "line": ln, "kind": kind, "value": mask(g),
                                        "context": re.sub(G, "<guid>", line.strip()).replace(WSN, "<workspace>")[:90]})
            for m in H.finditer(line):
                rec["findings"].append({"part": p["path"], "line": ln, "kind": "hex name (PBIR style)", "value": m.group(0)[:4] + "..", "context": line.strip()[:60]})
        for seg in p["path"].split("/"):
            if re.fullmatch(r"[0-9a-f]{20}", seg):
                rec["findings"].append({"part": p["path"], "line": 0, "kind": "hex name in path (PBIR)", "value": seg[:4] + "..", "context": "folder name"})
    lids = [f for f in rec["findings"] if f["kind"] == "logicalId"]
    pl = open(os.path.join(base, ".platform")).read() if os.path.exists(os.path.join(base, ".platform")) else ""
    lid = (json.loads(pl).get("config", {}).get("logicalId", "") if pl else "").lower()
    rec["logicalId_equals_item_id"] = (lid == it["id"].lower()) if lid else None
    if it["type"] == "Report":
        pbir = json.load(open(os.path.join(base, "definition.pbir")))
        rec["pbir_datasetReference"] = list(pbir.get("datasetReference", {}).keys())
    out["items"].append(rec)
json.dump(out, open(f"results/guid_scan_{LABEL}_ws.json", "w"), indent=2)
L = [f"GUID scan of the {LABEL} workspace getDefinition exports, {out['scanned_local']}", "GUID values masked to last 4 chars. Raw exports stay on the box in defs/ (not for publishing).", ""]
tot = {}
for r in out["items"]:
    L.append(f"## {r['item']} ({r['type']}) getDefinition {r['getDefinition']}  parts: {', '.join(r['parts']) or r.get('error','')}")
    c = {}
    for f in r["findings"]: c[f["kind"]] = c.get(f["kind"], 0) + 1; tot[f["kind"]] = tot.get(f["kind"], 0) + 1
    L.append("   counts: " + (", ".join(f"{k}={v}" for k, v in c.items()) or "none"))
    for f in r["findings"]: L.append(f"   {f['kind']:<26} {f['part']}:{f['line']} {f['value']}  | {f['context']}")
    L.append(f"   logicalId equals item id: {r['logicalId_equals_item_id']}")
    if "pbir_datasetReference" in r: L.append(f"   definition.pbir datasetReference in workspace export: {r['pbir_datasetReference']} (byPath expected only in the committed Git copy, check after step 4)")
    L.append("")
L.append("TOTAL by type: " + ", ".join(f"{k}={v}" for k, v in tot.items()))
open(f"results/guid_scan_{LABEL}_ws.txt", "w").write("\n".join(L) + "\n"); print("\n".join(L))
