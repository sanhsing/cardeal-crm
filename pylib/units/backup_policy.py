from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass(frozen=True)
class BackupPolicy:
    enabled: bool = False
    retention_days: int = 7
    notify: bool = False

def should_run_backup(policy: BackupPolicy) -> bool:
    return bool(policy.enabled)

def cutoff_time(*, now: Optional[datetime] = None, retention_days: int = 7) -> datetime:
    if now is None:
        now = datetime.now()
    return now - timedelta(days=max(0, int(retention_days)))
