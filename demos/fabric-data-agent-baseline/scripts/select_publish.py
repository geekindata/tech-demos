"""Select the 7 tables on the existing staging datasource and publish (create_agent.py ran before the async datasource sync finished)."""
import json, time
from common import *
f2_guard(); sdk_credential()
from fabric.dataagent.client import FabricDataAgentManagement
a = FabricDataAgentManagement(AGENT, WS); sel = []; tree = []
for d in a.list_datasources('staging'):
    def walk(root=None, depth=0):
        for el in d.get_elements('staging', root_id=root).get('value', []):
            name, typ = el.get('displayName'), (el.get('type') or '')
            tree.append((depth, name, typ))
            if name in TABLES and 'column' not in typ.lower():
                d.update_element(el['id'], is_selected=True); sel.append(name)
            elif depth < 3 and el.get('hasSubElements') and name not in TABLES: walk(el['id'], depth + 1)
    walk()
print('tree', tree); print('selected', sorted(set(sel)))
assert sorted(set(sel)) == sorted(TABLES), 'not all tables'
print('publish', a.publish_staging(description='Baseline, no instructions')); time.sleep(5)
rec = json.load(open(D / 'raw/agent_setup.json')); rec.update({'selected': sorted(set(sel)), 'tree': tree,
     'republished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'settings_published': a.get_settings('published'),
     'published_ds': [d.get_configuration('published') for d in a.list_datasources('published')]})
json.dump(rec, open(D / 'raw/agent_setup.json', 'w'), indent=1, default=str)
print('published ds', json.dumps(rec['published_ds'], default=str)[:800])
