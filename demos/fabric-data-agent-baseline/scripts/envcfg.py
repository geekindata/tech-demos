"""Names and ids come from scripts/env.local (gitignored, copy scripts/env.example) or the environment. Nothing real is in the repo."""
import os, sys, pathlib
_F = pathlib.Path(__file__).resolve().parent / 'env.local'
if _F.exists():
    for _line in _F.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1); os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
def env(name):
    v = os.environ.get(name)
    if not v and name == 'AGENT_WS_ID':   # older local setups keep the id in a gitignored file
        f = pathlib.Path(__file__).resolve().parent / 'agent_ws_id'
        v = f.read_text().strip() if f.exists() else None
    if not v: sys.exit(f'set {name} in scripts/env.local or the environment (see scripts/env.example)')
    return v
