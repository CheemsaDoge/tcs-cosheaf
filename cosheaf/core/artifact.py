"""Pydantic models for typed research artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class SourceMetadata(BaseModel):
    """Structured citation metadata for source-backed artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[
        "paper",
        "book",
        "survey",
        "lecture_note",
        "website",
        "internal_note",
        "other",
    ]
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str = ""
    arxiv: str = ""
    url: str = ""
    theorem_number: str = ""
    page: str = ""
    notes: str = ""

    @field_validator(
        "title",
        "doi",
        "arxiv",
        "url",
        "theorem_number",
        "page",
        "notes",
    )
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("authors")
    @classmethod
    def _strip_authors(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]

    @field_validator("year")
    @classmethod
    def _validate_year(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("year must be positive")
        return value


class FormalizationRef(BaseModel):
    """Reference to an external formal library declaration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    system: Literal["lean4"]
    library: str = Field(min_length=1)
    library_ref: str = Field(min_length=1)
    import_path: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    declaration_kind: Literal[
        "definition",
        "theorem",
        "lemma",
        "instance",
        "structure",
        "other",
    ]
    status: Literal["planned", "linked", "checked", "broken", "deprecated"]
    check_mode: Literal["external_library_ref", "local_file"]
    expected_type: str = ""
    notes: str = ""

    @field_validator(
        "id",
        "library",
        "library_ref",
        "import_path",
        "symbol",
        "expected_type",
        "notes",
    )
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("id", "library", "library_ref", "import_path", "symbol")
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("formalization reference field must not be empty")
        return stripped

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        return validate_artifact_id(value)


class AlignmentReview(BaseModel):
    """Semantic alignment review between informal and formal statements."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["none", "requested", "human_reviewed", "rejected"] = "none"
    reviewer: str = ""
    reviewed_at: datetime | None = None
    convention_notes: list[str] = Field(default_factory=list)
    limitations: str = ""

    @field_validator("reviewer", "limitations")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("convention_notes")
    @classmethod
    def _strip_convention_notes(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]

    @field_validator("reviewed_at")
    @classmethod
    def _validate_review_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("reviewed_at must include timezone information")
        return value

    @model_validator(mode="after")
    def _validate_reviewer_for_completed_review(self) -> AlignmentReview:
        if self.status in {"human_reviewed", "rejected"} and not self.reviewer:
            raise ValueError(
                "reviewer must be non-empty when alignment status is "
                "human_reviewed or rejected"
            )
        return self


class VerificationPolicy(BaseModel):
    """Per-artifact verification policy for formal links and alignment review."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    level: Literal[
        "source_reviewed",
        "source_reviewed_with_formal_link",
        "machine_checked",
        "lean_required",
    ] = "source_reviewed"
    require_formal_link: bool = False
    require_lean_check: bool = False
    require_alignment_review: bool = False

    @model_validator(mode="after")
    def _validate_policy_consistency(self) -> VerificationPolicy:
        if (
            self.level == "source_reviewed_with_formal_link"
            and not self.require_formal_link
        ):
            raise ValueError(
                "source_reviewed_with_formal_link policy must require a formal link"
            )
        if self.level == "lean_required" and not self.require_formal_link:
            raise ValueError("lean_required policy must require a formal link")
        if self.level == "lean_required" and not self.require_lean_check:
            raise ValueError(
                "lean_required policy must require a Lean check"
            )
        return self


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
    sources: list[SourceMetadata] = Field(default_factory=list)
    formalizations: list[FormalizationRef] = Field(default_factory=list)
    alignment: AlignmentReview = Field(default_factory=AlignmentReview)
    verification_policy: VerificationPolicy = Field(
        default_factory=VerificationPolicy
    )
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
