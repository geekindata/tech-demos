# Box-only T-SQL helper (Fabric SQL endpoint / Warehouse) via mssql-python with an Entra token. No secrets printed.
import sys, json, struct, subprocess, time
import mssql_python
def token():
    return subprocess.run(['/home/box/tools/azcli/bin/az', 'account', 'get-access-token', '--resource', 'https://database.windows.net/',
                           '--query', 'accessToken', '-o', 'tsv'], capture_output=True, text=True, check=True).stdout.strip()
def connect(server, database):
    t = token().encode('utf-16-le'); ts = struct.pack(f'<I{len(t)}s', len(t), t)
    return mssql_python.connect(f'Server={server},1433;Database={database};Encrypt=yes;TrustServerCertificate=no;', attrs_before={1256: ts}, autocommit=True)
if __name__ == '__main__':
    sql = json.load(open('/workspace/demos/.lab_lh_sql.json'))
    c = connect(sql['server'], 'lab_lh').cursor(); t = time.time(); c.execute(sys.argv[1])
    try: print(c.fetchall()[:20])
    except Exception as e: print('no rows', e)
    print('s', round(time.time() - t, 2))
