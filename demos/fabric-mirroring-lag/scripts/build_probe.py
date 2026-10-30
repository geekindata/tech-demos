import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent)); import nbutil
P = '''src_server = ""
src_db = ""
ep_server = ""
ep_db = "source_db"
'''
C = '''import json, struct, datetime, traceback, os, sys
out = {"py": sys.version}
def save():
    txt = json.dumps(out, indent=1)
    for p in ["/lakehouse/default/Files/mirror_lag"]:
        try:
            os.makedirs(p, exist_ok=True); open(p + "/probe.json", "w").write(txt); out["saved"] = p
        except Exception as e:
            out["save_err"] = str(e)
    try:
        import notebookutils
        notebookutils.fs.put("abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/mirror_lag/probe2.json", txt, True)
    except Exception as e:
        out["put_err"] = str(e)
try:
    import pyodbc; out["drivers"] = pyodbc.drivers()
except Exception as e:
    out["pyodbc_err"] = str(e)
try:
    import notebookutils
except Exception as e:
    out["nbu_err"] = str(e)
def conn(server, db):
    for aud in ["https://database.windows.net/", "sql"]:
        try:
            t = notebookutils.credentials.getToken(aud); break
        except Exception as e:
            out.setdefault("tok_err", []).append(f"{aud}: {e}")
    b = t.encode("utf-16-le"); ts = struct.pack(f"<I{len(b)}s", len(b), b)
    drv = [d for d in pyodbc.drivers() if "SQL Server" in d][-1]
    return pyodbc.connect(f"Driver={{{drv}}};Server={server};Database={db};Encrypt=yes;", attrs_before={1256: ts}, autocommit=True)
for k, s, d in ([] if "pyodbc_err" in out else [("src", src_server, src_db), ("ep", ep_server, ep_db)]):
    try:
        c = conn(s, d); r = c.execute("select @@version, sysutcdatetime(), db_name()").fetchone()
        out[k] = [str(x) for x in r]
    except Exception as e:
        out[k + "_err"] = traceback.format_exc()[-1500:]
save()
print(json.dumps(out, indent=1))
'''
nbutil.write(str(pathlib.Path(__file__).parent.parent / 'notebooks' / 'probe_conn.ipynb'), [P, C])
