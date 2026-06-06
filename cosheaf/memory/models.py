"""Pydantic models for deterministic memory and retrieval handoffs."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cosheaf.core.artifact import validate_dependency_ref
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path


class MemoryRootScope(StrEnum):
    """Repository or workspace scope for a memory card."""

    PUBLIC = "public"
    PRIVATE = "private"
    WORKSPACE = "workspace"
    FRAMEWORK = "framework"


class ArtifactCardType(StrEnum):
    """Compact type vocabulary for card-level retrieval records."""

    DEFINITION = "definition"
    THEOREM = "theorem"
    CLAIM = "claim"
    CONJECTURE = "conjecture"
    PROOF = "proof"
    PROOF_ATTEMPT = "proof_attempt"
    CONSTRUCTION = "construction"
    ALGORITHM = "algorithm"
    REDUCTION = "reduction"
    COUNTEREXAMPLE = "counterexample"
    EXPERIMENT = "experiment"
    REVIEW = "review"
    VERIFIER = "verifier"
    ISSUE = "issue"
    SOURCE_NOTE = "source_note"


class ArtifactCardStatus(StrEnum):
    """Lifecycle/trust status for a memory card."""

    RAW = "raw"
    DRAFT = "draft"
    LOCALLY_TESTED = "locally_tested"
    ADVERSARIALLY_TESTED = "adversarially_tested"
    MACHINE_CHECKED = "machine_checked"
    HUMAN_REVIEWED = "human_reviewed"
    ACCEPTED = "accepted"
    REFUTED = "refuted"
    OBSOLETE = "obsolete"
    SUPERSEDED = "superseded"


class RetrievalRole(StrEnum):
    """Caller role for bounded retrieval requests."""

    LIBRARIAN = "librarian"
    ORCHESTRATOR = "orchestrator"
    REASONER = "reasoner"
    VERIFIER = "verifier"
    FORMALIZER = "formalizer"
    LITERATURE_SCOUT = "literature_scout"
    COUNTEREXAMPLER = "counterexampleer"
    CONSTRUCTION_SEARCHER = "construction_searcher"


class MemoryModel(BaseModel):
    """Shared strict base model for memory DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic machine-readable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this model."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class ScoreBreakdown(MemoryModel):
    """Inspectable components of a retrieval score."""

    retrieval_hybrid: float = 0.0
    personalized_pagerank: float = 0.0
    global_pagerank: float = 0.0
    quality_prior: float = 0.0
    freshness: float = 0.0
    penalty: float = 0.0
    total: float = 0.0

    @field_validator(
        "retrieval_hybrid",
        "personalized_pagerank",
        "global_pagerank",
        "quality_prior",
        "freshness",
        "penalty",
        "total",
    )
    @classmethod
    def _validate_score(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("score component must be finite")
        if value < 0:
            raise ValueError("score component must be non-negative")
        return value


class ArtifactCard(MemoryModel):
    """Compact retrieval unit derived from repository metadata."""

    id: str
    path: str
    root_scope: MemoryRootScope
    type: ArtifactCardType
    status: ArtifactCardStatus
    title: str
    summary: str
    domain: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    review_state: str = "none"
    verifier_state: str = "none"
    formalization_state: str = "none"
    trust_score: float = 0.0
    retrieval_score: float = 0.0
    why_relevant: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    can_pull_full: bool = False

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        return validate_artifact_id(value)

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return _validate_repo_local_path(value)

    @field_validator("title", "summary")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="text field")

    @field_validator(
        "review_state",
        "verifier_state",
        "formalization_state",
        "why_relevant",
    )
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("domain", "tags", "sources", "risk_flags")
    @classmethod
    def _normalize_text_list(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)

    @field_validator("depends_on")
    @classmethod
    def _validate_dependencies(cls, values: list[str]) -> list[str]:
        return [validate_dependency_ref(value) for value in values]

    @field_validator("trust_score", "retrieval_score")
    @classmethod
    def _validate_card_score(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("score must be finite")
        if value < 0:
            raise ValueError("score must be non-negative")
        return value


class RetrievalRequest(MemoryModel):
    """Bounded, deterministic request for artifact-card retrieval."""

    schema_version: Literal[1] = 1
    query: str
    issue_id: str | None = None
    seed_artifacts: list[str] = Field(default_factory=list)
    pinned_artifacts: list[str] = Field(default_factory=list)
    allowed_scopes: list[MemoryRootScope] = Field(
        default_factory=lambda: [MemoryRootScope.PUBLIC]
    )
    allowed_statuses: list[ArtifactCardStatus] = Field(
        default_factory=lambda: [
            ArtifactCardStatus.ACCEPTED,
            ArtifactCardStatus.HUMAN_REVIEWED,
            ArtifactCardStatus.MACHINE_CHECKED,
            ArtifactCardStatus.LOCALLY_TESTED,
        ]
    )
    include_refuted: bool = False
    include_obsolete: bool = False
    max_cards: int = 20
    max_full_artifacts: int = 0
    role: RetrievalRole = RetrievalRole.LIBRARIAN

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="query")

    @field_validator("issue_id")
    @classmethod
    def _validate_issue_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("seed_artifacts", "pinned_artifacts")
    @classmethod
    def _validate_artifact_ids(cls, values: list[str]) -> list[str]:
        return [validate_artifact_id(value.strip()) for value in values]

    @field_validator("max_cards")
    @classmethod
    def _validate_max_cards(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_cards must be positive")
        return value

    @field_validator("max_full_artifacts")
    @classmethod
    def _validate_max_full_artifacts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_full_artifacts must be non-negative")
        return value


class RetrievedArtifactCard(MemoryModel):
    """One ordered retrieval hit with its score explanation."""

    card: ArtifactCard
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    why_relevant: list[str] = Field(default_factory=list)

    @field_validator("why_relevant")
    @classmethod
    def _normalize_why_relevant(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


class FullArtifactPull(MemoryModel):
    """Audit entry for a full artifact pulled beyond card metadata."""

    artifact_id: str
    path: str
    reason: str

    @field_validator("artifact_id")
    @classmethod
    def _validate_artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value)

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return _validate_repo_local_path(value)

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="reason")


