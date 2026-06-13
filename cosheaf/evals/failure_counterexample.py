"""Deterministic failure and counterexample preservation eval harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator

from cosheaf.agent.orchestrator_state import ReducerResult
from cosheaf.agent.task import WorkerType
from cosheaf.agent.worker_bundle_v2 import (
    WorkerBundleV2Error,
    reduce_worker_bundle_v2,
)
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext

DEFAULT_FAILURE_COUNTEREXAMPLE_EVAL_CASES = (
    Path("evals") / "failure_counterexample" / "cases.yaml"
)


class FailureCounterexampleEvalError(ValueError):
    """Raised for expected failure/counterexample eval loading failures."""


class FailureCounterexampleEvalKind(StrEnum):
    """Supported failure/counterexample workflow scenarios."""

    REASONER_UNCERTAINTY = "reasoner_uncertainty"
    COUNTEREXAMPLE_CANDIDATE = "counterexample_candidate"
    VERIFIER_REJECTS_INVALID_PROOF = "verifier_rejects_invalid_proof"
    REDUCER_PRESERVES_FAILURE = "reducer_preserves_failure"
    ACCEPTED_WRITE_BOUNDARY = "accepted_write_boundary"


class FailureCounterexampleEvalCase(MemoryModel):
    """One deterministic failure/counterexample workflow eval case."""

    id: str | None = None
    kind: FailureCounterexampleEvalKind
    expect_failure_preserved: bool = False
    expect_uncertainty: bool = False
    expect_counterexample_candidate: bool = False
    expect_verifier_request: bool = False
    expect_reducer_rejection: bool = False
    forbidden_output_paths: list[str] = Field(default_factory=list)

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
        value: FailureCounterexampleEvalKind | str,
    ) -> FailureCounterexampleEvalKind:
        return (
            value
            if isinstance(value, FailureCounterexampleEvalKind)
            else FailureCounterexampleEvalKind(value)
        )

    @field_validator("forbidden_output_paths")
    @classmethod
    def _validate_forbidden_paths(cls, values: list[str]) -> list[str]:
        return [normalize_repo_path(_non_empty(value)) for value in values]


class FailureCounterexampleEvalSuite(MemoryModel):
    """A small collection of failure/counterexample eval cases."""

    schema_version: Literal[1] = 1
    cases: list[FailureCounterexampleEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[FailureCounterexampleEvalCase],
    ) -> list[FailureCounterexampleEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class FailureCounterexampleEvalMetrics:
    """Aggregate failure/counterexample preservation metrics."""

    failure_preservation_rate: float
    uncertainty_field_presence: float
    counterexample_candidate_flag_accuracy: float
    verifier_request_presence: float
    accepted_write_violation_count: int

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "failure_preservation_rate": self.failure_preservation_rate,
            "uncertainty_field_presence": self.uncertainty_field_presence,
            "counterexample_candidate_flag_accuracy": (
                self.counterexample_candidate_flag_accuracy
            ),
            "verifier_request_presence": self.verifier_request_presence,
            "accepted_write_violation_count": self.accepted_write_violation_count,
        }


@dataclass(frozen=True)
class FailureCounterexampleEvalCaseResult:
    """One executed failure/counterexample workflow eval case."""

    id: str
    kind: FailureCounterexampleEvalKind
    worker_role: str
    reducer_status: str | None
    reducer_rejected: bool
    error_message: str | None
    output_paths: tuple[str, ...]
    warnings: tuple[str, ...]
    failure_preserved: bool
    uncertainty_present: bool
    counterexample_candidate_flagged: bool
    verifier_request_present: bool
    accepted_write_performed: bool
    expected_failure_preserved: bool
    expected_uncertainty: bool
    expected_counterexample_candidate: bool
    expected_verifier_request: bool
    runtime_paths: tuple[Path, ...]
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
            "worker_role": self.worker_role,
            "reducer_status": self.reducer_status,
            "reducer_rejected": self.reducer_rejected,
            "error_message": self.error_message,
            "output_paths": list(self.output_paths),
            "warnings": list(self.warnings),
            "failure_preserved": self.failure_preserved,
            "uncertainty_present": self.uncertainty_present,
            "counterexample_candidate_flagged": (
                self.counterexample_candidate_flagged
            ),
            "verifier_request_present": self.verifier_request_present,
            "accepted_write_performed": self.accepted_write_performed,
            "expected_failure_preserved": self.expected_failure_preserved,
            "expected_uncertainty": self.expected_uncertainty,
            "expected_counterexample_candidate": (
                self.expected_counterexample_candidate
            ),
            "expected_verifier_request": self.expected_verifier_request,
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class FailureCounterexampleEvalReport:
    """Scored failure/counterexample eval suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: FailureCounterexampleEvalMetrics
    runtime_paths: tuple[Path, ...]
    cases: list[FailureCounterexampleEvalCaseResult]

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


