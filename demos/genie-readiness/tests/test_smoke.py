"""Offline smoke test for sql/demo13_setup.sql.

1. Parses every statement with sqlglot (Databricks dialect).
2. Replays the INSERTs in DuckDB and asserts the documented join results.
Run: pip install sqlglot duckdb pytest && pytest -q tests/
"""
import re
from decimal import Decimal
from pathlib import Path

import duckdb
import sqlglot

SQL = (Path(__file__).resolve().parents[1] / "sql" / "demo13_setup.sql").read_text()

EXPECTED_JOIN = [
    ("A", "a1", 3, Decimal("42.00")),
    ("B", "a2", 3, Decimal("28.00")),
    ("C", "a1", 2, Decimal("55.00")),
]


def _db():
    con = duckdb.connect()
    con.execute("CREATE TABLE dim_a (segment_id INT PRIMARY KEY, segment VARCHAR, attribute_a VARCHAR)")
    con.execute("CREATE TABLE fact_a (id INT PRIMARY KEY, segment_id INT REFERENCES dim_a (segment_id), value DECIMAL(10,2))")
    for table, cols, vals in re.findall(r"INSERT INTO demo_dbx\.demo13\.(\w+) \((.*?)\) VALUES(.*?);", SQL, re.S):
        con.execute(f"INSERT INTO {table} ({cols}) VALUES {vals}")
    return con


def test_parses():
    assert len(sqlglot.parse(SQL, read="databricks")) == 9


def test_final_join():
    rows = _db().sql("""SELECT d.segment, d.attribute_a, COUNT(*), SUM(f.value)
                        FROM fact_a f JOIN dim_a d ON f.segment_id = d.segment_id
                        GROUP BY ALL ORDER BY 1""").fetchall()
    assert rows == EXPECTED_JOIN


def test_genie_answers():
    con = _db()
    assert con.execute("SELECT SUM(value) FROM fact_a f JOIN dim_a d USING (segment_id) WHERE attribute_a = 'a1'").fetchone()[0] == Decimal("97.00")
    assert con.execute("SELECT COUNT(*), SUM(value) FROM fact_a").fetchone() == (8, Decimal("125.00"))
