"""Side-by-side comparisons for review-context runtime records."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

from cosheaf.benchmark import BenchmarkRun, load_benchmark_run
from cosheaf.campaigns.storage import build_campaign_scorecard, load_campaign
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import WorkflowRecord, load_workflow

COMPARE_AUTHORITY_NOTICE = (
    "Comparison reports are analytical review context only; they are not proof, "
    "source metadata, human review, verifier pass, gate pass, accepted status, "
    "accepted theorem/refutation, or promotion authority. Better/worse is "
    "metric-scoped only."
)


class CompareSubject(StrEnum):
    """Supported comparison subjects."""

    WORKFLOW = "workflow"
    CAMPAIGN = "campaign"
    BENCHMARK = "benchmark"


class MetricDelta(MemoryModel):
    """One numeric metric delta."""

    metric: str
    before: int | float
    after: int | float
    delta: int | float
    direction: Literal["up", "down", "same"]


class SafetyRegression(MemoryModel):
    """One safety-relevant regression."""

    code: str
    severity: Literal["warning", "blocker"]
    metric: str
    before: int | float
    after: int | float
    message: str


class CompareResult(MemoryModel):
    """Deterministic comparison output."""

    schema_version: Literal[1] = 1
    kind: Literal["comparison_report"] = "comparison_report"
    subject: CompareSubject
    before_id: str
    after_id: str
    metric_deltas: tuple[MetricDelta, ...]
    evidence_changes: dict[str, Any] = Field(default_factory=dict)
    failure_repeats_avoided: int = 0
    memory_weight_differences: dict[str, Any] = Field(default_factory=dict)
    checker_matrix_differences: dict[str, Any] = Field(default_factory=dict)
    draft_proposal_changes: dict[str, Any] = Field(default_factory=dict)
    benchmark_metric_deltas: tuple[MetricDelta, ...] = ()
    safety_regressions: tuple[SafetyRegression, ...] = ()
    better_is_metric_scoped: Literal[True] = True
    accepted_write_performed: Literal[False] = False
    authority_notice: str = COMPARE_AUTHORITY_NOTICE


def compare_workflows(
    context: RepoContext,
    before_id: str,
    after_id: str,
) -> CompareResult:
    """Compare two persisted workflow records."""
    before = load_workflow(context, before_id)
    after = load_workflow(context, after_id)
    before_metrics = _workflow_metrics(before)
    after_metrics = _workflow_metrics(after)
    deltas = _metric_deltas(before_metrics, after_metrics)
    safety = _safety_regressions(
        before_metrics,
        after_metrics,
        blocker_metrics=("accepted_write_blocked_count", "private_leak_warning_count"),
    )
    return CompareResult(
        subject=CompareSubject.WORKFLOW,
        before_id=before.workflow_id,
        after_id=after.workflow_id,
        metric_deltas=deltas,
        evidence_changes={
            "before_evidence_ref_count": len(before.evidence_refs),
            "after_evidence_ref_count": len(after.evidence_refs),
            "before_actions": _workflow_actions(before),
            "after_actions": _workflow_actions(after),
        },
        failure_repeats_avoided=max(
            0,
            before_metrics["failure_count"] - after_metrics["failure_count"],
        ),
        memory_weight_differences={
            "available": False,
            "reason": "workflow comparison reads workflow records only",
        },
        checker_matrix_differences={
            "gate_or_checker_step_delta": _delta(
                before_metrics["gate_or_checker_step_count"],
                after_metrics["gate_or_checker_step_count"],
            )
        },
        draft_proposal_changes={
            "draft_proposal_ref_delta": _delta(
                before_metrics["draft_proposal_ref_count"],
                after_metrics["draft_proposal_ref_count"],
            )
        },
        safety_regressions=safety,
    )


def compare_campaigns(
    context: RepoContext,
    before_id: str,
    after_id: str,
) -> CompareResult:
    """Compare two persisted research campaign records."""
    before = load_campaign(context, before_id).campaign
    after = load_campaign(context, after_id).campaign
    before_metrics = _campaign_metrics(before)
    after_metrics = _campaign_metrics(after)
    deltas = _metric_deltas(before_metrics, after_metrics)
    safety = _safety_regressions(
        before_metrics,
        after_metrics,
        blocker_metrics=("blocker_count", "unsafe_output_count"),
    )
    return CompareResult(
        subject=CompareSubject.CAMPAIGN,
        before_id=before.campaign_id,
        after_id=after.campaign_id,
        metric_deltas=deltas,
        evidence_changes={
            "check_report_delta": _delta(
                before_metrics["check_report_count"],
                after_metrics["check_report_count"],
            ),
            "proof_obligation_delta": _delta(
                before_metrics["proof_obligation_count"],
                after_metrics["proof_obligation_count"],
            ),
            "handoff_ref_delta": _delta(
                before_metrics["handoff_ref_count"],
                after_metrics["handoff_ref_count"],
            ),
        },
        failure_repeats_avoided=max(
            0,
            before_metrics["repeat_failure_count"]
            - after_metrics["repeat_failure_count"],
        ),
        memory_weight_differences={
            "failure_reuse_delta": _delta(
                before_metrics["repeat_failure_count"],
                after_metrics["repeat_failure_count"],
            )
        },
        checker_matrix_differences={
            "check_report_delta": _delta(
                before_metrics["check_report_count"],
                after_metrics["check_report_count"],
            )
        },
        draft_proposal_changes={
            "draft_proposal_delta": _delta(
                before_metrics["draft_proposal_count"],
                after_metrics["draft_proposal_count"],
            )
        },
        safety_regressions=safety,
    )


def compare_benchmarks(
    context: RepoContext,
    before_id: str,
    after_id: str,
) -> CompareResult:
    """Compare two persisted benchmark runs."""
    before = load_benchmark_run(context, before_id)
    after = load_benchmark_run(context, after_id)
    before_metrics = _benchmark_metrics(before)
    after_metrics = _benchmark_metrics(after)
    deltas = _metric_deltas(before_metrics, after_metrics)
    safety = _safety_regressions(
        before_metrics,
        after_metrics,
        blocker_metrics=("authority_violation_count", "private_leak_count"),
        warning_metrics=("fail_count", "skipped_count"),
    )
    return CompareResult(
        subject=CompareSubject.BENCHMARK,
        before_id=before.run_id,
        after_id=after.run_id,
        metric_deltas=deltas,
        evidence_changes={
            "component_changes": _component_changes(before, after),
        },
        failure_repeats_avoided=0,
        memory_weight_differences={
            "failure_reuse_rate_delta": _delta(
                before_metrics["failure_reuse_rate"],
                after_metrics["failure_reuse_rate"],
            )
        },
        checker_matrix_differences={
            "checker_matrix_accuracy_delta": _delta(
                before_metrics["checker_matrix_accuracy"],
                after_metrics["checker_matrix_accuracy"],
            )
        },
        draft_proposal_changes={
            "review_handoff_validity_delta": _delta(
                before_metrics["review_handoff_validity"],
                after_metrics["review_handoff_validity"],
            )
        },
        benchmark_metric_deltas=deltas,
        safety_regressions=safety,
    )


def _workflow_metrics(workflow: WorkflowRecord) -> dict[str, int]:
    return {
        "step_count": len(workflow.steps),
        "evidence_ref_count": len(workflow.evidence_refs),
        "failure_count": workflow.failure_summary.failure_count,
        "blocker_count": len(workflow.failure_summary.blocker_details),
        "draft_proposal_ref_count": sum(
            1
            for step in workflow.steps
            for value in step.output_refs.values()
            if "draft" in value.lower() or "proposal" in value.lower()
        ),
        "gate_or_checker_step_count": sum(
            1
            for step in workflow.steps
            if "gate" in step.action.lower() or "checker" in step.action.lower()
        ),
        "accepted_write_blocked_count": sum(
            1
            for step in workflow.steps
            if step.output_refs.get("error_code") == "ACCEPTED_WRITE_BLOCKED"
        ),
        "private_leak_warning_count": sum(
            1
            for step in workflow.steps
            for warning in step.warnings
            if "private" in warning.lower()
        ),
    }


def _campaign_metrics(campaign: Any) -> dict[str, int]:
    scorecard = build_campaign_scorecard(campaign)
    directions = [
        attempt.attempted_direction.strip().lower()
        for attempt in campaign.attempts
        if attempt.outcome.value == "failure"
    ]
    repeated = len(directions) - len(set(directions))
    return {
        "attempt_count": scorecard.attempt_count,
        "result_count": scorecard.result_count,
        "failure_count": scorecard.failure_count,
        "inconclusive_count": scorecard.inconclusive_count,
        "blocked_count": scorecard.blocked_count,
        "risk_finding_count": scorecard.risk_finding_count,
        "blocker_count": scorecard.blocker_count,
        "draft_proposal_count": scorecard.draft_proposal_count,
        "check_report_count": scorecard.check_report_count,
        "comparison_count": scorecard.comparison_count,
        "budget_exhausted": int(scorecard.budget_exhausted),
        "repeat_failure_count": repeated,
        "unsafe_output_count": sum(
            1
            for finding in campaign.risk_findings
            if finding.severity.value == "blocker"
        ),
        "proof_obligation_count": sum(
            len(attempt.proof_obligation_refs) for attempt in campaign.attempts
        ),
        "handoff_ref_count": sum(
            len(attempt.handoff_refs) for attempt in campaign.attempts
        ),
    }


def _benchmark_metrics(run: BenchmarkRun) -> dict[str, int | float]:
    return dict(run.metrics.to_dict())


def _metric_deltas(
    before: Mapping[str, int | float],
    after: Mapping[str, int | float],
) -> tuple[MetricDelta, ...]:
    deltas: list[MetricDelta] = []
    for metric in sorted(before.keys() | after.keys()):
        before_value = before.get(metric, 0)
        after_value = after.get(metric, 0)
        if not isinstance(before_value, int | float) or not isinstance(
            after_value,
            int | float,
        ):
            continue
        delta = _delta(before_value, after_value)
        deltas.append(
            MetricDelta(
                metric=metric,
                before=before_value,
                after=after_value,
                delta=delta,
                direction="up" if delta > 0 else "down" if delta < 0 else "same",
            )
        )
    return tuple(deltas)


def _safety_regressions(
    before: Mapping[str, int | float],
    after: Mapping[str, int | float],
    *,
    blocker_metrics: tuple[str, ...],
    warning_metrics: tuple[str, ...] = (),
) -> tuple[SafetyRegression, ...]:
    regressions: list[SafetyRegression] = []
    for metric in blocker_metrics + warning_metrics:
        before_value = before.get(metric, 0)
        after_value = after.get(metric, 0)
        if not isinstance(before_value, int | float) or not isinstance(
            after_value,
            int | float,
        ):
            continue
        if after_value <= before_value:
            continue
        severity: Literal["warning", "blocker"] = (
            "warning" if metric in warning_metrics else "blocker"
        )
        regressions.append(
            SafetyRegression(
                code=f"{metric}_regressed",
                severity=severity,
                metric=metric,
                before=before_value,
                after=after_value,
                message=(
                    f"{metric} increased from {before_value} to {after_value}; "
                    "review before treating quality improvements as useful"
                ),
            )
        )
    return tuple(regressions)


def _workflow_actions(workflow: WorkflowRecord) -> tuple[str, ...]:
    return tuple(step.action for step in workflow.steps)


def _component_changes(
    before: BenchmarkRun,
    after: BenchmarkRun,
) -> tuple[dict[str, Any], ...]:
    before_by_name = {
        component.name.value: component for component in before.components
    }
    after_by_name = {component.name.value: component for component in after.components}
    changes: list[dict[str, Any]] = []
    for name in sorted(before_by_name.keys() | after_by_name.keys()):
        old = before_by_name.get(name)
        new = after_by_name.get(name)
        changes.append(
            {
                "component": name,
                "before_passed": None if old is None else old.passed,
                "after_passed": None if new is None else new.passed,
                "before_skipped_count": 0 if old is None else old.skipped_count,
                "after_skipped_count": 0 if new is None else new.skipped_count,
            }
        )
    return tuple(changes)


def _delta(before: int | float, after: int | float) -> int | float:
    value = after - before
    return round(value, 6) if isinstance(value, float) else value


__all__ = [
    "COMPARE_AUTHORITY_NOTICE",
    "CompareResult",
    "CompareSubject",
    "MetricDelta",
    "SafetyRegression",
    "compare_benchmarks",
    "compare_campaigns",
    "compare_workflows",
]
