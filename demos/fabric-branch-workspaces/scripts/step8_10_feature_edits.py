"""Steps 8 and 10 prep: UNCOMMITTED edits in the feature workspace only, via updateDefinition."""
import sys, base64, json; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
WN = FEATURE_WS(); W = ws_id(WN); assert WN != MAIN_WS()
items = {i["displayName"]: i for i in call(f"workspaces/{W}/items")[2]["value"] if i["type"] != "SQLEndpoint"}
dec = lambda p: base64.b64decode(p["payload"]).decode(); enc = lambda t: base64.b64encode(t.encode()).decode()
def get(n, q=""):
    s, b = lro(f"workspaces/{W}/items/{items[n]['id']}/getDefinition{q}"); assert s == 200, (n, s, b); return b["definition"]["parts"]
def put(n, parts):
    parts = [p for p in parts if p["path"] != ".platform"]
    return lro(f"workspaces/{W}/items/{items[n]['id']}/updateDefinition", body={"definition": {"parts": parts}})[0]
go = "--go" in sys.argv
# 1 model
parts = get("demo_model", "?format=TMDL")
for p in parts:
    if p["path"] == "definition/tables/sales.tmdl":
        t = dec(p); old = "\tmeasure 'Total Amount' = SUM(sales[Amount])\n\t\tformatString: #,0\n"
        assert old in t, t
        t = t.replace(old, "\tmeasure 'Total Amount' = SUM(sales[Amount])\n\t\tformatString: #,0.0\n\n\tmeasure 'Avg Amount' = AVERAGE(sales[Amount])\n\t\tformatString: #,0\n")
        p["payload"] = enc(t); print(t)
if go: print("model", put("demo_model", parts))
# 2 report
parts = get("demo_report")
for p in parts:
    if p["path"].endswith("total_card/visual.json"):
        v = json.loads(dec(p)); vo = v.setdefault("visual", {}).setdefault("visualContainerObjects", {})
        vo["title"] = [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'Total amount (feature)'"}}}}}]
        p["payload"] = enc(json.dumps(v, indent=2)); print(p["path"], json.dumps(vo))
    if p["path"] == "definition.pbir": print("pbir:", dec(p))
if go: print("report", put("demo_report", parts))
# 3 vl
parts = get("demo_vl")
for p in parts:
    if p["path"] == "variables.json":
        v = json.loads(dec(p)); [x.update(value="dev2") for x in v["variables"] if x["name"] == "env_label" and x["value"] == "dev"]
        p["payload"] = enc(json.dumps(v, indent=2)); print(json.dumps(v))
    if p["path"] == "valueSets/test.json":
        v = json.loads(dec(p)); [x.update(value=20) for x in v["variableOverrides"] if x["name"] == "row_limit" and x["value"] in (10, "10")]
        p["payload"] = enc(json.dumps(v, indent=2)); print(json.dumps(v))
if go: print("vl", put("demo_vl", parts))
