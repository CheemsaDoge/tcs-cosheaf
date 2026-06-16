"""Runtime storage for operator sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import repo_relative_posix
from cosheaf.operator_session.models import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    OperatorArtifactRef,
    OperatorCheckResult,
    OperatorPolicyFinding,
    OperatorPolicyMode,
    OperatorSession,
    OperatorSessionError,
    OperatorSessionEvent,
    OperatorToolCallRecord,
)
from cosheaf.storage.repo import RepoContext

OPERATOR_SESSION_RUNTIME_ROOT = Path(".cosheaf") / "operator-sessions"


@dataclass(frozen=True)
class OperatorSessionWriteResult:
    """One loaded or written operator session."""

    session: OperatorSession
    relative_path: Path
    events_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "operator_session",
            "session_id": self.session.session_id,
            "issue_id": self.session.issue_id,
            "status": self.session.status.value,
            "path": self.relative_path.as_posix(),
            "events_path": self.events_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": OPERATOR_SESSION_AUTHORITY_NOTICE,
            "session": self.session.to_dict(),
        }


@dataclass(frozen=True)
class OperatorSessionEventWriteResult:
    """One appended operator-session event."""

    session_id: str
    event: OperatorSessionEvent
    events_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "operator_session_event",
            "session_id": self.session_id,
            "sequence": self.event.sequence,
            "events_path": self.events_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": OPERATOR_SESSION_AUTHORITY_NOTICE,
            "event": self.event.to_dict(),
        }


def start_operator_session(
    context: RepoContext,
    *,
    issue_id: str,
    policy_mode: OperatorPolicyMode | str,
    operator_label: str,
    session_id: str | None = None,
    now: datetime | None = None,
) -> OperatorSessionWriteResult:
    """Create and persist a new runtime operator session."""
    timestamp = _normalize_timestamp(now or _utc_now())
    resolved_issue = validate_artifact_id(issue_id.strip())
    resolved_session_id = (
        validate_artifact_id(session_id.strip())
        if session_id
        else _allocate_session_id(context, resolved_issue, timestamp)
    )
    relative_path = operator_session_path(resolved_session_id)
    events_path = operator_session_events_path(resolved_session_id)
    target = context.resolve(relative_path)
    if target.exists():
        raise OperatorSessionError(
            f"operator session already exists: {resolved_session_id}",
            code="operator_session_path_exists",
            remediation="Use a new session_id or show the existing session.",
            details={"path": relative_path.as_posix()},
        )
    session = OperatorSession.start(
        session_id=resolved_session_id,
        issue_id=resolved_issue,
        policy_mode=policy_mode,
        operator_label=operator_label,
        now=timestamp,
    )
    _write_session(context, session)
    events_target = context.resolve(events_path)
    _ensure_repo_local(context, events_target)
    events_target.parent.mkdir(parents=True, exist_ok=True)
    events_target.write_text("", encoding="utf-8", newline="\n")
    return OperatorSessionWriteResult(
        session=session,
        relative_path=relative_path,
        events_path=events_path,
    )


def write_operator_session(
    context: RepoContext,
    session: OperatorSession,
) -> OperatorSessionWriteResult:
    """Persist an operator session runtime record."""
    relative_path = operator_session_path(session.session_id)
    events_path = operator_session_events_path(session.session_id)
    _write_session(context, session)
    events_target = context.resolve(events_path)
    _ensure_repo_local(context, events_target)
    events_target.parent.mkdir(parents=True, exist_ok=True)
    if not events_target.exists():
        events_target.write_text("", encoding="utf-8", newline="\n")
    return OperatorSessionWriteResult(
        session=session,
        relative_path=relative_path,
        events_path=events_path,
    )


def load_operator_session(
    context: RepoContext,
    session_id: str,
) -> OperatorSessionWriteResult:
    """Load one runtime operator session."""
    resolved = validate_artifact_id(session_id.strip())
    relative_path = operator_session_path(resolved)
    events_path = operator_session_events_path(resolved)
    target = context.resolve(relative_path)
    if not target.is_file():
        raise OperatorSessionError(
            f"operator session not found: {resolved}",
            code="operator_session_not_found",
            remediation="Start the session first or pass an existing session_id.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        session = OperatorSession.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise OperatorSessionError(
            f"operator session failed validation: {exc}",
            code="operator_session_validation_failed",
            remediation="Inspect the runtime session.json file and repair it.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return OperatorSessionWriteResult(
        session=session,
        relative_path=relative_path,
        events_path=events_path,
    )


def append_operator_session_event(
    context: RepoContext,
    *,
    session_id: str,
    event: OperatorToolCallRecord
    | OperatorArtifactRef
    | OperatorCheckResult
    | OperatorPolicyFinding,
) -> OperatorSessionEventWriteResult:
    """Append one bounded event to an existing operator session."""
    loaded = load_operator_session(context, session_id)
    events_path = loaded.events_path
    target = context.resolve(events_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    sequence = _next_sequence(target)
    wrapped = OperatorSessionEvent(
        session_id=loaded.session.session_id,
        sequence=sequence,
        event_kind=_event_kind(event),
        recorded_at=_event_recorded_at(event),
        event=event.to_dict(),
    )
    with target.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(wrapped.to_dict(), ensure_ascii=True) + "\n")
    return OperatorSessionEventWriteResult(
        session_id=loaded.session.session_id,
        event=wrapped,
        events_path=events_path,
    )


def load_operator_session_events(
    context: RepoContext,
    session_id: str,
) -> tuple[OperatorSessionEvent, ...]:
    """Load bounded events for one session."""
    loaded = load_operator_session(context, session_id)
    target = context.resolve(loaded.events_path)
    if not target.exists():
        return ()
    events: list[OperatorSessionEvent] = []
    for line in target.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            events.append(OperatorSessionEvent.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise OperatorSessionError(
                f"operator session event failed validation: {exc}",
                code="operator_session_event_validation_failed",
                remediation="Inspect the runtime events.jsonl file and repair it.",
                details={"path": loaded.events_path.as_posix()},
            ) from exc
    return tuple(events)


def operator_session_path(session_id: str) -> Path:
    """Return runtime session.json path for one session ID."""
    resolved = validate_artifact_id(session_id.strip())
    return OPERATOR_SESSION_RUNTIME_ROOT / resolved / "session.json"


def operator_session_events_path(session_id: str) -> Path:
    """Return runtime events.jsonl path for one session ID."""
    resolved = validate_artifact_id(session_id.strip())
    return OPERATOR_SESSION_RUNTIME_ROOT / resolved / "events.jsonl"


def _write_session(context: RepoContext, session: OperatorSession) -> None:
    relative_path = operator_session_path(session.session_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(session.to_json(), encoding="utf-8", newline="\n")


def _allocate_session_id(
    context: RepoContext,
    issue_id: str,
    timestamp: datetime,
) -> str:
    base = _default_session_id(issue_id, timestamp)
    candidate = base
    suffix = 2
    while context.resolve(operator_session_path(candidate)).exists():
        candidate = validate_artifact_id(f"{base}.{suffix}")
        suffix += 1
    return candidate


def _default_session_id(issue_id: str, timestamp: datetime) -> str:
    slug = f"s{timestamp:%Y%m%d}t{timestamp:%H%M%S}z"
    return validate_artifact_id(f"session.{issue_id}.{slug}")


def _next_sequence(path: Path) -> int:
    if not path.exists():
        return 1
    count = sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line)
    return count + 1


def _event_kind(
    event: OperatorToolCallRecord
    | OperatorArtifactRef
    | OperatorCheckResult
    | OperatorPolicyFinding,
) -> Literal["tool_call", "artifact_ref", "check_result", "policy_finding"]:
    if isinstance(event, OperatorToolCallRecord):
        return "tool_call"
    if isinstance(event, OperatorArtifactRef):
        return "artifact_ref"
    if isinstance(event, OperatorCheckResult):
        return "check_result"
    return "policy_finding"


def _event_recorded_at(
    event: OperatorToolCallRecord
    | OperatorArtifactRef
    | OperatorCheckResult
    | OperatorPolicyFinding,
) -> datetime:
    if isinstance(event, OperatorToolCallRecord | OperatorCheckResult):
        return event.recorded_at
    return _utc_now()


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise OperatorSessionError(
            "operator session target must stay repository-local",
            code="invalid_operator_session_path",
            remediation="Use the controlled .cosheaf/operator-sessions path.",
        ) from exc
    relative = repo_relative_posix(context.repo_root, target)
    if relative.startswith("kb/accepted/") or "/accepted/" in relative:
        raise OperatorSessionError(
            "operator session target must not be an accepted KB path",
            code="accepted_write_forbidden",
            remediation="Use runtime storage or review-context export paths only.",
        )


__all__ = [
    "OPERATOR_SESSION_RUNTIME_ROOT",
    "OperatorSessionEventWriteResult",
    "OperatorSessionWriteResult",
    "append_operator_session_event",
    "load_operator_session",
    "load_operator_session_events",
    "operator_session_events_path",
    "operator_session_path",
    "start_operator_session",
    "write_operator_session",
]
