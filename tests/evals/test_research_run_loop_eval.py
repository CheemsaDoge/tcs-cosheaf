from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.research_run_loop import (
    DEFAULT_RESEARCH_RUN_LOOP_EVAL_CASES,
    ResearchRunLoopEvalCase,
    ResearchRunLoopEvalKind,
    ResearchRunLoopEvalSuite,
    load_research_run_loop_eval_suite,
    run_research_run_loop_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_research_run_loop_eval_scores_required_cases(tmp_path: Path) -> None:
    suite = ResearchRunLoopEvalSuite(
        cases=[
            ResearchRunLoopEvalCase(
                id="case.research-run.complete-command-coverage",
                kind=ResearchRunLoopEvalKind.COMPLETE_COMMAND_COVERAGE,
            ),
            ResearchRunLoopEvalCase(
                id="case.research-run.skipped-not-pass",
                kind=ResearchRunLoopEvalKind.SKIPPED_NOT_PASS,
            ),
            ResearchRunLoopEvalCase(
                id="case.research-run.evidence-separation",
                kind=ResearchRunLoopEvalKind.EVIDENCE_SEPARATION,
            ),
            ResearchRunLoopEvalCase(
                id="case.research-run.private-leakage-prevention",
                kind=ResearchRunLoopEvalKind.PRIVATE_LEAKAGE_PREVENTION,
            ),
            ResearchRunLoopEvalCase(
                id="case.research-run.no-authority-escalation",
                kind=ResearchRunLoopEvalKind.NO_AUTHORITY_ESCALATION,
            ),
        ]
    )

    report = run_research_run_loop_eval_suite(RepoContext(tmp_path), suite)

    assert report.passed is True
    assert report.case_count == 5
    assert report.metrics.command_coverage_accuracy == 1.0
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.evidence_separation_count == 1
    assert report.metrics.private_leak_count == 0
    assert report.metrics.authority_escalation_count == 0
    assert not (tmp_path / "kb" / "accepted").exists()


def test_default_research_run_loop_eval_suite_lists_required_cases() -> None:
    suite = load_research_run_loop_eval_suite(
        ROOT / DEFAULT_RESEARCH_RUN_LOOP_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.research-run.complete-command-coverage",
        "case.research-run.skipped-not-pass",
        "case.research-run.evidence-separation",
        "case.research-run.private-leakage-prevention",
        "case.research-run.no-authority-escalation",
    }
    assert {case.kind for case in suite.cases} == set(ResearchRunLoopEvalKind)


def test_research_run_loop_eval_cli_json() -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "research-run-loop",
            "--repo-root",
            str(ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"passed": true' in result.output
    assert '"authority_escalation_count": 0' in result.output
