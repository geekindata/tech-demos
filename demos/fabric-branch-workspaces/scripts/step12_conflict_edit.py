"""Step 12 prep (no push): after the PR merge, make an UNCOMMITTED edit to the Total Amount format string (#,0 to #,0.00) in the main workspace via updateDefinition.
Run only after step 11 merged, and before Update from Git. Usage: python3 step12_conflict_edit.py --go"""
import sys, base64, re; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
W = ws_id(MAIN_WS())
mid = [i for i in call(f"workspaces/{W}/items?type=SemanticModel")[2]["value"] if i["displayName"] == "demo_model"][0]["id"]
s, b = lro(f"workspaces/{W}/items/{mid}/getDefinition?format=TMDL")
parts = b["definition"]["parts"]
for p in parts:
    if p["path"] == "definition/tables/sales.tmdl":
        t = base64.b64decode(p["payload"]).decode()
        t = t.replace("\tmeasure 'Total Amount' = SUM(sales[Amount])\n\t\tformatString: #,0",
                      "\tmeasure 'Total Amount' = SUM(sales[Amount])\n\t\tformatString: #,0.00")
        p["payload"] = base64.b64encode(t.encode()).decode()
parts = [p for p in parts if p["path"] != ".platform"]
print("edit prepared: Total Amount formatString #,0 -> #,0.00 (same lines the feature branch should touch)")
if "--go" in sys.argv:
    print("updateDefinition", lro(f"workspaces/{W}/items/{mid}/updateDefinition", body={"definition": {"parts": parts}})[0])
