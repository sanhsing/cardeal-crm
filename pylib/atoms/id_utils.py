from __future__ import annotations

import uuid

def uuid4_str() -> str:
    return str(uuid.uuid4())

def short_id(length: int = 8) -> str:
    return uuid.uuid4().hex[:length]
