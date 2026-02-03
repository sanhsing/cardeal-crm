from __future__ import annotations

import re
from typing import Tuple

_TENANT_CODE_RE = re.compile(r"^[a-z0-9]{3,20}$")

def validate_tenant_code(code: str) -> Tuple[bool, str]:
    """Validate tenant code: lowercase alnum 3-20 chars."""
    if not code:
        return False, "店家代碼不可為空"
    c = code.strip().lower()
    if not _TENANT_CODE_RE.match(c):
        return False, "店家代碼格式錯誤（僅限小寫英數，長度 3-20）"
    return True, c
