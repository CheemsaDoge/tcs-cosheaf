from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.research_loop import (
    DEFAULT_RESEARCH_LOOP_EVAL_CASES,
    ResearchLoopEvalCase,
    ResearchLoopEvalKind,
    ResearchLoopEvalSuite,
    load_research_loop_eval_suite,
    run_research_loop_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_research_loop_eval_scores_required_cases(tmp_path: Path) -> None:
    suite = ResearchLoopEvalSuite(
        cases=[
            ResearchLoopEvalCase(
                id="case.research-loop.loop-validity",
                kind=ResearchLoopEvalKind.LOOP_VALIDITY,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.attempt-schema-validity",
                kind=ResearchLoopEvalKind.ATTEMPT_SCHEMA_VALIDITY,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.repeat-failure-detection",
                kind=ResearchLoopEvalKind.REPEAT_FAILURE_DETECTION,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.unjustified-retry-block",
                kind=ResearchLoopEvalKind.UNJUSTIFIED_RETRY_BLOCK,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.public-private-leak-prevention",
                kind=ResearchLoopEvalKind.PUBLIC_PRIVATE_LEAK_PREVENTION,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.scanner-blocker-accuracy",
                kind=ResearchLoopEvalKind.SCANNER_BLOCKER_ACCURACY,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.handoff-review-context-validity",
                kind=ResearchLoopEvalKind.HANDOFF_REVIEW_CONTEXT_VALIDITY,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.policy-overclaim-rejection",
                kind=ResearchLoopEvalKind.POLICY_OVERCLAIM_REJECTION,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.budget-stop-accuracy",
                kind=ResearchLoopEvalKind.BUDGET_STOP_ACCURACY,
            ),
            ResearchLoopEvalCase(
                id="case.research-loop.skipped-not-pass",
                kind=ResearchLoopEvalKind.SKIPPED_NOT_PASS,
            ),
        ]
    )

    report = run_research_loop_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is True
    assert report.case_count == 10
    assert report.metrics.loop_validity_rate == 1.0
    assert report.metrics.attempt_schema_validity_rate == 1.0
    assert report.metrics.repeat_failure_detection_rate == 1.0
    assert report.metrics.unjustified_retry_block_rate == 1.0
    assert report.metrics.public_private_leak_count == 0
    assert report.metrics.scanner_blocker_accuracy == 1.0
    assert report.metrics.handoff_review_context_validity_rate == 1.0
    assert report.metrics.policy_overclaim_rejection_rate == 1.0
    assert report.metrics.budget_stop_accuracy == 1.0
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.accepted_write_violation_count == 0
    assert not (tmp_path / "kb" / "accepted").exists()


def test_default_research_loop_eval_suite_lists_required_cases() -> None:
    suite = load_research_loop_eval_suite(ROOT / DEFAULT_RESEARCH_LOOP_EVAL_CASES)
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.research-loop.loop-validity",
        "case.research-loop.attempt-schema-validity",
        "case.research-loop.repeat-failure-detection",
        "case.research-loop.unjustified-retry-block",
        "case.research-loop.public-private-leak-prevention",
        "case.research-loop.scanner-blocker-accuracy",
        "case.research-loop.handoff-review-context-validity",
        "case.research-loop.policy-overclaim-rejection",
        "case.research-loop.budget-stop-accuracy",
        "case.research-loop.skipped-not-pass",
    }
    assert {case.kind for case in suite.cases} == set(ResearchLoopEvalKind)


def test_research_loop_eval_cli_json() -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "research-loop",
            "--repo-root",
            str(ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "research_loop_eval"' in result.output
    assert '"passed": true' in result.output
    assert '"public_private_leak_count": 0' in result.output
