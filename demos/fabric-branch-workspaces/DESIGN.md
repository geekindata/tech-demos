# Demo design: Fabric branch workspaces, selective branching, compare and commit

Status: steps 0 to 4 BUILT (Oct 30, 21:30 to 21:36 Oslo). Steps 5 onward wait for the portal (no browser on Tech Demos). Step 2 refresh deferred until no mirroring-lag run is measuring (watcher running, see section 11).
Drafted: Fri Oct 30, 2026, 21:45 Oslo time (UTC+1). Revised after Fabric Expert review (approved with corrections, /workspace/fabric-expert/reviews/branch-workspaces-review.md) on Oct 30. Author: Tech Demos. Reviewer: Fabric Expert.
Sai decision (21:34 Oslo): Fabric system binding IDs (.platform logicalId, TMDL lineageTag) are allowed in public demo commits. Tenant, workspace, item, capacity and connection IDs are not.
Target: the free Trial capacity (Active), the main workspace.
Never: the paid F2 capacity, tenant settings, main branch, secrets in Git, new users.

## 0. What exists today (read-only check, Oct 30, about 21:35 Oslo)

- The main workspace is on the Trial capacity. Only role: Sai (User, Admin).
- Git: ConnectedAndInitialized to GitHub geekindata/tech-demos (public), branch fabric-demo-git, folder /fabric-ws. Done in post 11 through REST (connections, git/connect, git/initializeConnection), with a dedicated GitHub account.
- Items: Lakehouse demo_git_lh (plus its SQL endpoint), Notebook demo_nb. Git status: both "Added", uncommitted (2 changes). Nothing has ever been committed from Fabric.
- Branch fabric-demo-git, folder /fabric-ws holds only README.md.
- Repo branches: main, dev, fabric-demo-git.
- Definition scan (getDefinition, counts only): demo_nb notebook-content.py is empty (no default lakehouse bound), lakehouse JSON files carry no GUIDs. The only GUIDs are the `logicalId` values in each `.platform` file (see caveat 7.6).
- p11 notes: /workspace/blog/shots/11-fabric-cicd-blast-radius/README.md. There is no _work folder for p11.

## 1. What the features are, with sources

| Feature | Status (verified) | What it does |
|---|---|---|
| Branch workspaces | GA, September 2026 | Branch out from a Git-connected workspace creates a new Git branch plus a new (or existing) workspace connected to it, linked to the source as parent. Shown in the workspace tree, breadcrumbs and Source control > Related branches. |
| Selective branching | GA, September 2026 | "Select items individually" during branch out. Only the chosen items land in the new workspace; required dependencies must be included ("Select related items"). Learn's text says the status bar 'says selective branch'; in this run the status bar marked it with an icon next to the branch name (a branch with a pencil mark), not a text label. "Add more items" adds items later. |
| Compare and commit | GA, September 2026 | Side by side or inline diff of workspace vs branch, from the Changes tab (commit), Updates tab (incoming), or conflict dialog (3 modes: Last sync vs remote, Workspace vs remote, Last sync vs workspace). Commit items from the compare dialog. |
| File level commit | Preview | Commit only some files inside a supported item (Warehouse, SQL database, Notebook, Environment, Spark Job Definition, Pipeline, Dataflow Gen2, Variable Library). Also via Commit To Git API. |
| Branch workspace admin profile | Preview | Admin presets identity, role and capacity so developers can branch out without create-workspace or assign-capacity rights. |
| Allow Contributor+ to change Git branch | Preview | Per-workspace setting so Members/Contributors with write on all items can switch or check out branches. |
| Workspace Relation API | Preview | REST to create, query, update, delete parent/branch relationships for scripted branch out. This demo calls only the read-only List Workspace Relations GET (.../git/workspaceRelations) in step 6. Create Workspace Relation is named as the CI path, not run. |
| Branch out with deployment plan | Preview | Out of scope (needs a committed plan, can cause logical ID conflicts, plan actions can cost CU). One line mention at most. |