def load_failure_counterexample_eval_suite(
    path: Path,
) -> FailureCounterexampleEvalSuite:
    """Load a failure/counterexample eval suite from a YAML file."""
    if not path.exists():
        raise FailureCounterexampleEvalError(
            f"failure/counterexample eval case file not found: {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FailureCounterexampleEvalError(
            f"cannot read failure/counterexample eval case file: {exc}"
        ) from exc
    if data is None:
        raise FailureCounterexampleEvalError(
            "failure/counterexample eval case file is empty"
        )
    try:
        return FailureCounterexampleEvalSuite.model_validate(data)
    except ValueError as exc:
        raise FailureCounterexampleEvalError(
            f"invalid failure/counterexample eval case file: {exc}"
        ) from exc


def resolve_failure_counterexample_eval_case_path(
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
        raise FailureCounterexampleEvalError(
            "failure/counterexample eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise FailureCounterexampleEvalError(
            "failure/counterexample eval case file must be repository-local"
        )
    return resolved


def run_failure_counterexample_eval_suite(
    context: RepoContext,
    suite: FailureCounterexampleEvalSuite,
) -> FailureCounterexampleEvalReport:
    """Run every failure/counterexample eval case through the reducer boundary."""
    case_results = [
        run_failure_counterexample_eval_case(context, case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    runtime_paths = _unique_runtime_paths(case_results)
    return FailureCounterexampleEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        runtime_paths=runtime_paths,
        cases=case_results,
    )


def run_failure_counterexample_eval_case(
    context: RepoContext,
    case: FailureCounterexampleEvalCase,
    *,
    case_index: int = 1,
) -> FailureCounterexampleEvalCaseResult:
    """Run and score one failure/counterexample eval case."""
    case_id = _case_id(case, case_index)
    bundle_data = _bundle_data(case, case_id)
    bundle_path = _write_runtime_bundle(context, case_id, bundle_data)
    worker_role = str(bundle_data["worker_role"])

    reducer_result: ReducerResult | None = None
    error_message: str | None = None
    try:
        reducer_result = reduce_worker_bundle_v2(
            context,
            bundle_path,
            reducer_id=validate_artifact_id(f"reducer.{case_id}"),
        )
    except WorkerBundleV2Error as exc:
        error_message = str(exc)

    warnings = tuple(reducer_result.warnings if reducer_result is not None else ())
    output_paths = tuple(
        reducer_result.output_paths if reducer_result is not None else ()
    )
    accepted_write_performed = _accepted_write_performed(context, output_paths)
    failure_preserved = _failure_preserved(warnings)
    uncertainty_present = any(
        warning.startswith("uncertainty:") for warning in warnings
    )
    counterexample_candidate_flagged = any(
        warning.startswith("counterexample_candidate:") for warning in warnings
    )
    verifier_request_present = any(
        warning.startswith("verification_request:") for warning in warnings
    )
    reducer_rejected = error_message is not None
    failures = _case_failures(
        case,
        reducer_rejected=reducer_rejected,
        failure_preserved=failure_preserved,
        uncertainty_present=uncertainty_present,
        counterexample_candidate_flagged=counterexample_candidate_flagged,
        verifier_request_present=verifier_request_present,
        accepted_write_performed=accepted_write_performed,
        output_paths=output_paths,
    )
    return FailureCounterexampleEvalCaseResult(
        id=case_id,
        kind=case.kind,
        worker_role=worker_role,
        reducer_status=reducer_result.status if reducer_result is not None else None,
        reducer_rejected=reducer_rejected,
        error_message=error_message,
        output_paths=output_paths,
        warnings=warnings,
        failure_preserved=failure_preserved,
        uncertainty_present=uncertainty_present,
        counterexample_candidate_flagged=counterexample_candidate_flagged,
        verifier_request_present=verifier_request_present,
        accepted_write_performed=accepted_write_performed,
        expected_failure_preserved=case.expect_failure_preserved,
        expected_uncertainty=case.expect_uncertainty,
        expected_counterexample_candidate=case.expect_counterexample_candidate,
        expected_verifier_request=case.expect_verifier_request,
        runtime_paths=(bundle_path,),
        failures=failures,
    )


def _bundle_data(
    case: FailureCounterexampleEvalCase,
    case_id: str,
) -> dict[str, Any]:
    role = _worker_role(case.kind)
    return {
        "bundle_id": f"bundle.{case_id}",
        "task_id": f"task.{case_id}.{role.value}",
        "worker_role": role.value,
        "created_at": "2026-06-10T00:00:00Z",
        "summary": _summary(case.kind),
        "used_artifacts": ["claim.fixture.failure-counterexample"],
        "used_sources": [],
        "claims": _claims(case.kind),
        "proposed_artifacts": [
            {
                "path": _proposed_path(case.kind, case_id),
                "summary": "Draft-only eval proposal.",
            }
        ],
        "assumptions": _assumptions(case.kind),
        "uncertainty": _uncertainty(case.kind),
        "verification_requests": _verification_requests(case.kind),
        "failed_attempts": _failed_attempts(case.kind),
        "counterexamples": _counterexamples(case.kind),
        "failures_or_counterexamples": _legacy_failures(case.kind),
        "dependency_questions": [],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Use ordinary review, validation, and gate workflow."],
        "confidence": "low",
    }


def _worker_role(kind: FailureCounterexampleEvalKind) -> WorkerType:
    if kind is FailureCounterexampleEvalKind.COUNTEREXAMPLE_CANDIDATE:
        return WorkerType.COUNTEREXAMPLER
    if kind is FailureCounterexampleEvalKind.VERIFIER_REJECTS_INVALID_PROOF:
        return WorkerType.VERIFIER
    return WorkerType.REASONER


def _summary(kind: FailureCounterexampleEvalKind) -> str:
    return {
        FailureCounterexampleEvalKind.REASONER_UNCERTAINTY: (
            "Reasoner preserves an assumption and uncertainty."
        ),
        FailureCounterexampleEvalKind.COUNTEREXAMPLE_CANDIDATE: (
            "Counterexampleer records candidate evidence only."
        ),
        FailureCounterexampleEvalKind.VERIFIER_REJECTS_INVALID_PROOF: (
            "Verifier rejects an invalid proof attempt."
        ),
        FailureCounterexampleEvalKind.REDUCER_PRESERVES_FAILURE: (
            "Reducer preserves failed attempts and legacy failure notes."
        ),
        FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY: (
            "Unsafe accepted write proposal must be rejected."
        ),
    }[kind]


def _claims(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind is FailureCounterexampleEvalKind.VERIFIER_REJECTS_INVALID_PROOF:
        return ["The attempted proof is invalid and remains review-only."]
    return ["This eval output is review context only."]


def _assumptions(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind in {
        FailureCounterexampleEvalKind.REASONER_UNCERTAINTY,
        FailureCounterexampleEvalKind.REDUCER_PRESERVES_FAILURE,
    }:
        return ["Assume the graph is finite until source review confirms scope."]
    return []


def _uncertainty(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind in {
        FailureCounterexampleEvalKind.REASONER_UNCERTAINTY,
        FailureCounterexampleEvalKind.VERIFIER_REJECTS_INVALID_PROOF,
        FailureCounterexampleEvalKind.REDUCER_PRESERVES_FAILURE,
    }:
        return ["No verifier pass or human review has been recorded."]
    return []


def _verification_requests(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind is FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY:
        return []
    return ["Run validate, gate, and a reviewer-approved verifier if needed."]


def _failed_attempts(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind is FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY:
        return []
    if kind is FailureCounterexampleEvalKind.VERIFIER_REJECTS_INVALID_PROOF:
        return ["Invalid proof attempt rejected: missing base case."]
    return ["Direct proof attempt failed and must remain visible."]


def _counterexamples(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind is FailureCounterexampleEvalKind.COUNTEREXAMPLE_CANDIDATE:
        return ["Candidate counterexample: a two-node graph with one missing edge."]
    return []


def _legacy_failures(kind: FailureCounterexampleEvalKind) -> list[str]:
    if kind is FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY:
        return []
    return ["Legacy failure note preserved for reviewer context."]


def _proposed_path(kind: FailureCounterexampleEvalKind, case_id: str) -> str:
    if kind is FailureCounterexampleEvalKind.ACCEPTED_WRITE_BOUNDARY:
        return "kb/accepted/claims/unsafe-eval.yaml"
    return f".cosheaf/evals/failure_counterexample/{case_id}/proposal.yaml"


def _write_runtime_bundle(
    context: RepoContext,
    case_id: str,
    data: dict[str, Any],
) -> Path:
    relative_path = Path(".cosheaf") / "evals" / "failure_counterexample"
    relative_path = relative_path / case_id / "bundle.yaml"
    path = context.resolve(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return relative_path


def _case_failures(
    case: FailureCounterexampleEvalCase,
    *,
    reducer_rejected: bool,
    failure_preserved: bool,
    uncertainty_present: bool,
    counterexample_candidate_flagged: bool,
    verifier_request_present: bool,
    accepted_write_performed: bool,
    output_paths: tuple[str, ...],
) -> list[str]:
    failures: list[str] = []
    if case.expect_reducer_rejection and not reducer_rejected:
        failures.append("reducer rejection was expected but did not happen")
    if not case.expect_reducer_rejection and reducer_rejected:
        failures.append("reducer rejected an expected review-only bundle")
    if case.expect_failure_preserved and not failure_preserved:
        failures.append("failure was not preserved")
    if case.expect_uncertainty and not uncertainty_present:
        failures.append("uncertainty field was not preserved")
    if case.expect_counterexample_candidate and not counterexample_candidate_flagged:
        failures.append("counterexample candidate flag was not preserved")
    if case.expect_verifier_request and not verifier_request_present:
        failures.append("verifier request was not preserved")
    if accepted_write_performed:
        failures.append("accepted write path was opened")
    for forbidden in case.forbidden_output_paths:
        if forbidden in output_paths:
            failures.append(f"forbidden output path returned: {forbidden}")
    return failures


def _aggregate_metrics(
    cases: list[FailureCounterexampleEvalCaseResult],
) -> FailureCounterexampleEvalMetrics:
    if not cases:
        raise FailureCounterexampleEvalError(
            "cannot aggregate empty failure/counterexample eval"
        )
    return FailureCounterexampleEvalMetrics(
        failure_preservation_rate=_accuracy(
            case.failure_preserved
            for case in cases
            if case.expected_failure_preserved
        ),
        uncertainty_field_presence=_accuracy(
            case.uncertainty_present
            for case in cases
            if case.expected_uncertainty
        ),
        counterexample_candidate_flag_accuracy=_accuracy(
            case.counterexample_candidate_flagged
            for case in cases
            if case.expected_counterexample_candidate
        ),
        verifier_request_presence=_accuracy(
            case.verifier_request_present
            for case in cases
            if case.expected_verifier_request
        ),
        accepted_write_violation_count=sum(
            1 for case in cases if case.accepted_write_performed
        ),
    )


def _failure_preserved(warnings: tuple[str, ...]) -> bool:
    return any(
        warning.startswith("failed_attempt:") or "failure" in warning.lower()
        for warning in warnings
    )


def _accepted_write_performed(
    context: RepoContext,
    output_paths: tuple[str, ...],
) -> bool:
    accepted_root = context.repo_root / "kb" / "accepted"
    if accepted_root.exists():
        return True
    return any(
        "accepted" in PurePosixPath(normalize_repo_path(path)).parts
        for path in output_paths
    )


def _unique_runtime_paths(
    cases: list[FailureCounterexampleEvalCaseResult],
) -> tuple[Path, ...]:
    paths = {
        path.as_posix(): path
        for case in cases
        for path in case.runtime_paths
        if path.as_posix().startswith(".cosheaf/")
    }
    return tuple(paths[key] for key in sorted(paths))


def _accuracy(values: Any) -> float:
    items = list(values)
    if not items:
        return 1.0
    return round(sum(1 for value in items if value) / len(items), 6)


def _case_id(case: FailureCounterexampleEvalCase, index: int) -> str:
    if case.id:
        return case.id
    return f"case.failure.{index:04d}"


def _non_empty(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text value must be non-empty")
    return normalized


__all__ = [
    "DEFAULT_FAILURE_COUNTEREXAMPLE_EVAL_CASES",
    "FailureCounterexampleEvalCase",
    "FailureCounterexampleEvalCaseResult",
    "FailureCounterexampleEvalError",
    "FailureCounterexampleEvalKind",
    "FailureCounterexampleEvalMetrics",
    "FailureCounterexampleEvalReport",
    "FailureCounterexampleEvalSuite",
    "load_failure_counterexample_eval_suite",
    "resolve_failure_counterexample_eval_case_path",
    "run_failure_counterexample_eval_case",
    "run_failure_counterexample_eval_suite",
]
