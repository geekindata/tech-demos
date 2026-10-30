# Data agent baseline: runbook for the one approved F2 window

Runbook as planned before the run (kept for reference; what actually ran is in README.md and METHOD.md).
Approved: ONE window on an F2, moved to Fri 2026-10-30 evening (USED 21:54 to 22:01 Oslo), up to 2 h, then pause.
Plan: 60 to 90 min. Hard stop: the F2 is Paused at most 120 min after resume, no matter what
(f2.sh arms a background job that moves the workspace back and suspends at resume + 115 min).

Recommended start: Sat 10:00 Oslo (09:00 UTC). The 2a overload runs on the trial and does not matter for this
run, because the data agent, its lakehouse copy and the SQL endpoint all move to the F2 for the window. 10:00
keeps the workspace moves clear of the 2a results window (about 06:00 to 08:00 Oslo). Any later time also works.

All commands run from `scripts/`, with `PY=../.venv/bin/python`.
Never print tokens. No tenant setting changes. If anything shows a tenant setting blocking data agents: stop, run
`./f2.sh back`, report.

## Fixed inputs
- Workspace `agent_workspace` (id in `AGENT_WS_ID` or the gitignored `scripts/agent_ws_id`), on the trial until the window. Lakehouse `agent_lakehouse`
  with the 7 SF1 tables (region, nation, supplier, customer, part, orders, lineitem), a file level copy of
  the SF1 tables of a lab lakehouse in a trial workspace (lineitem 5,994,514 rows, sum l_extendedprice 229300179105.02).
- `questions.csv`: 20 questions, gold computed with DuckDB on the same Delta snapshot. `gold_alternatives.csv`:
  the other readings of the two ambiguous questions (Q19, Q20).
- Agent: `data_agent`, the 7 tables, no instructions, preview runtime left at its default (record it).

## Minute by minute
| T (min) | Oslo | Step | Command / check | Abort if |
|---|---|---|---|---|
| -10 | 09:50 | Cost check | `python3 cost_check.py --extra <estimate>` (full run upper estimate) | exit 2 (over the cost cap). If only the `--extra` estimate pushes it over, rerun without `--extra` and use the reduced budget below |
| -8 | 09:52 | Budget | `BUDGET_CU` = the CU-s that fit under the cost cap after F2 uptime and a margin, from the line above. Cap at 60000 | BUDGET_CU < 15000 (not worth it: stop, report) |
| -6 | 09:54 | State | `./f2.sh state` -> F2=Paused, workspace on the trial | F2 not Paused (someone else is using it: stop, ask) |
| 0 | 10:00 | Resume | `F2_NAME=<capacity name> F2_ARM=<ARM path> F2_WINDOW_OK=2026-10-30 ./f2.sh resume` (waits for Active, arms the 115 min hard stop) | resume fails: stop, report |
| 1 | 10:01 | Hard stop armed? | `./f2.sh hardstop_status` -> armed. Note the deadline: resume UTC + 100 min = `DEADLINE` for ask.py | not armed: `./f2.sh hardstop_arm` |
| 2 | 10:02 | Move workspace | `./f2.sh to_f2` -> 202/200, capacity = the F2 | assign fails twice: `./f2.sh back`, stop |
| 4 | 10:04 | Gold cross check (optional) | `python3 verify_gold_sql.py` (T-SQL gold on the agent_lakehouse SQL endpoint, a few seconds of SQL CU on F2). On Oct 30 the box driver failed with "Protocol error in TDS stream" for every endpoint, so skip after one try | none |
| 6 | 10:06 | Create agent | `$PY create_agent.py` -> created, 7 tables selected, published; writes `raw/agent_setup.json` (settings, runtime flags) | "tenant" or "disabled" or 403 on create: stop, `./f2.sh back`, report. Tables not selected: tick them in the portal (fallback A steps 2 and 4), then publish there |
| 10 | 10:10 | Record runtime | from `raw/agent_setup.json`: `experimental` flags (preview runtime = agentic NL2SQL path), date, model from the first response. Also open the agent in the portal once and note any runtime/version label | none |
| 12 | 10:12 | Pilot: 5 requests | `$PY ask.py --runs 1 --only Q01,Q06,Q11,Q17,Q19 --cu-budget $BUDGET_CU --deadline-utc $DEADLINE` | errors on all 5: try `--mode mcp --only Q01`; if that fails too, portal fallback B |
| 17 | 10:17 | Read pilot cost | tokens and `cu_s` per row in `results/results.csv`; mean CU-s per request = M. Requests affordable = BUDGET_CU / M | M missing (no usage returned): ask.py counts 2,500 CU-s per request, keep that |
| 18 | 10:18 | Main run | `$PY ask.py --runs 1,2,3 --cu-budget $BUDGET_CU --deadline-utc $DEADLINE --max-requests 60` (run 1 of all 20, then run 2, then run 3; it skips nothing, so the 5 pilot rows are extra run 1 rows tagged by start time; drop them or keep them as warm up). If BUDGET_CU/M < 60, it stops itself at the budget; run 1 complete (20) is the minimum useful result | `touch ../results/STOP` stops it between requests |
| 18 to 75 | | Watch | `tail -f` the ask.py output: one line per request with duration, verdict, CU estimate. Expect 15 to 60 s per request, so 60 requests take 25 to 55 min | 3 errors in a row: STOP, check portal |
| 75 | 11:15 | SQL capture check | `rows with generated_sql empty` in results.csv. If empty for all, open 3 conversations in the portal (fallback B) and copy the SQL from the steps view for those rows; note "sql from portal" | none |
| 80 | 11:20 | Close | `./f2.sh back` -> workspace on the trial, F2 suspended, waits for Paused, disarms the hard stop, prints F2 minutes | Paused not reached: rerun `./f2.sh back`; then `az rest ... /suspend` by hand |
| 82 | 11:22 | Confirm | `./f2.sh state` -> F2=Paused; `./f2.sh minutes` -> log the minutes in METHOD.md | |
| 85 | 11:25 | Cost after | `python3 cost_check.py` (Cost Management lags, so it will not show the run yet; re-check Sun morning) and `METRICS_MODEL_ID=<metrics model id> python3 metrics_cu.py <F2 capacity id> 2026-10-31` (best effort; it returned 0 for every item on Oct 30) | |
| 90 | 11:30 | Score | hand check every `partial` and every `yes` from rounded answers ("about 8.68 billion" is auto scored yes); set `correct` to yes/no; keep the auto note | |

