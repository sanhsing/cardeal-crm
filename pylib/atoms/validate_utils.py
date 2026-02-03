from __future__ import annotations

from typing import Any, Iterable

def is_non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""

def require_keys(data: dict, keys: Iterable[str]) -> bool:
    return all(k in data for k in keys)

def in_choices(v: Any, choices: Iterable[Any]) -> bool:
    return v in set(choices)
