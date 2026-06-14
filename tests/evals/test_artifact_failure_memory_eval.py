from __future__ import annotations

from pathlib import Path

from cosheaf.evals.artifact_failure_memory import (
    DEFAULT_ARTIFACT_FAILURE_MEMORY_EVAL_CASES,
    ArtifactFailureMemoryEvalCase,
    ArtifactFailureMemoryEvalKind,
    ArtifactFailureMemoryEvalSuite,
    load_artifact_failure_memory_eval_suite,
    run_artifact_failure_memory_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[2]


def _required_suite() -> ArtifactFailureMemoryEvalSuite:
    return ArtifactFailureMemoryEvalSuite(
        cases=[
            ArtifactFailureMemoryEvalCase(
                id="case.failure-memory.retrieval-recall",
                kind=ArtifactFailureMemoryEvalKind.FAILURE_RETRIEVAL,
                query="separator induction dead end",
                public_only=True,
                expect_failure_retrieved=True,
            ),
            ArtifactFailureMemoryEvalCase(
                id="case.failure-memory.repeat-direction",
                kind=ArtifactFailureMemoryEvalKind.REPEAT_FAILED_DIRECTION,
                query="separator induction dead end",
                public_only=True,
                expect_failure_retrieved=True,
                expect_repeat_detected=True,
            ),
            ArtifactFailureMemoryEvalCase(
                id="case.failure-memory.public-scope-boundary",
                kind=ArtifactFailureMemoryEvalKind.PUBLIC_SCOPE_BOUNDARY,
                query="private-failure-secret-do-not-leak",
                public_only=True,
            ),
            ArtifactFailureMemoryEvalCase(
                id="case.failure-memory.authority-boundary",
                kind=ArtifactFailureMemoryEvalKind.AUTHORITY_BOUNDARY,
                query="separator induction dead end proof review",
                public_only=True,
                expect_failure_retrieved=True,
            ),
            ArtifactFailureMemoryEvalCase(
                id="case.failure-memory.candidate-counterexample-boundary",
                kind=(
                    ArtifactFailureMemoryEvalKind.CANDIDATE_COUNTEREXAMPLE_BOUNDARY
                ),
                query="candidate failure separator",
                public_only=True,
                expect_failure_retrieved=True,
            ),
        ]
    )


def test_artifact_failure_memory_eval_scores_required_cases(
    tmp_path: Path,
) -> None:
    report = run_artifact_failure_memory_eval_suite(
        RepoContext(tmp_path),
        _required_suite(),
    )

    assert report.passed is True
    assert report.case_count == 5
    assert report.metrics.failure_retrieval_recall == 1.0
    assert report.metrics.repeat_failed_direction_rate == 0.0
    assert report.metrics.failure_scope_leak_count == 0
    assert report.metrics.failure_authority_violation_count == 0
    assert report.metrics.candidate_counterexample_mislabel_count == 0
    assert {case.kind for case in report.cases} == set(
        ArtifactFailureMemoryEvalKind
    )
    assert all(path.as_posix().startswith(".cosheaf/") for path in report.runtime_paths)
    assert not (tmp_path / "kb" / "accepted").exists()

    cases = {case.id: case for case in report.cases}
    assert cases["case.failure-memory.retrieval-recall"].failure_retrieved is True
    assert (
        cases["case.failure-memory.repeat-direction"]
        .repeated_failed_direction_detected
        is True
    )
    assert (
        cases["case.failure-memory.repeat-direction"].repeated_failed_direction_slipped
        is False
    )
    assert cases["case.failure-memory.public-scope-boundary"].scope_leak is False
    assert cases["case.failure-memory.authority-boundary"].authority_violation is False
    assert (
        cases["case.failure-memory.candidate-counterexample-boundary"]
        .candidate_counterexample_mislabel
        is False
    )


def test_artifact_failure_memory_eval_fails_when_failure_is_not_retrieved(
    tmp_path: Path,
) -> None:
    report = run_artifact_failure_memory_eval_suite(
        RepoContext(tmp_path),
        ArtifactFailureMemoryEvalSuite(
            cases=[
                ArtifactFailureMemoryEvalCase(
                    id="case.failure-memory.bad-recall",
                    kind=ArtifactFailureMemoryEvalKind.FAILURE_RETRIEVAL,
                    query="unmatched failed direction",
                    public_only=True,
                    expect_failure_retrieved=True,
                )
            ]
        ),
    )

    assert report.passed is False
    assert report.metrics.failure_retrieval_recall == 0.0
    assert "expected failure memory was not retrieved" in report.cases[0].failures


def test_default_artifact_failure_memory_eval_suite_lists_required_cases() -> None:
    suite = load_artifact_failure_memory_eval_suite(
        ROOT / DEFAULT_ARTIFACT_FAILURE_MEMORY_EVAL_CASES
    )
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.failure-memory.retrieval-recall",
        "case.failure-memory.repeat-direction",
        "case.failure-memory.public-scope-boundary",
        "case.failure-memory.authority-boundary",
        "case.failure-memory.candidate-counterexample-boundary",
    }
    assert {case.kind for case in suite.cases} == set(
        ArtifactFailureMemoryEvalKind
    )
