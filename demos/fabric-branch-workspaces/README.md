# Fabric branch workspaces, selective branching and compare and commit

Demo run on Oct 30, 2026 (Oslo time, UTC+1) on a Fabric Trial capacity. Repo: geekindata/tech-demos, Git folder /fabric-ws, dev branch fabric-demo-git, feature branch fabric-demo-feature. Nothing here touches main. In this write-up the Git-connected dev workspace is called the main workspace, and the workspace created by Branch out is called the feature workspace. The scripts read the real workspace names from env.local (not committed; copy env.example).

## What branch workspaces are

A developer working in a Git-connected workspace can **Branch out**. Fabric creates a new Git branch from the source workspace's last commit, plus a new (or existing) workspace connected to that branch. The new workspace is linked to its parent, and the link shows in the workspace tree and breadcrumbs and under Source control > Related branches. With **Select items individually** (selective branching), only the chosen items land in the new workspace. Fabric asks for required dependencies ("Select related items"), and **Add more items** brings in more later. Work goes back to the parent through a normal pull request, and the parent workspace picks it up from the Updates tab.

## GA vs Preview

| Piece | Status |
|---|---|
| Branch workspaces | GA, September 2026 |
| Selective branching (Select items individually, Add more items) | GA, September 2026 |
| Compare and commit (side by side and inline diff, conflict compare modes) | GA, September 2026 |
| File level commit (commit only some files of an item) | Preview |
| Branch workspace admin profile | Preview |
| Allow users with at least Contributor role to change Git branch | Preview |
| Workspace Relation API (create, update, delete) | Preview; the List Workspace Relations GET was used read only in step 6 |
| Branch out with a deployment plan | Preview, not part of this demo |

From February 28, 2027, users without read-write permissions on workspace items can't use Git integration (Git integration process page, checked Oct 30, 2026).

Note: branched-workspace.md (updated Sep 24, 2026) still labels deployment-plan item selection as "Select items individually (Preview)", while What's new lists selective branching as GA. Only the deployment plan path is Preview.

Sources:
- What's new in Fabric: https://learn.microsoft.com/en-us/fabric/fundamentals/whats-new
- Development process using branch workspace: https://learn.microsoft.com/en-us/fabric/cicd/git-integration/branched-workspace
- Compare and commit: https://learn.microsoft.com/en-us/fabric/cicd/git-integration/granular-compare
- Git integration process: https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-integration-process
- Branch workspace admin profile (Preview): https://learn.microsoft.com/en-us/fabric/cicd/git-integration/branch-workspace-admin-profile
- List Workspace Relations: https://learn.microsoft.com/en-us/rest/api/fabric/core/git/list-workspace-relations
- PBIR byPath and byConnection: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- Fabric September 2026 Feature Summary: https://community.fabric.microsoft.com/blog/fbc_fabricupdatesblogs/fabric-september-2026-feature-summary/5325825

## Items

| Item | Type | Content |
|---|---|---|
| demo_git_lh | Lakehouse | empty |
| demo_nb | Notebook | empty, never run |
| demo_model | Semantic model (TMDL) | table sales, 5 synthetic rows from an M #table, measure Total Amount |
| demo_report | Report (PBIR) | page overview, one card on Total Amount |
| demo_vl | Variable library | env_label (String), row_limit (Integer), value set test |

## Steps and what happened

Times are Oslo time. All timings are from a single run on a Trial capacity and are not benchmarks. The full list is in results/timeline.csv.

| # | Time | Step | What happened |
|---|---|---|---|
| 0 | 21:30 | Pre-flight (read only) | Trial capacity active. Every workspace used here sits on the Trial. |
| 1 | 21:31 to 21:33 | Create demo_model, demo_report and demo_vl via REST | The report needed the definitionProperties 2.0.0 schema in definition.pbir. The variable library rejected a string override for an Integer. |
| 2 | 21:54 to 21:57 | Refresh demo_model | Two on-demand refreshes (21:54:04 and 21:57:26), both Completed, after waiting until no other demo was measuring on the capacity. See results/refresh_log.txt. |
| 3 | 21:34 | GUID scan of the definitions | The workspace export of definition.pbir (byConnection) held the demo_model item ID. Otherwise only .platform logicalIds were found. That ID never reaches Git: the committed file is byPath (step 4). |
| 4 | 21:35 | Baseline commit of 5 items to fabric-demo-git | Committed definition.pbir is byPath ../demo_model.SemanticModel. The committed tree holds no real IDs. |
| 5 | 21:42 to 21:43 | Branch out with Select items individually | Picked demo_report, then Select related items added demo_model, then Create branch. A first attempt was abandoned and retaken. |
| 6 | 21:44 to 21:46 | Verify | Both workspaces are on the Trial. Right after branch out, the feature workspace shows 2 items (pBW-04, pBW-05); results/step6_verify.txt, read after Add more items, lists 3. List Workspace Relations (Preview) returns relationType Branch on the main workspace and Base on the feature workspace (Base: the related workspace is the base, or source, workspace). The tree and Related branches show the link. |
| 7 | 21:45 to 21:46 | Add more items | Added demo_vl, then Update all. 3 items synced. |
| 8 | 21:58 to 21:59 | Feature edits via REST | Total Amount format went from #,0 to #,0.0. Added measure Avg Amount. The card title became "Total amount (feature)". In demo_vl, env_label default became dev2 and test row_limit became 20. |
| 9 | 22:01 to 22:02 | Compare and commit | Review and commit changes showed the TMDL diff side by side, then inline. Committed "Add Avg Amount measure" (the commit also carried the card title change in visual.json). |
| 10 | 22:02 to 22:03 | File level commit (Preview) | Ticked only variables.json of demo_vl, got the partial selection dialog, and committed "Update env_label default". valueSets/test.json stayed uncommitted in the feature workspace (it still shows Modified there). |
| 11 | 22:05 to 22:14 | Pull request #6 | Opened fabric-demo-feature into fabric-demo-git, at 22:05:00, then merged at 22:14:27 (times from the GitHub PR). |
| 12 | 22:14 to 22:16 | Conflict | At 22:14:50, before updating, made an uncommitted edit in the main workspace: Total Amount format #,0 to #,0.00. The Updates tab showed the conflict, and the compare dialog offers 3 modes. |
| 13 | 22:17 to 22:18 | Review and update | Change Review, then the conflict dialog with Accept incoming changes, then Merge And Update. Synced at 22:18:40. |
| 14 | 22:19 | Settings (look only) | Workspace settings > Git integration: the Git branch controls (preview) toggle is Off, and the Branch workspaces tab is there. Nothing was enabled. |

