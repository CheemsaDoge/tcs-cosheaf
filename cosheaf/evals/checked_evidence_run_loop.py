"""Deterministic checked-evidence run-loop boundary eval harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.counterexample_evidence import (
    CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
    SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION,
    CandidateSource,
    CheckedCounterexampleEvidenceRecord,
    CheckedResult,
    CheckMethod,
)

DEFAULT_CHECKED_EVIDENCE_RUN_LOOP_EVAL_CASES = (
    Path("evals") / "checked_evidence_run_loop" / "cases.yaml"
)

CheckedEvidenceResultName = Literal[
    "checked_refutes",
    "checked_does_not_refute",
    "inconclusive",
    "error",
    "skipped",
]


class CheckedEvidenceRunLoopEvalError(ValueError):
    """Raised for expected checked-evidence eval loading failures."""


class CheckedEvidenceRunLoopEvalKind(StrEnum):
    """Supported checked-evidence run-loop scenarios."""

    CANDIDATE_REMAINS_CANDIDATE = "candidate_remains_candidate"
    CHECKED_REFUTES_WITH_SUPPORT = "checked_refutes_with_support"
    SKIPPED_NOT_PASS = "skipped_not_pass"
    INCONCLUSIVE_NOT_REFUTES = "inconclusive_not_refutes"
    ERROR_NOT_PASS = "error_not_pass"


class CheckedEvidenceRunLoopEvalCase(MemoryModel):
    """One deterministic checked-evidence run-loop eval case."""

    id: str | None = None
    kind: CheckedEvidenceRunLoopEvalKind
    expect_checked_result: CheckedEvidenceResultName | None = None
    expect_checked_refutation: bool | None = None
    expect_candidate_review_only: bool = False
    expect_support_required: bool = False
    expect_skipped_not_pass: bool = False

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("kind", mode="before")
    @classmethod
    def _validate_kind(
        cls,
        value: CheckedEvidenceRunLoopEvalKind | str,
    ) -> CheckedEvidenceRunLoopEvalKind:
        return (
            value
            if isinstance(value, CheckedEvidenceRunLoopEvalKind)
            else CheckedEvidenceRunLoopEvalKind(value)
        )


class CheckedEvidenceRunLoopEvalSuite(MemoryModel):
    """A small collection of checked-evidence eval cases."""

    schema_version: Literal[1] = 1
    cases: list[CheckedEvidenceRunLoopEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[CheckedEvidenceRunLoopEvalCase],
    ) -> list[CheckedEvidenceRunLoopEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class CheckedEvidenceRunLoopEvalMetrics:
    """Aggregate checked-evidence run-loop metrics."""

    candidate_checked_separation_accuracy: float
    checked_refutes_support_count: int
    skipped_not_pass_count: int
    non_refuting_result_count: int
    accepted_write_violation_count: int

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "candidate_checked_separation_accuracy": (
                self.candidate_checked_separation_accuracy
            ),
            "checked_refutes_support_count": self.checked_refutes_support_count,
            "skipped_not_pass_count": self.skipped_not_pass_count,
            "non_refuting_result_count": self.non_refuting_result_count,
            "accepted_write_violation_count": self.accepted_write_violation_count,
        }


@dataclass(frozen=True)
class CheckedEvidenceRunLoopEvalCaseResult:
    """One executed checked-evidence run-loop eval case."""

    id: str
    kind: CheckedEvidenceRunLoopEvalKind
    checked_result: str | None
    candidate_review_only: bool
    checked_refutation: bool
    support_present: bool
    skipped_treated_as_pass: bool
    authority_notice_preserved: bool
    accepted_write_performed: bool
    expected_checked_result: str | None
    expected_checked_refutation: bool | None
    expected_candidate_review_only: bool
    failures: list[str]

    @property
    def passed(self) -> bool:
        """Return whether this case satisfied every configured expectation."""
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable case output."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "checked_result": self.checked_result,
            "candidate_review_only": self.candidate_review_only,
            "checked_refutation": self.checked_refutation,
            "support_present": self.support_present,
            "skipped_treated_as_pass": self.skipped_treated_as_pass,
            "authority_notice_preserved": self.authority_notice_preserved,
            "accepted_write_performed": self.accepted_write_performed,
            "expected_checked_result": self.expected_checked_result,
            "expected_checked_refutation": self.expected_checked_refutation,
            "expected_candidate_review_only": self.expected_candidate_review_only,
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class CheckedEvidenceRunLoopEvalReport:
    """Scored checked-evidence run-loop suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: CheckedEvidenceRunLoopEvalMetrics
    runtime_paths: tuple[Path, ...]
    cases: list[CheckedEvidenceRunLoopEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic machine-readable report output."""
        return {
            "schema_version": self.schema_version,
            "case_count": self.case_count,
            "passed": self.passed,
            "metrics": self.metrics.to_dict(),
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self) -> str:
        """Return deterministic JSON for the report."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


@dataclass(frozen=True)
class _CheckedEvidenceObservation:
    checked_result: str | None
    candidate_review_only: bool
    checked_refutation: bool
    support_present: bool
    skipped_treated_as_pass: bool
    authority_notice_preserved: bool
    accepted_write_performed: bool


def load_checked_evidence_run_loop_eval_suite(
    path: Path,
) -> CheckedEvidenceRunLoopEvalSuite:
    """Load a checked-evidence run-loop eval suite from YAML."""
    if not path.exists():
        raise CheckedEvidenceRunLoopEvalError(
            f"checked evidence eval case file not found: {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CheckedEvidenceRunLoopEvalError(
            f"cannot read checked evidence eval case file: {exc}"
        ) from exc
    if data is None:
        raise CheckedEvidenceRunLoopEvalError(
            "checked evidence eval case file is empty"
        )
    try:
        return CheckedEvidenceRunLoopEvalSuite.model_validate(data)
    except ValueError as exc:
        raise CheckedEvidenceRunLoopEvalError(
            f"invalid checked evidence eval case file: {exc}"
        ) from exc


def resolve_checked_evidence_run_loop_eval_case_path(
    context: RepoContext,
    cases_path: Path,
) -> Path:
    """Resolve and constrain the case file path to the repository root."""
    repo_root = context.repo_root
    path = cases_path if cases_path.is_absolute() else repo_root / cases_path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise CheckedEvidenceRunLoopEvalError(
            "checked evidence eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise CheckedEvidenceRunLoopEvalError(
            "checked evidence eval case file must be repository-local"
        )
    return resolved


def run_checked_evidence_run_loop_eval_suite(
    context: RepoContext,
    suite: CheckedEvidenceRunLoopEvalSuite,
) -> CheckedEvidenceRunLoopEvalReport:
    """Run every checked-evidence run-loop eval case."""
    case_results = [
        run_checked_evidence_run_loop_eval_case(context, case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    return CheckedEvidenceRunLoopEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        runtime_paths=(),
        cases=case_results,
    )


def run_checked_evidence_run_loop_eval_case(
    context: RepoContext,
    case: CheckedEvidenceRunLoopEvalCase,
    *,
    case_index: int = 1,
) -> CheckedEvidenceRunLoopEvalCaseResult:
    """Run and score one checked-evidence run-loop eval case."""
    case_id = _case_id(case, case_index)
    observation = _observe_case(context, case.kind)
    failures = _case_failures(case, observation)
    return CheckedEvidenceRunLoopEvalCaseResult(
        id=case_id,
        kind=case.kind,
        checked_result=observation.checked_result,
        candidate_review_only=observation.candidate_review_only,
        checked_refutation=observation.checked_refutation,
        support_present=observation.support_present,
        skipped_treated_as_pass=observation.skipped_treated_as_pass,
        authority_notice_preserved=observation.authority_notice_preserved,
        accepted_write_performed=observation.accepted_write_performed,
        expected_checked_result=case.expect_checked_result,
        expected_checked_refutation=case.expect_checked_refutation,
        expected_candidate_review_only=case.expect_candidate_review_only,
        failures=failures,
    )


def _observe_case(
    context: RepoContext,
    kind: CheckedEvidenceRunLoopEvalKind,
) -> _CheckedEvidenceObservation:
    if kind is CheckedEvidenceRunLoopEvalKind.CANDIDATE_REMAINS_CANDIDATE:
        return _observation(context, record=None, candidate_review_only=True)
    if kind is CheckedEvidenceRunLoopEvalKind.CHECKED_REFUTES_WITH_SUPPORT:
        return _observation(
            context,
            record=_record(
                checked_result="checked_refutes",
                evidence_paths=[".cosheaf/evidence/checked-refutes.json"],
            ),
        )
    if kind is CheckedEvidenceRunLoopEvalKind.SKIPPED_NOT_PASS:
        return _observation(
            context,
            record=_record(
                checked_result="skipped",
                limitations=(
                    CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
                    SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION,
                ),
            ),
        )
    if kind is CheckedEvidenceRunLoopEvalKind.INCONCLUSIVE_NOT_REFUTES:
        return _observation(context, record=_record(checked_result="inconclusive"))
    if kind is CheckedEvidenceRunLoopEvalKind.ERROR_NOT_PASS:
        return _observation(context, record=_record(checked_result="error"))
    raise CheckedEvidenceRunLoopEvalError(f"unsupported checked evidence eval: {kind}")


def _observation(
    context: RepoContext,
    *,
    record: CheckedCounterexampleEvidenceRecord | None,
    candidate_review_only: bool = False,
) -> _CheckedEvidenceObservation:
    support_present = False
    checked_refutation = False
    skipped_treated_as_pass = False
    authority_notice_preserved = False
    checked_result = None
    if record is not None:
        support_present = bool(
            record.verifier_evidence_ids
            or record.review_record_paths
            or record.evidence_paths
        )
        checked_refutation = record.is_checked_refutation
        skipped_treated_as_pass = bool(
            record.is_skipped and record.is_checked_refutation
        )
        authority_notice_preserved = (
            CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE in record.limitations
        )
        checked_result = record.checked_result.value
    return _CheckedEvidenceObservation(
        checked_result=checked_result,
        candidate_review_only=candidate_review_only,
        checked_refutation=checked_refutation,
        support_present=support_present,
        skipped_treated_as_pass=skipped_treated_as_pass,
        authority_notice_preserved=authority_notice_preserved,
        accepted_write_performed=False,
    )


def _record(
    *,
    checked_result: CheckedEvidenceResultName,
    evidence_paths: list[str] | None = None,
    limitations: tuple[str, ...] | None = None,
) -> CheckedCounterexampleEvidenceRecord:
    result_slug = checked_result.replace("_", "-")
    return CheckedCounterexampleEvidenceRecord(
        schema_version=1,
        evidence_id=(
            f"checked-counterexample.claim.fixture.target.{result_slug}.habc123"
        ),
        target_artifact_id="claim.fixture.target",
        candidate_id=f"candidate.fixture.{result_slug}",
        candidate_source=CandidateSource.MANUAL_NOTE,
        check_method=CheckMethod.EXECUTABLE_CHECK,
        checked_result=CheckedResult(checked_result),
        verifier_evidence_ids=(),
        review_record_paths=(),
        evidence_paths=tuple(evidence_paths or ()),
        created_at=datetime(2026, 6, 15, 0, 0, tzinfo=UTC),
        checker="checked-evidence-eval",
        limitations=limitations or (CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,),
    )


def _case_failures(
    case: CheckedEvidenceRunLoopEvalCase,
    observation: _CheckedEvidenceObservation,
) -> list[str]:
    failures: list[str] = []
    if (
        case.expect_checked_result is not None
        and observation.checked_result != case.expect_checked_result
    ):
        failures.append(
            f"expected checked_result {case.expect_checked_result}, "
            f"got {observation.checked_result}"
        )
    if (
        case.expect_checked_refutation is not None
        and observation.checked_refutation != case.expect_checked_refutation
    ):
        failures.append(
            f"expected checked_refutation={case.expect_checked_refutation}, "
            f"got {observation.checked_refutation}"
        )
    if case.expect_candidate_review_only and not observation.candidate_review_only:
        failures.append("candidate counterexample was not kept review-only")
    if case.expect_support_required and not observation.support_present:
        failures.append("checked evidence support was missing")
    if case.expect_skipped_not_pass and observation.skipped_treated_as_pass:
        failures.append("skipped checked evidence was treated as pass")
    if observation.accepted_write_performed:
        failures.append("accepted_write_performed must remain false")
    if (
        observation.checked_result is not None
        and not observation.authority_notice_preserved
    ):
        failures.append("checked-evidence authority notice was not preserved")
    return failures


def _aggregate_metrics(
    cases: list[CheckedEvidenceRunLoopEvalCaseResult],
) -> CheckedEvidenceRunLoopEvalMetrics:
    if not cases:
        raise CheckedEvidenceRunLoopEvalError(
            "cannot aggregate empty checked evidence eval"
        )
    return CheckedEvidenceRunLoopEvalMetrics(
        candidate_checked_separation_accuracy=_accuracy(
            _case_separation_ok(case) for case in cases
        ),
        checked_refutes_support_count=sum(
            1
            for case in cases
            if case.checked_refutation and case.support_present
        ),
        skipped_not_pass_count=sum(
            1
            for case in cases
            if case.checked_result == "skipped" and not case.skipped_treated_as_pass
        ),
        non_refuting_result_count=sum(
            1
            for case in cases
            if case.checked_result in {"inconclusive", "error"}
            and not case.checked_refutation
        ),
        accepted_write_violation_count=sum(
            1 for case in cases if case.accepted_write_performed
        ),
    )


def _case_separation_ok(case: CheckedEvidenceRunLoopEvalCaseResult) -> bool:
    if case.expected_candidate_review_only:
        return case.candidate_review_only and not case.checked_refutation
    if case.expected_checked_refutation is not None:
        return case.checked_refutation == case.expected_checked_refutation
    return case.checked_result != "skipped" or not case.skipped_treated_as_pass


def _accuracy(values: Any) -> float:
    items = list(values)
    if not items:
        return 1.0
    return round(sum(1 for value in items if value) / len(items), 6)


def _case_id(case: CheckedEvidenceRunLoopEvalCase, index: int) -> str:
    if case.id:
        return case.id
    return f"case.checked-evidence.{index:04d}"


__all__ = [
    "DEFAULT_CHECKED_EVIDENCE_RUN_LOOP_EVAL_CASES",
    "CheckedEvidenceRunLoopEvalCase",
    "CheckedEvidenceRunLoopEvalCaseResult",
    "CheckedEvidenceRunLoopEvalError",
    "CheckedEvidenceRunLoopEvalKind",
    "CheckedEvidenceRunLoopEvalMetrics",
    "CheckedEvidenceRunLoopEvalReport",
    "CheckedEvidenceRunLoopEvalSuite",
    "load_checked_evidence_run_loop_eval_suite",
    "resolve_checked_evidence_run_loop_eval_case_path",
    "run_checked_evidence_run_loop_eval_case",
    "run_checked_evidence_run_loop_eval_suite",
]
