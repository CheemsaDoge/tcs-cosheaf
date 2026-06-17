"""Bounded research campaign DTOs.

Campaign records are runtime review context only. They coordinate repeated
attempts, budgets, comparisons, and scorecards, but they do not create proof,
human review, verifier pass, gate pass, accepted status, or promotion authority.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path

CAMPAIGN_AUTHORITY_NOTICE = (
    "Campaign records are review context only; they are not proof, verifier "
    "pass, gate pass, human review, source metadata, accepted status, accepted "
    "refutation, or promotion authority. Campaign success never means accepted "
    "promotion."
)

CampaignPolicyMode = Literal["public_only", "private_research"]

_TERMINAL_CAMPAIGN_STATUSES = frozenset({"finalized", "abandoned", "failed"})
_AUTHORITY_FIELD_NAMES = frozenset(
    {
        "accepted",
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
        "source_metadata",
        "verifier_pass",
        "verifier_result_mutated",
    }
)
_HIDDEN_REASONING_FIELD_NAMES = frozenset(
    {"chain_of_thought", "hidden_reasoning", "reasoning_trace"}
)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class CampaignError(ValueError):
    """Expected campaign service failure."""

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


class CampaignStatus(StrEnum):
    """Lifecycle status for one bounded campaign."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    BUDGET_EXHAUSTED = "budget_exhausted"
    FINALIZED = "finalized"
    ABANDONED = "abandoned"
    FAILED = "failed"


class CampaignAttemptOutcome(StrEnum):
    """Required outcome state for one campaign attempt."""

    RESULT = "result"
    FAILURE = "failure"
    INCONCLUSIVE = "inconclusive"
    BLOCKED = "blocked"


