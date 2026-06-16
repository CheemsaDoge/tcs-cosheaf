"""Strict DTOs for operator sessions.

Operator sessions are runtime review metadata only. They do not create proof,
human review, verifier pass, accepted status, accepted refutation, or
promotion authority.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.agent.run_logging import SECRET_VALUE_PATTERN
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path

OPERATOR_SESSION_AUTHORITY_NOTICE = (
    "Operator session records are bounded review metadata only; they are not "
    "proof, verifier pass, gate pass, human review, accepted status, accepted "
    "refutation, or promotion authority."
)
SKIPPED_OPERATOR_SESSION_LIMITATION = (
    "Skipped operator-session checks are not pass evidence."
)

AUTHORITY_CLAIM_FIELDS = frozenset(
    {
        "accepted",
        "accepted_write_performed",
        "accepted_status",
        "artifact_status",
        "gate_pass",
        "human_review",
        "human_review_created",
        "human_reviewed",
        "promote",
        "promotion_authority",
        "promotion_performed",
        "review_state",
        "verifier_pass",
        "verifier_result_mutated",
    }
)
HIDDEN_REASONING_FIELDS = frozenset(
    {"chain_of_thought", "hidden_reasoning", "reasoning_trace"}
)
RAW_OUTPUT_FIELDS = frozenset(
    {
        "stdout",
        "stderr",
        "raw_stdout",
        "raw_stderr",
        "raw_output",
        "full_output",
        "artifact_text",
        "full_artifact_text",
        "private_text",
    }
)
ENVIRONMENT_FIELDS = frozenset({"env", "environ", "environment", "env_dump"})
SECRET_KEYWORDS = frozenset(
    {
        "api-key",
        "apikey",
        "auth",
        "authorization",
        "bearer",
        "client-secret",
        "credential",
        "key",
        "password",
        "secret",
        "token",
    }
)
HIDDEN_REASONING_MARKERS = (
    "chain of thought",
    "chain-of-thought",
    "hidden reasoning",
    "reasoning trace",
)


class OperatorSessionError(ValueError):
    """Expected operator-session service failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        remediation: str,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.remediation = remediation
        self.details = dict(details or {})


class OperatorPolicyMode(StrEnum):
    """Policy scope for an operator session."""

    PUBLIC_ONLY = "public_only"
    PRIVATE_RESEARCH = "private_research"


class OperatorSessionStatus(StrEnum):
    """Operator session lifecycle state."""

    IN_PROGRESS = "in_progress"
    FINALIZED = "finalized"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class OperatorArtifactRefKind(StrEnum):
    """Kinds of safe references a session can store."""

    DRAFT = "draft"
    REVIEW_CONTEXT = "review_context"
    RUNTIME = "runtime"
    REPORT = "report"
    SOURCE_NOTE = "source_note"
    OTHER = "other"


class OperatorCheckKind(StrEnum):
    """Check result categories that can be referenced by a session."""

    VALIDATE = "validate"
    GATE = "gate"
    TEST = "test"
    EVAL = "eval"
    SMOKE = "smoke"
    OTHER = "other"