## Observations

1. **No "selective branch" label.** The docs (branched-workspace.md, checked Oct 30, 2026) say the status bar reads "selective branch" after a selective branch out. In this run (Oct 30, 2026), the feature workspace status bar showed only the branch name (fabric-demo-feature) and the last sync time. The selection itself worked: the workspace held only demo_report and demo_model until Add more items.
2. **File level commit is Preview, and it warns you.** The dialog reads: "Commit partial selection? (preview) Some items have only part of their files selected. Only the selected files will be committed. Committing part of an item's changes can leave its definition incomplete or invalid in Git. You may need to fix it manually before importing the item again. Unselected files stay as uncommitted changes in your workspace and won't be lost." It has Commit and Cancel buttons.
3. **Conflict labels.** The conflict dialog is titled "Merge and update content to resolve conflicts". It offers "Accept incoming changes" and "Keep current content", has a checkbox to confirm the deletion warning, and has a "Merge And Update" button.
4. **Three compare modes.** The compare dropdown in the conflict view offers "Last sync vs. remote", "Workspace vs Remote" and "Last sync vs. workspace".
5. **Which edit won.** The remote Total Amount format was #,0.0, from the feature branch. The local uncommitted edit was #,0.00. Accept incoming changes kept #,0.0, so the local edit was dropped.
6. **demo_report shows Uncommitted (Changes 1) right after the update.** Only demo_model was in conflict, yet after Merge And Update demo_report showed Uncommitted. Git status for the main workspace lists one change: demo_report, workspace Modified, no remote change, no conflict. The workspace head equals the remote head (the merge commit). A read-only comparison of getDefinition with the files on fabric-demo-git found:
   - visual.json, report.json, page.json, pages.json and version.json are byte-identical. There is no formatting normalisation of the indent=2 JSON, and the card title matches.
   - definition.pbir is byConnection (connection string with the semantic model ID) in the workspace export and byPath ../demo_model.SemanticModel in Git. This is the normal PBIR rewrite between workspace and Git, and it is not the change. The feature workspace export is also byConnection, and its demo_report shows no change.
   - .platform: the export has logicalId all zeros (normal for an export) and **no description**. Git has "description": "One card report on demo_model". The item metadata in the main workspace now has an empty description, while the same item in the feature workspace still has "One card report on demo_model".
   - Conclusion: the uncommitted change appears to be the item description. After the update, the demo_report description in the main workspace was empty, so it no longer matched the .platform in Git. The demo scripts never sent .platform or updateMetadata, and Git never changed demo_report/.platform, so the most likely cause is Update from Git applying the incoming visual.json change. This is one run, and we did not capture the description before and after the update, so treat it as an observation, not a confirmed bug. We found no documented behaviour or known issue for it (checked Oct 30, 2026). It was left alone. Either fix is a write: set the description back on the item, or commit, which would remove the description from Git. Masked evidence: results/description_evidence.md.
7. **Recording note.** The steps 12 to 14 recorder was not stopped at 22:19:35 as noted. It kept running until it was finalised at about 22:21, so its MP4 had no index (moov). Sending SIGINT to the recorder made ffmpeg write the index, and a stream copy remux gave session-steps12-14-recovered.mp4 (not published) (364.7 s, 1920x1200, decodes without errors). untrunc was not needed. The tail past 22:19:35 is not used in any clip.

## Files

Clips are not in the repo (the repo ignores *.mp4). They were cut from the session recordings on the demo machine:
- clip-branch-out.mp4: steps 5 and 6 (branch out with Select items individually, Select related items, Create branch, then the workspace tree and Related branches), 43 s, sync waits trimmed. Step 7 (Add more items) is shown in the still pBW-06, not in the clip.
- clip-compare-commit.mp4: step 9 (compare side by side, inline, commit), 32 s.
- clip-update-from-git.mp4: steps 12 to 13, 47 s. It is longer than the planned 20 s because it covers the conflict, compare modes, review, merge and the synced state.
- All clips are 1280x800, H.264, crf 18, faststart, no audio. The address bar, the commit hash in the status bar and the compare header are under a strong Gaussian blur (scripts/make_clips.py). A second pass (scripts/blur_names.py) blurs every workspace name, every item name (demo_model, demo_report, demo_vl and the rest) and anything that could show an email (the account area). Branch names and the UI stay readable.
- screenshots/pBW-*.png (captions in screenshots/README.md): the same blur applied to the screenshots, plus the workspace and item name pass. The GitHub PR shot (pBW-10) keeps its address bar because the repo URL is public. The unblurred originals and the full session recordings stay on the box and are not published.
- rec_notes.txt and rec_notes_session.txt: the recording notes taken during the run.
- results/timeline.csv: every step with Oslo times and the source of each time.