Sources:
- Learn, What's new (rows "September 2026 Branch workspaces and selective branching (Generally Available)" and "September 2026 Compare and commit Git changes (Generally Available)"; preview rows for file-level commit, admin profile, Contributor branch change, Workspace Relation API): https://learn.microsoft.com/en-us/fabric/fundamentals/whats-new
- Learn, Development process using branch workspace: https://learn.microsoft.com/en-us/fabric/cicd/git-integration/branched-workspace
- Learn, Compare and commit (docs source granular-compare.md, ms.date 09/01/2026): https://learn.microsoft.com/en-us/fabric/cicd/git-integration/granular-compare
- Learn, Git integration process (permissions, limits): https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-integration-process
- Learn, Branch workspace admin profile (Preview): https://learn.microsoft.com/en-us/fabric/cicd/git-integration/branch-workspace-admin-profile
- Learn REST, List Workspace Relations (read only, used in step 6): https://learn.microsoft.com/en-us/rest/api/fabric/core/git/list-workspace-relations
- Learn REST, Create Workspace Relation (Preview, mention only): https://learn.microsoft.com/en-us/rest/api/fabric/core/git/create-workspace-relation
- Learn, PBIR byPath vs byConnection: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- Fabric blog, September 2026 Feature Summary (GA of compare and commit, selective branching, branch workspace): https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/fabric-september-2026-feature-summary/5325825
- Fabric blog, original preview post: https://blog.fabric.microsoft.com/en-ie/blog/introducing-new-git-developer-experiences-in-microsoft-fabric-preview

Verification notes:
- GA: CONFIRMED on Learn What's new (September 2026) and the September 2026 Feature Summary. "Since FabCon" is consistent: the September summary is the FabCon Europe (Barcelona) release. I did not verify the exact conference dates on an official page.
- Doc inconsistency: the "Branch out with a deployment plan" section of branched-workspace.md still labels "Select items individually (Preview)". What's new and the main branch out section treat it as GA. We use GA and do not screenshot that sentence.
- blog.fabric.microsoft.com returned 403 to my fetcher for the feature summaries; I read the same posts on the Fabric Community blog mirror (community.fabric.microsoft.com). Not a sign the pages are missing.

### Permission date (governance note only, NOT the hook)

The hook is GA. The date gets one line in the governance close. Wording to use:

"Learn (updated Oct 26, 2026) says that from Feb 28, 2027 users without read-write permission on workspace items lose Git integration, and deployment pipelines block them in workspaces with sensitivity-labelled, protected items. Earlier posts said Dec 1, 2026."

