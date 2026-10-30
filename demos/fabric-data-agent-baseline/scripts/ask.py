"""Ask the 20 questions x 3 runs and append to results/results.csv. Fresh conversation per request.
Modes: --mode sdk (default; FabricOpenAIResponses, returns tool steps so the SQL can be captured)
       --mode mcp (published agent MCP endpoint; answer text only, SQL usually not included).
Guards: refuses unless agent_workspace is on the active F2; stops at --max-requests, at --deadline-utc,
when the token based CU estimate passes --cu-budget, or when results/STOP exists.
Usage: ask.py --runs 1,2,3 [--only Q01,Q05] [--max-requests 60] [--cu-budget 60000] [--deadline-utc 2026-10-31T10:30:00Z]"""
import argparse, csv, datetime as dt, json, re, sys, time, uuid
from common import *
import score
ap = argparse.ArgumentParser()
ap.add_argument('--mode', default='sdk'); ap.add_argument('--runs', default='1,2,3'); ap.add_argument('--only', default='')
ap.add_argument('--max-requests', type=int, default=60); ap.add_argument('--cu-budget', type=float, default=60000)
ap.add_argument('--deadline-utc', default=''); ap.add_argument('--experiment', default='data_agent_baseline')
ap.add_argument('--stage', default='production')
a = ap.parse_args()
f2_guard(); cred = sdk_credential()
Q = list(csv.DictReader(open(D / 'questions.csv'))); only = set(filter(None, a.only.split(',')))
COLS = ['experiment', 'variant', 'run_no', 'warm_or_cold', 'start_utc', 'duration_s', 'cu_s', 'rows', 'notes', 'answer',
        'generated_sql', 'correct', 'runtime_version', 'q_id', 'input_tokens', 'cached_tokens', 'output_tokens']
out = D / 'results/results.csv'; new = not out.exists()
fh = open(out, 'a', newline=''); w = csv.DictWriter(fh, COLS)
if new: w.writeheader()
def cu_from_usage(u):   # Learn: AI Query 100 CU-s per 1k input, 10 per 1k cached input, 400 per 1k output tokens
    if not u: return None
    i, c, o = u.get('input_tokens', 0) or 0, (u.get('input_tokens_details') or {}).get('cached_tokens', 0) or 0, u.get('output_tokens', 0) or 0
    return round((i - c) / 1000 * 100 + c / 1000 * 10 + o / 1000 * 400, 1), i, c, o
SQL_RE = re.compile(r'\b(SELECT|WITH)\b[\s\S]+?\bFROM\b[\s\S]+', re.I)
def find_sql(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and SQL_RE.search(v) and k not in ('text',): acc.append(v)
            else: find_sql(v, acc)
    elif isinstance(obj, list):
        for v in obj: find_sql(v, acc)
    elif isinstance(obj, str):
        try: find_sql(json.loads(obj), acc)
        except Exception: pass
    return acc
# ---- clients
if a.mode == 'sdk':
    from fabric.dataagent.client import FabricOpenAIResponses
    client = FabricOpenAIResponses(AGENT, WS, ai_skill_stage=a.stage, credential=cred)
    def ask(q):
        r = client.responses.create(input=q); d = r.model_dump() if hasattr(r, 'model_dump') else json.loads(json.dumps(r, default=str))
        text = getattr(r, 'output_text', None) or ' '.join(c.get('text', '') for it in d.get('output', []) if it.get('type') == 'message' for c in it.get('content', []))
        steps = [it for it in d.get('output', []) if it.get('type') != 'message']
        return text, find_sql(steps, []), d.get('usage'), f"model={d.get('model')}", d
else:
    import httpx
    URL = f'https://api.fabric.microsoft.com/v1/mcp/workspaces/{WS}/dataagents/{fab.call("GET", f"/workspaces/{WS}/items")[1]["value"] and [i["id"] for i in fab.call("GET", f"/workspaces/{WS}/items")[1]["value"] if i["displayName"] == AGENT][0]}/agent'
    def rpc(c, sid, method, params, rid=1):
        h = {'Authorization': 'Bearer ' + cred.get_token('https://api.fabric.microsoft.com/.default').token,
             'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json', 'MCP-Protocol-Version': '2025-06-18'}
        if sid: h['Mcp-Session-Id'] = sid
        body = {'jsonrpc': '2.0', 'method': method, 'params': params}
        if rid is not None: body['id'] = rid
        r = c.post(URL, headers=h, json=body, timeout=300); r.raise_for_status()
        sid = r.headers.get('Mcp-Session-Id', sid)
        if rid is None: return sid, None
        if 'text/event-stream' in r.headers.get('content-type', ''):
            msgs = [json.loads(l[5:]) for l in r.text.splitlines() if l.startswith('data:') and l[5:].strip()]
            j = [m for m in msgs if m.get('id') == rid][-1]
        else: j = r.json()
        if 'error' in j: raise RuntimeError(str(j['error'])[:400])
        return sid, j['result']
    def ask(q):
        with httpx.Client() as c:
            sid, init = rpc(c, None, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'baseline', 'version': '1'}})
            sid, _ = rpc(c, sid, 'notifications/initialized', {}, None)
            sid, tl = rpc(c, sid, 'tools/list', {}, 2); tool = tl['tools'][0]
            arg = next(iter(tool.get('inputSchema', {}).get('properties', {'userQuestion': 0})))
            sid, res = rpc(c, sid, 'tools/call', {'name': tool['name'], 'arguments': {arg: q}}, 3)
        text = ' '.join(x.get('text', '') for x in res.get('content', []) if x.get('type') == 'text')
        return text, find_sql(res.get('structuredContent') or {}, []), None, f"mcp server={init.get('serverInfo')}", {'init': init, 'tool': tool, 'result': res}
