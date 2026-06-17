"""Bounded research loop with multi-attempt failure memory.

Research loops enable exploring multiple bounded attempts on one research issue,
recording failures as useful memory, detecting repeat failures, and handing off
complete audit trails.

Research loop success never means accepted status. Loop outputs are draft
artifacts, checked-evidence candidates, failure logs, and review context only.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.storage.repo import RepoContext

RESEARCH_LOOP_AUTHORITY_NOTICE = (
    "Research loop records are review context only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, or promotion "
    "authority. Loop success never means accepted promotion."
)

RESEARCH_LOOP_RUNTIME_ROOT = Path(".cosheaf") / "research-loops"
RESEARCH_LOOP_REVIEW_ROOT = Path("reviews") / "research-loops"


class ResearchLoopError(ValueError):
    """Expected research-loop service failure."""

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


class ResearchLoopStatus(StrEnum):
    """Lifecycle state for a research loop."""

    ACTIVE = "active"
    CREATED = "created"
    RUNNING = "running"
    BLOCKED = "blocked"
    FINALIZED = "finalized"
    ABANDONED = "abandoned"
    FAILED = "failed"


class ResearchLoopAttemptStatus(StrEnum):
    """Lifecycle state for one bounded attempt."""

    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"
    ABANDONED = "abandoned"


class ResearchLoopFailureTag(StrEnum):
    """Structured failure classification tags."""

    INVALID_APPROACH = "invalid_approach"
    MISSING_DEPENDENCY = "missing_dependency"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FORMAL_MISMATCH = "formal_mismatch"
    COUNTEREXAMPLE_FOUND = "counterexample_found"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    TOOLING_UNAVAILABLE = "tooling_unavailable"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    UNKNOWN = "unknown"


class AttemptFailureRecord(BaseModel):
    """Structured failure record for one attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    failure_id: str = Field(description="Unique failure ID")
    attempt_id: str = Field(description="Parent attempt ID")
    tags: list[ResearchLoopFailureTag] = Field(
        description="Failure classification tags"
    )
    summary: str = Field(description="Human-readable failure summary")
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence paths or artifact IDs",
    )
    avoidance_guidance: str = Field(
        description="How to avoid this failure in next attempts"
    )
    signature: str = Field(
        description="Similarity signature for repeat detection"
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this failure occurred",
    )

    @field_validator("failure_id", "attempt_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ID must be non-empty")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(
        cls, v: list[ResearchLoopFailureTag]
    ) -> list[ResearchLoopFailureTag]:
        if not v:
            raise ValueError("At least one failure tag required")
        return v

    @field_validator("summary", "avoidance_guidance", "signature")
    @classmethod
    def validate_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v.strip()


