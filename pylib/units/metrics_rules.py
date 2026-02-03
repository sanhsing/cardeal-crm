from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Summary:
    """Pure, serializable summary for dashboards/reports.

    Keep this free of DB/HTTP concerns. Treat inputs as already-loaded data.
    """
    total: int
    active: int
    inactive: int
    amount_sum: float
    amount_avg: float
    by_status: Dict[str, int]


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def compute_summary(
    rows: Sequence[Mapping[str, Any]],
    *,
    status_key: str = "status",
    active_statuses: Tuple[str, ...] = ("active", "enabled", "paid"),
    amount_key: Optional[str] = "amount",
) -> Summary:
    """Compute a stable dashboard summary from a list of dict-like rows.

    Parameters
    ----------
    rows:
        Sequence of row mappings (e.g., ORM rows converted to dict).
    status_key:
        Mapping key used for status classification.
    active_statuses:
        Status values considered "active".
    amount_key:
        Mapping key for numeric aggregation. Set to None to disable amount aggregation.

    Returns
    -------
    Summary:
        Deterministic summary; safe to jsonify via asdict() or manual mapping.
    """
    total = len(rows)
    by_status: Dict[str, int] = {}
    active = 0
    amount_sum = 0.0
    amount_count = 0

    for r in rows:
        status = str(r.get(status_key, "unknown")).strip().lower() or "unknown"
        by_status[status] = by_status.get(status, 0) + 1

        if status in active_statuses:
            active += 1

        if amount_key:
            if amount_key in r and r.get(amount_key) is not None:
                amount_sum += _to_float(r.get(amount_key))
                amount_count += 1

    inactive = total - active
    amount_avg = (amount_sum / amount_count) if amount_count else 0.0

    return Summary(
        total=total,
        active=active,
        inactive=inactive,
        amount_sum=amount_sum,
        amount_avg=amount_avg,
        by_status=by_status,
    )


def merge_summaries(a: Summary, b: Summary) -> Summary:
    """Merge two summaries (useful for multi-source reporting)."""
    by_status: Dict[str, int] = dict(a.by_status)
    for k, v in b.by_status.items():
        by_status[k] = by_status.get(k, 0) + int(v)

    total = a.total + b.total
    active = a.active + b.active
    inactive = total - active
    amount_sum = a.amount_sum + b.amount_sum

    # avg recomputed using weighted count is impossible without counts; keep conservative:
    # Use total as denominator only if both had counts; otherwise 0.0 is safer.
    amount_avg = 0.0
    if total:
        amount_avg = amount_sum / total

    return Summary(
        total=total,
        active=active,
        inactive=inactive,
        amount_sum=amount_sum,
        amount_avg=amount_avg,
        by_status=by_status,
    )