Per page:
- Git integration process page: the rule is "tied to sensitivity labels with protection policies" (the page does not say "only"). https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-integration-process
- Deployment pipelines page: applies "only" to workspaces that contain items protected by sensitivity labels with protection policies. https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process (same on assign-pipeline.md)
- Source: the fabric-docs change "Update Git integration permission date to February 2027 (#17076)", Oct 26, 2026, 08:53 Oslo (https://github.com/MicrosoftDocs/fabric-docs/pull/17076). An earlier change (Aug 2, 2026) had set Dec 1.
- The August 2026 Feature Summary said Dec 1, 2026: https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/fabric-august-2026-feature-summary/5325824 . No Fabric blog post announces the postponement; Learn is the source.

## 2. The demo story (what a consultant would show)

"Git for Fabric finally feels like Git: branch workspaces, selective branching and compare and commit are GA." One shared dev workspace, one developer who needs only two items.

1. The shared dev workspace (the main workspace) is connected to Git and fully committed (baseline).
2. Developer branches out with Select items individually: picks only the report, Fabric flags the missing semantic model, "Select related items" adds it. A small feature workspace appears, linked to its parent, status bar shows the feature branch.
3. Developer changes a measure and the report title, opens Review and commit changes, reads the side by side diff of the TMDL, commits.
4. Bonus, file level commit (Preview): two edits in a variable library, commit only the finished one.
5. Pull request in GitHub from the feature branch into the dev branch; merge.
6. Bonus, conflict (teammate's PR merged): before updating, the dev workspace has its own uncommitted edit to the same measure. The Updates tab shows a conflict and the three compare modes.
7. Back in the dev workspace, the Updates tab shows the incoming change, Review changes shows the diff before Update all.
8. Governance close: the per-workspace "Allow users with at least Contributor role to change Git branch" setting, the admin profile (Preview), and one line on the Feb 28, 2027 read-write permission rule.

## 3. Items (built in the main workspace, Oct 30)

| Item | Type | Content as built | Why |
|---|---|---|---|
| demo_git_lh | Lakehouse (existed) | empty, metadata only in Git | Shows a non-selected item stays behind |
| demo_nb | Notebook (existed) | empty, no default lakehouse, never run (zero Spark CU) | "Add more items" candidate |
| demo_model | Semantic model, TMDL | table sales, Import partition from an M #table with 5 rows (Region, Amount), measure Total Amount. Sent without lineageTags | Dependency target. No data source, no gateway |
| demo_report | Report, PBIR | one page "overview", one card (Total Amount). Created via REST with byConnection semanticmodelid; committed as byPath ../demo_model.SemanticModel (verified). Page and visual folders use readable names (overview, total_card), so no PBIR hex names yet; portal edits may add hex names | The item that drags its dependency in |
| demo_vl | Variable library | env_label (String, default dev), row_limit (Integer, default 5); one value set test (env_label test, row_limit 10) | File level commit (Preview) |

Note on the model: an M #table Import partition was used instead of a DATATABLE calc table (same effect, no source). It still needs one refresh to hold data before the report renders.

New, created by branch out (portal):
- Workspace: the feature workspace (must land on the Trial capacity, see 7.3).
- Branch fabric-demo-feature in geekindata/tech-demos, created by Fabric from the last commit of the main workspace on fabric-demo-git.

GUIDs in Git: only `.platform` logicalId (one per item), allowed by Sai's 21:34 decision. TMDL lineageTag is also allowed but none are present now; re-scan after portal edits, since the service or the portal may add them. Before every commit run the scan (scripts/guid_scan.py on getDefinition, scripts/repo_id_scan.py on the committed tree): no logicalId may equal its item ID and no tenant, workspace, item, capacity or connection ID may appear.

## 4. Exact steps: UI vs REST

Legend: REST = Fabric REST via az token (read per command, never printed). GH = gh with GH_TOKEN read per command. UI = portal only.

| # | Step | How | Automatable? |
|---|---|---|---|
| 0 | Pre-flight: trial state Active, no 2a/recovery/benchmark window open, F2 still Paused (read only) | REST GET capacities | Yes |
| 1 | Create demo_model (TMDL), demo_report (PBIR, created with byConnection semanticmodelid as REST requires; check the committed definition.pbir is byPath), demo_vl in the main workspace | REST POST workspaces/{id}/items with definition | Yes |
| 2 | Refresh demo_model once so the calc table exists (tiny) | REST or UI | Yes |
| 3 | GUID scan of every definition part: list each GUID by type (logicalId, lineageTag, other) plus PBIR hex names; check no logicalId equals its item ID; stop on anything other than logicalId or lineageTag | REST getDefinition + local regex | Yes |
| 4 | Baseline commit of all 5 items to fabric-demo-git. Mandatory: branch out uses the source workspace's last commit, uncommitted items are not branched | REST git/commitToGit (mode All) | Yes |
| 5 | Branch out, new workspace (the feature workspace), new branch fabric-demo-feature, Select items individually: tick demo_report, see dependency warning, Select related items, Create branch | UI only. No Branch out REST API; scripted equivalent is create workspace + create branch + git/connect + Create Workspace Relation (Preview), which loses the point of the demo | UI |
| 6 | Verify new workspace capacity = Trial (if the dialog has a capacity picker choose Trial; if it lands on F2, reassign to Trial before anything loads). Relation by REST: read-only List Workspace Relations GET. UI: tree, breadcrumb, Related branches, status bar branch fabric-demo-feature. If Git is not enabled on the new workspace, a workspace-level toggle may be needed (workspace setting, not tenant) | REST GET + UI | Partly |
| 7 | Add more items: demo_vl, then Update all | UI only (Source control ... > Add more items) | UI |
| 8 | Edit: add measure Avg Amount in demo_model; change card title in demo_report | UI (model view / report edit) or REST updateDefinition | Either; UI for realism |
| 9 | Compare and commit: Changes > Review and commit changes, side by side then inline, commit message "Add Avg Amount measure" | UI only for the compare dialog; the commit itself also works via REST | UI |
| 10 | File level commit (Preview): edit existing values only, the env_label default in variables.json and row_limit in valueSets/test.json; commit only one. Do not add a variable or value set (touches settings.json, can break the partial commit) | UI (also REST commitToGit with file selection, Preview) | UI |
| 11 | PR fabric-demo-feature into fabric-demo-git (never main); merge. Uses the gh token (Pull requests write) | GH | Yes |
| 12 | Optional conflict, NO direct push: after the merge, make an uncommitted edit to the same TMDL measure in the main workspace (REST updateDefinition or UI), then open the Updates tab: conflict dialog, 3 compare modes; resolve by taking one side | REST + UI | Partly |
| 13 | In the main workspace: Updates tab > Review changes > Update all | UI (Update also via REST git/updateFromGit) | UI for shots |
| 14 | Settings shot: Workspace settings > Git integration: "Allow users with at least Contributor role to change Git branch" and Branch workspaces tab (admin profile, Preview). Look only, do not enable a profile | UI | UI |
| 15 | Cleanup (see section 8) | REST + GH | Only after Sai's OK |

## 5. Planned screenshots and short clips

Naming follows the repo pattern, prefix pBW (post number to be assigned by Blog). Masking: blur the capacity name if F2 ever shows in a picker; strong blur on commit hashes, workspace and item GUIDs in URLs (or crop browser chrome), tenant and subscription IDs; strong blur on workspace names, item names and any email; Sai's display name stays; public repo URL and branch names are fine.

| File | What |
|---|---|
| pBW-01-baseline-synced.png | The main workspace list, every item Git status Synced, status bar branch fabric-demo-git |
| pBW-02-branch-out-dialog.png | Branch out dialog: new workspace, branch name, Select items individually ticked |
| pBW-03-select-items-dependency.png | Select items dialog: demo_report picked, missing dependency warning, Select related items |
| pBW-04-selective-branch-status.png | New workspace with only 2 items, status bar branch fabric-demo-feature |
| pBW-05-related-branches.png | Workspace tree parent/child plus Source control > Related branches |
| pBW-06-add-more-items.png | Add more items dialog showing only non-selected items |
| pBW-07-compare-side-by-side.png | Review and commit changes: TMDL diff with the new measure |
| pBW-08-compare-inline.png | Same diff, inline mode |
| pBW-09-file-level-commit.png | demo_vl with one of two files ticked, partial commit warning (Preview label visible) |
| pBW-10-pr-files.png | GitHub PR fabric-demo-feature into fabric-demo-git, files changed view |
| pBW-11-conflict-modes.png | The main workspace Updates tab conflict dialog with the 3 compare modes dropdown (optional, after the merge) |
| pBW-12-updates-review.png | The main workspace Updates tab, Review changes before Update all |
| pBW-13-contributor-branch-setting.png | Workspace settings, Git integration, Contributor branch switch setting and Branch workspaces tab |

Clips (1280 wide, no audio, under 60 s, raw/):
- clip-branch-out.mp4: steps 5 to 6, from Branch out to landing in the selective branch (about 40 s; trim the sync wait).
- clip-compare-commit.mp4: step 9, open compare, flip to inline, commit (about 30 s).
- clip-update-from-git.mp4: step 13 (about 20 s).

## 6. Expected output

- Folder /workspace/demos/fabric-branch-workspaces/ with README (Trial capacity, item list, steps actually run, Oslo times), screenshots, raw/ clips, notes.md with timings written as "about X min on a Trial capacity" (single runs, not benchmarks). Optional results.csv in the same schema as the trial series (experiment=branch_ws, variant=step, duration_s).
- Git artefacts on throwaway branches only: fabric-demo-git gets the baseline plus the merged feature; fabric-demo-feature holds 2 to 3 small commits; one merged PR between them. main and dev untouched.
- Handoff to GeekInData Blog (priority message) with the folder path, captions, and the corrected permission-date wording, after Fabric Expert reviews.

## 7. Caveats and permissions

1. Permission change date. See section 1: Git page "tied to sensitivity labels with protection policies", deployment pipelines "only" for labelled, protected workspaces, from Feb 28, 2027 (Learn, updated Oct 26, 2026; Dec 1 was the earlier date). No sensitivity labels on the trial tenant, so this is a documented note only.
2. Roles (Learn permissions table):
   - Connect, disconnect, sync, Checkout new branch: workspace Admin.
   - Commit and Update from Git: Contributor with WRITE on all items (plus item owner if the tenant switch requires it, BUILD on external dependencies).
   - Branch out: Admin, Member or Contributor; branch out to a NEW workspace also needs the right to create workspaces and assign the capacity (or an admin profile, Preview).
   - Switch branch: Admin, or Member/Contributor with write on all items when the per-workspace Contributor setting is on (Preview).
   - Viewer: sees no Git info.
   - Sai is the only principal and is Admin; no new users will be added, so the Contributor path is shown as a settings screenshot only.
3. Capacity: branch out needs an available capacity. The new workspace must land on the Trial, never F2 (F2 is paused, but still check). Pick Trial if the dialog offers a picker. Verify with REST right after step 5; if it is on F2 or anywhere else, reassign it to Trial before any item loads.
4. GitHub token scope: the Fabric GitHub connection PAT needs Contents read and write (branch out, commit, new branch); GitHub adds Metadata read automatically. Also: repository access includes geekindata/tech-demos, org approval of fine-grained tokens if required, and no branch protection or ruleset on fabric-demo-git or fabric-demo-*. The step 11 PR uses the gh token, which needs Pull requests write. Baseline commit on Oct 30 proved Contents write works.
   Tenant switches checked read-only on Oct 30: GitIntegrationTenantSwitch, GitHubTenantSettings ("Users can sync workspace items with GitHub repositories"), CreateAppWorkspaces ("Create workspaces") and FabricGAWorkloads are all enabled. No tenant change needed.
5. Public repo: everything committed is public. Allowed (Sai, Oct 30 21:34): `.platform` logicalId and TMDL lineageTag. Not allowed: tenant, workspace, item, capacity, connection IDs. Fabric commits carry the author email of Sai's Fabric account (the account's email address); the same address is already on earlier merge commits in this repo.
6. Limits that matter here: branch out settings are not copied to the new branch; switching branch in a selective workspace resets the selection and syncs all items; disconnecting a branch workspace removes its relation; branch name max 244 characters; GitHub commit max 50 MB per commit; compare dialog does not show binary files or files over 1 MB; Update always takes the whole branch (no item pick); file-level commit only for supported items in Modified state, and not to another branch. Branch out creates the branch from the source workspace's last commit; uncommitted items are not included. Learn's deployment-plan section still labels selective branching Preview (doc inconsistency).
7. Branch out to an EXISTING workspace can delete uncommitted items; we only branch out to a new workspace.
8. CU: metadata and Git operations plus one tiny model refresh and a few report renders. No Spark, no notebook run. Expect well under 1% of the trial. Still, run only outside the 2a overload, its recovery, the benchmark timing runs and the mirroring-lag measurement windows. Log CU by item name in /workspace/demos/fabric-trial-lab/results/cu_ledger.csv.

## 8. Cleanup (needs Sai's OK for each deletion)

- Disconnect and delete the feature workspace. Deletion: ask Sai first.
- Delete GitHub branch fabric-demo-feature after Blog confirms shots. Deletion: ask Sai first.
- Leave the main workspace connected to fabric-demo-git (reused by post 11 and later Git posts).
- Nothing on F2, nothing on main or dev.

## 9. Rough time

| Block | Time |
|---|---|
| Build items via REST, GUID scan, baseline commit | 30 min |
| Branch out, add items, edits, compare and commit, file-level | 45 min |
| Conflict (optional), PR and merge, Update from Git | 30 min |
| Screenshots crop and blur, clips trim, README | 45 min |
| Total | about 2.5 h (2 h without the conflict step) |

Slot: tonight during the mirroring runs, before 2a starts (Sat morning), or right after the benchmark timing runs end. Not during 2a, its recovery or benchmark timing.

## 10. Review answers applied

Fabric Expert answers 1 to 9 and C1 to C9 are applied above: GA hook; byConnection then byPath; lineageTag and hex names in the scan; logicalId kept (not stripped, not regenerated) with the logicalId vs item ID check; PAT scope; capacity reassign; post-merge conflict with no direct push; edit existing variable values only; deployment plan skipped; Workspace Relation API read-only GET only; tenant switches checked; cleanup deletions need Sai.


## 11. Build log (Oct 30, Oslo time)

- 21:30 Step 0 pre-flight (read only): Trial capacity Active; the paid F2 capacity Inactive (paused); the main workspace and two other demo workspaces on Trial. Tenant switches read: Git integration, GitHub sync, Create workspaces, Create Fabric items all enabled.
- 21:30 Mirroring-lag check: notebook mirror_workload InProgress since 20:58 (9 runs at 10, 100, 1000 rows/s, 150 s bursts, 60 s gaps, up to 600 s tail each). Step boundaries are not visible from outside, so the refresh is deferred.
- 21:31 to 21:33 Step 1: demo_model, demo_report, demo_vl created via REST (scripts/create_items.py). Report needed the definitionProperties 2.0.0 schema in definition.pbir and no layoutOptimization in report.json. Variable library rejected a string "5" override for an Integer; uses 10.
- Step 2: scripts/refresh_when_clear.py runs in the background (up to 4 h). It refreshes demo_model once, only when no notebook in the mirroring demo workspace is InProgress, logs to results/refresh_log.txt and adds a cu_ledger row.
- 21:34 Step 3: GUID scan on getDefinition exports, results/guid_scan_main_ws.txt and .json. Only 5 logicalIds (all zero before the first commit), no lineageTag, no other GUID, no PBIR hex names. The workspace export of definition.pbir is byConnection and holds the demo_model item ID; it is not a Git file.
- 21:35 Step 4: baseline commit to fabric-demo-git ("Baseline: demo_git_lh, demo_nb, demo_model, demo_report, demo_vl"). Committed tree scan (scripts/repo_id_scan.py, results/repo_scan_baseline.txt): logicalId 5, no real tenant, workspace, item, capacity or connection ID. definition.pbir is byPath ../demo_model.SemanticModel.
- Next: portal steps 5 onward. Helpers: scripts/step6_verify.py (capacity check plus List Workspace Relations GET), scripts/step12_conflict_edit.py (uncommitted workspace edit, no push), scripts/repo_id_scan.py before every commit.
