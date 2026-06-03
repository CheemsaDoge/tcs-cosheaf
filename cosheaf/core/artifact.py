"""Pydantic models for typed research artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.status import ArtifactStatus, ArtifactType


class Evidence(BaseModel):
    """A repository-local evidence reference."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    path: str
    summary: str


class ReviewRef(BaseModel):
    """Inline review state attached to an artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state: Literal[
        "none",
        "requested",
        "in_review",
        "approved",
        "changes_requested",
        "human_reviewed",
        "accepted",
    ] = "none"
    notes: str = ""


class Risk(BaseModel):
    """Risk classification for an artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    level: Literal["low", "medium", "high"] = "low"
    notes: str = ""


class BaseArtifact(BaseModel):
    """Base typed artifact model shared by current artifact examples."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    id: str
    type: ArtifactType
    title: str
    domain: list[str] = Field(default_factory=list)
    status: ArtifactStatus
    created_at: datetime
    updated_at: datetime
    authors: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    statement: str
    evidence: list[Evidence] = Field(default_factory=list)
    review: ReviewRef = Field(default_factory=ReviewRef)
    risk: Risk = Field(default_factory=Risk)

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        return validate_artifact_id(value)

    @field_validator("depends_on")
    @classmethod
    def _validate_dependency_refs(cls, values: list[str]) -> list[str]:
        return [validate_dependency_ref(value) for value in values]

    @field_validator("supersedes")
    @classmethod
    def _validate_artifact_id_list(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value) for value in values]

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return value

    @field_validator("updated_at")
    @classmethod
    def _validate_update_order(cls, value: datetime, info: Any) -> datetime:
        created_at = info.data.get("created_at")
        if isinstance(created_at, datetime) and value < created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")
        return value


def is_external_dependency_ref(value: str) -> bool:
    """Return whether a dependency reference is explicitly external."""
    normalized = value.strip().lower()
    return normalized.startswith("external:") and bool(
        normalized.removeprefix("external:").strip()
    )


def validate_dependency_ref(value: str) -> str:
    """Validate a local artifact ID or explicit external dependency reference."""
    stripped = value.strip()
    if is_external_dependency_ref(stripped):
        return stripped
    return validate_artifact_id(stripped)
