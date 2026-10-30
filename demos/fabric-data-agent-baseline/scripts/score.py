"""Auto score an answer against gold_answer (and documented alternatives). yes = every gold value found,
partial = some found or an alternative reading matched, no = none. Always spot check by hand."""
import csv, re, pathlib
D = pathlib.Path(__file__).resolve().parent.parent
GOLD = {r['q_id']: r['gold_answer'] for r in csv.DictReader(open(D / 'questions.csv'))}
ALT = {}
for r in csv.DictReader(open(D / 'gold_alternatives.csv')): ALT.setdefault(r['q_id'], []).append((r['reading'], r['answer']))
NUM = re.compile(r'-?\d[\d,]*\.?\d*')
def tokens(gold):
    vals = [v.split('=', 1)[1].strip() if '=' in v else v.strip() for part in gold.split(';') for v in part.split(',')]
    return [v for v in vals if v]
def nums(text): return [float(x.replace(',', '')) for x in NUM.findall(text.replace('\u202f', '').replace(' ', ''))] + [float(x.replace(',', '')) for x in NUM.findall(text)]
def found(tok, text, ns):
    try: g = float(tok)
    except ValueError: return tok.lower() in text.lower()
    tol = max(0.006, abs(g) * 1e-6)
    return any(abs(n - g) <= tol for n in ns) or any(abs(n * s - g) <= abs(g) * 0.0051 for n in ns for s in (1e3, 1e6, 1e9) if n)
def score(qid, text):
    ns = nums(text); toks = tokens(GOLD[qid]); hit = [t for t in toks if found(t, text, ns)]
    if len(hit) == len(toks): return 'yes', f'{len(hit)}/{len(toks)} gold values'
    for name, ans in ALT.get(qid, []):
        at = tokens(ans)[:2]
        if at and all(found(t, text, ns) for t in at): return 'partial', f'alternative reading: {name}'
    return ('partial' if hit else 'no'), f'{len(hit)}/{len(toks)} gold values'
if __name__ == '__main__':
    for q, g in GOLD.items(): assert score(q, 'Answer: ' + g)[0] == 'yes', q
    print(score('Q11', 'Total revenue was 8,683,700,250.90'), score('Q11', 'about 8.68 billion'), score('Q19', 'Sales were 37,013,643,233.47'), score('Q09', 'Europe'))
    print('score self test ok')