class RetrievalExclusion(MemoryModel):
    """Audit entry for an artifact excluded by policy or filters."""

    artifact_id: str
    reason: str

    @field_validator("artifact_id")
    @classmethod
    def _validate_artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value)

    @field_validator("reason")
    @classmethod
    def _validate_reason(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="reason")


class RetrievalAudit(MemoryModel):
    """Inspectable retrieval filtering and warning metadata."""

    filters_applied: list[str] = Field(default_factory=list)
    excluded: list[RetrievalExclusion] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("filters_applied", "warnings")
    @classmethod
    def _normalize_text_values(cls, values: list[str]) -> list[str]:
        return _normalize_text_list(values)


class RetrievalResult(MemoryModel):
    """Ordered retrieval cards plus audit metadata."""

    schema_version: Literal[1] = 1
    request_id: str
    generated_at: datetime
    index_fingerprint: str
    cards: list[RetrievedArtifactCard] = Field(default_factory=list)
    full_artifact_pulls: list[FullArtifactPull] = Field(default_factory=list)
    audit: RetrievalAudit = Field(default_factory=RetrievalAudit)

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("generated_at")
    @classmethod
    def _normalize_generated_at(cls, value: datetime) -> datetime:
        return _normalize_utc_timestamp(value)

    @field_validator("index_fingerprint")
    @classmethod
    def _validate_index_fingerprint(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="index_fingerprint")


def _validate_repo_local_path(value: str) -> str:
    normalized = normalize_repo_path(value.strip())
    if (
        not normalized
        or normalized == "."
        or normalized == ".."
        or normalized.startswith("../")
        or normalized.startswith("/")
        or Path(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    ):
        raise ValueError("path must be repository-local")
    return normalized


def _validate_non_empty_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_text_list(values: list[str]) -> list[str]:
    return [normalized for value in values if (normalized := value.strip())]


def _normalize_utc_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)
