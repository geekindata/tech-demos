"""Create demo_data_agent in demo_agent_ws with the 7 agent_lh tables, NO instructions, preview runtime left at default; publish.
Refuses unless the workspace is on the active F2. Writes raw/agent_setup.json (settings, datasource elements) for the runtime record."""
import json, sys, time
from common import *
f2_guard(); cred = sdk_credential()
from fabric.dataagent.client import create_data_agent, FabricDataAgentManagement
items = fab.call('GET', f'/workspaces/{WS}/items')[1]['value']
ex = [i for i in items if i['displayName'] == AGENT]
agent = FabricDataAgentManagement(AGENT, WS) if ex else create_data_agent(AGENT, WS)
print('agent', 'exists' if ex else 'created')
rec = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
try:
    ds = agent.add_staging_datasource(LH, WS, type='lakehouse'); rec['add_ds'] = str(ds)[:500]
except Exception as e:
    rec['add_ds_error'] = repr(e)[:500]; print('add_staging_datasource failed:', repr(e)[:300])
time.sleep(10)
sel = []
for d in agent.list_datasources('staging'):
    def walk(root=None, depth=0):
        page = d.get_elements('staging', root_id=root)
        for el in page.get('value', page.get('elements', [])):
            name = el.get('displayName') or el.get('name'); eid = el.get('id')
            typ = (el.get('type') or '').lower()
            if name in TABLES and 'column' not in typ:
                d.update_element(eid, is_selected=True); sel.append(name)
            elif depth < 3 and name not in TABLES: walk(eid, depth + 1)
        rec.setdefault('elements_sample', []).append(page if depth == 0 else None)
    try: walk()
    except Exception as e: rec['elements_error'] = repr(e)[:500]
rec['selected'] = sorted(set(sel)); print('selected', rec['selected'])
if sorted(set(sel)) != sorted(TABLES):
    print('WARNING: not all 7 tables selected via API; select them in the portal (Explorer, tick the 7 tables) before publish')
rec['settings_staging'] = agent.get_settings('staging')
if '--no-publish' not in sys.argv:
    rec['publish'] = str(agent.publish_staging(description='Baseline, no instructions'))
    time.sleep(5); rec['settings_published'] = agent.get_settings('published')
json.dump(rec, open(D / 'raw/agent_setup.json', 'w'), indent=1, default=str)
print('settings:', json.dumps(rec.get('settings_published', rec['settings_staging']), default=str)[:800])
