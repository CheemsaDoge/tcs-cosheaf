from __future__ import annotations

from pathlib import Path

from cosheaf.evals.failure_counterexample import (
    DEFAULT_FAILURE_COUNTEREXAMPLE_EVAL_CASES,
    FailureCounterexampleEvalCase,
    FailureCounterexampleEvalKind,
    FailureCounterexampleEvalSuite,
    load_failure_counterexample_eval_suite,
    run_failure_counterexample_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]


def _required_suite() -> FailureCounterexampleEvalSuite:
    return FailureCounterexampleEvalSuite(
        cases=[
            FailureCounterexampleEvalCase(
                id="case.failure.reasoner-uncertainty",
                kind=FailureCounterexampleEvalKind.REASONER_UNCERTAINTY,
                expect_failure_preserved=True,
                expect_uncertainty=True,
                expect_verifier_request=True,
            ),
            FailureCounterexampleEvalCase(
                id="case.failure.counterexample-candidate",
                kind=FailureCounterexampleEvalKind.COUNTEREXAMPLE_CANDIDATE,
                expect_failure_preserved=True,
                expect_counterexample_candidate=True,
                expect_verifier_request=True,
            ),
            FailureCounterexampleEvalCase(
                id="case.failure.verifier-rejects-invalid-proof",
                kind=FailureCounterexampleEvalKind.VERIFIER_REJECTS_INVALID_PROOF,
                expect_failure_preserved=True,
                expect_uncertainty=True,
                expect_verifier_request=True,
            ),
            FailureCounterexampleEvalCase(
                id="case.failure.reducer-preserves-failure",
                kind=FailureCounterexampleEvalKind.REDUCER_PRESERVES_FAILURE,
                expect_failure_preserved=True,
                expect_uncertainty=True,
                expect_verifier_request=True,
            ),
            FailureCounterexampleEvalCase(
                id="case.failure.accepted-write-boundary",
                kind=FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY,
                expect_reducer_rejection=True,
            ),
        ]
    )


def test_failure_counterexample_eval_scores_required_cases(tmp_path: Path) -> None:
    report = run_failure_counterexample_eval_suite(
        RepoContext(tmp_path),
        _required_suite(),
    )

    assert report.passed is True
    assert report.case_count == 5
    assert report.metrics.failure_preservation_rate == 1.0
    assert report.metrics.uncertainty_field_presence == 1.0
    assert report.metrics.counterexample_candidate_flag_accuracy == 1.0
    assert report.metrics.verifier_request_presence == 1.0
    assert report.metrics.accepted_write_violation_count == 0
    assert {case.kind for case in report.cases} == set(FailureCounterexampleEvalKind)

    cases = {case.id: case for case in report.cases}
    assert cases["case.failure.reasoner-uncertainty"].failure_preserved is True
    assert (
        cases["case.failure.counterexample-candidate"].counterexample_candidate_flagged
    )
    assert cases["case.failure.verifier-rejects-invalid-proof"].worker_role == (
        "verifier"
    )
    assert cases["case.failure.reducer-preserves-failure"].reducer_status == (
        "accepted_for_review"
    )
    assert cases["case.failure.accepted-write-boundary"].reducer_rejected is True
    assert cases["case.failure.accepted-write-boundary"].accepted_write_performed is (
        False
    )
    assert not (tmp_path / "kb" / "accepted").exists()
    assert all(path.as_posix().startswith(".cosheaf/") for path in report.runtime_paths)


def test_failure_counterexample_eval_fails_when_failure_is_not_preserved(
    tmp_path: Path,
) -> None:
    report = run_failure_counterexample_eval_suite(
        RepoContext(tmp_path),
        FailureCounterexampleEvalSuite(
            cases=[
                FailureCounterexampleEvalCase(
                    id="case.failure.wrong-expectation",
                    kind=FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY,
                    expect_failure_preserved=True,
                    expect_reducer_rejection=True,
                )
            ]
        ),
    )

    assert report.passed is False
    assert report.metrics.failure_preservation_rate == 0.0
    assert "failure was not preserved" in report.cases[0].failures


def test_default_failure_counterexample_eval_suite_lists_required_cases() -> None:
    suite = load_failure_counterexample_eval_suite(
        ROOT / DEFAULT_FAILURE_COUNTEREXAMPLE_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.failure.reasoner-uncertainty",
        "case.failure.counterexample-candidate",
        "case.failure.verifier-rejects-invalid-proof",
        "case.failure.reducer-preserves-failure",
        "case.failure.accepted-write-boundary",
    }
    assert {case.kind for case in suite.cases} == set(FailureCounterexampleEvalKind)
