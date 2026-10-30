"""Build notebooks/sync_check.ipynb: one read only query on the SQL analytics endpoint to see which metadata sync it uses.
OBJECT_ID of sys.dm_db_external_tables_log_status and sys.sp_dw_refresh_ext_table is non NULL only with the new metadata sync (preview)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent)); import nbutil
P = '''ep_server = ""
ep_db = ""
files_root = ""   # abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files
'''
C = '''import json, struct, traceback, pyodbc, notebookutils
out = {}
try:
    t = notebookutils.credentials.getToken("https://database.windows.net/").encode("utf-16-le")
    drv = [d for d in pyodbc.drivers() if "SQL Server" in d][-1]
    c = pyodbc.connect(f"Driver={{{drv}}};Server={ep_server};Database={ep_db};Encrypt=yes;", attrs_before={1256: struct.pack(f"<I{len(t)}s", len(t), t)}, autocommit=True)
    r = c.execute("SELECT OBJECT_ID('sys.dm_db_external_tables_log_status') AS dmv_log_status, OBJECT_ID('sys.sp_dw_refresh_ext_table') AS sp_refresh, SYSUTCDATETIME()").fetchone()
    out["dmv_log_status"], out["sp_refresh"], out["utc"] = r[0], r[1], str(r[2])
    if r[0] is not None:
        cur = c.execute("SELECT TOP 5 * FROM sys.dm_db_external_tables_log_status")
        out["dmv_cols"] = [d[0] for d in cur.description]; out["dmv_rows"] = [[str(x) for x in row] for row in cur.fetchall()]
except Exception:
    out["err"] = traceback.format_exc()[-1500:]
txt = json.dumps(out, indent=1, default=str)
notebookutils.fs.put(files_root + "/mirror_lag/sync_check/sync_check.json", txt, True)
print(txt)
'''
nbutil.write(str(pathlib.Path(__file__).parent.parent / 'notebooks' / 'sync_check.ipynb'), [P, C])