# ---- loop: run 1 of every question, then run 2, then run 3 (no back to back repeats)
n, cu_total, last_t = 0, 0.0, None
for run in [int(x) for x in a.runs.split(',')]:
    for q in Q:
        if only and q['q_id'] not in only: continue
        now = dt.datetime.now(dt.timezone.utc)
        if (D / 'results/STOP').exists(): sys.exit('STOP file present')
        if n >= a.max_requests: sys.exit(f'max requests {n} reached')
        if a.deadline_utc and now >= dt.datetime.fromisoformat(a.deadline_utc.replace('Z', '+00:00')): sys.exit('deadline reached')
        if cu_total >= a.cu_budget: sys.exit(f'CU budget reached: est {cu_total:.0f} CU-s')
        cold = 'cold' if last_t is None or time.time() - last_t > 600 else 'warm'
        t0 = time.time(); start = now.strftime('%Y-%m-%dT%H:%M:%SZ'); note = ''
        try: text, sqls, usage, rt, raw = ask(q['question'])
        except Exception as e: text, sqls, usage, rt, raw, note = '', [], None, '', {'error': repr(e)}, 'ERROR ' + repr(e)[:300]
        dur = round(time.time() - t0, 2); last_t = time.time(); n += 1
        cu = cu_from_usage(usage); cu_s, i, c, o = cu if cu else ('', '', '', '')
        if cu: cu_total += cu_s
        else: cu_total += 2500   # conservative per request assumption when usage is not returned
        verdict, why = score.score(q['q_id'], text) if text else ('no', 'no answer')
        json.dump({'q_id': q['q_id'], 'run': run, 'start_utc': start, 'raw': raw}, open(D / f"raw/{q['q_id']}_r{run}_{uuid.uuid4().hex[:6]}.json", 'w'), default=str)
        w.writerow({'experiment': a.experiment, 'variant': f'{a.mode}_no_instructions', 'run_no': run, 'warm_or_cold': cold,
                    'start_utc': start, 'duration_s': dur, 'cu_s': cu_s, 'rows': '', 'notes': (note + ' auto score: ' + why).strip(),
                    'answer': text[:2000], 'generated_sql': ' ;; '.join(sqls)[:4000], 'correct': verdict, 'runtime_version': rt,
                    'q_id': q['q_id'], 'input_tokens': i, 'cached_tokens': c, 'output_tokens': o}); fh.flush()
        print(f"{start} {q['q_id']} r{run} {dur}s {verdict} cu={cu_s} est_total={cu_total:.0f} sql={'y' if sqls else 'n'}", flush=True)
print(f'done: {n} requests, est AI CU {cu_total:.0f} CU-s')
