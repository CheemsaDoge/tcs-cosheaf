"""Runtime storage for bounded research campaigns."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

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
from cosheaf.storage.repo import RepoContext

CAMPAIGN_RUNTIME_ROOT = Path(".cosheaf") / "campaigns"


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
    "CampaignAttemptWriteResult",
    "CampaignOperatorTaskExportResult",
    "CampaignScorecardResult",
    "CampaignWriteResult",
    "append_campaign_attempt",
    "append_campaign_event",
    "build_campaign_next_result",
    "build_campaign_operator_task",
    "campaign_attempt_path",
    "campaign_events_path",
    "campaign_operator_result_path",
    "campaign_path",
    "campaign_scorecard_path",
    "export_campaign_operator_task",
    "finalize_campaign",
    "import_campaign_operator_result",
    "load_campaign",
    "next_campaign_operator_task",
    "show_campaign_scorecard",
    "start_campaign",
    "write_campaign",
]
