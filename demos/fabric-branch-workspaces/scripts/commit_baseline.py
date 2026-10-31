import sys; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__))); from fab import *
W = ws_id(MAIN_WS())
s, _, st = call(f"workspaces/{W}/git/status")
print("status", s, "remoteCommit", (st.get("remoteCommitHash") or "")[:7], "changes", len(st["changes"]))
for c in st["changes"]: print("  ", c["itemMetadata"]["displayName"], c["itemMetadata"]["itemIdentifier"].get("objectId") and c["itemMetadata"]["itemType"], c.get("workspaceChange"), c.get("remoteChange"), c.get("conflictType"))
s, _, cn = call(f"workspaces/{W}/git/connection")
gd = cn["gitProviderDetails"]; print("conn", gd["ownerName"], gd["repositoryName"], gd["branchName"], gd["directoryName"])
assert gd["branchName"] == "fabric-demo-git"
if "--go" in sys.argv:
    s, b = lro(f"workspaces/{W}/git/commitToGit", body={"mode": "All", "workspaceHead": st["workspaceHead"],
                "comment": "Baseline: demo_git_lh, demo_nb, demo_model, demo_report, demo_vl"})
    print("commit", s, b if s != 200 else "")
    s, _, st = call(f"workspaces/{W}/git/status"); print("after: changes", len(st["changes"]), "remoteCommit", (st.get("remoteCommitHash") or "")[:7])
