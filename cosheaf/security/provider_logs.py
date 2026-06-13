"""Deterministic leak scanner for generated provider logs and run records."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

REDACTED_VALUES = frozenset(
    {
        "",
        "<redacted>",
        "redacted",
        "***",
        "present",
        "missing",
        "unavailable",
        "none",
        "null",
    }
)

SECRET_NAME_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "secret",
    "token",
)

SECRET_NAME_ALLOWLIST = frozenset(
    {
        "api_key_env",
        "api_key_present",
        "api_key_value",
        "provider_api_key_env",
    }
)

FINDING_MESSAGES = {
    "api_key": "provider log contains an API-key-shaped value",
    "bearer_token": "provider log contains an unredacted bearer token",
    "environment_dump": "provider log contains an environment-like dump",
    "secret_env_value": "provider log contains a secret-looking key with a value",
    "hidden_reasoning": "provider log contains hidden-reasoning marker text",
    "unapproved_private_context": (
        "provider log contains private context without matching policy and consent"
    ),
    "absolute_private_path": (
        "provider log contains an absolute user/workspace filesystem path"
    ),
}

API_KEY_PATTERN = re.compile(
    r"(?i)\b("
    r"sk-(?:proj-)?[A-Za-z0-9_-]{12,}|"
    r"gh[pousr]_[A-Za-z0-9_]{12,}|"
    r"xox[baprs]-[A-Za-z0-9-]{12,}|"
    r"AKIA[0-9A-Z]{16}"
    r")\b"
)
BEARER_PATTERN = re.compile(
    r"(?i)\bbearer\s+(?!<redacted>)([A-Za-z0-9._~+/=-]{12,})"
)
ENV_ASSIGNMENT_PATTERN = re.compile(
    r"(?m)^\s*([A-Z_][A-Z0-9_]{1,64})\s*=\s*(\S.*)$"
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?im)[\"']?([A-Z0-9_.-]*(?:API[_-]?KEY|APIKEY|AUTHORIZATION|BEARER|"
    r"CREDENTIAL|PASSWORD|SECRET|TOKEN)[A-Z0-9_.-]*)[\"']?\s*[:=]\s*"
    r"([\"']?[^\"'\s,}]+[\"']?)"
)
HIDDEN_REASONING_PATTERN = re.compile(
    r"(?i)(begin hidden reasoning|hidden reasoning|chain[- ]of[- ]thought|"
    r"<thinking>|</thinking>|internal reasoning|reasoning_trace)"
)
UNAPPROVED_PRIVATE_CONTEXT_PATTERN = re.compile(
    r"(?i)(unapproved[_ -]?private[_ -]?context|raw[_ -]?private[_ -]?context)"
)
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?i)\b[A-Z]:\\(?:Users\\|[^\"'\s,}]*\\kb\\private\\)[^\"'\s,}]*"
)
POSIX_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?i)(?:/Users/[^\s\"',}]+|/home/[^\s\"',}]+|/[^\s\"',}]*/kb/private/[^\s\"',}]*)"
)


@dataclass(frozen=True)
class ProviderLogLeakFinding:
    """One deterministic provider-log scanner finding."""

    kind: str
    message: str
    path: str | None = None
    line: int | None = None
    key: str | None = None


def scan_provider_log_file(path: str | Path) -> list[ProviderLogLeakFinding]:
    """Scan a generated provider log file for unredacted sensitive content."""
    log_path = Path(path)
    return scan_provider_log_text(
        log_path.read_text(encoding="utf-8"),
        path=str(log_path),
    )


def scan_provider_log_text(
    text: str,
    *,
    path: str | Path | None = None,
) -> list[ProviderLogLeakFinding]:
    """Scan provider log text and return stable, explainable leak findings."""
    scanner = _ProviderLogScanner(str(path) if path is not None else None)
    scanner.scan_text(text)
    parsed = _parse_json_object(text)
    if parsed is not None:
        scanner.scan_json(parsed)
    return scanner.findings


class _ProviderLogScanner:
    def __init__(self, path: str | None) -> None:
        self.path = path
        self.findings: list[ProviderLogLeakFinding] = []
        self._seen: set[tuple[str, int | None, str | None]] = set()

    def scan_text(self, text: str) -> None:
        expanded_text = text.replace("\\n", "\n")
        self._scan_pattern(text, API_KEY_PATTERN, "api_key")
        self._scan_pattern(text, BEARER_PATTERN, "bearer_token")
        self._scan_pattern(text, HIDDEN_REASONING_PATTERN, "hidden_reasoning")
        self._scan_pattern(
            text,
            UNAPPROVED_PRIVATE_CONTEXT_PATTERN,
            "unapproved_private_context",
        )
        self._scan_pattern(
            text,
            WINDOWS_ABSOLUTE_PATH_PATTERN,
            "absolute_private_path",
        )
        self._scan_pattern(
            text,
            POSIX_ABSOLUTE_PATH_PATTERN,
            "absolute_private_path",
        )
        self._scan_secret_assignments(text)
        self._scan_environment_dump(expanded_text)

    def scan_json(self, value: object) -> None:
        if isinstance(value, Mapping):
            self._scan_private_context_policy(value)
        for key_path, scalar in _walk_scalars(value):
            key = key_path[-1] if key_path else None
            if isinstance(scalar, str):
                self._scan_json_string(key, scalar)
            if key is not None and _is_secret_key_name(key):
                if _is_allowed_secret_metadata_key(key):
                    continue
                if _is_sensitive_value(scalar):
                    self._add("secret_env_value", key=key)

    def _scan_json_string(self, key: str | None, value: str) -> None:
        if _is_redacted_value(value):
            return
        if API_KEY_PATTERN.search(value):
            self._add("api_key", key=key)
        if BEARER_PATTERN.search(value):
            self._add("bearer_token", key=key)
        if HIDDEN_REASONING_PATTERN.search(value):
            self._add("hidden_reasoning", key=key)
        if UNAPPROVED_PRIVATE_CONTEXT_PATTERN.search(value):
            self._add("unapproved_private_context", key=key)
        if WINDOWS_ABSOLUTE_PATH_PATTERN.search(value) or (
            POSIX_ABSOLUTE_PATH_PATTERN.search(value)
        ):
            self._add("absolute_private_path", key=key)

    def _scan_pattern(
        self,
        text: str,
        pattern: re.Pattern[str],
        kind: str,
    ) -> None:
        for match in pattern.finditer(text):
            if _is_redacted_value(match.group(0)):
                continue
            self._add(kind, line=_line_number(text, match.start()))

    def _scan_secret_assignments(self, text: str) -> None:
        for match in SECRET_ASSIGNMENT_PATTERN.finditer(text):
            key = match.group(1)
            value = match.group(2).strip("\"'")
            if _is_allowed_secret_metadata_key(key) or _looks_like_env_var_name(value):
                continue
            if _is_sensitive_value(value):
                self._add(
                    "secret_env_value",
                    line=_line_number(text, match.start()),
                    key=key,
                )

    def _scan_environment_dump(self, text: str) -> None:
        assignments = [
            match.group(1)
            for match in ENV_ASSIGNMENT_PATTERN.finditer(text)
            if not _is_redacted_value(match.group(2))
        ]
        if len(assignments) < 3:
            return
        common_env_names = {
            "PATH",
            "HOME",
            "USER",
            "USERNAME",
            "SHELL",
            "PWD",
            "HTTP_PROXY",
            "HTTPS_PROXY",
        }
        if common_env_names.intersection(assignments):
            self._add("environment_dump")

    def _scan_private_context_policy(self, mapping: Mapping[object, object]) -> None:
        private_context_sent = mapping.get("private_context_sent")
        root_scopes = mapping.get("root_scopes")
        has_private_scope = private_context_sent is True or (
            isinstance(root_scopes, Sequence)
            and not isinstance(root_scopes, str)
            and "private" in root_scopes
        )
        if not has_private_scope:
            return
        policy_scope = mapping.get("policy_scope")
        consent_granted = mapping.get("consent_granted")
        if policy_scope != "private_research" or consent_granted is not True:
            self._add("unapproved_private_context")

    def _add(
        self,
        kind: str,
        *,
        line: int | None = None,
        key: str | None = None,
    ) -> None:
        marker = (kind, line, key)
        if marker in self._seen:
            return
        self._seen.add(marker)
        self.findings.append(
            ProviderLogLeakFinding(
                kind=kind,
                message=FINDING_MESSAGES[kind],
                path=self.path,
                line=line,
                key=key,
            )
        )


def _parse_json_object(text: str) -> object | None:
    try:
        return cast(object, json.loads(text))
    except json.JSONDecodeError:
        return None


def _walk_scalars(
    value: object,
    path: tuple[str, ...] = (),
) -> Iterator[tuple[tuple[str, ...], object]]:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            yield from _walk_scalars(child, (*path, key))
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_scalars(child, (*path, str(index)))
        return
    yield path, value


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _is_secret_key_name(key: str) -> bool:
    normalized = _normalize_key(key)
    return any(marker in normalized for marker in SECRET_NAME_MARKERS)


def _is_allowed_secret_metadata_key(key: str) -> bool:
    normalized = _normalize_key(key)
    return normalized in SECRET_NAME_ALLOWLIST or normalized.endswith("_env")


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(".", "_")


def _is_sensitive_value(value: object) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip().strip("\"'")
    if _is_redacted_value(stripped) or _looks_like_env_var_name(stripped):
        return False
    if API_KEY_PATTERN.search(stripped) or BEARER_PATTERN.search(stripped):
        return True
    return len(stripped) >= 8


def _is_redacted_value(value: str) -> bool:
    return value.strip().strip("\"'").lower() in REDACTED_VALUES


def _looks_like_env_var_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", value.strip()))


__all__ = [
    "ProviderLogLeakFinding",
    "scan_provider_log_file",
    "scan_provider_log_text",
]
