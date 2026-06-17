"""Bounded research-loop DTOs, storage, and safety checks.

Research loops are runtime memory for repeated external research attempts.
They are review context only. A loop can remember attempts, evidence, and
failures, but it cannot create accepted knowledge, human review, verifier
passes, gate passes, or promotion authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.storage.repo import RepoContext

RESEARCH_LOOP_AUTHORITY_NOTICE = (
    "Research loop records are review context only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, or promotion "
    "authority. Loop success never means accepted promotion."
)

RESEARCH_LOOP_RUNTIME_ROOT = Path(".cosheaf") / "research-loops"
RESEARCH_LOOP_REVIEW_ROOT = Path("reviews") / "research-loops"

ResearchLoopPolicyMode = Literal["public_only", "private_research"]
AttemptPolicySeverity = Literal["info", "warning", "blocking"]
AttemptNextActionKind = Literal[
    "start_attempt",
    "retry_with_justification",
    "request_operator_input",
    "finalize_loop",
    "abandon_loop",
]

_TERMINAL_LOOP_STATUSES = frozenset(
    {"finalized", "abandoned", "failed"}
)
_TERMINAL_ATTEMPT_STATUSES = frozenset(
    {"succeeded", "failed", "blocked", "inconclusive", "abandoned"}
)
_AUTHORITY_FIELD_NAMES = frozenset(
    {
        "accepted",
        "accepted_write_performed",
        "artifact_status",
        "gate_pass",
        "human_review",
        "human_reviewed",
        "promote",
        "promotion_authority",
        "review_state",
        "verifier_pass",
    }
)
_HIDDEN_REASONING_FIELD_NAMES = frozenset(
    {"chain_of_thought", "hidden_reasoning", "reasoning_trace"}
)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


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


class ResearchLoopModel(BaseModel):
    """Strict base model for research-loop runtime records."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this model."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class ResearchLoopBudget(ResearchLoopModel):
    """Bounded resource budget for a research loop."""

    max_attempts: int = Field(default=10, ge=1, le=1000)
    max_wallclock_minutes: int | None = Field(default=None, ge=1)
    max_tokens: int | None = Field(default=None, ge=1)
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def _notes(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)


