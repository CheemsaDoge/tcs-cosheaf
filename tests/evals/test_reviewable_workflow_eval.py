from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.reviewable_workflow import (
    DEFAULT_REVIEWABLE_WORKFLOW_EVAL_CASES,
    ReviewableWorkflowEvalCase,
    ReviewableWorkflowEvalKind,
    ReviewableWorkflowEvalSuite,
    load_reviewable_workflow_eval_suite,
    run_reviewable_workflow_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_reviewable_workflow_eval_scores_required_cases(tmp_path: Path) -> None:
    suite = ReviewableWorkflowEvalSuite(
        cases=[
            ReviewableWorkflowEvalCase(
                id="case.reviewable-workflow.accepted-dependency-draft-target",
                kind=ReviewableWorkflowEvalKind.ACCEPTED_DEPENDENCY_DRAFT_TARGET,
            ),
            ReviewableWorkflowEvalCase(
                id="case.reviewable-workflow.repeated-failure-memory",
                kind=ReviewableWorkflowEvalKind.REPEATED_FAILURE_MEMORY,
            ),
            ReviewableWorkflowEvalCase(
                id="case.reviewable-workflow.unchecked-counterexample",
                kind=ReviewableWorkflowEvalKind.UNCHECKED_COUNTEREXAMPLE,
            ),
            ReviewableWorkflowEvalCase(
                id="case.reviewable-workflow.private-leakage-risk",
                kind=ReviewableWorkflowEvalKind.PRIVATE_LEAKAGE_RISK,
            ),
            ReviewableWorkflowEvalCase(
                id="case.reviewable-workflow.gate-scanner-blocker",
                kind=ReviewableWorkflowEvalKind.GATE_SCANNER_BLOCKER,
            ),
            ReviewableWorkflowEvalCase(
                id="case.reviewable-workflow.draft-proposal-ready",
                kind=ReviewableWorkflowEvalKind.DRAFT_PROPOSAL_READY,
            ),
        ]
    )

    report = run_reviewable_workflow_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is True
    assert report.case_count == 6
    assert report.metrics.workflow_validity_rate == 1.0
    assert report.metrics.librarian_trace_completeness_rate == 1.0
    assert report.metrics.fsm_replay_validity_rate == 1.0
    assert report.metrics.local_action_whitelist_rate == 1.0
    assert report.metrics.draft_proposal_validity_rate == 4 / 6
    assert report.metrics.handoff_scanner_block_rate == 1.0
    assert report.metrics.authority_overclaim_rejection_rate == 1.0
    assert report.metrics.private_leak_rejection_rate == 1.0
    assert report.metrics.review_readiness_classification_rate == 1.0
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.accepted_write_violation_count == 0
    assert not (tmp_path / "kb" / "accepted").exists()


def test_default_reviewable_workflow_eval_suite_lists_required_cases() -> None:
    suite = load_reviewable_workflow_eval_suite(
        ROOT / DEFAULT_REVIEWABLE_WORKFLOW_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.reviewable-workflow.accepted-dependency-draft-target",
        "case.reviewable-workflow.repeated-failure-memory",
        "case.reviewable-workflow.unchecked-counterexample",
        "case.reviewable-workflow.private-leakage-risk",
        "case.reviewable-workflow.gate-scanner-blocker",
        "case.reviewable-workflow.draft-proposal-ready",
    }
    assert {case.kind for case in suite.cases} == set(ReviewableWorkflowEvalKind)


def test_reviewable_workflow_eval_cli_json() -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "reviewable-workflow",
            "--repo-root",
            str(ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "reviewable_workflow_eval"' in result.output
    assert '"passed": true' in result.output
    assert '"skipped_not_pass_count": 1' in result.output
    assert '"accepted_write_violation_count": 0' in result.output
