"""Normalized verifier result model."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.core.ids import validate_artifact_id

if TYPE_CHECKING:
    from cosheaf.verification.evidence import VerifierEvidenceRecord


class VerificationStatus(StrEnum):
    """Normalized verifier result status."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"


class VerificationResult(BaseModel):
    """Machine-readable result returned by verifier adapters."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    verifier: str
    artifact_id: str
    status: VerificationStatus
    started_at: datetime
    ended_at: datetime
    command: tuple[str, ...] | None = None
    cwd: str | None = None
    exit_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: float | None = None
    input_paths: tuple[str, ...] = Field(default_factory=tuple)
    output_paths: tuple[str, ...] = Field(default_factory=tuple)
    tool_name: str | None = None
    tool_version: str | None = None
    seed: str | None = None
    environment: str | None = None
    message: str

    @field_validator("artifact_id")
    @classmethod
    def _validate_artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value)

    @field_validator("verifier")
    @classmethod
    def _validate_verifier_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("verifier name must not be empty")
        return normalized

    @field_validator("started_at", "ended_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return value

    @field_validator("command", mode="before")
    @classmethod
    def _normalize_command(cls, value: Any) -> tuple[str, ...] | None:
        if value is None:
            return None
        if isinstance(value, str):
            raise ValueError("command must be a sequence of command arguments")
        try:
            parts = tuple(str(part) for part in value)
        except TypeError as exc:
            raise ValueError("command must be a sequence of command arguments") from exc
        if not parts:
            return None
        return parts

    @field_validator("evidence_paths", mode="before")
    @classmethod
    def _normalize_evidence_paths(cls, value: Any) -> tuple[str, ...]:
        return _normalize_path_tuple(value, field_name="evidence_paths")

    @field_validator("input_paths", "output_paths", mode="before")
    @classmethod
    def _normalize_path_sequence(cls, value: Any, info: Any) -> tuple[str, ...]:
        return _normalize_path_tuple(value, field_name=str(info.field_name))

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: float | None) -> float | None:
        if value is not None and value <= 0:
            raise ValueError("timeout_seconds must be positive when recorded")
        return value

    @field_validator("tool_name", "tool_version", "seed", "environment")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def _validate_result_consistency(self) -> Self:
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")
        if self.command and not self.cwd:
            raise ValueError("cwd is required when command is recorded")
        return self

    @property
    def is_pass(self) -> bool:
        """Return whether verification passed."""
        return self.status is VerificationStatus.PASS

    @property
    def is_fail(self) -> bool:
        """Return whether verification found an artifact-level failure."""
        return self.status is VerificationStatus.FAIL

    @property
    def is_error(self) -> bool:
        """Return whether verification hit a tool or runtime error."""
        return self.status is VerificationStatus.ERROR

    @property
    def is_skipped(self) -> bool:
        """Return whether verification was skipped."""
        return self.status is VerificationStatus.SKIPPED

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic machine-readable result mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this result."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"

    def to_evidence_record(self) -> VerifierEvidenceRecord:
        """Return a serializable verifier evidence record for this result."""
        from cosheaf.verification.evidence import VerifierEvidenceRecord

        return VerifierEvidenceRecord.from_verification_result(self)


def _normalize_path_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    paths: tuple[str, ...]
    if isinstance(value, str):
        paths = (value,)
    else:
        try:
            paths = tuple(str(path) for path in value)
        except TypeError as exc:
            raise ValueError(f"{field_name} must be a sequence") from exc
    return tuple(sorted(dict.fromkeys(path for path in paths if path)))
