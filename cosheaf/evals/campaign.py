"""Deterministic campaign handoff/eval harness."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.campaigns import (
    CAMPAIGN_AUTHORITY_NOTICE,
    CampaignAttempt,
    CampaignAttemptOutcome,
    CampaignBudget,
    CampaignOperatorResult,
    build_campaign_handoff,
    import_campaign_operator_result,
    run_campaign,
    start_campaign,
)
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext

DEFAULT_CAMPAIGN_EVAL_CASES = Path("evals") / "campaign" / "cases.yaml"
_STARTED_AT = datetime(2026, 6, 18, 2, 0, tzinfo=UTC)
_ENDED_AT = datetime(2026, 6, 18, 2, 5, tzinfo=UTC)


class CampaignEvalError(ValueError):
    """Raised for expected campaign eval loading failures."""


class CampaignEvalKind(StrEnum):
    """Supported campaign eval scenarios."""

    REVIEWABLE_HANDOFF = "reviewable_handoff"
    UNSAFE_OUTPUT_BLOCKED = "unsafe_output_blocked"
    BUDGET_STOP_ACCURACY = "budget_stop_accuracy"
    OPERATOR_CONTRACT_BOUNDARY = "operator_contract_boundary"


class CampaignEvalCase(MemoryModel):
    """One deterministic campaign eval case."""

    id: str | None = None
    kind: CampaignEvalKind

    @field_validator("id")
    @classmethod
    def _id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("case id must be non-empty")
        return normalized


class CampaignEvalCaseResult(MemoryModel):
    """One campaign eval case result."""

    id: str
    kind: CampaignEvalKind
    passed: bool
    attempt_count: int = 0
    unique_direction_count: int = 0
    repeat_failure_count: int = 0
    reviewable_draft_count: int = 0
    checked_evidence_count: int = 0
    gap_count: int = 0
    unsafe_output_count: int = 0
    budget_stop_accuracy: bool = False
    operator_contract_validity: bool = False
    accepted_write_performed: bool = False
    failures: list[str]


class CampaignEvalMetrics(MemoryModel):
    """Aggregate campaign eval metrics."""

    attempt_count: int
    unique_direction_count: int
    repeat_failure_count: int
    reviewable_draft_count: int
    checked_evidence_count: int
    gap_count: int
    unsafe_output_count: int
    budget_stop_accuracy: float
    operator_contract_validity: float
    accepted_write_violation_count: int


class CampaignEvalReport(MemoryModel):
    """Campaign eval report."""

    schema_version: int = 1
    kind: str = "campaign_eval"
    case_count: int
    passed: bool
    metrics: CampaignEvalMetrics
    cases: list[CampaignEvalCaseResult]
    authority_notice: str = CAMPAIGN_AUTHORITY_NOTICE

    def to_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
        ) + "\n"


@dataclass(frozen=True)
class CampaignEvalSuite:
    """Loaded campaign eval cases."""

    cases: list[CampaignEvalCase]


def resolve_campaign_eval_case_path(context: RepoContext, cases_path: Path) -> Path:
    """Resolve explicit or default campaign eval case path."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise CampaignEvalError(
            "campaign eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise CampaignEvalError("campaign eval case file must be repository-local")
    return resolved


