"""DuckDB views over the local SF1 Delta snapshot (active files only, via deltalake)."""
import duckdb
from deltalake import DeltaTable
TABLES = ['region', 'nation', 'supplier', 'customer', 'part', 'orders', 'lineitem']
def connect(root='data'):
    c = duckdb.connect()
    for t in TABLES:
        files = [f.replace('file://', '') for f in DeltaTable(f'{root}/{t}_sf1').file_uris()]
        c.execute(f"create view {t} as select * from read_parquet({files!r})")
    return c
