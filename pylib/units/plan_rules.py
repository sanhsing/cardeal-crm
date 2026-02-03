from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    max_users: int
    max_records: int
    ai_queries_per_day: int

def normalize_plan_key(plan_key: Optional[str]) -> str:
    """Normalize plan key to canonical internal keys."""
    if not plan_key:
        return "free"
    p = plan_key.strip().lower()
    aliases = {
        "basic": "pro_monthly",
        "pro": "pro_monthly",
        "pro-yearly": "pro_yearly",
        "yearly": "pro_yearly",
        "monthly": "pro_monthly",
    }
    return aliases.get(p, p)

def is_plan_active(plan_expires: Optional[str], *, today: Optional[date] = None) -> bool:
    """Return True if plan is active given an ISO date string (YYYY-MM-DD) or ISO datetime."""
    if not plan_expires:
        return True  # no expiry means active by default
    if today is None:
        today = date.today()
    try:
        # Accept date or datetime strings
        dt = datetime.fromisoformat(plan_expires)
        exp_date = dt.date()
    except ValueError:
        try:
            exp_date = date.fromisoformat(plan_expires)
        except ValueError:
            return False
    return exp_date >= today

def resolve_plan(plans_cfg: Dict[str, Any], plan_key: Optional[str]) -> Dict[str, Any]:
    """Return plan dict from config, falling back to free."""
    key = normalize_plan_key(plan_key)
    plan = plans_cfg.get(key) or plans_cfg.get("free") or {}
    if not isinstance(plan, dict):
        return {}
    return plan
