from datetime import date

from pylib.units.plan_rules import normalize_plan_key, is_plan_active, resolve_plan
from pylib.units.tenant_rules import validate_tenant_code
from pylib.units.backup_policy import BackupPolicy, should_run_backup

def test_plan_normalize():
    assert normalize_plan_key("pro") == "pro_monthly"
    assert normalize_plan_key("basic") == "pro_monthly"
    assert normalize_plan_key(None) == "free"

def test_plan_active():
    assert is_plan_active(None)
    assert is_plan_active("2099-01-01", today=date(2026,1,1))
    assert not is_plan_active("2000-01-01", today=date(2026,1,1))

def test_resolve_plan():
    plans={"free":{"max_users":1},"pro_monthly":{"max_users":5}}
    assert resolve_plan(plans,"pro")["max_users"]==5
    assert resolve_plan(plans,"unknown")["max_users"]==1

def test_tenant_code():
    ok, v = validate_tenant_code("abc123")
    assert ok and v == "abc123"
    ok, _ = validate_tenant_code("ABC")  # should normalize
    assert ok
    ok, _ = validate_tenant_code("a-1")
    assert not ok

def test_backup_policy():
    assert not should_run_backup(BackupPolicy(enabled=False))
    assert should_run_backup(BackupPolicy(enabled=True))


def test_metrics_compute_summary_basic():
    from pylib.units.metrics_rules import compute_summary
    rows = [
        {"status": "active", "amount": 10},
        {"status": "inactive", "amount": 5},
        {"status": "active", "amount": 0},
    ]
    s = compute_summary(rows)
    assert s.total == 3
    assert s.active == 2
    assert s.inactive == 1
    assert s.amount_sum == 15.0

def test_payload_build_and_map():
    from pylib.units.payload_rules import build_notification, to_webpush, to_email
    p = build_notification(title="T", body="B", level="warning", meta={"x": 1, "bad": {"k": "v"}})
    wp = to_webpush(p)
    em = to_email(p)
    assert wp["notification"]["title"] == "T"
    assert em["subject"] == "T"
    assert "bad" not in wp["notification"].get("meta", {})