def load_campaign_eval_suite(path: Path) -> CampaignEvalSuite:
    """Load campaign eval cases from YAML."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise CampaignEvalError(f"could not read eval cases: {path}") from exc
    if not isinstance(raw, dict):
        raise CampaignEvalError("campaign eval cases must be a mapping")
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list):
        raise CampaignEvalError("campaign eval cases require a cases list")
    cases = [CampaignEvalCase.model_validate(item) for item in cases_raw]
    return CampaignEvalSuite(cases=cases)


def run_campaign_eval_suite(
    context: RepoContext,
    suite: CampaignEvalSuite,
) -> CampaignEvalReport:
    """Run deterministic campaign eval cases."""
    _ = context
    results = [_run_case(case) for case in suite.cases]
    case_count = len(results)
    metrics = CampaignEvalMetrics(
        attempt_count=sum(result.attempt_count for result in results),
        unique_direction_count=sum(
            result.unique_direction_count for result in results
        ),
        repeat_failure_count=sum(result.repeat_failure_count for result in results),
        reviewable_draft_count=sum(
            result.reviewable_draft_count for result in results
        ),
        checked_evidence_count=sum(
            result.checked_evidence_count for result in results
        ),
        gap_count=sum(result.gap_count for result in results),
        unsafe_output_count=sum(result.unsafe_output_count for result in results),
        budget_stop_accuracy=_rate(results, "budget_stop_accuracy"),
        operator_contract_validity=_rate(results, "operator_contract_validity"),
        accepted_write_violation_count=sum(
            1 for result in results if result.accepted_write_performed
        ),
    )
    return CampaignEvalReport(
        case_count=case_count,
        passed=all(result.passed for result in results),
        metrics=metrics,
        cases=results,
    )


def _run_case(case: CampaignEvalCase) -> CampaignEvalCaseResult:
    with tempfile.TemporaryDirectory(prefix="cosheaf-campaign-eval-") as temp_dir:
        context = RepoContext(Path(temp_dir))
        return _evaluate_case(context, case)


def _evaluate_case(
    context: RepoContext,
    case: CampaignEvalCase,
) -> CampaignEvalCaseResult:
    failures: list[str] = []
    campaign_id = f"campaign.issue.eval.{case.kind.value.replace('_', '-')}"
    campaign_id = campaign_id.replace("-", ".")
    budget = CampaignBudget(max_attempts=4, max_failure_repeats=1)
    if case.kind is CampaignEvalKind.BUDGET_STOP_ACCURACY:
        budget = CampaignBudget(max_attempts=1)
    start_campaign(
        context,
        issue_id="issue.eval.campaign",
        campaign_id=campaign_id,
        budget=budget,
        now=_STARTED_AT,
    )

    if case.kind is CampaignEvalKind.REVIEWABLE_HANDOFF:
        _append_failure_attempt(context, campaign_id, 1)
        _append_result_attempt(context, campaign_id, 2)
        handoff = build_campaign_handoff(context, campaign_id, "reviews/campaign")
        metrics = handoff.metrics
        if metrics.reviewable_draft_count < 1:
            failures.append("expected reviewable draft in campaign handoff")
        if handoff.accepted_write_performed:
            failures.append("campaign handoff performed an accepted write")
        operator_contract_validity = metrics.operator_contract_validity
    elif case.kind is CampaignEvalKind.UNSAFE_OUTPUT_BLOCKED:
        _append_failure_attempt(context, campaign_id, 1)
        _append_failure_attempt(context, campaign_id, 2)
        unsafe = (
            context.repo_root
            / ".cosheaf"
            / "campaigns"
            / campaign_id
            / "operator-results"
            / "unsafe.json"
        )
        unsafe.parent.mkdir(parents=True, exist_ok=True)
        unsafe.write_text(
            json.dumps({"accepted_status": True, "path": "kb/accepted/claims/x.yaml"}),
            encoding="utf-8",
        )
        handoff = build_campaign_handoff(context, campaign_id, "reviews/campaign")
        metrics = handoff.metrics
        if metrics.unsafe_output_count < 1:
            failures.append("expected unsafe output blocker in handoff metrics")
        operator_contract_validity = not metrics.operator_contract_validity
    elif case.kind is CampaignEvalKind.BUDGET_STOP_ACCURACY:
        _append_result_attempt(context, campaign_id, 1)
        run = run_campaign(context, campaign_id, max_attempts=1)
        handoff = build_campaign_handoff(context, campaign_id, "reviews/campaign")
        metrics = handoff.metrics
        if not run.stop_conditions["all_budget_exhausted"]:
            failures.append("expected budget exhaustion stop condition")
        if not metrics.budget_stop_accuracy:
            failures.append("expected budget stop accuracy metric")
        operator_contract_validity = metrics.operator_contract_validity
    elif case.kind is CampaignEvalKind.OPERATOR_CONTRACT_BOUNDARY:
        rejected = False
        try:
            CampaignOperatorResult.model_validate(
                {
                    "attempted_direction": "Try authority overclaim",
                    "drafts_created": ["kb/private/draft/claims/claim.fixture.yaml"],
                    "authority_claims": {"accepted_status": True},
                }
            )
        except ValueError:
            rejected = True
        valid_payload = CampaignOperatorResult.model_validate(
            {
                "attempted_direction": "Try bounded draft",
                "actions_taken": ["cosheaf validate"],
                "artifacts_read": ["definition.graph"],
                "drafts_created": ["kb/private/draft/claims/claim.fixture.yaml"],
                "claims_made": ["Draft only; needs human review."],
                "checks_requested": ["cosheaf validate"],
                "evidence_refs": ["reviews/runs/campaign-result.json"],
                "authority_claims": {"accepted_status": False},
            }
        )
        imported = import_campaign_operator_result(context, campaign_id, valid_payload)
        handoff = build_campaign_handoff(context, campaign_id, "reviews/campaign")
        metrics = handoff.metrics
        if not rejected:
            failures.append("expected authority overclaim rejection")
        if imported.accepted_write_performed:
            failures.append("operator import performed an accepted write")
        operator_contract_validity = rejected and not imported.accepted_write_performed
    else:  # pragma: no cover - StrEnum exhaustiveness guard
        metrics = build_campaign_handoff(
            context,
            campaign_id,
            "reviews/campaign",
        ).metrics
        failures.append(f"unsupported campaign eval case: {case.kind}")
        operator_contract_validity = False

    budget_stop_accuracy = metrics.budget_stop_accuracy
    passed = not failures
    return CampaignEvalCaseResult(
        id=case.id or f"campaign.{case.kind.value}",
        kind=case.kind,
        passed=passed,
        attempt_count=metrics.attempt_count,
        unique_direction_count=metrics.unique_direction_count,
        repeat_failure_count=metrics.repeat_failure_count,
        reviewable_draft_count=metrics.reviewable_draft_count,
        checked_evidence_count=metrics.checked_evidence_count,
        gap_count=metrics.gap_count,
        unsafe_output_count=metrics.unsafe_output_count,
        budget_stop_accuracy=budget_stop_accuracy,
        operator_contract_validity=operator_contract_validity,
        accepted_write_performed=False,
        failures=failures,
    )


def _append_failure_attempt(
    context: RepoContext,
    campaign_id: str,
    attempt_number: int,
) -> None:
    from cosheaf.campaigns import append_campaign_attempt

    append_campaign_attempt(
        context,
        campaign_id,
        CampaignAttempt(
            attempt_id=f"{campaign_id}.attempt.{attempt_number}",
            campaign_id=campaign_id,
            attempt_number=attempt_number,
            outcome=CampaignAttemptOutcome.FAILURE,
            attempted_direction="Try direct induction",
            completed_at=_ENDED_AT,
            failure_summary="The induction hypothesis is too weak",
            proof_obligation_refs=("gap.issue.eval.campaign.induction",),
            check_report_refs=(".cosheaf/reports/checker.json",),
        ),
    )


def _append_result_attempt(
    context: RepoContext,
    campaign_id: str,
    attempt_number: int,
) -> None:
    from cosheaf.campaigns import append_campaign_attempt

    append_campaign_attempt(
        context,
        campaign_id,
        CampaignAttempt(
            attempt_id=f"{campaign_id}.attempt.{attempt_number}",
            campaign_id=campaign_id,
            attempt_number=attempt_number,
            outcome=CampaignAttemptOutcome.RESULT,
            attempted_direction="Try source-reviewed draft",
            completed_at=_ENDED_AT,
            result_summary="Draft proposal ready for human review only",
            check_report_refs=(".cosheaf/reports/validate.json",),
            proof_obligation_refs=("obligation.issue.eval.campaign.review",),
            draft_proposal_refs=("kb/private/draft/claims/claim.fixture.yaml",),
        ),
    )


def _rate(results: list[CampaignEvalCaseResult], field: str) -> float:
    if not results:
        return 1.0
    return sum(1 for result in results if bool(getattr(result, field))) / len(results)


__all__ = [
    "DEFAULT_CAMPAIGN_EVAL_CASES",
    "CampaignEvalCase",
    "CampaignEvalCaseResult",
    "CampaignEvalError",
    "CampaignEvalKind",
    "CampaignEvalMetrics",
    "CampaignEvalReport",
    "CampaignEvalSuite",
    "load_campaign_eval_suite",
    "resolve_campaign_eval_case_path",
    "run_campaign_eval_suite",
]
