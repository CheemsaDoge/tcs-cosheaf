from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.evals.checker_crosscheck import (
    DEFAULT_CHECKER_CROSSCHECK_EVAL_CASES,
    CheckerCrossCheckEvalCase,
    CheckerCrossCheckEvalKind,
    CheckerCrossCheckEvalSuite,
    load_checker_crosscheck_eval_suite,
    run_checker_crosscheck_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def _required_suite() -> CheckerCrossCheckEvalSuite:
    return CheckerCrossCheckEvalSuite(
        cases=[
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.valid-checked-local-claim",
                kind=CheckerCrossCheckEvalKind.VALID_CHECKED_LOCAL_CLAIM,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.failed-checker-claim",
                kind=CheckerCrossCheckEvalKind.FAILED_CHECKER_CLAIM,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.skipped-optional-checker",
                kind=CheckerCrossCheckEvalKind.SKIPPED_OPTIONAL_CHECKER,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.overclaimed-accepted-proof",
                kind=CheckerCrossCheckEvalKind.OVERCLAIMED_ACCEPTED_PROOF,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.private-leakage-in-crosscheck",
                kind=CheckerCrossCheckEvalKind.PRIVATE_LEAKAGE_IN_CROSSCHECK,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.source-gap",
                kind=CheckerCrossCheckEvalKind.SOURCE_GAP,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.formalization-gap",
                kind=CheckerCrossCheckEvalKind.FORMALIZATION_GAP,
            ),
            CheckerCrossCheckEvalCase(
                id="case.checker-crosscheck.inconclusive-evidence",
                kind=CheckerCrossCheckEvalKind.INCONCLUSIVE_EVIDENCE,
            ),
        ]
    )


def test_checker_crosscheck_eval_scores_required_cases(tmp_path: Path) -> None:
    report = run_checker_crosscheck_eval_suite(
        RepoContext(tmp_path),
        _required_suite(),
    )

    assert report.passed is True
    assert report.case_count == 8
    assert report.metrics.case_pass_rate == 1.0
    assert report.metrics.checked_pass_boundary_rate == 1.0
    assert report.metrics.failed_checker_detection_rate == 1.0
    assert report.metrics.authority_overclaim_rejection_rate == 1.0
    assert report.metrics.private_leak_rejection_rate == 1.0
    assert report.metrics.source_gap_detection_rate == 1.0
    assert report.metrics.formalization_gap_detection_rate == 1.0
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.inconclusive_not_pass_count == 1
    assert report.metrics.accepted_write_violation_count == 0
    assert {case.kind for case in report.cases} == set(CheckerCrossCheckEvalKind)
    assert not (tmp_path / "kb" / "accepted").exists()

    cases = {case.id: case for case in report.cases}
    assert (
        cases["case.checker-crosscheck.valid-checked-local-claim"]
        .checked_pass_not_accepted
        is True
    )
    assert (
        cases["case.checker-crosscheck.overclaimed-accepted-proof"]
        .authority_overclaim_rejected
        is True
    )
    assert (
        cases["case.checker-crosscheck.private-leakage-in-crosscheck"]
        .private_leak_rejected
        is True
    )
    assert (
        cases["case.checker-crosscheck.formalization-gap"]
        .semantic_alignment_gap_detected
        is True
    )


def test_default_checker_crosscheck_eval_suite_lists_required_cases() -> None:
    suite = load_checker_crosscheck_eval_suite(
        ROOT / DEFAULT_CHECKER_CROSSCHECK_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.checker-crosscheck.valid-checked-local-claim",
        "case.checker-crosscheck.failed-checker-claim",
        "case.checker-crosscheck.skipped-optional-checker",
        "case.checker-crosscheck.overclaimed-accepted-proof",
        "case.checker-crosscheck.private-leakage-in-crosscheck",
        "case.checker-crosscheck.source-gap",
        "case.checker-crosscheck.formalization-gap",
        "case.checker-crosscheck.inconclusive-evidence",
    }
    assert {case.kind for case in suite.cases} == set(CheckerCrossCheckEvalKind)


def test_checker_crosscheck_eval_cli_json() -> None:
    result = runner.invoke(
        app,
        [
            "eval",
            "checker-crosscheck",
            "--repo-root",
            str(ROOT),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"kind": "checker_crosscheck_eval"' in result.output
    assert '"passed": true' in result.output
    assert '"skipped_not_pass_count": 1' in result.output
    assert '"accepted_write_violation_count": 0' in result.output
