"""Shared bits: ids, guard that the agent workspace is on the ACTIVE F2, SDK credential setup (Azure CLI, tokens never printed)."""
import os, sys, subprocess, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import fab
os.environ['PATH'] = '/home/box/tools/azcli/bin:' + os.environ['PATH']   # AzureCliCredential needs az on PATH
D = pathlib.Path(__file__).resolve().parent.parent
WS = os.environ.get('AGENT_WS_ID') or (D / 'scripts/agent_ws_id').read_text().strip()   # local only, gitignored
AGENT, LH = 'data_agent', 'agent_lakehouse'
TABLES = ['region', 'nation', 'supplier', 'customer', 'part', 'orders', 'lineitem']
def f2_guard():
    caps = {c['id']: c for c in fab.call('GET', '/capacities')[1]['value']}
    cap = caps.get(fab.call('GET', f'/workspaces/{WS}')[1].get('capacityId'), {})
    if cap.get('sku') != 'F2' or cap.get('state') != 'Active':
        sys.exit(f"REFUSED: agent_workspace is on {cap.get('sku')} ({cap.get('state')}); data agents need the active F2")
    return cap['id']
def sdk_credential():
    from azure.identity import AzureCliCredential
    from fabric.analytics.environment.credentials import SetFabricAnalyticsDefaultTokenCredentialsGlobally
    cred = AzureCliCredential(process_timeout=60); SetFabricAnalyticsDefaultTokenCredentialsGlobally(cred); return cred
# No .NET on the box: sempy's resolve_workspace_name/id load the AS client. Resolve via the Fabric REST API instead.
def _patch_sempy():
    import sempy.fabric as sf
    def _ws(w):
        w = str(w)
        for x in fab.call('GET', '/workspaces')[1]['value']:
            if x['id'].lower() == w.lower() or x['displayName'] == w: return x
        raise ValueError('workspace not found: ' + w)
    sf.resolve_workspace_name = lambda workspace=None, **k: _ws(workspace or WS)['displayName']
    sf.resolve_workspace_id = lambda workspace=None, **k: _ws(workspace or WS)['id']
    import pandas as pd
    def list_items(type=None, workspace=None, item_type=None, **k):
        t = item_type or type; wid = _ws(workspace or WS)['id']
        v = fab.call('GET', f'/workspaces/{wid}/items')[1]['value']
        v = [i for i in v if t is None or i['type'].lower() == str(t).lower()]
        return pd.DataFrame([{'Id': i['id'], 'Display Name': i['displayName'], 'Description': i.get('description', ''),
                              'Type': i['type'], 'Workspace Id': wid} for i in v], columns=['Id', 'Display Name', 'Description', 'Type', 'Workspace Id'])
    sf.list_items = list_items
    import fabric.dataagent.client._fabric_data_agent_mgmt as m
    m.resolve_workspace_id = sf.resolve_workspace_id; m.list_items = list_items
_patch_sempy()
try:   # no Fabric runtime on the box: give the context provider the workspace instead of prompting on stdin
    from fabric.analytics.environment.context_plugin import BaseContextProvider; BaseContextProvider._workspace_id = WS
except Exception: pass
