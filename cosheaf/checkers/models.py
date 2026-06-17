"""Typed checker registry models."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CHECKER_AUTHORITY_MESSAGE = (
    "checker results are review context only; checker pass is not proof, "
    "human review, source metadata, gate pass, verifier pass, accepted status, "
    "accepted theorem/refutation, or promotion authority; skipped is not pass"
)


class CheckerStatus(StrEnum):
    """Normalized checker result statuses."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"
    INCONCLUSIVE = "inconclusive"
    UNSUPPORTED = "unsupported"
    BLOCKED_BY_POLICY = "blocked_by_policy"


class CheckerType(StrEnum):
    """Built-in checker type identifiers."""

    SCHEMA_CHECK = "schema_check"
    ARTIFACT_PATH_POLICY_CHECK = "artifact_path_policy_check"
    GATE_CHECK = "gate_check"
    PYTHON_LOCAL_CHECK = "python_local_check"
    SAT_OPTIONAL_CHECK = "sat_optional_check"
    SMT_OPTIONAL_CHECK = "smt_optional_check"
    LEAN_OPTIONAL_CHECK = "lean_optional_check"
    SOURCE_METADATA_CHECK = "source_metadata_check"
    PRIVATE_LEAK_CHECK = "private_leak_check"
    AUTHORITY_OVERCLAIM_CHECK = "authority_overclaim_check"


class CheckerCapability(StrEnum):
    """Checker capability labels exposed by the registry."""

    SCHEMA = "schema"
    PATH_POLICY = "path_policy"
    GATE = "gate"
    LOCAL_PYTHON = "local_python"
    OPTIONAL_TOOL = "optional_tool"
    SOURCE_METADATA = "source_metadata"
    PRIVACY_POLICY = "privacy_policy"
    AUTHORITY_POLICY = "authority_policy"


class CheckerAuthorityNotice(BaseModel):
    """Machine-readable authority boundary attached to checker output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    message: str = CHECKER_AUTHORITY_MESSAGE
    checker_pass_is_not_accepted_status: bool = True
    checker_pass_is_not_human_review: bool = True
    checker_pass_is_not_proof: bool = True
    checker_pass_is_not_source_metadata: bool = True
    skipped_is_not_pass: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""
        return self.model_dump(mode="json")


class CheckerSpec(BaseModel):
    """Registry metadata for one checker."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    checker_id: str
    checker_type: CheckerType
    title: str
    description: str
    capabilities: tuple[CheckerCapability, ...] = Field(default_factory=tuple)
    optional: bool = False
    default_timeout_seconds: float | None = None
    authority_notice: CheckerAuthorityNotice = Field(
        default_factory=CheckerAuthorityNotice
    )

    @field_validator("checker_id")
    @classmethod
    def _validate_checker_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("checker_id must not be empty")
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_.-")
        if any(char not in allowed for char in normalized):
            raise ValueError(
                "checker_id must contain only lowercase letters, digits, _, ., or -"
            )
        return normalized

    @field_validator("title", "description")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("checker text fields must not be empty")
        return normalized

    @field_validator("default_timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: float | None) -> float | None:
        if value is not None and value <= 0:
            raise ValueError("default_timeout_seconds must be positive")
        return value

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""
        return self.model_dump(mode="json")


class CheckerInput(BaseModel):
    """Generic input packet accepted by checker CLI commands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = 1
    artifact_id: str | None = None
    artifact_path: str | None = None
    paths: tuple[str, ...] = Field(default_factory=tuple)
    text: str = ""
    mode: str = "workspace"
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("checker input schema_version must be 1")
        return value

    @field_validator("artifact_id", "artifact_path")
    @classmethod
    def _strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("paths", mode="before")
    @classmethod
    def _normalize_paths(cls, value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            raw_paths: tuple[str, ...] = (value,)
        else:
            try:
                raw_paths = tuple(str(path) for path in value)
            except TypeError as exc:
                raise ValueError("paths must be a sequence of strings") from exc
        return tuple(
            dict.fromkeys(_normalize_repoish_path(path) for path in raw_paths if path)
        )

    @field_validator("text", "mode")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""
        return self.model_dump(mode="json")


class CheckerResult(BaseModel):
    """One normalized checker result."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    checker_id: str
    checker_type: CheckerType
    status: CheckerStatus
    started_at: datetime
    ended_at: datetime
    message: str
    diagnostic_paths: tuple[str, ...] = Field(default_factory=tuple)
    command: tuple[str, ...] | None = None
    cwd: str | None = None
    exit_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    input_paths: tuple[str, ...] = Field(default_factory=tuple)
    output_paths: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: float | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    limitations: tuple[str, ...] = Field(default_factory=tuple)
    authority_notice: CheckerAuthorityNotice = Field(
        default_factory=CheckerAuthorityNotice
    )

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
            raise ValueError("command must be a sequence of arguments")
        try:
            command = tuple(str(part) for part in value)
        except TypeError as exc:
            raise ValueError("command must be a sequence of arguments") from exc
        return command or None

    @field_validator(
        "diagnostic_paths",
        "input_paths",
        "output_paths",
        "limitations",
        mode="before",
    )
    @classmethod
    def _normalize_tuple(cls, value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            raw_values: tuple[str, ...] = (value,)
        else:
            try:
                raw_values = tuple(str(item) for item in value)
            except TypeError as exc:
                raise ValueError("field must be a sequence of strings") from exc
        return tuple(sorted(dict.fromkeys(item for item in raw_values if item)))

    @field_validator("message")
    @classmethod
    def _strip_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("checker result message must not be empty")
        return normalized

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: float | None) -> float | None:
        if value is not None and value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")
        if self.command and not self.cwd:
            raise ValueError("cwd is required when command is recorded")
        return self

    @property
    def is_pass(self) -> bool:
        """Return whether the checker result is an actual pass."""
        return self.status is CheckerStatus.PASS

    @property
    def is_skipped(self) -> bool:
        """Return whether the checker was skipped."""
        return self.status is CheckerStatus.SKIPPED

    @property
    def is_blocking(self) -> bool:
        """Return whether this result should fail a checker CLI invocation."""
        return self.status in {
            CheckerStatus.FAIL,
            CheckerStatus.ERROR,
            CheckerStatus.BLOCKED_BY_POLICY,
        }

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class CheckerRunRecord(BaseModel):
    """Stored record for a checker execution."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    schema_version: int = 1
    run_id: str
    checker: CheckerSpec
    input: CheckerInput
    result: CheckerResult
    created_at: datetime
    result_path: str
    stdout_path: str
    stderr_path: str
    authority_notice: CheckerAuthorityNotice = Field(
        default_factory=CheckerAuthorityNotice
    )

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("checker run schema_version must be 1")
        return value

    @field_validator("created_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return value

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible data."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


def _normalize_repoish_path(path: str) -> str:
    return PurePosixPath(PureWindowsPath(path.strip()).as_posix()).as_posix()
