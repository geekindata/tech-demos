"""Upload the local SF1 Delta snapshot (current files plus _delta_log) to <workspace>/<lakehouse>/Tables/<table>."""
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import onelake
from deltalake import DeltaTable
from local_db import TABLES
here = pathlib.Path(__file__).resolve().parent.parent
ws = open(here / 'scripts/agent_ws_id').read().strip(); lh = onelake.lh_id(ws, 'agent_lakehouse')
tot = 0
for t in TABLES:
    src = here / 'data' / f'{t}_sf1'
    files = [pathlib.Path(f.replace('file://', '')) for f in DeltaTable(str(src)).file_uris()]
    files += sorted((src / '_delta_log').rglob('*'))
    for f in files:
        if f.is_dir(): continue
        rel = f.relative_to(src).as_posix()
        tot += onelake.upload(ws, f'{lh}/Tables/{t}/{rel}', str(f))
    print(t, len(files), 'files', flush=True)
print('MB', round(tot / 1e6, 1))
