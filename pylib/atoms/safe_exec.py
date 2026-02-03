from __future__ import annotations

from typing import Callable, TypeVar, Optional, Any

T = TypeVar("T")

def safe_call(fn: Callable[[], T], *, default: Optional[T] = None, log: Optional[Callable[[Exception], Any]] = None) -> Optional[T]:
    """Execute fn and swallow exceptions, returning default.

    Use this to keep try/except out of business logic.
    """
    try:
        return fn()
    except Exception as e:
        if log:
            log(e)
        return default