class ResearchLoopStopCondition(ResearchLoopModel):
    """One explicit stop condition for a loop."""

    condition_id: str
    kind: str
    description: str
    triggered: bool = False
    triggered_at: datetime | None = None

    @field_validator("condition_id")
    @classmethod
    def _id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("kind", "description")
    @classmethod
    def _text(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("triggered_at")
    @classmethod
    def _timestamp(cls, value: datetime | None) -> datetime | None:
        return _normalize_timestamp(value)

    @model_validator(mode="after")
    def _trigger_consistency(self) -> Self:
        if self.triggered and self.triggered_at is None:
            raise ValueError("triggered stop conditions require triggered_at")
        return self


class ResearchLoopDecision(ResearchLoopModel):
    """Recorded operator or deterministic-system decision."""

    decision_id: str
    loop_id: str
    decision: str
    rationale: str
    attempt_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: _utc_now())

    @field_validator("decision_id", "loop_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("attempt_id")
    @classmethod
    def _attempt_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("decision", "rationale")
    @classmethod
    def _text(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("created_at")
    @classmethod
    def _timestamp(cls, value: datetime) -> datetime:
        return _normalize_required_timestamp(value)


class AttemptEvidenceSummary(ResearchLoopModel):
    """Safe references collected by one attempt."""

    evidence_refs: tuple[str, ...] = ()
    related_artifacts: tuple[str, ...] = ()
    operator_session_refs: tuple[str, ...] = ()
    research_run_refs: tuple[str, ...] = ()
    strategy_plan_refs: tuple[str, ...] = ()
    checked_counterexample_ids: tuple[str, ...] = ()
    counterexample_candidate_ids: tuple[str, ...] = ()
    draft_artifact_refs: tuple[str, ...] = ()
    handoff_bundle_refs: tuple[str, ...] = ()
    summary: str | None = None

    @field_validator(
        "evidence_refs",
        "related_artifacts",
        "operator_session_refs",
        "research_run_refs",
        "strategy_plan_refs",
        "checked_counterexample_ids",
        "counterexample_candidate_ids",
        "draft_artifact_refs",
        "handoff_bundle_refs",
        mode="before",
    )
    @classmethod
    def _refs(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_safe_reference(item) for item in _text_items(value))

    @field_validator("summary")
    @classmethod
    def _summary(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    def has_evidence(self) -> bool:
        """Return whether this summary contains any concrete evidence reference."""
        return any(
            (
                self.evidence_refs,
                self.related_artifacts,
                self.operator_session_refs,
                self.research_run_refs,
                self.strategy_plan_refs,
                self.checked_counterexample_ids,
                self.counterexample_candidate_ids,
                self.draft_artifact_refs,
                self.handoff_bundle_refs,
            )
        )


class AttemptPolicyFinding(ResearchLoopModel):
    """Policy finding produced while checking an attempt record."""

    finding_id: str
    severity: AttemptPolicySeverity
    finding_type: str
    summary: str
    blocking: bool = False
    evidence_refs: tuple[str, ...] = ()

    @field_validator("finding_id")
    @classmethod
    def _id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("finding_type", "summary")
    @classmethod
    def _text(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("evidence_refs", mode="before")
    @classmethod
    def _refs(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_safe_reference(item) for item in _text_items(value))

    @model_validator(mode="after")
    def _blocking_consistency(self) -> Self:
        if self.severity == "blocking" and not self.blocking:
            raise ValueError("blocking severity requires blocking=true")
        return self


class AttemptNextAction(ResearchLoopModel):
    """Suggested next action after one attempt."""

    action_id: str
    kind: AttemptNextActionKind
    summary: str
    rationale: str
    required_inputs: tuple[str, ...] = ()
    retry_requires_justification: bool = False

    @field_validator("action_id")
    @classmethod
    def _id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("summary", "rationale")
    @classmethod
    def _text(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("required_inputs", mode="before")
    @classmethod
    def _inputs(cls, value: Any) -> tuple[str, ...]:
        return tuple(_safe_text(item) for item in _text_items(value))


class AttemptFailureRecord(ResearchLoopModel):
    """Structured failure record for one bounded attempt."""

    failure_id: str
    attempt_id: str
    attempted_direction: str
    why_it_failed: str
    evidence_for_failure: tuple[str, ...]
    related_artifacts: tuple[str, ...] = ()
    related_previous_attempts: tuple[str, ...] = ()
    counterexample_candidate_ids: tuple[str, ...] = ()
    checked_counterexample_ids: tuple[str, ...] = ()
    verifier_or_gate_errors: tuple[str, ...] = ()
    should_retry: bool = False
    retry_conditions: str | None = None
    avoid_in_future: str
    tags: tuple[ResearchLoopFailureTag, ...]
    signature: str
    occurred_at: datetime = Field(default_factory=lambda: _utc_now())

    @field_validator("failure_id", "attempt_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("attempted_direction", "why_it_failed", "avoid_in_future")
    @classmethod
    def _text(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("retry_conditions")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator(
        "evidence_for_failure",
        "related_artifacts",
        "related_previous_attempts",
        "counterexample_candidate_ids",
        "checked_counterexample_ids",
        "verifier_or_gate_errors",
        mode="before",
    )
    @classmethod
    def _refs(cls, value: Any) -> tuple[str, ...]:
        return tuple(_validate_safe_reference(item) for item in _text_items(value))

    @field_validator("tags", mode="before")
    @classmethod
    def _tags(cls, value: Any) -> tuple[ResearchLoopFailureTag, ...]:
        tags = tuple(ResearchLoopFailureTag(item) for item in _text_items(value))
        if not tags:
            raise ValueError("failure records require at least one tag")
        return tags

    @field_validator("signature")
    @classmethod
    def _signature(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("occurred_at")
    @classmethod
    def _timestamp(cls, value: datetime) -> datetime:
        return _normalize_required_timestamp(value)

    @model_validator(mode="after")
    def _failure_consistency(self) -> Self:
        if not self.evidence_for_failure:
            raise ValueError("failure records require evidence_for_failure")
        if self.should_retry and not self.retry_conditions:
            raise ValueError("should_retry=true requires retry_conditions")
        return self


class ResearchLoopAttempt(ResearchLoopModel):
    """One bounded attempt within a research loop."""

    attempt_id: str
    loop_id: str
    attempt_number: int = Field(ge=1)
    status: ResearchLoopAttemptStatus = ResearchLoopAttemptStatus.PLANNED
    planned_direction: str
    policy_mode: ResearchLoopPolicyMode = "private_research"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_summary: str | None = None
    blocked_reason: str | None = None
    actions_taken: tuple[str, ...] = ()
    failures: tuple[AttemptFailureRecord, ...] = ()
    evidence: AttemptEvidenceSummary = Field(default_factory=AttemptEvidenceSummary)
    policy_findings: tuple[AttemptPolicyFinding, ...] = ()
    next_action: AttemptNextAction | None = None
    authority_notice: str = RESEARCH_LOOP_AUTHORITY_NOTICE

    @field_validator("attempt_id", "loop_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("planned_direction")
    @classmethod
    def _direction(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("started_at", "completed_at")
    @classmethod
    def _timestamp(cls, value: datetime | None) -> datetime | None:
        return _normalize_timestamp(value)

    @field_validator("result_summary", "blocked_reason")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("actions_taken", mode="before")
    @classmethod
    def _actions(cls, value: Any) -> tuple[str, ...]:
        return tuple(_safe_text(item) for item in _text_items(value))

    @model_validator(mode="before")
    @classmethod
    def _reject_payload_overclaims(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        forbidden = sorted(_AUTHORITY_FIELD_NAMES.intersection(value))
        hidden = sorted(_HIDDEN_REASONING_FIELD_NAMES.intersection(value))
        if forbidden:
            raise ValueError(
                "attempt payload cannot claim accepted, verifier, gate, "
                "human-review, or promotion authority: " + ", ".join(forbidden)
            )
        if hidden:
            raise ValueError(
                "attempt payload cannot store hidden reasoning fields: "
                + ", ".join(hidden)
            )
        return value

    @model_validator(mode="after")
    def _attempt_consistency(self) -> Self:
        if (
            self.completed_at
            and self.started_at
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot be before started_at")
        if self.status is ResearchLoopAttemptStatus.SUCCEEDED:
            if not self.result_summary and not self.evidence.has_evidence():
                raise ValueError(
                    "succeeded attempts require result_summary or evidence"
                )
        if self.status in {
            ResearchLoopAttemptStatus.FAILED,
            ResearchLoopAttemptStatus.INCONCLUSIVE,
            ResearchLoopAttemptStatus.ABANDONED,
        } and not self.failures:
            raise ValueError(f"{self.status.value} attempts require failures")
        if self.status is ResearchLoopAttemptStatus.BLOCKED:
            if not self.blocked_reason and not self.failures:
                raise ValueError("blocked attempts require blocked_reason or failures")
        if (
            self.status.value in _TERMINAL_ATTEMPT_STATUSES
            and self.completed_at is None
        ):
            raise ValueError("terminal attempts require completed_at")
        if self.policy_mode == "public_only":
            _ensure_no_private_markers(self.to_dict())
        return self


class LoopReviewSummary(ResearchLoopModel):
    """Review-oriented summary of one loop."""

    loop_id: str
    issue_id: str
    status: ResearchLoopStatus
    attempt_count: int = Field(ge=0)
    failed_attempt_count: int = Field(ge=0)
    succeeded_attempt_count: int = Field(ge=0)
    blocking_policy_findings: int = Field(ge=0)
    authority_notice: str = RESEARCH_LOOP_AUTHORITY_NOTICE

    @field_validator("loop_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())


class ResearchLoop(ResearchLoopModel):
    """Top-level bounded research loop."""

    loop_id: str
    issue_id: str
    status: ResearchLoopStatus = ResearchLoopStatus.CREATED
    budget: ResearchLoopBudget = Field(default_factory=ResearchLoopBudget)
    attempts: tuple[ResearchLoopAttempt, ...] = ()
    decisions: tuple[ResearchLoopDecision, ...] = ()
    stop_conditions: tuple[ResearchLoopStopCondition, ...] = ()
    created_at: datetime = Field(default_factory=lambda: _utc_now())
    updated_at: datetime = Field(default_factory=lambda: _utc_now())
    finalized_at: datetime | None = None
    notes: str | None = None
    authority_notice: str = RESEARCH_LOOP_AUTHORITY_NOTICE

    @field_validator("loop_id")
    @classmethod
    def _loop_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("issue_id")
    @classmethod
    def _issue_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("created_at", "updated_at", "finalized_at")
    @classmethod
    def _timestamp(cls, value: datetime | None) -> datetime | None:
        return _normalize_timestamp(value)

    @field_validator("notes")
    @classmethod
    def _notes(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @model_validator(mode="after")
    def _loop_consistency(self) -> Self:
        if len(self.attempts) > self.budget.max_attempts:
            raise ValueError(
                f"Cannot exceed budget.max_attempts={self.budget.max_attempts}"
            )
        if self.finalized_at and self.finalized_at < self.created_at:
            raise ValueError("finalized_at cannot be before created_at")
        if self.status.value in _TERMINAL_LOOP_STATUSES and self.finalized_at is None:
            raise ValueError("terminal loops require finalized_at")
        return self

    def add_attempt(self, attempt: ResearchLoopAttempt) -> ResearchLoop:
        """Return a copy with one validated attempt appended."""
        if len(self.attempts) >= self.budget.max_attempts:
            raise ResearchLoopError(
                f"Cannot add attempt: max_attempts={self.budget.max_attempts} reached",
                code="loop_max_attempts_reached",
                remediation="Finalize this loop or start a new bounded loop.",
            )
        if self.status.value in _TERMINAL_LOOP_STATUSES:
            raise ResearchLoopError(
                f"Cannot add attempt to loop with status={self.status.value}",
                code="loop_terminal",
                remediation="Start a new loop or inspect the finalized loop.",
            )
        if attempt.loop_id != self.loop_id:
            raise ResearchLoopError(
                f"Attempt loop_id mismatch: {attempt.loop_id} != {self.loop_id}",
                code="loop_id_mismatch",
                remediation="Ensure attempt.loop_id matches the target loop.",
            )
        expected_number = len(self.attempts) + 1
        if attempt.attempt_number != expected_number:
            raise ResearchLoopError(
                f"attempt_number must be {expected_number}",
                code="attempt_number_out_of_order",
                remediation="Append attempts in deterministic sequence order.",
            )
        return self.model_copy(
            update={
                "status": ResearchLoopStatus.RUNNING,
                "attempts": (*self.attempts, attempt),
                "updated_at": _utc_now(),
            }
        )

    def finalize(
        self,
        *,
        status: ResearchLoopStatus = ResearchLoopStatus.FINALIZED,
        reason: str | None = None,
    ) -> ResearchLoop:
        """Return a finalized or terminal copy of this loop."""
        if self.status.value in _TERMINAL_LOOP_STATUSES:
            raise ResearchLoopError(
                "Loop is already terminal",
                code="loop_already_terminal",
                remediation="Inspect the existing terminal loop instead.",
            )
        if status.value not in _TERMINAL_LOOP_STATUSES:
            raise ResearchLoopError(
                "finalize requires a terminal loop status",
                code="invalid_terminal_status",
                remediation="Use finalized, abandoned, or failed.",
            )
        note = self.notes
        if reason:
            note = f"{note or ''}\nFinalized: {_safe_text(reason)}".strip()
        now = _utc_now()
        return self.model_copy(
            update={
                "status": status,
                "updated_at": now,
                "finalized_at": now,
                "notes": note,
            }
        )

    def review_summary(self) -> LoopReviewSummary:
        """Return a review-context summary for this loop."""
        return LoopReviewSummary(
            loop_id=self.loop_id,
            issue_id=self.issue_id,
            status=self.status,
            attempt_count=len(self.attempts),
            failed_attempt_count=sum(
                1 for attempt in self.attempts
                if attempt.status is ResearchLoopAttemptStatus.FAILED
            ),
            succeeded_attempt_count=sum(
                1 for attempt in self.attempts
                if attempt.status is ResearchLoopAttemptStatus.SUCCEEDED
            ),
            blocking_policy_findings=sum(
                1
                for attempt in self.attempts
                for finding in attempt.policy_findings
                if finding.blocking
            ),
        )


@dataclass(frozen=True)
class ResearchLoopWriteResult:
    """Filesystem write result for one loop record."""

    loop: ResearchLoop
    relative_path: Path
    events_path: Path

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""
        return {
            "loop": self.loop.to_dict(),
            "relative_path": self.relative_path.as_posix(),
            "events_path": self.events_path.as_posix(),
            "authority_notice": RESEARCH_LOOP_AUTHORITY_NOTICE,
        }


@dataclass(frozen=True)
class ResearchLoopAttemptWriteResult:
    """Filesystem write result for one attempt record."""

    loop: ResearchLoop
    attempt: ResearchLoopAttempt
    relative_path: Path
    events_path: Path

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""
        return {
            "loop": self.loop.to_dict(),
            "attempt": self.attempt.to_dict(),
            "relative_path": self.relative_path.as_posix(),
            "events_path": self.events_path.as_posix(),
            "authority_notice": RESEARCH_LOOP_AUTHORITY_NOTICE,
        }


def start_loop(
    context: RepoContext,
    *,
    issue_id: str,
    loop_id: str | None = None,
    budget: ResearchLoopBudget | None = None,
) -> ResearchLoopWriteResult:
    """Create a new runtime research loop."""
    timestamp = _utc_now()
    resolved_issue = validate_artifact_id(issue_id.strip())
    resolved_loop_id = loop_id or _default_loop_id(resolved_issue, timestamp)
    loop = ResearchLoop(
        loop_id=resolved_loop_id,
        issue_id=resolved_issue,
        budget=budget or ResearchLoopBudget(),
        created_at=timestamp,
        updated_at=timestamp,
    )
    result = write_loop(context, loop)
    append_loop_event(
        context,
        loop_id=loop.loop_id,
        event_kind="loop_started",
        payload={"issue_id": loop.issue_id},
        recorded_at=timestamp,
    )
    return result


def write_loop(context: RepoContext, loop: ResearchLoop) -> ResearchLoopWriteResult:
    """Persist a research-loop runtime record."""
    relative_path = research_loop_path(loop.loop_id)
    events_path = research_loop_events_path(loop.loop_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    _write_json(target, loop)
    events_target = context.resolve(events_path)
    _ensure_repo_local(context, events_target)
    events_target.parent.mkdir(parents=True, exist_ok=True)
    if not events_target.exists():
        events_target.write_text("", encoding="utf-8", newline="\n")
    return ResearchLoopWriteResult(
        loop=loop,
        relative_path=relative_path,
        events_path=events_path,
    )


def save_loop(repo: RepoContext, loop: ResearchLoop) -> Path:
    """Compatibility wrapper returning the absolute loop.json path."""
    return repo.resolve(write_loop(repo, loop).relative_path)


def load_loop(context: RepoContext, loop_id: str) -> ResearchLoop:
    """Load one runtime research loop."""
    resolved = validate_artifact_id(loop_id.strip())
    relative_path = research_loop_path(resolved)
    target = context.resolve(relative_path)
    if not target.is_file():
        raise ResearchLoopError(
            f"research loop not found: {resolved}",
            code="loop_not_found",
            remediation="Start the loop first or pass an existing loop_id.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        return ResearchLoop.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ResearchLoopError(
            f"research loop failed validation: {exc}",
            code="loop_validation_failed",
            remediation="Inspect the runtime loop.json file and repair it.",
            details={"path": relative_path.as_posix()},
        ) from exc


def append_attempt(
    context: RepoContext,
    loop_id: str,
    attempt: ResearchLoopAttempt,
) -> ResearchLoopAttemptWriteResult:
    """Append one validated attempt to an existing loop."""
    loop = load_loop(context, loop_id)
    updated = loop.add_attempt(attempt)
    attempt_path = research_loop_attempt_path(updated.loop_id, attempt.attempt_id)
    target = context.resolve(attempt_path)
    _ensure_repo_local(context, target)
    _write_json(target, attempt)
    write_loop(context, updated)
    events_path = append_loop_event(
        context,
        loop_id=updated.loop_id,
        event_kind="attempt_appended",
        payload={
            "attempt_id": attempt.attempt_id,
            "attempt_number": attempt.attempt_number,
            "status": attempt.status.value,
        },
        recorded_at=attempt.completed_at or _utc_now(),
    )
    return ResearchLoopAttemptWriteResult(
        loop=updated,
        attempt=attempt,
        relative_path=attempt_path,
        events_path=events_path,
    )


def save_attempt(repo: RepoContext, attempt: ResearchLoopAttempt) -> Path:
    """Persist one standalone attempt record and return its absolute path."""
    attempt_path = research_loop_attempt_path(attempt.loop_id, attempt.attempt_id)
    target = repo.resolve(attempt_path)
    _ensure_repo_local(repo, target)
    _write_json(target, attempt)
    return target


def append_loop_event(
    context: RepoContext,
    *,
    loop_id: str,
    event_kind: str,
    payload: dict[str, Any],
    recorded_at: datetime | None = None,
) -> Path:
    """Append one bounded event to a research-loop event log."""
    resolved = validate_artifact_id(loop_id.strip())
    events_path = research_loop_events_path(resolved)
    target = context.resolve(events_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "loop_id": resolved,
        "sequence": _next_sequence(target),
        "event_kind": _safe_text(event_kind),
        "recorded_at": _normalize_required_timestamp(
            recorded_at or _utc_now()
        ).isoformat(),
        "payload": _reject_forbidden_payload(payload),
    }
    with target.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(line, ensure_ascii=True) + "\n")
    return events_path


def list_loops(context: RepoContext) -> list[str]:
    """List all runtime loop IDs in deterministic order."""
    loops_dir = context.resolve(RESEARCH_LOOP_RUNTIME_ROOT)
    if not loops_dir.exists():
        return []
    return sorted(
        d.name
        for d in loops_dir.iterdir()
        if d.is_dir() and (d / "loop.json").is_file()
    )


def research_loop_path(loop_id: str) -> Path:
    """Return repository-relative loop.json path."""
    return RESEARCH_LOOP_RUNTIME_ROOT / validate_artifact_id(loop_id) / "loop.json"


def research_loop_attempt_path(loop_id: str, attempt_id: str) -> Path:
    """Return repository-relative attempt JSON path."""
    return (
        RESEARCH_LOOP_RUNTIME_ROOT
        / validate_artifact_id(loop_id)
        / "attempts"
        / f"{validate_artifact_id(attempt_id)}.json"
    )


def research_loop_events_path(loop_id: str) -> Path:
    """Return repository-relative events.jsonl path."""
    return RESEARCH_LOOP_RUNTIME_ROOT / validate_artifact_id(loop_id) / "events.jsonl"


def _write_json(target: Path, model: ResearchLoopModel) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(model.to_json(), encoding="utf-8", newline="\n")


def _default_loop_id(issue_id: str, timestamp: datetime) -> str:
    slug = timestamp.strftime("l%Y%m%d.t%H%M%Sz")
    return validate_artifact_id(f"loop.{issue_id}.{slug}")


def _normalize_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _normalize_required_timestamp(value: datetime) -> datetime:
    normalized = _normalize_timestamp(value)
    if normalized is None:
        raise ValueError("timestamp is required")
    return normalized


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
    return normalized


def _validate_safe_reference(value: str) -> str:
    normalized = _safe_text(value)
    if _looks_like_path(normalized):
        repo_path = normalize_repo_path(normalized)
        parts = PurePosixPath(repo_path).parts
        is_absolute = Path(normalized).is_absolute() or PureWindowsPath(
            normalized
        ).is_absolute()
        if (
            is_absolute
            or normalized.startswith("/")
            or repo_path == ".."
            or repo_path.startswith("../")
            or ".." in parts
        ):
            raise ValueError("references must be repository-local")
        if parts and parts[0] == "kb" and "accepted" in parts:
            raise ValueError("research-loop records cannot reference accepted KB paths")
        return repo_path
    if "kb.accepted" in normalized.lower() or normalized.lower().startswith(
        "accepted."
    ):
        raise ValueError("research-loop records cannot reference accepted KB paths")
    return normalized


def _looks_like_path(value: str) -> bool:
    return "/" in value or "\\" in value or value.startswith(".")


def _ensure_no_private_markers(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True).lower()
    private_markers = (
        "kb/private",
        "kb\\\\private",
        "/private/",
        "\\\\private\\\\",
        "private.",
        "private:",
    )
    if any(marker in encoded for marker in private_markers):
        raise ValueError(
            "public_only research-loop attempts cannot include private refs"
        )


def _reject_forbidden_payload(payload: dict[str, Any]) -> dict[str, Any]:
    forbidden = sorted(_AUTHORITY_FIELD_NAMES.intersection(payload))
    hidden = sorted(_HIDDEN_REASONING_FIELD_NAMES.intersection(payload))
    if forbidden:
        raise ResearchLoopError(
            "research-loop event cannot claim accepted, verifier, gate, "
            "human-review, or promotion authority",
            code="authority_claim_forbidden",
            remediation=(
                "Remove authority fields; loop records are review context only."
            ),
            details={"forbidden_fields": ",".join(forbidden)},
        )
    if hidden:
        raise ResearchLoopError(
            "research-loop event cannot store hidden reasoning fields",
            code="hidden_reasoning_forbidden",
            remediation="Store only concise operator-visible summaries.",
            details={"forbidden_fields": ",".join(hidden)},
        )
    return dict(payload)


def _next_sequence(path: Path) -> int:
    if not path.exists():
        return 1
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines()
               if line.strip()) + 1


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise ResearchLoopError(
            "research-loop target must stay repository-local",
            code="invalid_runtime_path",
            remediation="Use the controlled research-loop runtime path.",
        ) from exc


__all__ = [
    "AttemptEvidenceSummary",
    "AttemptFailureRecord",
    "AttemptNextAction",
    "AttemptPolicyFinding",
    "LoopReviewSummary",
    "RESEARCH_LOOP_AUTHORITY_NOTICE",
    "RESEARCH_LOOP_REVIEW_ROOT",
    "RESEARCH_LOOP_RUNTIME_ROOT",
    "ResearchLoop",
    "ResearchLoopAttempt",
    "ResearchLoopAttemptStatus",
    "ResearchLoopBudget",
    "ResearchLoopDecision",
    "ResearchLoopError",
    "ResearchLoopFailureTag",
    "ResearchLoopStatus",
    "ResearchLoopStopCondition",
    "ResearchLoopWriteResult",
    "append_attempt",
    "append_loop_event",
    "list_loops",
    "load_loop",
    "research_loop_attempt_path",
    "research_loop_events_path",
    "research_loop_path",
    "save_attempt",
    "save_loop",
    "start_loop",
    "write_loop",
]
