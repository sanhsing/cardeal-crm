from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class NotificationPayload:
    """A channel-agnostic notification payload.

    Convert to platform-specific payloads in adapters outside pylib (HTTP/SDK layer).
    """
    title: str
    body: str
    url: Optional[str] = None
    level: str = "info"  # info|warning|error
    meta: Dict[str, Any] = None  # small, JSON-serializable only


def build_notification(
    *,
    title: str,
    body: str,
    url: Optional[str] = None,
    level: str = "info",
    meta: Optional[Mapping[str, Any]] = None,
) -> NotificationPayload:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("body must be a non-empty string")
    level = (level or "info").strip().lower()
    if level not in ("info", "warning", "error"):
        level = "info"

    safe_meta: Dict[str, Any] = {}
    if meta:
        # Keep meta JSON-safe by shallow-copying primitives only.
        for k, v in dict(meta).items():
            if isinstance(k, str) and len(k) <= 64:
                if isinstance(v, (str, int, float, bool)) or v is None:
                    safe_meta[k] = v

    return NotificationPayload(
        title=title.strip(),
        body=body.strip(),
        url=(url.strip() if isinstance(url, str) and url.strip() else None),
        level=level,
        meta=safe_meta,
    )


def to_webpush(payload: NotificationPayload) -> Dict[str, Any]:
    """Map to a typical Web Push JSON payload shape (no SDK calls)."""
    data: Dict[str, Any] = {
        "title": payload.title,
        "body": payload.body,
        "level": payload.level,
    }
    if payload.url:
        data["url"] = payload.url
    if payload.meta:
        data["meta"] = payload.meta
    return {"notification": data}


def to_email(payload: NotificationPayload) -> Dict[str, Any]:
    """Map to an email-ready dict (rendering handled elsewhere)."""
    return {
        "subject": payload.title,
        "text": payload.body,
        "url": payload.url,
        "level": payload.level,
        "meta": payload.meta or {},
    }
