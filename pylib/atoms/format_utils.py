from __future__ import annotations

def human_number(n: int | float) -> str:
    """Format numbers like 1200 -> 1.2K, 1500000 -> 1.5M."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def safe_str(v) -> str:
    return "" if v is None else str(v)
