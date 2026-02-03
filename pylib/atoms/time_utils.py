from __future__ import annotations

from datetime import datetime, timezone

def now_utc() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)

def isoformat(dt: datetime | None = None) -> str:
    """Return ISO-8601 string (timezone-aware)."""
    if dt is None:
        dt = now_utc()
    return dt.isoformat()

def from_iso(s: str) -> datetime:
    """Parse ISO-8601 string to datetime."""
    return datetime.fromisoformat(s)
