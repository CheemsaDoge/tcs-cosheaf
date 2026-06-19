"""Append-only audit logging for web-originated actions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cosheaf.storage.repo import RepoContext
from cosheaf.web_actions.models import WebActionAuditEntry

WEB_ACTION_AUDIT_PATH = Path(".cosheaf") / "audit" / "web-actions.jsonl"
_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "private_key",
)
_SECRET_VALUE_PATTERN = re.compile(
    r"(?i)\b(token|secret|password|authorization|cookie|api[_-]?key)"
    r"(\s*[:=]\s*|\s+)([^\s,;]+)"
)
_GITHUB_TOKEN_PATTERN = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{8,}\b")


def append_web_action_audit(
    context: RepoContext,
    entry: WebActionAuditEntry,
) -> Path:
    """Append one redacted web-action audit entry and return its repo path."""
    payload = _redact(entry.to_dict())
    audit_path = context.resolve(WEB_ACTION_AUDIT_PATH)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
    return WEB_ACTION_AUDIT_PATH


def _redact(value: Any, *, key: str = "") -> Any:
    if _is_sensitive_key(key):
        return "[REDACTED]"
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        return {
            str(item_key): _redact(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.replace("-", "_").lower()
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_string(value: str) -> str:
    redacted = _SECRET_VALUE_PATTERN.sub(r"\1\2[REDACTED]", value)
    return _GITHUB_TOKEN_PATTERN.sub("[REDACTED]", redacted)
