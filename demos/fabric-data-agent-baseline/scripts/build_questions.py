"""Compute gold answers on the local SF1 snapshot (DuckDB) and write questions.csv plus gold_alternatives.csv."""
import csv, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import local_db
from questions_src import Q, ALT
here = pathlib.Path(__file__).resolve().parent.parent
c = local_db.connect(str(here / 'data'))
def fmt(rows, cols):
    if len(rows) == 1 and len(cols) == 1: return str(rows[0][0])
    return '; '.join(', '.join(f'{k}={v}' for k, v in zip(cols, r)) for r in rows)
with open(here / 'questions.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['q_id', 'question', 'gold_sql', 'gold_answer'])
    for qid, q, tsql, duck in Q:
        r = c.execute(duck or tsql); cols = [d[0] for d in r.description]; rows = r.fetchall()
        w.writerow([qid, q, tsql, fmt(rows, cols)]); print(qid, fmt(rows, cols))
with open(here / 'gold_alternatives.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['q_id', 'reading', 'sql', 'answer'])
    for qid, alts in ALT.items():
        for name, sql in alts:
            r = c.execute(sql); cols = [d[0] for d in r.description]; rows = r.fetchall()
            w.writerow([qid, name, sql, fmt(rows, cols)]); print(' ', qid, name, fmt(rows, cols))
