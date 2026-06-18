"""Static Markdown/JSON reports for review-context runtime records."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from pydantic import Field

from cosheaf.benchmark import load_benchmark_run
from cosheaf.campaigns.storage import build_campaign_scorecard, load_campaign
from cosheaf.core.paths import normalize_repo_path
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import WorkflowRecord, load_workflow

STATIC_REPORT_AUTHORITY_NOTICE = (
    "Static reports are review context only; they are not proof, source "
    "metadata, human review, verifier pass, gate pass, accepted status, "
    "accepted theorem/refutation, or promotion authority."
)


class StaticReportError(ValueError):
    """Expected static report generation failure."""


class StaticReportSubject(StrEnum):
    """Supported report subjects."""

    WORKFLOW = "workflow"
    CAMPAIGN = "campaign"
    BENCHMARK = "benchmark"


class StaticReportResult(MemoryModel):
    """Result for one static report directory."""

    schema_version: Literal[1] = 1
    kind: Literal["static_report"] = "static_report"
    subject: StaticReportSubject
    record_id: str
    out_dir: str
    files: dict[str, str] = Field(default_factory=dict)
    public_only: bool = False
    accepted_write_performed: Literal[False] = False
    authority_notice: str = STATIC_REPORT_AUTHORITY_NOTICE


def write_workflow_report(
    context: RepoContext,
    workflow_id: str,
    out_dir: Path,
    *,
    public_only: bool = False,
) -> StaticReportResult:
    """Write a static report for one workflow."""
    workflow = load_workflow(context, workflow_id)
    if public_only:
        _reject_private_markers(workflow.to_dict())
    metrics = _workflow_metrics(workflow)
    authority = _workflow_authority_findings(workflow)
    files = _write_static_files(
        context,
        out_dir,
        summary=_summary_markdown("Workflow", workflow.workflow_id, metrics),
        metrics=metrics,
        authority_findings=authority,
        memory_changes={
            "memory_update_performed": False,
            "note": "report generation does not update memory weights",
        },
        checker_matrix={
            "gate_or_checker_steps": [
                {"action": step.action, "status": step.status}
                for step in workflow.steps
                if "gate" in step.action.lower() or "checker" in step.action.lower()
            ]
        },
        review_handoff_summary=_review_markdown(
            "Workflow",
            workflow.workflow_id,
            workflow.status.value,
            metrics,
        ),
    )
    return StaticReportResult(
        subject=StaticReportSubject.WORKFLOW,
        record_id=workflow.workflow_id,
        out_dir=_validate_output_dir(context, out_dir).as_posix(),
        files=files,
        public_only=public_only,
    )


def write_campaign_report(
    context: RepoContext,
    campaign_id: str,
    out_dir: Path,
    *,
    public_only: bool = False,
) -> StaticReportResult:
    """Write a static report for one campaign."""
    campaign = load_campaign(context, campaign_id).campaign
    if public_only:
        _reject_private_markers(campaign.to_dict())
    scorecard = build_campaign_scorecard(campaign)
    metrics = scorecard.to_dict()
    authority = {
        "risk_findings": [finding.to_dict() for finding in campaign.risk_findings],
        "accepted_write_performed": False,
    }
    files = _write_static_files(
        context,
        out_dir,
        summary=_summary_markdown("Campaign", campaign.campaign_id, metrics),
        metrics=metrics,
        authority_findings=authority,
        memory_changes={
            "memory_update_performed": False,
            "repeat_failure_count": _repeat_failure_count(campaign),
        },
        checker_matrix={
            "check_report_count": scorecard.check_report_count,
            "check_report_refs": sorted(
                {
                    ref
                    for attempt in campaign.attempts
                    for ref in attempt.check_report_refs
                }
            ),
        },
        review_handoff_summary=_review_markdown(
            "Campaign",
            campaign.campaign_id,
            campaign.status.value,
            metrics,
        ),
    )
    return StaticReportResult(
        subject=StaticReportSubject.CAMPAIGN,
        record_id=campaign.campaign_id,
        out_dir=_validate_output_dir(context, out_dir).as_posix(),
        files=files,
        public_only=public_only,
    )


def write_benchmark_static_report(
    context: RepoContext,
    run_id: str,
    out_dir: Path,
    *,
    public_only: bool = False,
) -> StaticReportResult:
    """Write a static report for one benchmark run."""
    run = load_benchmark_run(context, run_id)
    metrics = run.metrics.to_dict()
    files = _write_static_files(
        context,
        out_dir,
        summary=_summary_markdown("Benchmark", run.run_id, metrics),
        metrics=metrics,
        authority_findings={
            "authority_violation_count": run.metrics.authority_violation_count,
            "private_leak_count": run.metrics.private_leak_count,
            "accepted_write_performed": run.accepted_write_performed,
            "yaml_artifacts_mutated": run.yaml_artifacts_mutated,
        },
        memory_changes={
            "memory_update_performed": False,
            "failure_reuse_rate": run.metrics.failure_reuse_rate,
        },
        checker_matrix={
            "checker_matrix_accuracy": run.metrics.checker_matrix_accuracy,
            "components": [
                {
                    "name": component.name.value,
                    "passed": component.passed,
                    "skipped_count": component.skipped_count,
                }
                for component in run.components
            ],
        },
        review_handoff_summary=_review_markdown(
            "Benchmark",
            run.run_id,
            "pass" if run.passed else "fail",
            metrics,
        ),
    )
    return StaticReportResult(
        subject=StaticReportSubject.BENCHMARK,
        record_id=run.run_id,
        out_dir=_validate_output_dir(context, out_dir).as_posix(),
        files=files,
        public_only=public_only,
    )


def _write_static_files(
    context: RepoContext,
    out_dir: Path,
    *,
    summary: str,
    metrics: dict[str, Any],
    authority_findings: dict[str, Any],
    memory_changes: dict[str, Any],
    checker_matrix: dict[str, Any],
    review_handoff_summary: str,
) -> dict[str, str]:
    relative_dir = _validate_output_dir(context, out_dir)
    target_dir = context.resolve(relative_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    payloads: dict[str, str | dict[str, Any]] = {
        "summary.md": summary,
        "metrics.json": metrics,
        "authority_findings.json": authority_findings,
        "memory_changes.json": memory_changes,
        "checker_matrix.json": checker_matrix,
        "review_handoff_summary.md": review_handoff_summary,
    }
    files: dict[str, str] = {}
    for name, payload in payloads.items():
        path = relative_dir / name
        target = context.resolve(path)
        if isinstance(payload, str):
            target.write_text(payload, encoding="utf-8", newline="\n")
        else:
            target.write_text(_json(payload), encoding="utf-8", newline="\n")
        files[name] = path.as_posix()
    return files


def _workflow_metrics(workflow: WorkflowRecord) -> dict[str, Any]:
    return {
        "workflow_id": workflow.workflow_id,
        "status": workflow.status.value,
        "step_count": len(workflow.steps),
        "evidence_ref_count": len(workflow.evidence_refs),
        "failure_count": workflow.failure_summary.failure_count,
        "blocker_count": len(workflow.failure_summary.blocker_details),
        "readiness": None if workflow.readiness is None else workflow.readiness.value,
    }


def _workflow_authority_findings(workflow: WorkflowRecord) -> dict[str, Any]:
    return {
        "accepted_write_blocks": [
            step.step_number
            for step in workflow.steps
            if step.output_refs.get("error_code") == "ACCEPTED_WRITE_BLOCKED"
        ],
        "private_warnings": [
            warning for step in workflow.steps for warning in step.warnings
        ],
        "accepted_write_performed": False,
    }


def _summary_markdown(subject: str, record_id: str, metrics: dict[str, Any]) -> str:
    lines = [
        f"# {subject} Report",
        "",
        f"- id: `{record_id}`",
        f"- authority: {STATIC_REPORT_AUTHORITY_NOTICE}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in sorted(metrics.items()):
        if isinstance(value, dict | list):
            continue
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def _review_markdown(
    subject: str,
    record_id: str,
    status: str,
    metrics: dict[str, Any],
) -> str:
    return (
        f"# {subject} Review Handoff Summary\n\n"
        f"- id: `{record_id}`\n"
        f"- status: `{status}`\n"
        f"- metric_count: `{len(metrics)}`\n"
        f"- authority: {STATIC_REPORT_AUTHORITY_NOTICE}\n"
    )


def _repeat_failure_count(campaign: Any) -> int:
    directions = [
        attempt.attempted_direction.strip().lower()
        for attempt in campaign.attempts
        if attempt.outcome.value == "failure"
    ]
    return len(directions) - len(set(directions))


def _validate_output_dir(context: RepoContext, out_dir: Path) -> Path:
    normalized = normalize_repo_path(str(out_dir))
    if not normalized or normalized == ".":
        raise StaticReportError("report output directory must be repository-local")
    relative = Path(normalized)
    if (
        Path(out_dir).is_absolute()
        or PureWindowsPath(str(out_dir)).is_absolute()
        or normalized.startswith("../")
        or normalized == ".."
        or ".." in relative.parts
    ):
        raise StaticReportError("report output directory must be repository-local")
    if normalized.startswith("kb/accepted/") or "/accepted/" in normalized:
        raise StaticReportError("static reports must not be written to accepted KB")
    target = context.resolve(relative)
    root = context.repo_root.resolve()
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise StaticReportError("report output directory escapes repository")
    if target.exists() and not target.is_dir():
        raise StaticReportError("report output path exists and is not a directory")
    return relative


def _reject_private_markers(payload: object) -> None:
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True).lower()
    markers = ("kb/private", "kb\\\\private", "/private/", "\\\\private\\\\")
    if any(marker in text for marker in markers):
        raise StaticReportError("public-only static report would include private refs")


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


__all__ = [
    "STATIC_REPORT_AUTHORITY_NOTICE",
    "StaticReportError",
    "StaticReportResult",
    "StaticReportSubject",
    "write_benchmark_static_report",
    "write_campaign_report",
    "write_workflow_report",
]
