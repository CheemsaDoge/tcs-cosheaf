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
    CampaignBudget,
    CampaignError,
    CampaignOperatorPolicy,
    CampaignScorecard,
    CampaignStatus,
    ResearchCampaign,
    build_campaign_scorecard,
)
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import repo_relative_posix
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


def _write_scorecard(context: RepoContext, campaign: ResearchCampaign) -> Path:
    scorecard = build_campaign_scorecard(campaign)
    relative_path = campaign_scorecard_path(campaign.campaign_id)
    target = context.resolve(relative_path)
    _ensure_repo_local(context, target)
    _write_json(target, scorecard)
    return relative_path


def _write_json(
    target: Path,
    model: ResearchCampaign | CampaignAttempt | CampaignScorecard,
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
    "CampaignScorecardResult",
    "CampaignWriteResult",
    "append_campaign_attempt",
    "append_campaign_event",
    "campaign_attempt_path",
    "campaign_events_path",
    "campaign_path",
    "campaign_scorecard_path",
    "finalize_campaign",
    "load_campaign",
    "show_campaign_scorecard",
    "start_campaign",
    "write_campaign",
]
