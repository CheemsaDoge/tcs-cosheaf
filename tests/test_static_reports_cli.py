from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from typer.testing import CliRunner

from cosheaf.benchmark import (
    BenchmarkComponentName,
    BenchmarkComponentResult,
    BenchmarkMetrics,
    BenchmarkRun,
    BenchmarkSuiteName,
    write_benchmark_run,
)
from cosheaf.campaigns import (
    CampaignAttempt,
    CampaignAttemptOutcome,
    CampaignBudget,
    append_campaign_attempt,
    start_campaign,
)
from cosheaf.cli import app
from cosheaf.reports import (
    StaticReportError,
    write_benchmark_static_report,
    write_campaign_report,
    write_workflow_report,
)
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WorkflowStep,
    append_step,
    load_workflow,
    start_workflow,
    write_workflow,
)

runner = CliRunner()
NOW = datetime(2026, 6, 18, 8, 0, tzinfo=UTC)
REPORT_FILES = {
    "summary.md",
    "metrics.json",
    "authority_findings.json",
    "memory_changes.json",
    "checker_matrix.json",
    "review_handoff_summary.md",
}


def _json(output: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(output))


def test_static_workflow_report_writes_expected_files(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(context, issue_id="issue.report", workflow_id="workflow.report")

    result = write_workflow_report(
        context,
        "workflow.report",
        Path(".cosheaf/static/workflow.report"),
    )

    assert set(result.files) == REPORT_FILES
    for relative in result.files.values():
        assert (tmp_path / relative).is_file()
    assert result.accepted_write_performed is False
    assert "not proof" in result.authority_notice


def test_static_campaign_report_writes_expected_files(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_campaign(
        context,
        issue_id="issue.report",
        campaign_id="campaign.issue.report",
        budget=CampaignBudget(max_attempts=2),
        now=NOW,
    )

    result = write_campaign_report(
        context,
        "campaign.issue.report",
        Path(".cosheaf/static/campaign.report"),
    )

    assert set(result.files) == REPORT_FILES
    for relative in result.files.values():
        assert (tmp_path / relative).is_file()


def test_static_benchmark_report_writes_expected_files(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    _write_benchmark(context, "benchmark.report")

    result = write_benchmark_static_report(
        context,
        "benchmark.report",
        Path(".cosheaf/static/benchmark.report"),
    )

    assert set(result.files) == REPORT_FILES
    for relative in result.files.values():
        assert (tmp_path / relative).is_file()


def test_static_report_rejects_accepted_output(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(context, issue_id="issue.report", workflow_id="workflow.report")

    with pytest.raises(StaticReportError, match="accepted KB"):
        write_workflow_report(
            context,
            "workflow.report",
            Path("kb/accepted/reports/workflow.report"),
        )


def test_public_only_rejects_private_workflow_and_campaign_refs(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    start_workflow(context, issue_id="issue.report", workflow_id="workflow.report")
    workflow = load_workflow(context, "workflow.report")
    write_workflow(
        context,
        append_step(
            workflow,
            WorkflowStep(
                step_number=1,
                action="draft.proposal",
                status="ok",
                output_refs={"proposal": "kb/private/draft/claims/claim.yaml"},
            ),
        ),
    )
    start_campaign(context, issue_id="issue.report", campaign_id="campaign.report")
    append_campaign_attempt(
        context,
        "campaign.report",
        CampaignAttempt(
            attempt_id="campaign.report.attempt.1",
            campaign_id="campaign.report",
            attempt_number=1,
            outcome=CampaignAttemptOutcome.RESULT,
            attempted_direction="Draft a private approach",
            completed_at=NOW,
            result_summary="Private draft proposal ready for review.",
            draft_proposal_refs=("kb/private/draft/claims/claim.yaml",),
        ),
    )

    with pytest.raises(StaticReportError, match="private refs"):
        write_workflow_report(
            context,
            "workflow.report",
            Path(".cosheaf/static/workflow-public"),
            public_only=True,
        )
    with pytest.raises(StaticReportError, match="private refs"):
        write_campaign_report(
            context,
            "campaign.report",
            Path(".cosheaf/static/campaign-public"),
            public_only=True,
        )


def test_static_report_cli_json_smoke(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    _write_benchmark(context, "benchmark.report")

    result = runner.invoke(
        app,
        [
            "report",
            "benchmark",
            "benchmark.report",
            "--out",
            ".cosheaf/static/benchmark.report",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.output)
    assert payload["subject"] == "benchmark"
    assert payload["record_id"] == "benchmark.report"
    assert set(payload["files"]) == REPORT_FILES
    assert payload["accepted_write_performed"] is False


def _write_benchmark(context: RepoContext, run_id: str) -> None:
    write_benchmark_run(
        context,
        BenchmarkRun(
            run_id=run_id,
            suite=BenchmarkSuiteName.SMOKE,
            passed=True,
            metrics=BenchmarkMetrics(pass_count=1, checker_matrix_accuracy=1.0),
            components=(
                BenchmarkComponentResult(
                    name=BenchmarkComponentName.CHECKER_CROSSCHECK,
                    passed=True,
                    case_count=1,
                    pass_count=1,
                    fail_count=0,
                    skipped_count=0,
                ),
            ),
        ),
    )
