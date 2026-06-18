"""Runtime storage for bounded research campaigns."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import ValidationError

from cosheaf.campaigns.models import (
    CAMPAIGN_AUTHORITY_NOTICE,
    CampaignAttempt,
    CampaignAttemptOutcome,
    CampaignBudget,
    CampaignError,
    CampaignNextResult,
    CampaignOperatorImportResult,
    CampaignOperatorPolicy,
    CampaignOperatorResult,
    CampaignOperatorTask,
    CampaignOutputContract,
    CampaignPreviousFailure,
    CampaignScorecard,
    CampaignStatus,
    CampaignStopCondition,
    ResearchCampaign,
    build_campaign_scorecard,
)
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path, repo_relative_posix
from cosheaf.security.provider_logs import scan_provider_log_text
from cosheaf.storage.repo import RepoContext

CAMPAIGN_RUNTIME_ROOT = Path(".cosheaf") / "campaigns"
CAMPAIGN_SCAN_KIND = "campaign_scan"
_CAMPAIGN_TERMINAL_STATUSES = frozenset({"finalized", "abandoned", "failed"})
_PRIVATE_PATH_PATTERN = re.compile(
    r"(?i)(?:^|[/\\])kb[/\\]private[/\\]|(?:^|[/\\])private[/\\]"
)
_ACCEPTED_PATH_PATTERN = re.compile(r"(?i)(?:^|[/\\])kb[/\\][^\"'\s,}]*accepted[/\\]")
_AUTHORITY_BOOLEAN_KEYS = frozenset(
    {
        "accepted",
        "accepted_refutation",
        "accepted_status",
        "accepted_write",
        "accepted_write_performed",
        "artifact_status",
        "gate_pass",
        "human_review",
        "human_review_created",
        "human_reviewed",
        "promote",
        "promotion",
        "promotion_authority",
        "promotion_performed",
        "review_state",
        "source_metadata",
        "source_metadata_created",
        "verifier_pass",
        "verifier_result_mutated",
    }
)
_AUTHORITY_TEXT_PATTERN = re.compile(
    r"(?i)(accepted_status\s*[:=]\s*accepted|accepted_refutation|"
    r"human_reviewed|mark\s+human\s+review|mark\s+.*reviewed|"
    r"promote\s+this|promotion_authority|"
    r"verifier_pass\s*[:=]\s*true|gate_pass\s*[:=]\s*true)"
)
_PROVIDER_PAYLOAD_KEYS = frozenset(
    {
        "provider_payload",
        "provider_request",
        "provider_response",
        "raw_provider_payload",
        "raw_provider_request",
        "raw_provider_response",
        "raw_request",
        "raw_response",
    }
)
_ENVIRONMENT_DUMP_KEYS = frozenset({"env", "environ", "environment", "env_dump"})
_CAMPAIGN_SCAN_FINDING_MESSAGES = {
    "accepted_authority_overclaim": (
        "campaign runtime output claims accepted status or acceptance authority"
    ),
    "accepted_refutation_overclaim": (
        "campaign runtime output claims accepted refutation authority"
    ),
    "accepted_write_attempt": (
        "campaign runtime output references an accepted KB write target"
    ),
    "api_key": "campaign runtime output contains an API-key-shaped value",
    "authority_claim": (
        "campaign runtime output claims review, verifier, gate, accepted, or "
        "promotion authority"
    ),
    "bearer_token": "campaign runtime output contains an unredacted bearer token",
    "environment_dump": "campaign runtime output contains an environment-like dump",
    "events_json_invalid": "campaign event JSON could not be parsed",
    "gate_verifier_overclaim": (
        "campaign runtime output claims verifier or gate pass authority"
    ),
    "hidden_reasoning": "campaign runtime output contains hidden-reasoning marker text",
    "human_review_overclaim": "campaign runtime output claims human-review authority",
    "operator_result_json_invalid": "campaign operator-result JSON could not be parsed",
    "private_reference_in_public_mode": (
        "public-only campaign runtime output references private content"
    ),
    "promotion_overclaim": "campaign runtime output claims promotion authority",
    "provider_payload": "campaign runtime output stores raw provider payload data",
    "repeated_failure": (
        "campaign repeated the same failed direction beyond its configured budget"
    ),
    "runtime_json_invalid": "campaign runtime JSON could not be parsed",
    "secret_env_value": (
        "campaign runtime output contains a secret-looking key with a value"
    ),
    "absolute_private_path": (
        "campaign runtime output contains an absolute user or private path"
    ),
    "unapproved_private_context": (
        "campaign runtime output contains private context without matching policy"
    ),
}


@dataclass(frozen=True)
class CampaignWriteResult:
    """Filesystem write result for one campaign record."""

    campaign: ResearchCampaign
    relative_path: Path
    events_path: Path
    scorecard_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign",
            "campaign_id": self.campaign.campaign_id,
            "issue_id": self.campaign.issue_id,
            "status": self.campaign.status.value,
            "path": self.relative_path.as_posix(),
            "events_path": self.events_path.as_posix(),
            "scorecard_path": self.scorecard_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": CAMPAIGN_AUTHORITY_NOTICE,
            "campaign": self.campaign.to_dict(),
        }


@dataclass(frozen=True)
class CampaignAttemptWriteResult:
    """Filesystem write result for one campaign attempt."""

    campaign: ResearchCampaign
    attempt: CampaignAttempt
    relative_path: Path
    attempt_path: Path
    events_path: Path
    scorecard_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign_attempt",
            "campaign_id": self.campaign.campaign_id,
            "attempt_id": self.attempt.attempt_id,
            "status": self.campaign.status.value,
            "path": self.relative_path.as_posix(),
            "attempt_path": self.attempt_path.as_posix(),
            "events_path": self.events_path.as_posix(),
            "scorecard_path": self.scorecard_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": CAMPAIGN_AUTHORITY_NOTICE,
            "campaign": self.campaign.to_dict(),
            "attempt": self.attempt.to_dict(),
        }


@dataclass(frozen=True)
class CampaignScorecardResult:
    """Filesystem write result for one campaign scorecard."""

    campaign: ResearchCampaign
    scorecard: CampaignScorecard
    scorecard_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign_scorecard",
            "campaign_id": self.campaign.campaign_id,
            "scorecard_path": self.scorecard_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": CAMPAIGN_AUTHORITY_NOTICE,
            "scorecard": self.scorecard.to_dict(),
        }


@dataclass(frozen=True)
class CampaignOperatorTaskExportResult:
    """Filesystem write result for one operator task packet."""

    campaign: ResearchCampaign
    task: CampaignOperatorTask
    relative_path: Path
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign_operator_task_export",
            "campaign_id": self.campaign.campaign_id,
            "attempt_id": self.task.attempt_id,
            "path": self.relative_path.as_posix(),
            "writes_performed": True,
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": CAMPAIGN_AUTHORITY_NOTICE,
            "operator_task": self.task.to_dict(),
        }


@dataclass(frozen=True)
class CampaignScanFinding:
    """One deterministic campaign runtime scan finding."""

    code: str
    severity: Literal["warning", "blocker"]
    message: str
    source_path: str
    line: int | None = None
    field_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "source_path": self.source_path,
        }
        if self.line is not None:
            payload["line"] = self.line
        if self.field_path is not None:
            payload["field_path"] = self.field_path
        return payload


@dataclass(frozen=True)
class CampaignScanResult:
    """One campaign runtime scan report."""

    campaign: ResearchCampaign
    policy_mode: str
    findings: tuple[CampaignScanFinding, ...]
    report_path: Path
    accepted_write_performed: Literal[False] = False
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE

    @property
    def campaign_id(self) -> str:
        return self.campaign.campaign_id

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def blocking_finding_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "blocker")

    @property
    def run_blocked(self) -> bool:
        return self.blocking_finding_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": CAMPAIGN_SCAN_KIND,
            "campaign_id": self.campaign.campaign_id,
            "policy_mode": self.policy_mode,
            "finding_count": self.finding_count,
            "blocking_finding_count": self.blocking_finding_count,
            "run_blocked": self.run_blocked,
            "report_path": self.report_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": self.authority_notice,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class CampaignRunResult:
    """Deterministic campaign controller result."""

    campaign: ResearchCampaign
    scan: CampaignScanResult
    stop_conditions: dict[str, bool]
    writes_performed: bool
    shell_commands_performed: Literal[False] = False
    provider_calls_performed: Literal[False] = False
    accepted_write_performed: Literal[False] = False
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign_run",
            "campaign_id": self.campaign.campaign_id,
            "status": self.campaign.status.value,
            "stop_conditions": self.stop_conditions,
            "writes_performed": self.writes_performed,
            "shell_commands_performed": self.shell_commands_performed,
            "provider_calls_performed": self.provider_calls_performed,
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": self.authority_notice,
            "scan": self.scan.to_dict(),
            "campaign": self.campaign.to_dict(),
        }


@dataclass(frozen=True)
class CampaignReviewMetrics:
    """Non-authoritative campaign review/handoff metrics."""

    attempt_count: int
    unique_direction_count: int
    repeat_failure_count: int
    reviewable_draft_count: int
    checked_evidence_count: int
    gap_count: int
    unsafe_output_count: int
    budget_stop_accuracy: bool
    operator_contract_validity: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_count": self.attempt_count,
            "unique_direction_count": self.unique_direction_count,
            "repeat_failure_count": self.repeat_failure_count,
            "reviewable_draft_count": self.reviewable_draft_count,
            "checked_evidence_count": self.checked_evidence_count,
            "gap_count": self.gap_count,
            "unsafe_output_count": self.unsafe_output_count,
            "budget_stop_accuracy": self.budget_stop_accuracy,
            "operator_contract_validity": self.operator_contract_validity,
        }


@dataclass(frozen=True)
class CampaignHandoffResult:
    """Filesystem write result for one campaign review handoff summary."""

    campaign: ResearchCampaign
    metrics: CampaignReviewMetrics
    scan: CampaignScanResult
    handoff_path: Path
    accepted_write_performed: Literal[False] = False
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE

    def handoff_to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign_handoff",
            "campaign_id": self.campaign.campaign_id,
            "issue_id": self.campaign.issue_id,
            "status": self.campaign.status.value,
            "generated_at": self.campaign.updated_at.isoformat(),
            "metrics": self.metrics.to_dict(),
            "attempts": [
                _attempt_handoff_summary(attempt)
                for attempt in self.campaign.attempts
            ],
            "risk_findings": [
                finding.to_dict() for finding in self.campaign.risk_findings
            ],
            "scan": self.scan.to_dict(),
            "limitations": _campaign_handoff_limitations(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": self.authority_notice,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "campaign_handoff_export",
            "campaign_id": self.campaign.campaign_id,
            "handoff_path": self.handoff_path.as_posix(),
            "accepted_write_performed": self.accepted_write_performed,
            "authority_notice": self.authority_notice,
            "handoff": self.handoff_to_dict(),
        }


def start_campaign(
    context: RepoContext,
    *,
    issue_id: str,
    campaign_id: str | None = None,
    budget: CampaignBudget | None = None,
    operator_policy: CampaignOperatorPolicy | None = None,
    now: datetime | None = None,
) -> CampaignWriteResult:
    """Create and persist a new campaign runtime record."""
    timestamp = _normalize_timestamp(now or _utc_now())
    resolved_issue = validate_artifact_id(issue_id.strip())
    resolved_campaign_id = (
        validate_artifact_id(campaign_id.strip())
        if campaign_id
        else _allocate_campaign_id(context, resolved_issue, timestamp)
    )
    relative_path = campaign_path(resolved_campaign_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    if target.exists():
        raise CampaignError(
            f"campaign already exists: {resolved_campaign_id}",
            code="campaign_path_exists",
            remediation="Use a new campaign_id or show the existing campaign.",
            details={"path": relative_path.as_posix()},
        )
    campaign = ResearchCampaign.start(
        campaign_id=resolved_campaign_id,
        issue_id=resolved_issue,
        budget=budget,
        operator_policy=operator_policy,
        now=timestamp,
    )
    result = write_campaign(context, campaign)
    append_campaign_event(
        context,
        campaign_id=campaign.campaign_id,
        event_kind="campaign_started",
        payload={"issue_id": campaign.issue_id},
        recorded_at=timestamp,
    )
    return result


def load_campaign(context: RepoContext, campaign_id: str) -> CampaignWriteResult:
    """Load one campaign runtime record."""
    resolved = validate_artifact_id(campaign_id.strip())
    relative_path = campaign_path(resolved)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    if not target.is_file():
        raise CampaignError(
            f"campaign not found: {resolved}",
            code="campaign_not_found",
            remediation="Start the campaign first or pass an existing campaign_id.",
            details={"path": relative_path.as_posix()},
        )
    try:
        raw = json.loads(target.read_text(encoding="utf-8-sig"))
        campaign = ResearchCampaign.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise CampaignError(
            f"campaign failed validation: {exc}",
            code="campaign_validation_failed",
            remediation="Inspect the runtime campaign.json file and repair it.",
            details={"path": relative_path.as_posix()},
        ) from exc
    return CampaignWriteResult(
        campaign=campaign,
        relative_path=relative_path,
        events_path=campaign_events_path(campaign.campaign_id),
        scorecard_path=campaign_scorecard_path(campaign.campaign_id),
    )


def write_campaign(
    context: RepoContext,
    campaign: ResearchCampaign,
) -> CampaignWriteResult:
    """Persist a campaign record and its current scorecard."""
    relative_path = campaign_path(campaign.campaign_id)
    events_path = campaign_events_path(campaign.campaign_id)
    scorecard_path = campaign_scorecard_path(campaign.campaign_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    _write_json(target, campaign)
    events_target = context.resolve(events_path)
    _ensure_repo_local(context, events_target)
    events_target.parent.mkdir(parents=True, exist_ok=True)
    if not events_target.exists():
        events_target.write_text("", encoding="utf-8", newline="\n")
    _write_scorecard(context, campaign)
    return CampaignWriteResult(
        campaign=campaign,
        relative_path=relative_path,
        events_path=events_path,
        scorecard_path=scorecard_path,
    )


def append_campaign_attempt(
    context: RepoContext,
    campaign_id: str,
    attempt: CampaignAttempt,
) -> CampaignAttemptWriteResult:
    """Append one validated attempt to an existing campaign."""
    loaded = load_campaign(context, campaign_id)
    updated = loaded.campaign.add_attempt(attempt)
    attempt_path = campaign_attempt_path(updated.campaign_id, attempt.attempt_id)
    attempt_target = context.resolve(attempt_path)
    _ensure_repo_local(context, attempt_target)
    if attempt_target.exists():
        raise CampaignError(
            f"campaign attempt already exists: {attempt.attempt_id}",
            code="campaign_attempt_path_exists",
            remediation="Use a new attempt_id or inspect the existing attempt.",
            details={"path": attempt_path.as_posix()},
        )
    _write_json(attempt_target, attempt)
    write_campaign(context, updated)
    events_path = append_campaign_event(
        context,
        campaign_id=updated.campaign_id,
        event_kind="attempt_appended",
        payload={
            "attempt_id": attempt.attempt_id,
            "attempt_number": attempt.attempt_number,
            "outcome": attempt.outcome.value,
        },
        recorded_at=attempt.completed_at,
    )
    return CampaignAttemptWriteResult(
        campaign=updated,
        attempt=attempt,
        relative_path=campaign_path(updated.campaign_id),
        attempt_path=attempt_path,
        events_path=events_path,
        scorecard_path=campaign_scorecard_path(updated.campaign_id),
    )


def show_campaign_scorecard(
    context: RepoContext,
    campaign_id: str,
) -> CampaignScorecardResult:
    """Load a campaign, write the current scorecard, and return it."""
    loaded = load_campaign(context, campaign_id)
    scorecard_path = _write_scorecard(context, loaded.campaign)
    return CampaignScorecardResult(
        campaign=loaded.campaign,
        scorecard=build_campaign_scorecard(loaded.campaign),
        scorecard_path=scorecard_path,
    )


def finalize_campaign(
    context: RepoContext,
    campaign_id: str,
    *,
    status: CampaignStatus | str = CampaignStatus.FINALIZED,
    now: datetime | None = None,
    reason: str | None = None,
) -> CampaignWriteResult:
    """Finalize a campaign with a terminal status."""
    loaded = load_campaign(context, campaign_id)
    updated = loaded.campaign.finalize(
        status=status,
        now=now,
        reason=reason,
    )
    result = write_campaign(context, updated)
    append_campaign_event(
        context,
        campaign_id=updated.campaign_id,
        event_kind="campaign_finalized",
        payload={"status": updated.status.value},
        recorded_at=updated.finalized_at,
    )
    return result


def pause_campaign(
    context: RepoContext,
    campaign_id: str,
    *,
    reason: str | None = None,
) -> CampaignWriteResult:
    """Pause a mutable campaign without executing any work."""
    loaded = load_campaign(context, campaign_id)
    _ensure_campaign_mutable(loaded.campaign)
    updated = loaded.campaign._replace(
        status=CampaignStatus.PAUSED,
        updated_at=_utc_now(),
    )
    result = write_campaign(context, updated)
    append_campaign_event(
        context,
        campaign_id=updated.campaign_id,
        event_kind="campaign_paused",
        payload={"reason": _safe_text(reason) if reason else "manual pause"},
        recorded_at=updated.updated_at,
    )
    return result


def resume_campaign(
    context: RepoContext,
    campaign_id: str,
) -> CampaignWriteResult:
    """Resume a paused campaign without bypassing blockers or budgets."""
    loaded = load_campaign(context, campaign_id)
    if loaded.campaign.status is not CampaignStatus.PAUSED:
        raise CampaignError(
            "only paused campaigns can be resumed",
            code="campaign_not_paused",
            remediation=(
                "Resume only paused campaigns. Start a new campaign when blocked "
                "or budget exhausted."
            ),
        )
    updated = loaded.campaign._replace(
        status=CampaignStatus.RUNNING,
        updated_at=_utc_now(),
    )
    result = write_campaign(context, updated)
    append_campaign_event(
        context,
        campaign_id=updated.campaign_id,
        event_kind="campaign_resumed",
        payload={"status": updated.status.value},
        recorded_at=updated.updated_at,
    )
    return result


def scan_campaign(
    context: RepoContext,
    campaign_id: str,
    *,
    write_report: bool = True,
) -> CampaignScanResult:
    """Scan campaign runtime outputs for unsafe authority or leakage claims."""
    loaded = load_campaign(context, campaign_id)
    campaign = loaded.campaign
    scanner = _CampaignRuntimeScanner(campaign=campaign)
    runtime_root = context.resolve(campaign_path(campaign.campaign_id).parent)
    _ensure_repo_local(context, runtime_root)
    for relative_path, target in _iter_campaign_scan_files(
        context,
        campaign.campaign_id,
    ):
        text = target.read_text(encoding="utf-8-sig")
        if target.suffix.lower() == ".jsonl":
            scanner.scan_events_jsonl(text, source_path=relative_path.as_posix())
            continue
        scanner.scan_json_file(
            text,
            source_path=relative_path.as_posix(),
            invalid_code=_invalid_json_code(relative_path),
        )
    scanner.scan_budget_state()
    result = CampaignScanResult(
        campaign=campaign,
        policy_mode=_campaign_policy_mode(campaign),
        findings=tuple(scanner.findings),
        report_path=campaign_scan_path(campaign.campaign_id),
    )
    if write_report:
        target = context.resolve(result.report_path)
        _ensure_repo_local(context, target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(result.to_dict(), ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


def run_campaign(
    context: RepoContext,
    campaign_id: str,
    *,
    max_attempts: int | None = None,
) -> CampaignRunResult:
    """Apply deterministic campaign stop policies without running providers or shell."""
    loaded = load_campaign(context, campaign_id)
    campaign = loaded.campaign
    _ensure_campaign_mutable(campaign)
    scan = scan_campaign(context, campaign.campaign_id)
    stop_conditions = _campaign_stop_conditions(
        campaign,
        scan,
        max_attempts=max_attempts,
    )
    next_status = campaign.status
    if campaign.status is CampaignStatus.PAUSED:
        next_status = CampaignStatus.PAUSED
    elif stop_conditions["unsafe_runtime_output"] or stop_conditions[
        "repeated_failure_without_justification"
    ]:
        next_status = CampaignStatus.BLOCKED
    elif stop_conditions["all_budget_exhausted"]:
        next_status = CampaignStatus.BUDGET_EXHAUSTED
    elif campaign.status is CampaignStatus.CREATED:
        next_status = CampaignStatus.RUNNING

    status_changed = next_status is not campaign.status
    updated = campaign
    if status_changed:
        updated = campaign._replace(status=next_status, updated_at=_utc_now())
        write_campaign(context, updated)
    append_campaign_event(
        context,
        campaign_id=updated.campaign_id,
        event_kind="campaign_run_controller",
        payload={
            "status": updated.status.value,
            "stop_conditions": stop_conditions,
            "shell_commands_performed": False,
            "provider_calls_performed": False,
        },
        recorded_at=updated.updated_at,
    )
    return CampaignRunResult(
        campaign=updated,
        scan=scan,
        stop_conditions=stop_conditions,
        writes_performed=True,
    )


def build_campaign_review_metrics(
    campaign: ResearchCampaign,
    scan: CampaignScanResult,
) -> CampaignReviewMetrics:
    """Build deterministic review metrics without granting authority."""
    directions = [
        attempt.attempted_direction.strip().lower() for attempt in campaign.attempts
    ]
    failure_counts: dict[str, int] = {}
    checked_evidence: set[str] = set()
    gaps: set[str] = set()
    for attempt in campaign.attempts:
        if attempt.outcome is CampaignAttemptOutcome.FAILURE:
            key = attempt.attempted_direction.strip().lower()
            failure_counts[key] = failure_counts.get(key, 0) + 1
        checked_evidence.update(attempt.check_report_refs)
        gaps.update(attempt.proof_obligation_refs)
    expected_budget_exhausted = (
        len(campaign.attempts) >= campaign.budget.max_attempts
        or _draft_budget_exhausted(campaign)
    )
    budget_stop_accuracy = (
        campaign.status is CampaignStatus.BUDGET_EXHAUSTED
    ) == expected_budget_exhausted
    operator_contract_validity = (
        not scan.run_blocked
        and not campaign.accepted_write_performed
        and not campaign.human_review_created
        and not campaign.promotion_performed
        and not campaign.verifier_result_mutated
        and all(
            attempt.authority_notice == CAMPAIGN_AUTHORITY_NOTICE
            for attempt in campaign.attempts
        )
    )
    return CampaignReviewMetrics(
        attempt_count=len(campaign.attempts),
        unique_direction_count=len(set(directions)),
        repeat_failure_count=sum(
            max(0, count - 1) for count in failure_counts.values()
        ),
        reviewable_draft_count=_draft_output_count(campaign),
        checked_evidence_count=len(checked_evidence),
        gap_count=len(gaps),
        unsafe_output_count=scan.blocking_finding_count,
        budget_stop_accuracy=budget_stop_accuracy,
        operator_contract_validity=operator_contract_validity,
    )


def build_campaign_handoff(
    context: RepoContext,
    campaign_id: str,
    out: str | Path,
) -> CampaignHandoffResult:
    """Write a deterministic campaign review handoff summary."""
    loaded = load_campaign(context, campaign_id)
    scan = scan_campaign(context, campaign_id)
    metrics = build_campaign_review_metrics(loaded.campaign, scan)
    handoff_path = campaign_handoff_path(out)
    target = context.resolve(handoff_path)
    _ensure_repo_local(context, target)
    result = CampaignHandoffResult(
        campaign=loaded.campaign,
        metrics=metrics,
        scan=scan,
        handoff_path=handoff_path,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result.handoff_to_dict(), ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    append_campaign_event(
        context,
        campaign_id=campaign_id,
        event_kind="campaign_handoff_exported",
        payload={
            "path": handoff_path.as_posix(),
            "writes_performed": True,
        },
    )
    return result


def next_campaign_operator_task(
    context: RepoContext,
    campaign_id: str,
) -> CampaignNextResult:
    """Return the deterministic next operator-task preview for one campaign."""
    loaded = load_campaign(context, campaign_id)
    return build_campaign_next_result(loaded.campaign)


def build_campaign_next_result(campaign: ResearchCampaign) -> CampaignNextResult:
    """Build a deterministic next-task preview without writing files."""
    failures = _previous_failures(campaign)
    proof_obligations = _proof_obligations(campaign)
    stop_conditions = _next_stop_conditions(campaign)
    exhausted = len(campaign.attempts) >= campaign.budget.max_attempts
    terminal = campaign.status.value in {"finalized", "abandoned", "failed"}
    if exhausted or terminal:
        return CampaignNextResult(
            campaign_id=campaign.campaign_id,
            issue_id=campaign.issue_id,
            next_action="finalize_campaign",
            previous_failures_to_avoid=failures,
            proof_obligations=proof_obligations,
            stop_conditions=stop_conditions,
            retry_requires_justification=bool(failures),
        )
    attempt_number = len(campaign.attempts) + 1
    attempt_id = _campaign_attempt_id(campaign, attempt_number)
    task = build_campaign_operator_task(
        campaign,
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        previous_failures=failures,
        proof_obligations=proof_obligations,
        stop_conditions=stop_conditions,
    )
    return CampaignNextResult(
        campaign_id=campaign.campaign_id,
        issue_id=campaign.issue_id,
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        next_action="start_attempt",
        operator_task=task,
        previous_failures_to_avoid=failures,
        proof_obligations=proof_obligations,
        stop_conditions=stop_conditions,
        retry_requires_justification=bool(failures),
    )


def build_campaign_operator_task(
    campaign: ResearchCampaign,
    *,
    attempt_id: str | None = None,
    attempt_number: int | None = None,
    previous_failures: tuple[CampaignPreviousFailure, ...] | None = None,
    proof_obligations: tuple[str, ...] | None = None,
    stop_conditions: tuple[CampaignStopCondition, ...] | None = None,
) -> CampaignOperatorTask:
    """Build a bounded operator task packet for the next campaign attempt."""
    resolved_number = attempt_number or (len(campaign.attempts) + 1)
    resolved_attempt_id = attempt_id or _campaign_attempt_id(campaign, resolved_number)
    failures = (
        previous_failures
        if previous_failures is not None
        else _previous_failures(campaign)
    )
    obligations = (
        proof_obligations
        if proof_obligations is not None
        else _proof_obligations(campaign)
    )
    stops = (
        stop_conditions
        if stop_conditions is not None
        else _next_stop_conditions(campaign)
    )
    return CampaignOperatorTask(
        campaign_id=campaign.campaign_id,
        workflow_id=_campaign_workflow_id(campaign),
        attempt_id=resolved_attempt_id,
        issue_id=campaign.issue_id,
        objective=(
            f"Make bounded campaign attempt {resolved_number} for {campaign.issue_id}."
        ),
        context_refs=_context_refs(campaign),
        hot_memory_cards=tuple(failure.summary for failure in failures),
        previous_failures_to_avoid=failures,
        proof_obligations=obligations,
        checker_requirements=(
            "run cosheaf validate when draft artifacts are touched",
            "run cosheaf gate run before claiming readiness",
            "record skipped checker rows as skipped, not pass",
        ),
        allowed_actions=(
            "read repository files",
            "run documented cosheaf CLI commands",
            "write draft or review-context outputs only",
            "return operator_result_v2.json",
        ),
        forbidden_actions=(
            "write kb/accepted",
            "create or mark human review",
            "claim verifier pass without a verifier result",
            "claim gate pass without running gate",
            "promote artifacts",
            "claim accepted status or accepted refutation",
            "call hosted providers by default",
            "run arbitrary shell through campaign runtime",
        ),
        budget=campaign.budget,
        stop_conditions=stops,
        output_contract=CampaignOutputContract(),
    )


def export_campaign_operator_task(
    context: RepoContext,
    campaign_id: str,
    out: str | Path,
) -> Path:
    """Write a bounded operator task packet to a repository-local JSON path."""
    loaded = load_campaign(context, campaign_id)
    next_result = build_campaign_next_result(loaded.campaign)
    if next_result.operator_task is None:
        raise CampaignError(
            "campaign has no exportable operator task",
            code="campaign_no_operator_task",
            remediation="Start a new campaign or inspect the terminal/budget state.",
        )
    relative_path = _validate_output_path(out)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    _write_json(target, next_result.operator_task)
    append_campaign_event(
        context,
        campaign_id=loaded.campaign.campaign_id,
        event_kind="operator_task_v2_exported",
        payload={
            "attempt_id": next_result.operator_task.attempt_id,
            "path": relative_path.as_posix(),
            "writes_performed": True,
        },
    )
    return relative_path


def import_campaign_operator_result(
    context: RepoContext,
    campaign_id: str,
    payload: CampaignOperatorResult,
) -> CampaignOperatorImportResult:
    """Import one structured external-operator result as a campaign attempt."""
    loaded = load_campaign(context, campaign_id)
    campaign = loaded.campaign
    if campaign.operator_policy.policy_mode == "public_only":
        _ensure_public_result_payload(payload)
    attempt_number = len(campaign.attempts) + 1
    attempt_id = _campaign_attempt_id(campaign, attempt_number)
    attempt = _attempt_from_operator_result(
        campaign=campaign,
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        payload=payload,
    )
    appended = append_campaign_attempt(context, campaign.campaign_id, attempt)
    operator_result_path = campaign_operator_result_path(
        campaign.campaign_id,
        attempt_id,
    )
    result_target = context.resolve(operator_result_path)
    _ensure_repo_local(context, result_target)
    _write_json(result_target, payload)
    append_campaign_event(
        context,
        campaign_id=campaign.campaign_id,
        event_kind="operator_result_v2_imported",
        payload={
            "attempt_id": attempt_id,
            "path": operator_result_path.as_posix(),
            "writes_performed": True,
        },
    )
    return CampaignOperatorImportResult(
        campaign_id=appended.campaign.campaign_id,
        attempt_id=attempt.attempt_id,
        attempt=attempt,
        campaign=appended.campaign,
        relative_path=appended.relative_path.as_posix(),
        attempt_path=appended.attempt_path.as_posix(),
        operator_result_path=operator_result_path.as_posix(),
    )


def append_campaign_event(
    context: RepoContext,
    *,
    campaign_id: str,
    event_kind: str,
    payload: dict[str, Any],
    recorded_at: datetime | None = None,
) -> Path:
    """Append one bounded campaign event line."""
    resolved = validate_artifact_id(campaign_id.strip())
    events_path = campaign_events_path(resolved)
    target = context.resolve(events_path)
    _ensure_repo_local(context, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "campaign_id": resolved,
        "sequence": _next_sequence(target),
        "event_kind": _safe_text(event_kind),
        "recorded_at": _normalize_timestamp(recorded_at or _utc_now()).isoformat(),
        "payload": _reject_forbidden_event_payload(payload),
        "authority_notice": CAMPAIGN_AUTHORITY_NOTICE,
    }
    with target.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(line, ensure_ascii=True, sort_keys=True) + "\n")
    return events_path


def campaign_path(campaign_id: str) -> Path:
    """Return runtime campaign.json path."""
    resolved = validate_artifact_id(campaign_id.strip())
    return CAMPAIGN_RUNTIME_ROOT / resolved / "campaign.json"


def campaign_attempt_path(campaign_id: str, attempt_id: str) -> Path:
    """Return runtime attempt JSON path."""
    resolved_campaign = validate_artifact_id(campaign_id.strip())
    resolved_attempt = validate_artifact_id(attempt_id.strip())
    return CAMPAIGN_RUNTIME_ROOT / resolved_campaign / "attempts" / (
        f"{resolved_attempt}.json"
    )


def campaign_scorecard_path(campaign_id: str) -> Path:
    """Return runtime scorecard JSON path."""
    resolved = validate_artifact_id(campaign_id.strip())
    return CAMPAIGN_RUNTIME_ROOT / resolved / "scorecard.json"


def campaign_events_path(campaign_id: str) -> Path:
    """Return runtime events JSONL path."""
    resolved = validate_artifact_id(campaign_id.strip())
    return CAMPAIGN_RUNTIME_ROOT / resolved / "events.jsonl"


def campaign_scan_path(campaign_id: str) -> Path:
    """Return runtime campaign scan report path."""
    resolved = validate_artifact_id(campaign_id.strip())
    return CAMPAIGN_RUNTIME_ROOT / resolved / "scan.json"


def campaign_handoff_path(out: str | Path) -> Path:
    """Return campaign handoff summary path under one repo-local directory."""
    return _validate_output_dir_path(out) / "campaign_handoff.json"


def campaign_operator_result_path(campaign_id: str, attempt_id: str) -> Path:
    """Return runtime operator result packet path."""
    resolved_campaign = validate_artifact_id(campaign_id.strip())
    resolved_attempt = validate_artifact_id(attempt_id.strip())
    return (
        CAMPAIGN_RUNTIME_ROOT
        / resolved_campaign
        / "operator-results"
        / f"{resolved_attempt}.json"
    )


def _write_scorecard(context: RepoContext, campaign: ResearchCampaign) -> Path:
    scorecard = build_campaign_scorecard(campaign)
    relative_path = campaign_scorecard_path(campaign.campaign_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    _write_json(target, scorecard)
    return relative_path


def _write_json(
    target: Path,
    model: (
        ResearchCampaign
        | CampaignAttempt
        | CampaignScorecard
        | CampaignOperatorTask
        | CampaignOperatorResult
    ),
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(model.to_json(), encoding="utf-8", newline="\n")


def _attempt_handoff_summary(attempt: CampaignAttempt) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "attempt_number": attempt.attempt_number,
        "outcome": attempt.outcome.value,
        "attempted_direction": attempt.attempted_direction,
        "result_summary": attempt.result_summary,
        "failure_summary": attempt.failure_summary,
        "inconclusive_reason": attempt.inconclusive_reason,
        "blocked_reason": attempt.blocked_reason,
        "draft_proposal_refs": list(attempt.draft_proposal_refs),
        "check_report_refs": list(attempt.check_report_refs),
        "proof_obligation_refs": list(attempt.proof_obligation_refs),
        "accepted_write_performed": False,
        "authority_notice": attempt.authority_notice,
    }


def _campaign_handoff_limitations() -> dict[str, bool]:
    return {
        "not_proof": True,
        "not_source_metadata": True,
        "not_human_review": True,
        "not_verifier_pass": True,
        "not_gate_pass": True,
        "not_accepted_status": True,
        "not_accepted_refutation": True,
        "not_promotion_authority": True,
    }


def _allocate_campaign_id(
    context: RepoContext,
    issue_id: str,
    timestamp: datetime,
) -> str:
    base = _default_campaign_id(issue_id, timestamp)
    candidate = base
    suffix = 2
    while context.resolve(campaign_path(candidate)).exists():
        candidate = validate_artifact_id(f"{base}.{suffix}")
        suffix += 1
    return candidate


def _default_campaign_id(issue_id: str, timestamp: datetime) -> str:
    slug = timestamp.strftime("c%Y%m%d.t%H%M%Sz")
    return validate_artifact_id(f"campaign.{issue_id}.{slug}")


def _next_sequence(path: Path) -> int:
    if not path.exists():
        return 1
    return (
        sum(
            1
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        )
        + 1
    )


def _reject_forbidden_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    forbidden = {
        "accepted",
        "accepted_write_performed",
        "human_reviewed",
        "human_review_created",
        "promotion_performed",
        "verifier_pass",
        "gate_pass",
    }.intersection(payload)
    if forbidden:
        raise CampaignError(
            "campaign events cannot claim accepted, review, verifier, gate, "
            "or promotion authority",
            code="campaign_authority_claim_forbidden",
            remediation=(
                "Remove authority fields; campaign events are review context only."
            ),
            details={"forbidden_fields": ",".join(sorted(forbidden))},
        )
    return dict(payload)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _safe_text(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text field must be non-empty")
    return normalized


def _campaign_attempt_id(campaign: ResearchCampaign, attempt_number: int) -> str:
    return validate_artifact_id(f"{campaign.campaign_id}.attempt.{attempt_number}")


def _campaign_workflow_id(campaign: ResearchCampaign) -> str:
    for attempt in reversed(campaign.attempts):
        for ref in attempt.workflow_refs:
            if "/" not in ref and "\\" not in ref and not ref.startswith("."):
                return validate_artifact_id(ref)
    return validate_artifact_id(f"workflow.{campaign.issue_id}.campaign")


def _previous_failures(
    campaign: ResearchCampaign,
) -> tuple[CampaignPreviousFailure, ...]:
    failures: list[CampaignPreviousFailure] = []
    for attempt in campaign.attempts:
        summary = _attempt_failure_summary(attempt)
        if summary is None:
            continue
        failures.append(
            CampaignPreviousFailure(
                attempt_id=attempt.attempt_id,
                attempted_direction=attempt.attempted_direction,
                outcome=attempt.outcome,
                summary=summary,
                evidence_refs=attempt.check_report_refs,
            )
        )
    return tuple(failures)


def _attempt_failure_summary(attempt: CampaignAttempt) -> str | None:
    if attempt.outcome.value == "failure":
        return attempt.failure_summary
    if attempt.outcome.value == "inconclusive":
        return attempt.inconclusive_reason
    if attempt.outcome.value == "blocked":
        return attempt.blocked_reason
    return None


def _proof_obligations(campaign: ResearchCampaign) -> tuple[str, ...]:
    seen: set[str] = set()
    obligations: list[str] = []
    for attempt in campaign.attempts:
        for ref in attempt.proof_obligation_refs:
            if ref in seen:
                continue
            seen.add(ref)
            obligations.append(ref)
    return tuple(obligations)


def _context_refs(campaign: ResearchCampaign) -> tuple[str, ...]:
    seen: set[str] = set()
    refs: list[str] = []
    for attempt in campaign.attempts:
        for ref in (
            *attempt.workflow_refs,
            *attempt.check_report_refs,
            *attempt.handoff_refs,
            *attempt.benchmark_report_refs,
        ):
            if ref in seen:
                continue
            seen.add(ref)
            refs.append(ref)
    return tuple(refs)


def _next_stop_conditions(
    campaign: ResearchCampaign,
) -> tuple[CampaignStopCondition, ...]:
    exhausted = len(campaign.attempts) >= campaign.budget.max_attempts
    generated = CampaignStopCondition(
        condition_id=f"stop.{campaign.campaign_id}.max-attempts",
        kind="max_attempts",
        description=(
            f"Stop when {campaign.budget.max_attempts} attempts have been reached"
        ),
        triggered=exhausted,
        triggered_at=_utc_now() if exhausted else None,
    )
    return (*campaign.stop_conditions, generated)


def _attempt_from_operator_result(
    *,
    campaign: ResearchCampaign,
    attempt_id: str,
    attempt_number: int,
    payload: CampaignOperatorResult,
) -> CampaignAttempt:
    if payload.drafts_created or payload.claims_made:
        outcome = CampaignAttemptOutcome.RESULT
        result_summary = _result_summary(payload)
        failure_summary = None
        inconclusive_reason = None
    elif payload.failures:
        outcome = CampaignAttemptOutcome.FAILURE
        result_summary = None
        failure_summary = "; ".join(
            failure.why_it_failed for failure in payload.failures
        )
        inconclusive_reason = None
    else:
        outcome = CampaignAttemptOutcome.INCONCLUSIVE
        result_summary = None
        failure_summary = None
        inconclusive_reason = "; ".join(payload.remaining_gaps)
    return CampaignAttempt(
        attempt_id=attempt_id,
        campaign_id=campaign.campaign_id,
        attempt_number=attempt_number,
        outcome=outcome,
        policy_mode=campaign.operator_policy.policy_mode,
        attempted_direction=payload.attempted_direction,
        completed_at=_utc_now(),
        result_summary=result_summary,
        failure_summary=failure_summary,
        inconclusive_reason=inconclusive_reason,
        actions_taken=payload.actions_taken,
        workflow_refs=(_campaign_workflow_id(campaign),),
        check_report_refs=payload.checks_requested,
        proof_obligation_refs=campaign_proof_refs_from_result(payload),
        draft_proposal_refs=payload.drafts_created,
        benchmark_report_refs=payload.evidence_refs,
    )


def campaign_proof_refs_from_result(
    payload: CampaignOperatorResult,
) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in (*payload.claims_made, *payload.remaining_gaps)
        if ref.startswith("obligation.") or ref.startswith("gap.")
    )


def _result_summary(payload: CampaignOperatorResult) -> str:
    if payload.claims_made:
        return "; ".join(payload.claims_made)
    if payload.next_recommendation:
        return payload.next_recommendation
    return "Structured campaign operator result imported for review only"


def _ensure_public_result_payload(payload: CampaignOperatorResult) -> None:
    encoded = json.dumps(payload.to_dict(), ensure_ascii=True, sort_keys=True).lower()
    private_markers = (
        "kb/private",
        "kb\\\\private",
        "/private/",
        "\\\\private\\\\",
        "private.",
        "private:",
    )
    if any(marker in encoded for marker in private_markers):
        raise CampaignError(
            "public_only campaign operator results cannot include private refs",
            code="public_private_leak_forbidden",
            remediation="Remove private references or use private_research mode.",
        )


def _ensure_campaign_mutable(campaign: ResearchCampaign) -> None:
    if campaign.status.value in _CAMPAIGN_TERMINAL_STATUSES:
        raise CampaignError(
            "terminal campaigns cannot be modified",
            code="campaign_terminal",
            remediation="Start a new campaign or inspect the terminal campaign.",
        )


def _iter_campaign_scan_files(
    context: RepoContext,
    campaign_id: str,
) -> Iterator[tuple[Path, Path]]:
    base = campaign_path(campaign_id).parent
    root = context.resolve(base)
    if not root.is_dir():
        return
    candidates = sorted(
        target
        for target in root.rglob("*")
        if target.is_file() and target.suffix.lower() in {".json", ".jsonl"}
    )
    for target in candidates:
        relative = Path(repo_relative_posix(context.repo_root, target))
        if relative == campaign_scan_path(campaign_id):
            continue
        yield relative, target


def _invalid_json_code(relative_path: Path) -> str:
    text = relative_path.as_posix()
    if "/operator-results/" in text:
        return "operator_result_json_invalid"
    return "runtime_json_invalid"


def _campaign_policy_mode(campaign: ResearchCampaign) -> str:
    if campaign.operator_policy.policy_mode == "public_only":
        return "public_only"
    if any(attempt.policy_mode == "public_only" for attempt in campaign.attempts):
        return "public_only"
    return "private_research"


def _campaign_stop_conditions(
    campaign: ResearchCampaign,
    scan: CampaignScanResult,
    *,
    max_attempts: int | None,
) -> dict[str, bool]:
    effective_max_attempts = campaign.budget.max_attempts
    if max_attempts is not None:
        effective_max_attempts = min(effective_max_attempts, max_attempts)
    attempt_budget_exhausted = len(campaign.attempts) >= effective_max_attempts
    draft_budget_exhausted = _draft_budget_exhausted(campaign)
    return {
        "human_pause_requested": campaign.status is CampaignStatus.PAUSED,
        "unsafe_runtime_output": scan.run_blocked,
        "repeated_failure_without_justification": any(
            finding.code == "repeated_failure" and finding.severity == "blocker"
            for finding in scan.findings
        ),
        "reviewable_draft_created": draft_budget_exhausted,
        "all_budget_exhausted": attempt_budget_exhausted or draft_budget_exhausted,
    }


def _draft_budget_exhausted(campaign: ResearchCampaign) -> bool:
    if campaign.budget.max_draft_outputs is None:
        return False
    return _draft_output_count(campaign) >= campaign.budget.max_draft_outputs


def _draft_output_count(campaign: ResearchCampaign) -> int:
    return sum(len(attempt.draft_proposal_refs) for attempt in campaign.attempts)


def _repeated_failure_directions(campaign: ResearchCampaign) -> tuple[str, ...]:
    if campaign.budget.max_failure_repeats is None:
        return ()
    counts: dict[str, int] = {}
    for attempt in campaign.attempts:
        if attempt.outcome is not CampaignAttemptOutcome.FAILURE:
            continue
        key = attempt.attempted_direction.strip().lower()
        counts[key] = counts.get(key, 0) + 1
    return tuple(
        direction
        for direction, count in sorted(counts.items())
        if count > campaign.budget.max_failure_repeats
    )


class _CampaignRuntimeScanner:
    def __init__(self, *, campaign: ResearchCampaign) -> None:
        self.campaign = campaign
        self.policy_mode = _campaign_policy_mode(campaign)
        self.findings: list[CampaignScanFinding] = []
        self._seen: set[tuple[str, str, int | None, str | None]] = set()

    def scan_json_file(
        self,
        text: str,
        *,
        source_path: str,
        invalid_code: str,
    ) -> object | None:
        self.scan_text(text, source_path=source_path)
        try:
            parsed = cast(object, json.loads(text))
        except json.JSONDecodeError as exc:
            self._add(
                invalid_code,
                source_path=source_path,
                line=exc.lineno,
                severity="blocker",
            )
            return None
        self.scan_json(parsed, source_path=source_path)
        return parsed

    def scan_events_jsonl(self, text: str, *, source_path: str) -> None:
        self.scan_text(text, source_path=source_path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                self._add(
                    "events_json_invalid",
                    source_path=source_path,
                    line=line_number,
                    severity="blocker",
                )
                continue
            self.scan_json(parsed, source_path=source_path)

    def scan_text(self, text: str, *, source_path: str) -> None:
        for finding in scan_provider_log_text(text, path=source_path):
            self._add(
                finding.kind,
                source_path=source_path,
                line=finding.line,
                field_path=finding.key,
                severity="blocker",
            )
        if _ACCEPTED_PATH_PATTERN.search(text):
            self._add(
                "accepted_write_attempt",
                source_path=source_path,
                severity="blocker",
            )
        if _AUTHORITY_TEXT_PATTERN.search(text):
            self._add(
                "authority_claim",
                source_path=source_path,
                severity="blocker",
            )
        if self.policy_mode == "public_only" and _PRIVATE_PATH_PATTERN.search(text):
            self._add(
                "private_reference_in_public_mode",
                source_path=source_path,
                severity="blocker",
            )

    def scan_json(self, value: object, *, source_path: str) -> None:
        for field_path, scalar in _walk_json(value):
            key = field_path[-1] if field_path else ""
            normalized_key = _normalize_key(key)
            path_text = ".".join(field_path)
            if normalized_key in _PROVIDER_PAYLOAD_KEYS:
                self._add(
                    "provider_payload",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if normalized_key in _ENVIRONMENT_DUMP_KEYS:
                self._add(
                    "environment_dump",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if normalized_key in _AUTHORITY_BOOLEAN_KEYS and _truthy_authority(scalar):
                self._add(
                    _authority_code(normalized_key),
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if isinstance(scalar, str) and _AUTHORITY_TEXT_PATTERN.search(scalar):
                self._add(
                    "authority_claim",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )
            if isinstance(scalar, str) and _ACCEPTED_PATH_PATTERN.search(scalar):
                self._add(
                    "accepted_write_attempt",
                    source_path=source_path,
                    field_path=path_text,
                    severity="blocker",
                )

    def scan_budget_state(self) -> None:
        for direction in _repeated_failure_directions(self.campaign):
            self._add(
                "repeated_failure",
                source_path=campaign_path(self.campaign.campaign_id).as_posix(),
                field_path=direction,
                severity="blocker",
            )

    def _add(
        self,
        code: str,
        *,
        source_path: str,
        severity: Literal["warning", "blocker"],
        line: int | None = None,
        field_path: str | None = None,
    ) -> None:
        marker = (code, source_path, line, field_path)
        if marker in self._seen:
            return
        self._seen.add(marker)
        self.findings.append(
            CampaignScanFinding(
                code=code,
                severity=severity,
                message=_CAMPAIGN_SCAN_FINDING_MESSAGES.get(
                    code,
                    f"campaign runtime scanner finding: {code}",
                ),
                source_path=source_path,
                line=line,
                field_path=field_path,
            )
        )


def _walk_json(
    value: object,
    path: tuple[str, ...] = (),
) -> Iterator[tuple[tuple[str, ...], object]]:
    yield path, value
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            yield from _walk_json(child, (*path, str(raw_key)))
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, (*path, str(index)))


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(".", "_")


def _truthy_authority(value: object) -> bool:
    if value is True:
        return True
    if not isinstance(value, str):
        return False
    return value.strip().lower() in {
        "true",
        "accepted",
        "approved",
        "human_reviewed",
        "promote",
        "promotion_performed",
        "verifier_pass",
    }


def _authority_code(normalized_key: str) -> str:
    if normalized_key in {"accepted", "accepted_status", "artifact_status"}:
        return "accepted_authority_overclaim"
    if normalized_key == "accepted_refutation":
        return "accepted_refutation_overclaim"
    if normalized_key in {"accepted_write", "accepted_write_performed"}:
        return "accepted_write_attempt"
    if normalized_key in {
        "human_review",
        "human_review_created",
        "human_reviewed",
        "review_state",
    }:
        return "human_review_overclaim"
    if normalized_key in {"gate_pass", "verifier_pass", "verifier_result_mutated"}:
        return "gate_verifier_overclaim"
    if normalized_key in {
        "promote",
        "promotion",
        "promotion_authority",
        "promotion_performed",
    }:
        return "promotion_overclaim"
    return "authority_claim"


def _validate_output_path(value: str | Path) -> Path:
    normalized = normalize_repo_path(str(value))
    if not normalized or normalized == ".":
        raise CampaignError(
            "operator task export path must be repository-local",
            code="invalid_export_path",
            remediation="Pass --out with a repository-local .json path.",
        )
    path = Path(normalized)
    parts = Path(normalized).parts
    if (
        path.is_absolute()
        or normalized.startswith("../")
        or normalized == ".."
        or ".." in parts
    ):
        raise CampaignError(
            "operator task export path must be repository-local",
            code="invalid_export_path",
            remediation="Pass --out with a repository-local .json path.",
        )
    if path.suffix.lower() != ".json":
        raise CampaignError(
            "operator task export path must end in .json",
            code="invalid_export_path",
            remediation="Pass --out with a repository-local .json path.",
        )
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise CampaignError(
            "operator task export path must not be an accepted KB path",
            code="accepted_write_forbidden",
            remediation="Use runtime storage or review-context export paths only.",
        )
    return path


def _validate_output_dir_path(value: str | Path) -> Path:
    normalized = normalize_repo_path(str(value))
    if not normalized or normalized == ".":
        raise CampaignError(
            "campaign handoff output directory must be repository-local",
            code="invalid_handoff_path",
            remediation="Pass --out with a repository-local directory path.",
        )
    path = Path(normalized)
    parts = path.parts
    if (
        path.is_absolute()
        or normalized.startswith("../")
        or normalized == ".."
        or ".." in parts
    ):
        raise CampaignError(
            "campaign handoff output directory must be repository-local",
            code="invalid_handoff_path",
            remediation="Pass --out with a repository-local directory path.",
        )
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise CampaignError(
            "campaign handoff output directory must not be an accepted KB path",
            code="accepted_write_forbidden",
            remediation="Use runtime storage or review-context export paths only.",
        )
    return path


def _ensure_repo_local(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise CampaignError(
            "campaign target must stay repository-local",
            code="invalid_campaign_path",
            remediation="Use the controlled .cosheaf/campaigns runtime path.",
        ) from exc
    relative = repo_relative_posix(context.repo_root, target)
    if relative.startswith("kb/accepted/") or "/accepted/" in relative:
        raise CampaignError(
            "campaign target must not be an accepted KB path",
            code="accepted_write_forbidden",
            remediation="Use runtime storage or review-context export paths only.",
        )


__all__ = [
    "CAMPAIGN_RUNTIME_ROOT",
    "CAMPAIGN_SCAN_KIND",
    "CampaignAttemptWriteResult",
    "CampaignHandoffResult",
    "CampaignReviewMetrics",
    "CampaignRunResult",
    "CampaignScanFinding",
    "CampaignScanResult",
    "CampaignOperatorTaskExportResult",
    "CampaignScorecardResult",
    "CampaignWriteResult",
    "append_campaign_attempt",
    "append_campaign_event",
    "build_campaign_handoff",
    "build_campaign_next_result",
    "build_campaign_operator_task",
    "build_campaign_review_metrics",
    "campaign_attempt_path",
    "campaign_events_path",
    "campaign_handoff_path",
    "campaign_operator_result_path",
    "campaign_path",
    "campaign_scan_path",
    "campaign_scorecard_path",
    "export_campaign_operator_task",
    "finalize_campaign",
    "import_campaign_operator_result",
    "load_campaign",
    "next_campaign_operator_task",
    "pause_campaign",
    "resume_campaign",
    "run_campaign",
    "scan_campaign",
    "show_campaign_scorecard",
    "start_campaign",
    "write_campaign",
]