class ResearchLoopAttempt(BaseModel):
    """One bounded attempt within a research loop."""

    model_config = ConfigDict(extra="forbid")

    attempt_id: str = Field(description="Unique attempt ID")
    loop_id: str = Field(description="Parent loop ID")
    attempt_number: int = Field(ge=1, description="Attempt sequence number")
    status: ResearchLoopAttemptStatus = Field(
        default=ResearchLoopAttemptStatus.PLANNED
    )
    planned_direction: str = Field(description="What this attempt will try")
    started_at: datetime | None = Field(
        default=None, description="When execution started"
    )
    completed_at: datetime | None = Field(
        default=None, description="When execution finished"
    )
    actions_taken: list[str] = Field(
        default_factory=list,
        description="Actions executed during this attempt",
    )
    failures: list[AttemptFailureRecord] = Field(
        default_factory=list, description="Failures encountered"
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence artifact IDs or file paths",
    )
    next_recommendation: str | None = Field(
        default=None,
        description="Recommendation for next attempt if this fails",
    )
    authority_notice: str = Field(
        default=RESEARCH_LOOP_AUTHORITY_NOTICE,
        description="Authority disclaimer",
    )

    @field_validator("attempt_id", "loop_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ID must be non-empty")
        return v

    @field_validator("planned_direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Planned direction must be non-empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_timing(self) -> Self:
        if self.completed_at and self.started_at:
            if self.completed_at < self.started_at:
                raise ValueError("completed_at cannot be before started_at")
        return self




class ResearchLoop(BaseModel):
    """Main research loop model, coordinates multiple bounded attempts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    loop_id: str = Field(description="Unique loop identifier")
    issue_id: str = Field(description="Issue this loop targets")
    status: ResearchLoopStatus = Field(default=ResearchLoopStatus.ACTIVE)
    attempts: list[ResearchLoopAttempt] = Field(
        default_factory=list, description="Ordered list of attempts"
    )
    max_attempts: int = Field(default=10, ge=1, le=100)
    budget: dict[str, int | float] = Field(
        default_factory=dict,
        description="Resource budgets (tokens, time, etc.)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Loop creation time"
    )
    finalized_at: datetime | None = Field(
        default=None, description="When loop was finalized"
    )
    notes: str = Field(default="", description="Operator notes")
    authority_notice: str = Field(
        default=RESEARCH_LOOP_AUTHORITY_NOTICE,
        description="Authority disclaimer",
    )

    @field_validator("loop_id", "issue_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ID must be non-empty")
        return v

    @field_validator("max_attempts")
    @classmethod
    def validate_max_attempts(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("max_attempts must be between 1 and 100")
        return v

    @model_validator(mode="after")
    def validate_attempt_limit(self) -> Self:
        if len(self.attempts) > self.max_attempts:
            raise ValueError(
                f"Cannot exceed max_attempts={self.max_attempts}"
            )
        return self

    @model_validator(mode="after")
    def validate_timing(self) -> Self:
        if self.finalized_at and self.finalized_at < self.created_at:
            raise ValueError("finalized_at cannot be before created_at")
        return self

    def add_attempt(self, attempt: ResearchLoopAttempt) -> None:
        """Add a new attempt to this loop."""
        if len(self.attempts) >= self.max_attempts:
            raise ResearchLoopError(
                f"Cannot add attempt: max_attempts={self.max_attempts} reached",
                code="loop_max_attempts_reached",
                remediation="Finalize this loop or increase max_attempts",
            )
        if self.status != ResearchLoopStatus.ACTIVE:
            raise ResearchLoopError(
                f"Cannot add attempt to loop with status={self.status.value}",
                code="loop_not_active",
                remediation="Loop must be in ACTIVE status to add attempts",
            )
        if attempt.loop_id != self.loop_id:
            raise ResearchLoopError(
                f"Attempt loop_id mismatch: {attempt.loop_id} != {self.loop_id}",
                code="loop_id_mismatch",
                remediation="Ensure attempt.loop_id matches the target loop",
            )
        self.attempts.append(attempt)

    def finalize(self, reason: str = "") -> None:
        """Mark loop as finalized."""
        if self.status == ResearchLoopStatus.FINALIZED:
            raise ResearchLoopError(
                "Loop is already finalized",
                code="loop_already_finalized",
                remediation="Cannot finalize a loop that is already finalized",
            )
        self.status = ResearchLoopStatus.FINALIZED
        self.finalized_at = datetime.now(UTC)
        if reason:
            self.notes = f"{self.notes}\nFinalized: {reason}".strip()


# Storage functions


def save_loop(repo: RepoContext, loop: ResearchLoop) -> Path:
    """Save research loop to .cosheaf/research-loops/<loop-id>/loop.json."""
    from cosheaf.storage.writer import write_yaml_deterministic

    loop_dir = repo.repo_root / ".cosheaf" / "research-loops" / loop.loop_id
    loop_dir.mkdir(parents=True, exist_ok=True)

    loop_path = loop_dir / "loop.json"
    data = loop.model_dump(mode="json")
    write_yaml_deterministic(loop_path, data)

    return loop_path


def load_loop(repo: RepoContext, loop_id: str) -> ResearchLoop:
    """Load research loop from runtime storage."""
    import yaml

    loop_path = repo.repo_root / ".cosheaf" / "research-loops" / loop_id / "loop.json"
    if not loop_path.exists():
        raise ResearchLoopError(
            f"Loop not found: {loop_id}",
            code="loop_not_found",
            remediation="Check loop_id or create loop first with research-loop-start",
        )

    with open(loop_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ResearchLoop.model_validate(data)


def save_attempt(repo: RepoContext, attempt: ResearchLoopAttempt) -> Path:
    """Save attempt to .cosheaf/research-loops/<loop-id>/attempts/<attempt-id>.json."""
    from cosheaf.storage.writer import write_yaml_deterministic

    attempt_dir = (
        repo.repo_root / ".cosheaf" / "research-loops" / attempt.loop_id / "attempts"
    )
    attempt_dir.mkdir(parents=True, exist_ok=True)

    attempt_path = attempt_dir / f"{attempt.attempt_id}.json"
    data = attempt.model_dump(mode="json")
    write_yaml_deterministic(attempt_path, data)

    return attempt_path


def list_loops(repo: RepoContext) -> list[str]:
    """List all loop IDs in the repository."""
    loops_dir = repo.repo_root / ".cosheaf" / "research-loops"
    if not loops_dir.exists():
        return []

    return [
        d.name
        for d in loops_dir.iterdir()
        if d.is_dir() and (d / "loop.json").exists()
    ]



