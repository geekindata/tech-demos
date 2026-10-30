"""Smoke test: bundle YAML parses, prod runs as a variable SP, and no IDs are committed."""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "databricks"
GUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def load(name):
    return yaml.safe_load((BUNDLE / name).read_text())


def test_yaml_parses():
    assert load("databricks.yml")["bundle"]
    assert load("resources/demo_daily_job.yml")["resources"]["jobs"]["demo_daily_job"]


def test_prod_run_as_and_permissions():
    cfg = load("databricks.yml")
    assert "default" not in cfg["variables"]["prod_sp_app_id"]
    prod = cfg["targets"]["prod"]
    assert prod["run_as"] == {"service_principal_name": "${var.prod_sp_app_id}"}
    perms = {(p["level"], p.get("user_name") or p.get("group_name")) for p in prod["permissions"]}
    assert perms == {("CAN_MANAGE", "${workspace.current_user.userName}"), ("CAN_VIEW", "analysts")}


def test_schedule_ships_paused():
    job = load("resources/demo_daily_job.yml")["resources"]["jobs"]["demo_daily_job"]
    assert job["schedule"]["pause_status"] == "PAUSED"


def test_no_ids_committed():
    for f in ROOT.rglob("*"):
        if f.is_file() and f.suffix in {".yml", ".md", ".sql", ".py"} and f.name != "test_bundle.py":
            assert not GUID.search(f.read_text()), f