class OperatorCheckStatus(StrEnum):
    """Normalized session check status."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"


class OperatorToolCallStatus(StrEnum):
    """Normalized status for a recorded operator tool call."""

    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    DENIED = "denied"
    SKIPPED = "skipped"


class OperatorPolicyFindingSeverity(StrEnum):
    """Policy finding severity."""

    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class OperatorSessionModel(BaseModel):
    """Strict deterministic base model for operator-session DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable data."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON text."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class OperatorArtifactRef(OperatorSessionModel):
    """One safe file or artifact reference attached to a session."""

    kind: OperatorArtifactRefKind
    path: str | None = None
    artifact_id: str | None = None
    summary: str | None = None
    scope: Literal["public", "private", "workspace", "framework", "unknown"] = (
        "unknown"
    )

    @field_validator("path")
    @classmethod
    def _path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("summary")
    @classmethod
    def _summary(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @model_validator(mode="after")
    def _has_path_or_id(self) -> Self:
        if self.path is None and self.artifact_id is None:
            raise ValueError("operator artifact references require path or artifact_id")
        return self


class OperatorCheckResult(OperatorSessionModel):
    """One check status referenced by a session."""

    kind: OperatorCheckKind
    status: OperatorCheckStatus
    summary: str
    report_path: str | None = None
    recorded_at: datetime

    @field_validator("summary")
    @classmethod
    def _summary(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("report_path")
    @classmethod
    def _report_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)

    @field_validator("recorded_at")
    @classmethod
    def _recorded_at(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value)

    @model_validator(mode="after")
    def _skipped_is_not_pass(self) -> Self:
        if (
            self.status is OperatorCheckStatus.SKIPPED
            and SKIPPED_OPERATOR_SESSION_LIMITATION.lower()
            not in self.summary.lower()
        ):
            raise ValueError("skipped check results must say skipped is not pass")
        return self


class OperatorPolicyFinding(OperatorSessionModel):
    """One policy finding discovered during a session."""

    finding_id: str
    severity: OperatorPolicyFindingSeverity
    code: str
    message: str
    path: str | None = None

    @field_validator("finding_id")
    @classmethod
    def _finding_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("code", "message")
    @classmethod
    def _text(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("path")
    @classmethod
    def _path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value)


class OperatorToolCallRecord(OperatorSessionModel):
    """One bounded tool-call record for session replay."""

    event_id: str
    tool_name: str
    status: OperatorToolCallStatus
    recorded_at: datetime
    input_metadata: dict[str, str] = Field(default_factory=dict)
    result_summary: str | None = None
    warning_codes: tuple[str, ...] = ()

    @field_validator("event_id")
    @classmethod
    def _event_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("tool_name")
    @classmethod
    def _tool_name(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("recorded_at")
    @classmethod
    def _recorded_at(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value)

    @field_validator("input_metadata", mode="before")
    @classmethod
    def _metadata(cls, value: Any) -> dict[str, str]:
        return _safe_metadata(value)

    @field_validator("result_summary")
    @classmethod
    def _result_summary(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("warning_codes", mode="before")
    @classmethod
    def _warning_codes(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))


class OperatorSessionSummary(OperatorSessionModel):
    """Compact non-authoritative summary for one operator session."""

    schema_version: Literal[1] = 1
    session_id: str
    issue_id: str
    policy_mode: OperatorPolicyMode
    status: OperatorSessionStatus
    started_at: datetime
    finalized_at: datetime | None = None
    artifact_ref_count: int
    check_result_count: int
    skipped_check_count: int
    blocking_finding_count: int
    accepted_write_performed: Literal[False] = False
    authority_notice: str = OPERATOR_SESSION_AUTHORITY_NOTICE


class OperatorSession(OperatorSessionModel):
    """Durable v1 operator session runtime record."""

    schema_version: Literal[1] = 1
    session_id: str
    issue_id: str
    policy_mode: OperatorPolicyMode
    operator_label: str
    status: OperatorSessionStatus
    started_at: datetime
    finalized_at: datetime | None = None
    base_commit: str | None = None
    head_commit: str | None = None
    artifact_refs: tuple[OperatorArtifactRef, ...] = ()
    check_results: tuple[OperatorCheckResult, ...] = ()
    policy_findings: tuple[OperatorPolicyFinding, ...] = ()
    limitations: tuple[str, ...] = Field(
        default_factory=lambda: (OPERATOR_SESSION_AUTHORITY_NOTICE,)
    )
    operator_notes: tuple[str, ...] = ()
    authority_notice: str = OPERATOR_SESSION_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False
    human_review_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    verifier_result_mutated: Literal[False] = False

    @classmethod
    def start(
        cls,
        *,
        session_id: str,
        issue_id: str,
        policy_mode: OperatorPolicyMode | str,
        operator_label: str,
        now: datetime | None = None,
        base_commit: str | None = None,
    ) -> OperatorSession:
        """Create an in-progress operator session record."""
        timestamp = _normalize_timestamp(now or _utc_now())
        return cls(
            session_id=session_id,
            issue_id=issue_id,
            policy_mode=OperatorPolicyMode(policy_mode),
            operator_label=operator_label,
            status=OperatorSessionStatus.IN_PROGRESS,
            started_at=timestamp,
            base_commit=base_commit,
        )

    @field_validator("session_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("operator_label")
    @classmethod
    def _operator_label(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("base_commit", "head_commit")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("started_at", "finalized_at")
    @classmethod
    def _timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _normalize_timestamp(value)

    @field_validator("limitations", "operator_notes", mode="before")
    @classmethod
    def _safe_text_tuple(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @model_validator(mode="after")
    def _consistency(self) -> Self:
        if self.finalized_at is not None and self.finalized_at < self.started_at:
            raise ValueError("finalized_at must not be earlier than started_at")
        if self.status is OperatorSessionStatus.IN_PROGRESS:
            if self.finalized_at is not None:
                raise ValueError("in-progress sessions cannot have finalized_at")
        elif self.finalized_at is None:
            raise ValueError("terminal sessions require finalized_at")
        if OPERATOR_SESSION_AUTHORITY_NOTICE not in self.limitations:
            raise ValueError("limitations must include operator-session notice")
        if self.authority_notice != OPERATOR_SESSION_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve session boundary")
        return self

    def with_artifact_ref(self, ref: OperatorArtifactRef) -> OperatorSession:
        """Return a copy with a safe artifact/file reference appended."""
        self._ensure_mutable()
        return self._replace(artifact_refs=(*self.artifact_refs, ref))

    def with_check_result(self, result: OperatorCheckResult) -> OperatorSession:
        """Return a copy with one check result appended."""
        self._ensure_mutable()
        return self._replace(check_results=(*self.check_results, result))

    def with_policy_finding(
        self,
        finding: OperatorPolicyFinding,
    ) -> OperatorSession:
        """Return a copy with one policy finding appended."""
        self._ensure_mutable()
        return self._replace(policy_findings=(*self.policy_findings, finding))

    def finalize(
        self,
        *,
        now: datetime | None = None,
        status: OperatorSessionStatus | str = OperatorSessionStatus.FINALIZED,
        head_commit: str | None = None,
    ) -> OperatorSession:
        """Return a terminal session record."""
        self._ensure_mutable()
        resolved = OperatorSessionStatus(status)
        if resolved is OperatorSessionStatus.IN_PROGRESS:
            raise ValueError("final status must be terminal")
        return self._replace(
            status=resolved,
            finalized_at=_normalize_timestamp(now or _utc_now()),
            head_commit=head_commit,
        )

    def summary(self) -> OperatorSessionSummary:
        """Return a compact session summary."""
        return OperatorSessionSummary(
            session_id=self.session_id,
            issue_id=self.issue_id,
            policy_mode=self.policy_mode,
            status=self.status,
            started_at=self.started_at,
            finalized_at=self.finalized_at,
            artifact_ref_count=len(self.artifact_refs),
            check_result_count=len(self.check_results),
            skipped_check_count=sum(
                1
                for result in self.check_results
                if result.status is OperatorCheckStatus.SKIPPED
            ),
            blocking_finding_count=sum(
                1
                for finding in self.policy_findings
                if finding.severity is OperatorPolicyFindingSeverity.BLOCKER
            ),
        )

    def _replace(self, **updates: Any) -> OperatorSession:
        data = self.model_dump(mode="python")
        data.update(updates)
        return OperatorSession.model_validate(data)

    def _ensure_mutable(self) -> None:
        if self.status is not OperatorSessionStatus.IN_PROGRESS:
            raise ValueError("terminal operator sessions cannot be modified")


class OperatorSessionEvent(OperatorSessionModel):
    """One bounded event line in an operator-session transcript."""

    schema_version: Literal[1] = 1
    session_id: str
    sequence: int
    event_kind: Literal[
        "tool_call",
        "artifact_ref",
        "check_result",
        "policy_finding",
    ]
    recorded_at: datetime
    event: dict[str, Any]
    authority_notice: str = OPERATOR_SESSION_AUTHORITY_NOTICE

    @field_validator("session_id")
    @classmethod
    def _session_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("recorded_at")
    @classmethod
    def _recorded_at(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value)

    @model_validator(mode="after")
    def _authority_notice(self) -> Self:
        if self.sequence < 1:
            raise ValueError("event sequence must be positive")
        if self.authority_notice != OPERATOR_SESSION_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve session boundary")
        return self


def _safe_metadata(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("input_metadata must be an object")
    result: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = _safe_metadata_key(str(raw_key))
        text = _safe_text(str(raw_value))
        if _is_path_key(key):
            text = _validate_repo_local_path(text)
        result[key] = text
    return dict(sorted(result.items()))


def _safe_metadata_key(key: str) -> str:
    normalized = key.strip()
    if not normalized:
        raise ValueError("metadata key must be non-empty")
    lowered = normalized.replace("_", "-").lower()
    if (
        lowered in AUTHORITY_CLAIM_FIELDS
        or lowered.replace("-", "_") in AUTHORITY_CLAIM_FIELDS
    ):
        raise ValueError(
            "metadata cannot claim review, verifier, or promotion authority"
        )
    if lowered in HIDDEN_REASONING_FIELDS or lowered.replace("-", "_") in (
        HIDDEN_REASONING_FIELDS
    ):
        raise ValueError("metadata cannot store hidden reasoning")
    if lowered in RAW_OUTPUT_FIELDS or lowered.replace("-", "_") in RAW_OUTPUT_FIELDS:
        raise ValueError("metadata cannot store raw stdout/stderr or full text")
    if lowered in ENVIRONMENT_FIELDS or lowered.replace("-", "_") in ENVIRONMENT_FIELDS:
        raise ValueError("metadata cannot store environment dumps")
    if _contains_secret_keyword(lowered):
        raise ValueError("metadata key must not request secrets")
    return normalized


def _is_path_key(key: str) -> bool:
    lowered = key.strip().replace("-", "_").lower()
    return lowered == "path" or lowered.endswith("_path")


def _validate_repo_local_path(value: str, *, allow_dot: bool = False) -> str:
    raw = str(value).strip()
    normalized = normalize_repo_path(raw)
    is_absolute = Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or is_absolute
        or raw.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or (normalized == "." and not allow_dot)
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    if parts and parts[0] == "kb" and "accepted" in parts:
        raise ValueError("operator session records cannot reference accepted KB paths")
    return normalized


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _text_items(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    values: tuple[str, ...]
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(str(item) for item in value)
        except TypeError as exc:
            raise ValueError("field must be a sequence of strings") from exc
    return tuple(item.strip() for item in values if item.strip())


def _dedupe(values: Any) -> tuple[Any, ...]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _safe_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return _safe_text(normalized)


def _safe_text(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text field must be non-empty")
    if SECRET_VALUE_PATTERN.search(normalized):
        raise ValueError("text field contains secret-looking value")
    if any(marker in normalized.lower() for marker in HIDDEN_REASONING_MARKERS):
        raise ValueError("text field contains hidden-reasoning marker")
    return normalized


def _contains_secret_keyword(value: str) -> bool:
    normalized = value.strip().lstrip("-").replace("_", "-").lower()
    return any(keyword in normalized for keyword in SECRET_KEYWORDS)


__all__ = [
    "AUTHORITY_CLAIM_FIELDS",
    "HIDDEN_REASONING_FIELDS",
    "OPERATOR_SESSION_AUTHORITY_NOTICE",
    "SKIPPED_OPERATOR_SESSION_LIMITATION",
    "OperatorArtifactRef",
    "OperatorArtifactRefKind",
    "OperatorCheckKind",
    "OperatorCheckResult",
    "OperatorCheckStatus",
    "OperatorPolicyFinding",
    "OperatorPolicyFindingSeverity",
    "OperatorPolicyMode",
    "OperatorSession",
    "OperatorSessionError",
    "OperatorSessionEvent",
    "OperatorSessionStatus",
    "OperatorSessionSummary",
    "OperatorToolCallRecord",
    "OperatorToolCallStatus",
]
