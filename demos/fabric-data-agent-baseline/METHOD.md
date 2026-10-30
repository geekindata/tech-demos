# Data agent baseline: method

Status: run on Fri Oct 30, 2026, in one approved F2 window, then paused.

Method (Fabric Expert, Oct 30):
- 20 fixed questions over one lakehouse, each with a known-correct SQL answer (gold computed with DuckDB on the
  same Delta snapshot).
- Planned: each question asked 3 times. Superseded: round 1 only, n=1 per question, to keep cost as low as
  possible. No pilot, no rounds 2 and 3, so there is no variance figure.
- Recorded per request: answer, generated SQL, correct (yes / partial / no), latency, returned token usage.
- Recorded the date, the model string in the responses (gpt-5.1) and the tool steps.
- Runtime: standard. Read afterwards from the agent's published and staging settings through the Fabric REST API
  (no `experimental` block, so the preview runtime switch is off). Nothing was changed.
- Paused the F2 right after the run and confirmed Paused.

Statistics:
- Median of the 20 latencies: 7.605 s, reported as 7.6 s.
- p90 uses linear interpolation (numpy default): 11.43 s. Nearest rank gives 11.36 s.
- Min 5.28 s, max 15.70 s (Q01, first request after publishing).
- CU-s per request from the returned usage with the Learn rates (100 CU-s per 1k input tokens, 10 per 1k cached
  input, 400 per 1k output). The sum, 2,875.4 CU-s, is a lower bound; the Capacity Metrics app figure follows.

Scoring: `scripts/score.py` matches gold values in the answer, then every partial and every rounded yes was checked by
hand (see README). Q19 and Q20 are ambiguous by design; `gold_alternatives.csv` lists the other readings.

## Run Fri Oct 30
- F2 resumed 21:54 Oslo (Active 21:54:19), Paused 22:01:22 Oslo, confirmed. F2 uptime 7.0 min.
- Round 1 only: 20 requests, 21:57 to 22:00 Oslo. 19/20 correct, 1 partial. See README.md.
