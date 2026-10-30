# After-run plan (NOT SCHEDULED: waiting on approval)

Nothing here runs until a new F2 window is approved. Open decisions: the window itself (about 7 to 10 min,
similar cost to the baseline), n=1 or n=3 (n=3 costs about 3x the AI CU but supports a variance statement), and
whether cost figures or the capacity name are published.

1. Gate: run only after Nov 10, 2026, and only if the response model string is no longer gpt-5.1 or the trace shows
   the new advanced NL2SQL steps. Otherwise the rollout hasn't reached the tenant yet.
2. Framing: "standard runtime before vs after the Nov 2 to 10 update". The model and the SQL tool change together,
   so this is not a model-only comparison. With 19/20 already, don't frame it as "watch it get better".
3. Keep identical:
   - the 20 questions, byte for byte and in the same order
   - no instructions and no example queries
   - the same 7 tables and the same agent lakehouse snapshot (lineitem 5,994,514 rows; sum of l_extendedprice
     229300179105.02)
   - the runtime (standard), with no republish
   - `FabricOpenAIResponses` with a new conversation per question
   - the same F2 and region
   - the same scorer and gold
4. Record: the runtime, the model string, the step names, and the Capacity Metrics figure.
5. Pre-registered scoring: a clarifying question (advanced NL2SQL may ask one on Q19 and Q20) counts as its own
   category, "clarified", neither correct nor wrong.
