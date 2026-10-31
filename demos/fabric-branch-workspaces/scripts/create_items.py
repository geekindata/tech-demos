import json, base64, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
W = ws_id(MAIN_WS())
def parts(d): return {"parts": [{"path": k, "payload": base64.b64encode(v.encode()).decode(), "payloadType": "InlineBase64"} for k, v in d.items()]}
def existing():
    return {(i["type"], i["displayName"]): i["id"] for i in call(f"workspaces/{W}/items")[2]["value"]}
def create(name, typ, d, desc):
    ex = existing()
    if (typ, name) in ex: print("exists", name); return ex[(typ, name)]
    s, b = lro(f"workspaces/{W}/items", body={"displayName": name, "type": typ, "description": desc, "definition": parts(d)})
    print("create", name, s, "" if s in (200, 201) else b)
    return existing().get((typ, name))
rows = [("North", 120), ("South", 95), ("East", 140), ("West", 80), ("Central", 65)]
mrows = ", ".join(f'{{"{r}", {a}}}' for r, a in rows)
model = {
 "definition.pbism": json.dumps({"version": "4.0", "settings": {}}),
 "definition/database.tmdl": "database\n\tcompatibilityLevel: 1604\n",
 "definition/model.tmdl": "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\nref table sales\n",
 "definition/tables/sales.tmdl": f"""/// Five synthetic rows for the branch demo.
table sales

\tmeasure 'Total Amount' = SUM(sales[Amount])
\t\tformatString: #,0

\tcolumn Region
\t\tdataType: string
\t\tsourceColumn: Region
\t\tsummarizeBy: none

\tcolumn Amount
\t\tdataType: int64
\t\tsourceColumn: Amount
\t\tsummarizeBy: sum

\tpartition sales = m
\t\tmode: import
\t\tsource = #table(type table [Region = text, Amount = Int64.Type], {{{mrows}}})
"""}
mid = create("demo_model", "SemanticModel", model, "Five row synthetic model for the branch workspace demo")
S = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
visual = {"$schema": S + "visualContainer/2.0.0/schema.json", "name": "total_card",
  "position": {"x": 40, "y": 40, "z": 0, "width": 320, "height": 160},
  "visual": {"visualType": "card", "query": {"queryState": {"Values": {"projections": [{"field": {"Measure": {
     "Expression": {"SourceRef": {"Entity": "sales"}}, "Property": "Total Amount"}}, "queryRef": "sales.Total Amount"}]}}}}}
report = {
 "definition.pbir": json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0", "datasetReference": {"byConnection": {"connectionString": f"semanticmodelid={mid}"}}}),
 "definition/version.json": json.dumps({"$schema": S + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"}),
 "definition/report.json": json.dumps({"$schema": S + "report/2.0.0/schema.json",
     "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59", "type": "SharedResources"}}}),
 "definition/pages/pages.json": json.dumps({"$schema": S + "pagesMetadata/1.0.0/schema.json", "pageOrder": ["overview"], "activePageName": "overview"}),
 "definition/pages/overview/page.json": json.dumps({"$schema": S + "page/1.0.0/schema.json", "name": "overview", "displayName": "Overview",
     "displayOption": "FitToPage", "height": 720, "width": 1280}),
 "definition/pages/overview/visuals/total_card/visual.json": json.dumps(visual)}
if "--report" in sys.argv or True:
    create("demo_report", "Report", report, "One card report on demo_model")
V = "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/"
vl = {
 "variables.json": json.dumps({"$schema": V + "variables/1.0.0/schema.json", "variables": [
    {"name": "env_label", "type": "String", "value": "dev", "note": "Label shown in the demo"},
    {"name": "row_limit", "type": "Integer", "value": 5, "note": "Rows the demo reads"}]}, indent=2),
 "settings.json": json.dumps({"$schema": V + "settings/1.0.0/schema.json", "valueSetsOrder": ["test"]}, indent=2),
 "valueSets/test.json": json.dumps({"$schema": V + "valueSet/1.0.0/schema.json", "name": "test", "variableOverrides": [
    {"name": "env_label", "value": "test"}, {"name": "row_limit", "value": 10}]}, indent=2)}
create("demo_vl", "VariableLibrary", vl, "Two variables for the branch workspace demo")
for (t, n), i in sorted(existing().items()): print(t, n)
