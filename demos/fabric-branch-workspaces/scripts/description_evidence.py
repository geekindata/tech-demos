"""Read-only evidence for the README Conclusion: the demo_report item description in both workspaces
(GET items), the .platform from the main workspace (getDefinition, a read) and from Git (GitHub contents API),
and a diff of the two .platform files. All IDs are masked, workspace names are generic.
Writes results/description_evidence.md. Needs GH_TOKEN in the environment for the GitHub read."""
import base64, difflib, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fab
GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
def mask(s):
    s = GUID.sub(lambda m: m.group() if set(m.group().replace("-", "")) == {"0"} else "00000000-0000-0000-0000-000000000000", s)
    for k, v in (("FEATURE_WS", "<feature workspace>"), ("MAIN_WS", "<main workspace>")):
        s = s.replace(fab.env(k), v)
    return s
def item(ws):
    s, _, b = fab.call(f"workspaces/{ws}/items?type=Report")
    return [i for i in b["value"] if i["displayName"] == "demo_report"][0]
out = ["# demo_report description evidence", "", "Read-only calls, Oct 30, 2026. IDs masked to all zeros, workspace names generic.",
       "The workspace exports return an all-zero logicalId themselves; the Git logicalId is a real value and is masked here.", "",
       "Finding: Git and the feature workspace carry the description \"One card report on demo_model\"; the main workspace item has an empty description, so its export has no description line.", ""]
platforms = {}
for label, name in (("main workspace", fab.MAIN_WS()), ("feature workspace", fab.FEATURE_WS())):
    ws = fab.ws_id(name); it = item(ws)
    out += [f"## GET items, {label}", "", "```json", mask(json.dumps({k: it.get(k) for k in ("type", "displayName", "description")}, indent=2)), "```", ""]
    s, b = fab.lro(f"workspaces/{ws}/items/{it['id']}/getDefinition", "POST")
    parts = {p["path"]: base64.b64decode(p["payload"]).decode() for p in (b or {}).get("definition", {}).get("parts", [])}
    if ".platform" in parts: platforms[label] = parts[".platform"]
r = subprocess.run(["gh", "api", "repos/geekindata/tech-demos/contents/fabric-ws/demo_report.Report/.platform?ref=fabric-demo-git",
                    "--jq", ".content"], capture_output=True, text=True)
platforms["Git, branch fabric-demo-git"] = base64.b64decode(r.stdout).decode() if r.returncode == 0 else ""
for k, v in platforms.items():
    out += [f"## .platform, {k}", "", "```json", mask(v).strip(), "```", ""]
a, g = mask(platforms.get("main workspace", "")), mask(platforms["Git, branch fabric-demo-git"])
d = list(difflib.unified_diff(g.splitlines(), a.splitlines(), "git/.platform", "main-workspace/.platform", lineterm=""))
out += ["## Diff, Git vs main workspace .platform (masked)", "", "```diff", "\n".join(d) or "(no differences)", "```", ""]
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "description_evidence.md"), "w").write("\n".join(out))
print("written; platforms:", list(platforms), "diff lines:", len(d))
