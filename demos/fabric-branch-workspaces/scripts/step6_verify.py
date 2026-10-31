"""Step 6 (read only): new branch workspace capacity, Git connection, items, and List Workspace Relations GET."""
import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
caps = {c["id"]: c for c in call("capacities")[2]["value"]}
for label, name in (("main workspace", MAIN_WS()), ("feature workspace", FEATURE_WS())):
    try: W = ws_id(name)
    except IndexError: print(label, "not found"); continue
    w = call("workspaces/" + W)[2]; c = caps.get(w.get("capacityId"), {})
    flag = "OK Trial" if c.get("sku") == env("TRIAL_SKU") else "STOP: not on Trial, reassign to Trial"
    print(f"{label}: capacity: Trial (OK)" if flag == "OK Trial" else f"{label}: capacity {c.get('sku')} {flag}")
    s, _, g = call(f"workspaces/{W}/git/connection")
    if s == 200: print("  git", g.get("gitSyncDetails", {}) and "", g.get("gitConnectionState"), g.get("gitProviderDetails", {}).get("branchName"))
    print("  items", sorted(f"{i['type']}:{i['displayName']}" for i in call(f"workspaces/{W}/items")[2]["value"]))
    s, _, r = call(f"workspaces/{W}/git/workspaceRelations")
    print("  workspaceRelations GET", s, [ {k: v for k, v in x.items() if "id" not in k.lower()} for x in (r or {}).get("value", [])] if s == 200 else str(r)[:200])
