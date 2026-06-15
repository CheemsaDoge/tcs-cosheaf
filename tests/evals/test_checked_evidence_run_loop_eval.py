from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.checked_evidence_run_loop import (
    DEFAULT_CHECKED_EVIDENCE_RUN_LOOP_EVAL_CASES,
    CheckedEvidenceRunLoopEvalCase,
    CheckedEvidenceRunLoopEvalKind,
    CheckedEvidenceRunLoopEvalSuite,
    load_checked_evidence_run_loop_eval_suite,
    run_checked_evidence_run_loop_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def _required_suite() -> CheckedEvidenceRunLoopEvalSuite:
    return CheckedEvidenceRunLoopEvalSuite(
        cases=[
            CheckedEvidenceRunLoopEvalCase(
                id="case.checked-evidence.candidate-remains-candidate",
                kind=(
                    CheckedEvidenceRunLoopEvalKind.CANDIDATE_REMAINS_CANDIDATE
                ),
                expect_candidate_review_only=True,
            ),
            CheckedEvidenceRunLoopEvalCase(
                id="case.checked-evidence.checked-refutes-with-support",
                kind=(
                    CheckedEvidenceRunLoopEvalKind.CHECKED_REFUTES_WITH_SUPPORT
                ),
                expect_checked_result="checked_refutes",
                expect_checked_refutation=True,
                expect_support_required=True,
            ),
            CheckedEvidenceRunLoopEvalCase(
                id="case.checked-evidence.skipped-not-pass",
                kind=CheckedEvidenceRunLoopEvalKind.SKIPPED_NOT_PASS,
                expect_checked_result="skipped",
                expect_skipped_not_pass=True,
            ),
            CheckedEvidenceRunLoopEvalCase(
                id="case.checked-evidence.inconclusive-not-refutes",
                kind=CheckedEvidenceRunLoopEvalKind.INCONCLUSIVE_NOT_REFUTES,
                expect_checked_result="inconclusive",
                expect_checked_refutation=False,
            ),
            CheckedEvidenceRunLoopEvalCase(
                id="case.checked-evidence.error-not-pass",
                kind=CheckedEvidenceRunLoopEvalKind.ERROR_NOT_PASS,
                expect_checked_result="error",
                expect_checked_refutation=False,
            ),
        ]
    )


def test_checked_evidence_run_loop_eval_scores_required_cases(
    tmp_path: Path,
) -> None:
    report = run_checked_evidence_run_loop_eval_suite(
        RepoContext(tmp_path),
        _required_suite(),
    )

    assert report.passed is True
    assert report.case_count == 5
    assert report.metrics.candidate_checked_separation_accuracy == 1.0
    assert report.metrics.checked_refutes_support_count == 1
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.non_refuting_result_count == 2
    assert report.metrics.accepted_write_violation_count == 0
    assert {case.kind for case in report.cases} == set(
        CheckedEvidenceRunLoopEvalKind
    )
    assert not (tmp_path / "kb" / "accepted").exists()

    cases = {case.id: case for case in report.cases}
    assert (
        cases["case.checked-evidence.candidate-remains-candidate"]
        .candidate_review_only
        is True
    )
    assert (
        cases["case.checked-evidence.checked-refutes-with-support"]
        .checked_refutation
        is True
    )
    assert (
        cases["case.checked-evidence.checked-refutes-with-support"]
        .support_present
        is True
    )
    assert cases["case.checked-evidence.skipped-not-pass"].skipped_treated_as_pass is (
        False
    )
    assert cases["case.checked-evidence.error-not-pass"].checked_result == "error"


def test_checked_evidence_run_loop_eval_fails_bad_checked_refutes_expectation(
    tmp_path: Path,
) -> None:
    report = run_checked_evidence_run_loop_eval_suite(
        RepoContext(tmp_path),
        CheckedEvidenceRunLoopEvalSuite(
            cases=[
                CheckedEvidenceRunLoopEvalCase(
                    id="case.checked-evidence.bad-expectation",
                    kind=CheckedEvidenceRunLoopEvalKind.INCONCLUSIVE_NOT_REFUTES,
                    expect_checked_result="inconclusive",
                    expect_checked_refutation=True,
                )
            ]
        ),
    )

    assert report.passed is False
    assert report.metrics.candidate_checked_separation_accuracy == 0.0
    assert "expected checked_refutation=True, got False" in report.cases[0].failures


def test_default_checked_evidence_run_loop_eval_suite_lists_required_cases() -> None:
    suite = load_checked_evidence_run_loop_eval_suite(
        ROOT / DEFAULT_CHECKED_EVIDENCE_RUN_LOOP_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.checked-evidence.candidate-remains-candidate",
        "case.checked-evidence.checked-refutes-with-support",
        "case.checked-evidence.skipped-not-pass",
        "case.checked-evidence.inconclusive-not-refutes",
        "case.checked-evidence.error-not-pass",
    }
    assert {case.kind for case in suite.cases} == set(
        CheckedEvidenceRunLoopEvalKind
    )


def test_checked_evidence_run_loop_eval_cli_json(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "checked-evidence-run-loop",
            "--repo-root",
            str(ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"passed": true' in result.output
    assert '"accepted_write_violation_count": 0' in result.output
