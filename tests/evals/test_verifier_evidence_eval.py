from __future__ import annotations

from pathlib import Path

from cosheaf.evals.verifier_evidence import (
    DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES,
    VerifierEvidenceEvalCase,
    VerifierEvidenceEvalKind,
    VerifierEvidenceEvalSuite,
    load_verifier_evidence_eval_suite,
    run_verifier_evidence_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]


def _required_suite() -> VerifierEvidenceEvalSuite:
    return VerifierEvidenceEvalSuite(
        cases=[
            VerifierEvidenceEvalCase(
                id="case.verifier.pass-policy",
                kind=VerifierEvidenceEvalKind.PASS_EVIDENCE_POLICY_ALLOWED,
                expect_ready=True,
                expect_evidence_result="pass",
            ),
            VerifierEvidenceEvalCase(
                id="case.verifier.failed-blocks",
                kind=VerifierEvidenceEvalKind.FAILED_EVIDENCE_BLOCKS_READINESS,
                expect_ready=False,
                expect_evidence_result="fail",
                expected_reason_codes=["failed_verifier"],
            ),
            VerifierEvidenceEvalCase(
                id="case.verifier.skipped-required",
                kind=VerifierEvidenceEvalKind.SKIPPED_CHECKER_REQUIRED,
                expect_ready=False,
                expect_evidence_result="skipped",
                expected_reason_codes=["skipped_verifier"],
                expect_skipped_not_pass=True,
            ),
            VerifierEvidenceEvalCase(
                id="case.verifier.candidate-remains-candidate",
                kind=VerifierEvidenceEvalKind.COUNTEREXAMPLE_REMAINS_CANDIDATE,
                expect_candidate_review_only=True,
            ),
            VerifierEvidenceEvalCase(
                id="case.verifier.lean-symbol-only",
                kind=VerifierEvidenceEvalKind.LEAN_CHECK_SYMBOL_ONLY,
                expect_evidence_result="pass",
                expect_lean_symbol_only=True,
                expect_semantic_alignment_claim=False,
            ),
        ]
    )


def test_verifier_evidence_eval_scores_required_cases(tmp_path: Path) -> None:
    report = run_verifier_evidence_eval_suite(
        RepoContext(tmp_path),
        _required_suite(),
    )

    assert report.passed is True
    assert report.case_count == 5
    assert report.metrics.readiness_boundary_accuracy == 1.0
    assert report.metrics.failed_evidence_block_count == 1
    assert report.metrics.skipped_not_pass_count == 1
    assert report.metrics.candidate_counterexample_review_only_count == 1
    assert report.metrics.lean_alignment_claim_count == 0
    assert report.metrics.accepted_write_violation_count == 0
    assert {case.kind for case in report.cases} == set(VerifierEvidenceEvalKind)

    cases = {case.id: case for case in report.cases}
    assert cases["case.verifier.pass-policy"].ready is True
    assert cases["case.verifier.pass-policy"].evidence_result == "pass"
    assert cases["case.verifier.failed-blocks"].ready is False
    assert "failed_verifier" in cases["case.verifier.failed-blocks"].reason_codes
    assert cases["case.verifier.skipped-required"].ready is False
    assert "skipped_verifier" in cases["case.verifier.skipped-required"].reason_codes
    assert cases["case.verifier.skipped-required"].skipped_treated_as_pass is False
    assert (
        cases["case.verifier.candidate-remains-candidate"]
        .candidate_counterexample_review_only
        is True
    )
    assert (
        cases["case.verifier.candidate-remains-candidate"].checked_counterexample
        is False
    )
    assert cases["case.verifier.lean-symbol-only"].lean_check_symbol_only is True
    assert cases["case.verifier.lean-symbol-only"].semantic_alignment_claimed is False
    assert all(case.accepted_write_performed is False for case in report.cases)


def test_verifier_evidence_eval_fails_when_skipped_is_expected_ready(
    tmp_path: Path,
) -> None:
    report = run_verifier_evidence_eval_suite(
        RepoContext(tmp_path),
        VerifierEvidenceEvalSuite(
            cases=[
                VerifierEvidenceEvalCase(
                    id="case.verifier.bad-skipped-pass-expectation",
                    kind=VerifierEvidenceEvalKind.SKIPPED_CHECKER_REQUIRED,
                    expect_ready=True,
                    expect_evidence_result="skipped",
                    expected_reason_codes=["skipped_verifier"],
                    expect_skipped_not_pass=True,
                )
            ]
        ),
    )

    assert report.passed is False
    assert report.metrics.readiness_boundary_accuracy == 0.0
    assert "expected ready=True, got False" in report.cases[0].failures


def test_default_verifier_evidence_eval_suite_lists_required_cases() -> None:
    suite = load_verifier_evidence_eval_suite(
        ROOT / DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.verifier.pass-policy",
        "case.verifier.failed-blocks",
        "case.verifier.skipped-required",
        "case.verifier.candidate-remains-candidate",
        "case.verifier.lean-symbol-only",
    }
    assert {case.kind for case in suite.cases} == set(VerifierEvidenceEvalKind)
