from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

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
from cosheaf.compare import (
    COMPARE_AUTHORITY_NOTICE,
    compare_benchmarks,
    compare_campaigns,
    compare_workflows,
)
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WorkflowStep,
    append_step,
    load_workflow,
    start_workflow,
    step_workflow,
    write_workflow,
)

runner = CliRunner()
NOW = datetime(2026, 6, 18, 8, 0, tzinfo=UTC)


def _json(output: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(output))


def test_compare_workflows_highlights_safety_regression(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(context, issue_id="issue.compare", workflow_id="workflow.before")
    step_workflow(context, "workflow.before", action_id="workspace.info")

    start_workflow(context, issue_id="issue.compare", workflow_id="workflow.after")
    step_workflow(context, "workflow.after", action_id="workspace.info")
    after = load_workflow(context, "workflow.after")
    blocked = WorkflowStep(
        step_number=2,
        action="accepted.write",
        status="blocked",
        output_refs={"error_code": "ACCEPTED_WRITE_BLOCKED"},
    )
    write_workflow(context, append_step(after, blocked))

    result = compare_workflows(context, "workflow.before", "workflow.after")

    assert result.subject.value == "workflow"
    assert result.authority_notice == COMPARE_AUTHORITY_NOTICE
    assert any(
        item.metric == "accepted_write_blocked_count"
        for item in result.safety_regressions
    )
    assert result.better_is_metric_scoped is True


def test_compare_campaigns_reports_failure_reuse_and_draft_delta(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    before_id = "campaign.issue.compare.before"
    after_id = "campaign.issue.compare.after"
    start_campaign(
        context,
        issue_id="issue.compare",
        campaign_id=before_id,
        budget=CampaignBudget(max_attempts=3),
        now=NOW,
    )
    for number in (1, 2):
        append_campaign_attempt(
            context,
            before_id,
            CampaignAttempt(
                attempt_id=f"{before_id}.attempt.{number}",
                campaign_id=before_id,
                attempt_number=number,
                outcome=CampaignAttemptOutcome.FAILURE,
                attempted_direction="Try direct induction",
                completed_at=NOW,
                failure_summary="Same route failed",
            ),
        )
    start_campaign(context, issue_id="issue.compare", campaign_id=after_id, now=NOW)
    append_campaign_attempt(
        context,
        after_id,
        CampaignAttempt(
            attempt_id=f"{after_id}.attempt.1",
            campaign_id=after_id,
            attempt_number=1,
            outcome=CampaignAttemptOutcome.RESULT,
            attempted_direction="Try strengthened invariant",
            completed_at=NOW,
            result_summary="Draft proposal ready for review",
            draft_proposal_refs=("kb/private/draft/claims/claim.compare.yaml",),
            check_report_refs=(".cosheaf/reports/checker.json",),
        ),
    )

    result = compare_campaigns(context, before_id, after_id)

    assert result.failure_repeats_avoided == 1
    assert result.draft_proposal_changes["draft_proposal_delta"] == 1
    assert result.checker_matrix_differences["check_report_delta"] == 1


def test_compare_benchmarks_reports_metric_deltas_and_safety_regression(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    _write_benchmark(
        context,
        "benchmark.before",
        BenchmarkMetrics(pass_count=1, checker_matrix_accuracy=1.0),
    )
    _write_benchmark(
        context,
        "benchmark.after",
        BenchmarkMetrics(
            pass_count=2,
            checker_matrix_accuracy=1.0,
            authority_violation_count=1,
        ),
        passed=False,
    )

    result = compare_benchmarks(context, "benchmark.before", "benchmark.after")

    assert result.subject.value == "benchmark"
    assert any(
        item.metric == "pass_count" and item.delta == 1
        for item in result.metric_deltas
    )
    assert result.safety_regressions[0].metric == "authority_violation_count"
    assert result.benchmark_metric_deltas == result.metric_deltas


def test_compare_cli_json_smoke(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    _write_benchmark(context, "benchmark.before", BenchmarkMetrics(pass_count=1))
    _write_benchmark(context, "benchmark.after", BenchmarkMetrics(pass_count=2))

    result = runner.invoke(
        app,
        [
            "compare",
            "benchmarks",
            "benchmark.before",
            "benchmark.after",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.output)
    assert payload["subject"] == "benchmark"
    assert payload["before_id"] == "benchmark.before"
    assert payload["after_id"] == "benchmark.after"
    assert payload["accepted_write_performed"] is False
    assert "metric-scoped" in payload["authority_notice"]


def _write_benchmark(
    context: RepoContext,
    run_id: str,
    metrics: BenchmarkMetrics,
    *,
    passed: bool = True,
) -> None:
    write_benchmark_run(
        context,
        BenchmarkRun(
            run_id=run_id,
            suite=BenchmarkSuiteName.SMOKE,
            passed=passed,
            metrics=metrics,
            components=(
                BenchmarkComponentResult(
                    name=BenchmarkComponentName.CHECKER_CROSSCHECK,
                    passed=passed,
                    case_count=1,
                    pass_count=int(passed),
                    fail_count=int(not passed),
                    skipped_count=metrics.skipped_count,
                ),
            ),
        ),
    )