class CampaignRiskSeverity(StrEnum):
    """Risk finding severity."""

    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class CampaignModel(BaseModel):
    """Strict deterministic base model for campaign DTOs."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable data."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON text."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class CampaignBudget(CampaignModel):
    """Bounded resource budget for a campaign."""

    max_attempts: int = Field(default=10, ge=1, le=1000)
    max_runtime_minutes: int | None = Field(default=None, ge=1)
    max_failure_repeats: int | None = Field(default=None, ge=1)
    max_draft_outputs: int | None = Field(default=None, ge=1)
    max_checker_errors: int | None = Field(default=None, ge=1)
    max_private_findings: int | None = Field(default=None, ge=1)
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def _notes(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)


class CampaignStopCondition(CampaignModel):
    """One explicit campaign stop condition."""

    condition_id: str
    kind: str
    description: str
    triggered: bool = False
    triggered_at: datetime | None = None

    @field_validator("condition_id")
    @classmethod
    def _condition_id(cls, value: str) -> str:
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


class CampaignOperatorPolicy(CampaignModel):
    """Operator policy inherited by campaign attempts."""

    policy_mode: CampaignPolicyMode = "private_research"
    allow_network: Literal[False] = False
    allow_hosted_provider: Literal[False] = False
    allow_shell: Literal[False] = False
    allow_accepted_writes: Literal[False] = False
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def _notes(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)


class CampaignRiskFinding(CampaignModel):
    """One non-authoritative risk finding on campaign output."""

    finding_id: str
    severity: CampaignRiskSeverity
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
        return _validate_safe_reference(value)


class CampaignComparison(CampaignModel):
    """A deterministic comparison between campaign attempts."""

    comparison_id: str
    attempt_ids: tuple[str, ...]
    summary: str
    preferred_attempt_id: str | None = None
    rationale: str | None = None

    @field_validator("comparison_id")
    @classmethod
    def _comparison_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("attempt_ids", mode="before")
    @classmethod
    def _attempt_ids(cls, value: Any) -> tuple[str, ...]:
        ids = _dedupe(validate_artifact_id(item) for item in _text_items(value))
        if not ids:
            raise ValueError("campaign comparisons require attempt_ids")
        return ids

    @field_validator("preferred_attempt_id")
    @classmethod
    def _preferred_attempt_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("summary", "rationale")
    @classmethod
    def _optional_text_fields(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @model_validator(mode="after")
    def _preferred_in_attempts(self) -> Self:
        if (
            self.preferred_attempt_id is not None
            and self.preferred_attempt_id not in self.attempt_ids
        ):
            raise ValueError("preferred_attempt_id must be one of attempt_ids")
        return self


class CampaignAttempt(CampaignModel):
    """One bounded attempt within a campaign."""

    attempt_id: str
    campaign_id: str
    attempt_number: int = Field(ge=1)
    outcome: CampaignAttemptOutcome
    policy_mode: CampaignPolicyMode = "private_research"
    attempted_direction: str
    started_at: datetime | None = None
    completed_at: datetime
    result_summary: str | None = None
    failure_summary: str | None = None
    inconclusive_reason: str | None = None
    blocked_reason: str | None = None
    actions_taken: tuple[str, ...] = ()
    workflow_refs: tuple[str, ...] = ()
    check_report_refs: tuple[str, ...] = ()
    proof_obligation_refs: tuple[str, ...] = ()
    draft_proposal_refs: tuple[str, ...] = ()
    handoff_refs: tuple[str, ...] = ()
    benchmark_report_refs: tuple[str, ...] = ()
    risk_findings: tuple[CampaignRiskFinding, ...] = ()
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False

    @model_validator(mode="before")
    @classmethod
    def _reject_payload_overclaims(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        forbidden = sorted(_AUTHORITY_FIELD_NAMES.intersection(value))
        hidden = sorted(_HIDDEN_REASONING_FIELD_NAMES.intersection(value))
        if forbidden:
            raise ValueError(
                "campaign attempt payload cannot claim accepted, source, "
                "verifier, gate, human-review, or promotion authority: "
                + ", ".join(forbidden)
            )
        if hidden:
            raise ValueError(
                "campaign attempt payload cannot store hidden reasoning fields: "
                + ", ".join(hidden)
            )
        return value

    @field_validator("attempt_id", "campaign_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("attempted_direction")
    @classmethod
    def _direction(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator(
        "result_summary",
        "failure_summary",
        "inconclusive_reason",
        "blocked_reason",
    )
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("actions_taken", mode="before")
    @classmethod
    def _actions(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @field_validator(
        "workflow_refs",
        "check_report_refs",
        "proof_obligation_refs",
        "draft_proposal_refs",
        "handoff_refs",
        "benchmark_report_refs",
        mode="before",
    )
    @classmethod
    def _refs(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_validate_safe_reference(item) for item in _text_items(value))

    @field_validator("started_at", "completed_at")
    @classmethod
    def _timestamp(cls, value: datetime | None) -> datetime | None:
        return _normalize_timestamp(value)

    @model_validator(mode="after")
    def _attempt_consistency(self) -> Self:
        if self.started_at and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot be before started_at")
        if self.outcome is CampaignAttemptOutcome.RESULT and not self.result_summary:
            raise ValueError("result attempts require result_summary")
        if self.outcome is CampaignAttemptOutcome.FAILURE and not self.failure_summary:
            raise ValueError("failure attempts require failure_summary")
        if (
            self.outcome is CampaignAttemptOutcome.INCONCLUSIVE
            and not self.inconclusive_reason
        ):
            raise ValueError("inconclusive attempts require inconclusive_reason")
        if self.outcome is CampaignAttemptOutcome.BLOCKED and not self.blocked_reason:
            raise ValueError("blocked attempts require blocked_reason")
        if self.authority_notice != CAMPAIGN_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve campaign boundary")
        if self.policy_mode == "public_only":
            _ensure_no_private_markers(self.to_dict())
        return self


class CampaignScorecard(CampaignModel):
    """Deterministic non-authoritative campaign scorecard."""

    schema_version: Literal[1] = 1
    campaign_id: str
    issue_id: str
    status: CampaignStatus
    generated_at: datetime
    attempt_count: int
    result_count: int
    failure_count: int
    inconclusive_count: int
    blocked_count: int
    risk_finding_count: int
    blocker_count: int
    draft_proposal_count: int
    check_report_count: int
    comparison_count: int
    budget_exhausted: bool
    accepted_write_performed: Literal[False] = False
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE

    @field_validator("campaign_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("generated_at")
    @classmethod
    def _generated_at(cls, value: datetime) -> datetime:
        normalized = _normalize_timestamp(value)
        if normalized is None:
            raise ValueError("generated_at is required")
        return normalized


class ResearchCampaign(CampaignModel):
    """Top-level bounded multi-run campaign record."""

    schema_version: Literal[1] = 1
    campaign_id: str
    issue_id: str
    status: CampaignStatus = CampaignStatus.CREATED
    budget: CampaignBudget = Field(default_factory=CampaignBudget)
    operator_policy: CampaignOperatorPolicy = Field(
        default_factory=CampaignOperatorPolicy
    )
    stop_conditions: tuple[CampaignStopCondition, ...] = ()
    attempts: tuple[CampaignAttempt, ...] = ()
    risk_findings: tuple[CampaignRiskFinding, ...] = ()
    comparisons: tuple[CampaignComparison, ...] = ()
    created_at: datetime
    updated_at: datetime
    finalized_at: datetime | None = None
    notes: str | None = None
    limitations: tuple[str, ...] = Field(
        default_factory=lambda: (CAMPAIGN_AUTHORITY_NOTICE,)
    )
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE
    accepted_write_performed: Literal[False] = False
    human_review_created: Literal[False] = False
    promotion_performed: Literal[False] = False
    verifier_result_mutated: Literal[False] = False

    @classmethod
    def start(
        cls,
        *,
        campaign_id: str,
        issue_id: str,
        budget: CampaignBudget | None = None,
        operator_policy: CampaignOperatorPolicy | None = None,
        now: datetime | None = None,
    ) -> ResearchCampaign:
        """Create a new campaign record."""
        timestamp = _normalize_required_timestamp(now or _utc_now())
        return cls(
            campaign_id=campaign_id,
            issue_id=issue_id,
            budget=budget or CampaignBudget(),
            operator_policy=operator_policy or CampaignOperatorPolicy(),
            created_at=timestamp,
            updated_at=timestamp,
        )

    @field_validator("campaign_id", "issue_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("created_at", "updated_at", "finalized_at")
    @classmethod
    def _timestamps(cls, value: datetime | None) -> datetime | None:
        return _normalize_timestamp(value)

    @field_validator("notes")
    @classmethod
    def _notes(cls, value: str | None) -> str | None:
        return _safe_optional_text(value)

    @field_validator("limitations", mode="before")
    @classmethod
    def _limitations(cls, value: Any) -> tuple[str, ...]:
        return _dedupe(_safe_text(item) for item in _text_items(value))

    @model_validator(mode="after")
    def _campaign_consistency(self) -> Self:
        if len(self.attempts) > self.budget.max_attempts:
            raise ValueError("campaign attempts exceed budget.max_attempts")
        if self.finalized_at is not None and self.finalized_at < self.created_at:
            raise ValueError("finalized_at cannot be before created_at")
        if self.status.value in _TERMINAL_CAMPAIGN_STATUSES:
            if self.finalized_at is None:
                raise ValueError("terminal campaigns require finalized_at")
        elif self.finalized_at is not None:
            raise ValueError("non-terminal campaigns cannot have finalized_at")
        if CAMPAIGN_AUTHORITY_NOTICE not in self.limitations:
            raise ValueError("limitations must include campaign authority notice")
        if self.authority_notice != CAMPAIGN_AUTHORITY_NOTICE:
            raise ValueError("authority_notice must preserve campaign boundary")
        return self

    def with_stop_condition(
        self,
        condition: CampaignStopCondition,
    ) -> ResearchCampaign:
        """Return a copy with one stop condition appended."""
        self._ensure_mutable()
        return self._replace(
            stop_conditions=(*self.stop_conditions, condition),
            updated_at=_utc_now(),
        )

    def with_risk_finding(self, finding: CampaignRiskFinding) -> ResearchCampaign:
        """Return a copy with one campaign-level risk finding appended."""
        self._ensure_mutable()
        return self._replace(
            risk_findings=(*self.risk_findings, finding),
            updated_at=_utc_now(),
        )

    def with_comparison(self, comparison: CampaignComparison) -> ResearchCampaign:
        """Return a copy with one attempt comparison appended."""
        self._ensure_mutable()
        known = {attempt.attempt_id for attempt in self.attempts}
        if known and any(
            attempt_id not in known for attempt_id in comparison.attempt_ids
        ):
            raise CampaignError(
                "campaign comparison references unknown attempt_id",
                code="campaign_comparison_unknown_attempt",
                remediation="Append attempts before comparing them.",
            )
        return self._replace(
            comparisons=(*self.comparisons, comparison),
            updated_at=_utc_now(),
        )

    def add_attempt(self, attempt: CampaignAttempt) -> ResearchCampaign:
        """Return a copy with one attempt appended."""
        self._ensure_mutable()
        if len(self.attempts) >= self.budget.max_attempts:
            raise CampaignError(
                f"Cannot add attempt: max_attempts={self.budget.max_attempts} reached",
                code="campaign_max_attempts_reached",
                remediation="Finalize this campaign or start a new campaign.",
            )
        if attempt.campaign_id != self.campaign_id:
            raise CampaignError(
                "Attempt campaign_id mismatch: "
                f"{attempt.campaign_id} != {self.campaign_id}",
                code="campaign_id_mismatch",
                remediation="Ensure attempt.campaign_id matches the target campaign.",
            )
        expected_number = len(self.attempts) + 1
        if attempt.attempt_number != expected_number:
            raise CampaignError(
                f"attempt_number must be {expected_number}",
                code="attempt_number_out_of_order",
                remediation="Append attempts in deterministic sequence order.",
            )
        status = CampaignStatus.RUNNING
        if expected_number >= self.budget.max_attempts:
            status = CampaignStatus.BUDGET_EXHAUSTED
        return self._replace(
            status=status,
            attempts=(*self.attempts, attempt),
            updated_at=attempt.completed_at,
        )

    def finalize(
        self,
        *,
        status: CampaignStatus | str = CampaignStatus.FINALIZED,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> ResearchCampaign:
        """Return a terminal campaign copy."""
        self._ensure_mutable()
        resolved = CampaignStatus(status)
        if resolved.value not in _TERMINAL_CAMPAIGN_STATUSES:
            raise CampaignError(
                "finalize requires finalized, abandoned, or failed status",
                code="invalid_terminal_status",
                remediation="Use finalized, abandoned, or failed.",
            )
        note = self.notes
        if reason:
            note = f"{note or ''}\nFinalized: {_safe_text(reason)}".strip()
        timestamp = _normalize_required_timestamp(now or _utc_now())
        return self._replace(
            status=resolved,
            updated_at=timestamp,
            finalized_at=timestamp,
            notes=note,
        )

    def _ensure_mutable(self) -> None:
        if self.status.value in _TERMINAL_CAMPAIGN_STATUSES:
            raise CampaignError(
                "terminal campaigns cannot be modified",
                code="campaign_terminal",
                remediation="Start a new campaign or inspect the terminal campaign.",
            )

    def _replace(self, **updates: Any) -> ResearchCampaign:
        data = self.model_dump(mode="python")
        data.update(updates)
        return ResearchCampaign.model_validate(data)


def build_campaign_scorecard(campaign: ResearchCampaign) -> CampaignScorecard:
    """Build a deterministic non-authoritative scorecard."""
    attempts = campaign.attempts
    all_findings = [
        finding
        for attempt in attempts
        for finding in attempt.risk_findings
    ] + list(campaign.risk_findings)
    return CampaignScorecard(
        campaign_id=campaign.campaign_id,
        issue_id=campaign.issue_id,
        status=campaign.status,
        generated_at=campaign.updated_at,
        attempt_count=len(attempts),
        result_count=sum(
            1
            for attempt in attempts
            if attempt.outcome is CampaignAttemptOutcome.RESULT
        ),
        failure_count=sum(
            1
            for attempt in attempts
            if attempt.outcome is CampaignAttemptOutcome.FAILURE
        ),
        inconclusive_count=sum(
            1
            for attempt in attempts
            if attempt.outcome is CampaignAttemptOutcome.INCONCLUSIVE
        ),
        blocked_count=sum(
            1
            for attempt in attempts
            if attempt.outcome is CampaignAttemptOutcome.BLOCKED
        ),
        risk_finding_count=len(all_findings),
        blocker_count=sum(
            1
            for finding in all_findings
            if finding.severity is CampaignRiskSeverity.BLOCKER
        ),
        draft_proposal_count=sum(
            len(attempt.draft_proposal_refs) for attempt in attempts
        ),
        check_report_count=sum(len(attempt.check_report_refs) for attempt in attempts),
        comparison_count=len(campaign.comparisons),
        budget_exhausted=campaign.status is CampaignStatus.BUDGET_EXHAUSTED
        or len(attempts) >= campaign.budget.max_attempts,
    )


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
    return normalized


def _validate_safe_reference(value: str) -> str:
    normalized = _safe_text(value)
    if _looks_like_path(normalized):
        repo_path = normalize_repo_path(normalized)
        parts = PurePosixPath(repo_path).parts
        is_absolute = (
            Path(normalized).is_absolute() or PureWindowsPath(normalized).is_absolute()
        )
        if (
            is_absolute
            or normalized.startswith("/")
            or repo_path == ".."
            or repo_path.startswith("../")
            or ".." in parts
        ):
            raise ValueError("campaign references must be repository-local")
        if parts and parts[0] == "kb" and "accepted" in parts:
            raise ValueError("campaign records cannot reference accepted KB paths")
        return repo_path
    if "kb.accepted" in normalized.lower() or normalized.lower().startswith(
        "accepted."
    ):
        raise ValueError("campaign records cannot reference accepted KB paths")
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
        raise ValueError("public_only campaign attempts cannot include private refs")


__all__ = [
    "CAMPAIGN_AUTHORITY_NOTICE",
    "CampaignAttempt",
    "CampaignAttemptOutcome",
    "CampaignBudget",
    "CampaignComparison",
    "CampaignError",
    "CampaignModel",
    "CampaignOperatorPolicy",
    "CampaignPolicyMode",
    "CampaignRiskFinding",
    "CampaignRiskSeverity",
    "CampaignScorecard",
    "CampaignStatus",
    "CampaignStopCondition",
    "ResearchCampaign",
    "build_campaign_scorecard",
]