## results.csv
`results/results.csv` columns: experiment, variant, run_no, warm_or_cold, start_utc, duration_s, cu_s, rows,
notes, answer, generated_sql, correct, runtime_version, plus q_id, input_tokens, cached_tokens, output_tokens.
- cu_s: AI Query CU-s from the returned token usage with the Learn rates (100 CU-s per 1k input tokens, 10 per
  1k cached, 400 per 1k output). The SQL the agent runs bills separately to the SQL endpoint (small at SF1).
- warm_or_cold: cold = first request of the session or after a 10 min gap.
- rows: left empty unless the tool output shows a row count.
- Raw response JSON per request in `raw/` (gitignored), for the SQL and the steps.

## Cost model (for the guard)
- `cost_check.py` reads month-to-date actual and forecast from Cost Management and exits 2 over the cap.
  Personal cost figures are kept out of the repo.
- AI Query is background, smoothed over 24 h; pausing bills the rest of the smoothed usage at once.

## Fallback A: portal, create the agent
1. Fabric portal, workspace agent_workspace (must show F2 capacity), New item, Data agent, name data_agent.
2. Add data, OneLake catalog, agent_lakehouse, tick region, nation, supplier, customer, part, orders, lineitem.
3. Leave Agent instructions and data source instructions empty. Do not add example queries.
4. Publish, description "Baseline, no instructions". Note any runtime/version label shown in settings.

## Fallback B: portal, ask the questions
1. Open data_agent, start a new chat for every request (New chat button), paste the question text.
2. Time with a stopwatch from send to final answer (duration_s). Expand the steps to copy the generated SQL.
3. Fill results.csv by hand: variant `portal_no_instructions`, cu_s empty (read later from the Metrics app,
   item kind LlmPlugin, operation "AI Query"), runtime_version from the agent settings.
4. With the portal, do run 1 of all 20 first, then runs 2 and 3 if the time and budget allow.
