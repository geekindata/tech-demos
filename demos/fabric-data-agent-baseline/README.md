# Fabric data agent baseline (before the Nov 2 to 10 NL2SQL/DAX update)

Measured on a paid F2, Oct 30, 2026, n=1 run per question.

Run: Fri 2026-10-30, 21:57 to 22:00 Oslo (UTC+1), in one short paid window on an F2.
Scope: as cheap as possible, so each of the 20 questions was asked once (round 1 only, no pilot, no rounds 2 and 3).
With one run per question there is no run-to-run variance in this baseline.

Setup: a lakehouse with 7 TPC-H-style tables, the data agent, no instructions, no example
queries, all 7 tables selected, published. Asked through the published agent from a Python script (`scripts/ask.py`, not a
notebook) using the Fabric data agent Python SDK (`FabricOpenAIResponses`), a fresh conversation per question. Gold answers computed independently with DuckDB
on the same Delta snapshot.

## Results
| Metric | Value |
|---|---|
| Accuracy | 19 of 20 correct, 1 answered a different reasonable reading (Q20), 0 wrong |
| Latency, median | 7.6 s |
| Latency, p90 | 11.43 s (linear interpolation; nearest rank gives 11.36 s) |
| Latency, min / max | 5.3 s / 15.7 s (max is Q01, the first request after publishing) |
| Generated SQL captured | yes, 20/20 (T-SQL from the agent's nl2code step) |
| Runtime | standard (read from the agent's published and staging settings through the Fabric REST API, see below) |
| Model seen | the API responses reported model gpt-5.1 |
| Tool steps seen | fewshots.loading, analyze_lakehouse_tables, nl2code, execute |
| AI CU from returned usage | about 2,875 CU-s for 20 requests, a lower bound (see Cost) |
| F2 uptime | 7.0 min |

Runtime: read on Oct 30, 2026 at about 22:10 Oslo, read only, with nothing changed. The published and the staging
settings (`GET .../dataAgents/{id}/settings` and `.../staging/settings`) return only `aiInstructions: null`, with no
`experimental` block, so `enableExperimentalFeatures` (the preview runtime switch) is not set. The item definition
(`getDefinition`) has no runtime override either. The API does not return an explicit "standard" field: standard is
what an agent runs when the preview switch is off.

Notes on scoring (hand checked):
- Q11: answer 8,683,700,250.8999, gold rounds to .90, counted correct.
- Q16: "July, 20,773 orders" matches gold month 7, counted correct (the auto score said partial).
- Q19 "What were our total sales in 1995?" and Q20 "Who is our biggest customer?" are ambiguous by design, and we
  chose the primary reading. On Q19 the agent picked our primary reading (net revenue by order date). On Q20 it
  ranked by account balance, which is the alternative listed in `gold_alternatives.csv`, instead of revenue.
  Counted partial.

## The "Verified ontology join path" block (unverified)
In 8 of the 9 questions where the agent's SQL joined tables (Q03, Q09, Q10, Q11, Q12, Q15, Q17, Q18; not Q19), the
agent's trace shows it handing its SQL step an explicit list of join keys, labelled "Verified ontology join path".
No ontology was attached to this agent, and Microsoft's docs don't describe this step, so we're only reporting what
the trace shows. No `plan_ontology_traversal` call appears in any trace. A re-run after the Nov 2 to 10 update is planned but
not scheduled; if it goes ahead, it will check whether this block is still there.

## Question style and data (disclosure)
- The questions use the schema's own vocabulary. Q11, Q12, Q17 and Q18 give the revenue formula ("extended price
  times one minus discount"). Five questions use literal
  column values: Q04 (ship mode AIR), Q05 (BUILDING market segment), Q13 (return flag R), Q17 (EUROPE region) and
  Q18 (order priorities 1-URGENT and 5-LOW). Q05, Q13, Q14, Q15 and Q18 specify rounding.
- Only Q19 and Q20 are phrased the way a business user would ask, and both are deliberately ambiguous, with us
  choosing the primary reading.
- The data is synthetic and TPC-H-derived, made by a seeded generator. It is not official TPC-H SF1 (no dbgen).
  lineitem has 5,994,514 rows. No client data.

## Cost
The API's own token counts put the AI cost at about 2,875 CU-s for 20 questions (about 145 CU-s each). That's a
lower bound: the returned usage looks like the orchestrator call only, not the model call inside the SQL generation
step, and the SQL the agent runs bills separately as SQL Endpoint Query. The Capacity Metrics app figure (item kind
LlmPlugin, operation "AI query") follows in an update, on Sun Nov 1 or later because of data lag. No currency
figure is given until then.

Cleanup: the F2 was paused right after the run and confirmed Paused, and the workspace went back to the trial
capacity. The agent and lakehouse are kept for a possible re-run after the update, which is
planned but not scheduled and needs a new approved F2 window (see `AFTER_RUN.md`).

## Wording for posts
- Label: "Measured on a paid F2, Oct 30, 2026, n=1 run per question." No variance or consistency claims.
- Accuracy: "19 of 20 correct, 1 answered a different reasonable reading". Not "95%".
- Model: "The API responses reported model gpt-5.1." Don't attribute the model to Microsoft docs; Learn doesn't
  name it.
- Q01's 15.7 s: "first request after publishing", not a general cold start.
- Ontology block: "In 8 of the 9 questions that needed joins, the agent's trace shows it handing its SQL step an
  explicit list of join keys labelled 'Verified ontology join path'. No ontology was attached to this agent, and
  Microsoft's docs don't describe this step, so we're only reporting what the trace shows." Don't call it Fabric IQ
  grounding.
- Cost: "The API's own token counts put the AI cost at about 2,900 CU-s for 20 questions (~145 CU-s each). That's a
  lower bound; the Capacity Metrics number follows in an update." No kr or USD figure until Metrics confirms it.
- NL2SQL status: Learn's SQL sources page (Aug 31) still says advanced NL2SQL is in preview, while the October GA
  blog post says it's GA. Re-check Learn on publish day.

## Caveats
- Single run per question: no variance figure. Rounds 2 and 3 were dropped to keep cost down.
- Small synthetic data, simple schema, English questions. Not a general accuracy claim.
- The box has no .NET, so sempy's workspace and item lookups were swapped for Fabric REST calls in
  `scripts/common.py`; the agent API calls themselves are unchanged.

## Running the scripts
The scripts were written for one scratch environment. They take the Azure CLI token at runtime and never print it.
Copy `scripts/env.example` to `scripts/env.local` (gitignored) and fill it in; none of the values are in the repo.
It holds `AGENT_WS_ID` for the workspace, `DATA_AGENT_NAME` and `AGENT_LAKEHOUSE` for the item names,
`METRICS_MODEL_ID` for the Capacity Metrics semantic model, and `TRIAL_CAPACITY`, `F2_NAME` and `F2_ARM` for the
capacities used by `scripts/f2.sh`. The Azure CLI path is set at the top of each script.

Files: `results/results.csv` (generated_sql = final SQL only, IDs scrubbed; dashes in agent answers normalised to hyphens), `results/f2_window_log.csv`,
`results/ask_run1.out`, `questions.csv`, `gold_alternatives.csv`, `METHOD.md`, `AFTER_RUN.md`, `run_baseline.md`
(the runbook as planned), `scripts/`. Raw JSON stays local in `raw/` (gitignored).
