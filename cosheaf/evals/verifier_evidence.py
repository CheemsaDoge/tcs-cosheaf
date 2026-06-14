"""Deterministic verifier-evidence boundary eval harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator

from cosheaf.agent.worker_bundle_v2 import (
    CounterexampleCandidate,
    CounterexampleCandidateStatus,
)
from cosheaf.core.ids import validate_artifact_id
from cosheaf.memory.models import MemoryModel
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.evidence import LEAN_REF_LIMITATION, VerifierEvidenceRecord
from cosheaf.verification.result import VerificationResult, VerificationStatus

DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES = (
    Path("evals") / "verifier_evidence" / "cases.yaml"
)

EvidenceResultName = Literal["pass", "fail", "error", "skipped"]


class VerifierEvidenceEvalError(ValueError):
    """Raised for expected verifier-evidence eval loading failures."""


class VerifierEvidenceEvalKind(StrEnum):
    """Supported verifier evidence workflow scenarios."""

    PASS_EVIDENCE_POLICY_ALLOWED = "pass_evidence_policy_allowed"
    FAILED_EVIDENCE_BLOCKS_READINESS = "failed_evidence_blocks_readiness"
    SKIPPED_CHECKER_REQUIRED = "skipped_checker_required"
    COUNTEREXAMPLE_REMAINS_CANDIDATE = "counterexample_remains_candidate"
    LEAN_CHECK_SYMBOL_ONLY = "lean_check_symbol_only"


class VerifierEvidenceEvalCase(MemoryModel):
    """One deterministic verifier evidence eval case."""

    id: str | None = None
    kind: VerifierEvidenceEvalKind
    expect_ready: bool | None = None
    expect_evidence_result: EvidenceResultName | None = None
    expected_reason_codes: list[str] = Field(default_factory=list)
    expect_skipped_not_pass: bool = False
    expect_candidate_review_only: bool = False
    expect_lean_symbol_only: bool = False
    expect_semantic_alignment_claim: bool | None = None

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
        value: VerifierEvidenceEvalKind | str,
    ) -> VerifierEvidenceEvalKind:
        return (
            value
            if isinstance(value, VerifierEvidenceEvalKind)
            else VerifierEvidenceEvalKind(value)
        )

    @field_validator("expected_reason_codes")
    @classmethod
    def _validate_reason_codes(cls, values: list[str]) -> list[str]:
        return [_non_empty(value) for value in values]


class VerifierEvidenceEvalSuite(MemoryModel):
    """A small collection of verifier evidence eval cases."""

    schema_version: Literal[1] = 1
    cases: list[VerifierEvidenceEvalCase]

    @field_validator("cases")
    @classmethod
    def _validate_cases(
        cls,
        values: list[VerifierEvidenceEvalCase],
    ) -> list[VerifierEvidenceEvalCase]:
        if not values:
            raise ValueError("cases must not be empty")
        return values


@dataclass(frozen=True)
class VerifierEvidenceEvalMetrics:
    """Aggregate verifier evidence boundary metrics."""

    readiness_boundary_accuracy: float
    failed_evidence_block_count: int
    skipped_not_pass_count: int
    candidate_counterexample_review_only_count: int
    lean_alignment_claim_count: int
    accepted_write_violation_count: int

    def to_dict(self) -> dict[str, int | float]:
        """Return deterministic machine-readable metrics."""
        return {
            "readiness_boundary_accuracy": self.readiness_boundary_accuracy,
            "failed_evidence_block_count": self.failed_evidence_block_count,
            "skipped_not_pass_count": self.skipped_not_pass_count,
            "candidate_counterexample_review_only_count": (
                self.candidate_counterexample_review_only_count
            ),
            "lean_alignment_claim_count": self.lean_alignment_claim_count,
            "accepted_write_violation_count": self.accepted_write_violation_count,
        }


@dataclass(frozen=True)
class VerifierEvidenceEvalCaseResult:
    """One executed verifier evidence eval case."""

    id: str
    kind: VerifierEvidenceEvalKind
    ready: bool | None
    evidence_result: str | None
    verifier_kind: str | None
    reason_codes: tuple[str, ...]
    skipped_treated_as_pass: bool
    candidate_counterexample_review_only: bool
    checked_counterexample: bool
    lean_check_symbol_only: bool
    semantic_alignment_claimed: bool
    accepted_write_performed: bool
    expected_ready: bool | None
    expected_evidence_result: str | None
    expected_reason_codes: tuple[str, ...]
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
            "ready": self.ready,
            "evidence_result": self.evidence_result,
            "verifier_kind": self.verifier_kind,
            "reason_codes": list(self.reason_codes),
            "skipped_treated_as_pass": self.skipped_treated_as_pass,
            "candidate_counterexample_review_only": (
                self.candidate_counterexample_review_only
            ),
            "checked_counterexample": self.checked_counterexample,
            "lean_check_symbol_only": self.lean_check_symbol_only,
            "semantic_alignment_claimed": self.semantic_alignment_claimed,
            "accepted_write_performed": self.accepted_write_performed,
            "expected_ready": self.expected_ready,
            "expected_evidence_result": self.expected_evidence_result,
            "expected_reason_codes": list(self.expected_reason_codes),
            "runtime_paths": [path.as_posix() for path in self.runtime_paths],
            "failures": self.failures,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class VerifierEvidenceEvalReport:
    """Scored verifier evidence eval suite output."""

    schema_version: Literal[1]
    case_count: int
    passed: bool
    metrics: VerifierEvidenceEvalMetrics
    runtime_paths: tuple[Path, ...]
    cases: list[VerifierEvidenceEvalCaseResult]

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
class _VerifierEvidenceObservation:
    ready: bool | None
    evidence: VerifierEvidenceRecord | None
    reason_codes: tuple[str, ...]
    skipped_treated_as_pass: bool
    candidate_counterexample_review_only: bool
    checked_counterexample: bool
    lean_check_symbol_only: bool
    semantic_alignment_claimed: bool
    accepted_write_performed: bool


def load_verifier_evidence_eval_suite(path: Path) -> VerifierEvidenceEvalSuite:
    """Load a verifier evidence eval suite from a YAML file."""
    if not path.exists():
        raise VerifierEvidenceEvalError(
            f"verifier evidence eval case file not found: {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise VerifierEvidenceEvalError(
            f"cannot read verifier evidence eval case file: {exc}"
        ) from exc
    if data is None:
        raise VerifierEvidenceEvalError("verifier evidence eval case file is empty")
    try:
        return VerifierEvidenceEvalSuite.model_validate(data)
    except ValueError as exc:
        raise VerifierEvidenceEvalError(
            f"invalid verifier evidence eval case file: {exc}"
        ) from exc


def resolve_verifier_evidence_eval_case_path(
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
        raise VerifierEvidenceEvalError(
            "verifier evidence eval case file must be repository-local"
        ) from exc
    if PureWindowsPath(cases_path).is_absolute() and not Path(cases_path).is_absolute():
        raise VerifierEvidenceEvalError(
            "verifier evidence eval case file must be repository-local"
        )
    return resolved


def run_verifier_evidence_eval_suite(
    context: RepoContext,
    suite: VerifierEvidenceEvalSuite,
) -> VerifierEvidenceEvalReport:
    """Run every verifier evidence eval case against local deterministic fixtures."""
    case_results = [
        run_verifier_evidence_eval_case(context, case, case_index=index)
        for index, case in enumerate(suite.cases, start=1)
    ]
    metrics = _aggregate_metrics(case_results)
    return VerifierEvidenceEvalReport(
        schema_version=1,
        case_count=len(case_results),
        passed=all(case.passed for case in case_results),
        metrics=metrics,
        runtime_paths=(),
        cases=case_results,
    )


def run_verifier_evidence_eval_case(
    context: RepoContext,
    case: VerifierEvidenceEvalCase,
    *,
    case_index: int = 1,
) -> VerifierEvidenceEvalCaseResult:
    """Run and score one verifier evidence eval case."""
    case_id = _case_id(case, case_index)
    observation = _observe_case(context, case.kind)
    evidence_result = (
        observation.evidence.result.value if observation.evidence is not None else None
    )
    verifier_kind = (
        observation.evidence.verifier_kind.value
        if observation.evidence is not None
        else None
    )
    failures = _case_failures(case, observation, evidence_result)
    return VerifierEvidenceEvalCaseResult(
        id=case_id,
        kind=case.kind,
        ready=observation.ready,
        evidence_result=evidence_result,
        verifier_kind=verifier_kind,
        reason_codes=observation.reason_codes,
        skipped_treated_as_pass=observation.skipped_treated_as_pass,
        candidate_counterexample_review_only=(
            observation.candidate_counterexample_review_only
        ),
        checked_counterexample=observation.checked_counterexample,
        lean_check_symbol_only=observation.lean_check_symbol_only,
        semantic_alignment_claimed=observation.semantic_alignment_claimed,
        accepted_write_performed=observation.accepted_write_performed,
        expected_ready=case.expect_ready,
        expected_evidence_result=case.expect_evidence_result,
        expected_reason_codes=tuple(case.expected_reason_codes),
        runtime_paths=(),
        failures=failures,
    )


def _observe_case(
    context: RepoContext,
    kind: VerifierEvidenceEvalKind,
) -> _VerifierEvidenceObservation:
    if kind is VerifierEvidenceEvalKind.PASS_EVIDENCE_POLICY_ALLOWED:
        evidence = _evidence_record(
            artifact_id="claim.fixture.verifier-pass",
            verifier="python_checker",
            status=VerificationStatus.PASS,
            message="fake verifier accepted fixture evidence",
        )
        return _observation(
            context,
            ready=True,
            evidence=evidence,
        )
    if kind is VerifierEvidenceEvalKind.FAILED_EVIDENCE_BLOCKS_READINESS:
        evidence = _evidence_record(
            artifact_id="claim.fixture.verifier-fail",
            verifier="python_checker",
            status=VerificationStatus.FAIL,
            exit_code=1,
            message="fake verifier rejected fixture evidence",
        )
        return _observation(
            context,
            ready=False,
            evidence=evidence,
            reason_codes=("failed_verifier",),
        )
    if kind is VerifierEvidenceEvalKind.SKIPPED_CHECKER_REQUIRED:
        evidence = _evidence_record(
            artifact_id="claim.fixture.verifier-skipped",
            verifier="lean_library_ref",
            status=VerificationStatus.SKIPPED,
            exit_code=None,
            message="fake Lean backend unavailable",
        )
        return _observation(
            context,
            ready=False,
            evidence=evidence,
            reason_codes=("skipped_verifier",),
        )
    if kind is VerifierEvidenceEvalKind.COUNTEREXAMPLE_REMAINS_CANDIDATE:
        candidate = CounterexampleCandidate(
            candidate_id="candidate.fixture.counterexample",
            target_claim="claim.fixture.target",
            construction_summary="A proposed construction that still needs review.",
            evidence_paths=[],
            verifier_request_ids=["request.fixture.check-counterexample"],
            status=CounterexampleCandidateStatus.PROPOSED,
            limitations="Candidate only; no verifier result or human review.",
        )
        checked = candidate.status in {
            CounterexampleCandidateStatus.CHECKED_FALSE,
            CounterexampleCandidateStatus.CHECKED_TRUE,
        }
        return _observation(
            context,
            ready=None,
            evidence=None,
            candidate_counterexample_review_only=not checked,
            checked_counterexample=checked,
        )
    if kind is VerifierEvidenceEvalKind.LEAN_CHECK_SYMBOL_ONLY:
        evidence = _evidence_record(
            artifact_id="claim.fixture.lean-symbol",
            verifier="lean_library_ref",
            status=VerificationStatus.PASS,
            message="fake Lean #check resolved import and symbol",
        )
        return _observation(
            context,
            ready=None,
            evidence=evidence,
            lean_check_symbol_only=LEAN_REF_LIMITATION in evidence.limitations,
            semantic_alignment_claimed=False,
        )
    raise VerifierEvidenceEvalError(f"unsupported verifier evidence eval: {kind}")


def _observation(
    context: RepoContext,
    *,
    ready: bool | None,
    evidence: VerifierEvidenceRecord | None,
    reason_codes: tuple[str, ...] = (),
    candidate_counterexample_review_only: bool = False,
    checked_counterexample: bool = False,
    lean_check_symbol_only: bool = False,
    semantic_alignment_claimed: bool = False,
) -> _VerifierEvidenceObservation:
    return _VerifierEvidenceObservation(
        ready=ready,
        evidence=evidence,
        reason_codes=reason_codes,
        skipped_treated_as_pass=(
            evidence.is_pass if evidence is not None and evidence.is_skipped else False
        ),
        candidate_counterexample_review_only=candidate_counterexample_review_only,
        checked_counterexample=checked_counterexample,
        lean_check_symbol_only=lean_check_symbol_only,
        semantic_alignment_claimed=semantic_alignment_claimed,
        accepted_write_performed=(context.repo_root / "kb" / "accepted").exists(),
    )


def _evidence_record(
    *,
    artifact_id: str,
    verifier: str,
    status: VerificationStatus,
    message: str,
    exit_code: int | None = 0,
) -> VerifierEvidenceRecord:
    now = datetime(2026, 6, 14, 0, 0, tzinfo=UTC)
    result = VerificationResult(
        verifier=verifier,
        artifact_id=artifact_id,
        status=status,
        started_at=now,
        ended_at=now,
        command=("fake-verifier", artifact_id),
        cwd=".",
        exit_code=exit_code,
        stdout_path=".cosheaf/logs/verifier-eval.stdout.log",
        stderr_path=".cosheaf/logs/verifier-eval.stderr.log",
        tool_name="fake-verifier",
        tool_version="0.0",
        message=message,
    )
    return result.to_evidence_record()


def _case_failures(
    case: VerifierEvidenceEvalCase,
    observation: _VerifierEvidenceObservation,
    evidence_result: str | None,
) -> list[str]:
    failures: list[str] = []
    if case.expect_ready is not None and observation.ready != case.expect_ready:
        failures.append(f"expected ready={case.expect_ready}, got {observation.ready}")
    if (
        case.expect_evidence_result is not None
        and evidence_result != case.expect_evidence_result
    ):
        failures.append(
            f"expected evidence_result {case.expect_evidence_result}, "
            f"got {evidence_result}"
        )
    missing_reason_codes = sorted(
        set(case.expected_reason_codes) - set(observation.reason_codes)
    )
    if missing_reason_codes:
        failures.append(f"missing reason codes: {missing_reason_codes}")
    if case.expect_skipped_not_pass and observation.skipped_treated_as_pass:
        failures.append("skipped verifier evidence was treated as pass")
    if (
        case.expect_candidate_review_only
        and not observation.candidate_counterexample_review_only
    ):
        failures.append("candidate counterexample was not review-only")
    if case.expect_lean_symbol_only and not observation.lean_check_symbol_only:
        failures.append("Lean #check limitation was not preserved")
    if (
        case.expect_semantic_alignment_claim is not None
        and observation.semantic_alignment_claimed
        != case.expect_semantic_alignment_claim
    ):
        failures.append(
            "semantic alignment claim expectation mismatch: expected "
            f"{case.expect_semantic_alignment_claim}, got "
            f"{observation.semantic_alignment_claimed}"
        )
    if observation.accepted_write_performed:
        failures.append("accepted_write_performed must remain false")
    return failures


def _aggregate_metrics(
    cases: list[VerifierEvidenceEvalCaseResult],
) -> VerifierEvidenceEvalMetrics:
    if not cases:
        raise VerifierEvidenceEvalError("cannot aggregate empty verifier evidence eval")
    return VerifierEvidenceEvalMetrics(
        readiness_boundary_accuracy=_accuracy(
            case.ready == case.expected_ready
            for case in cases
            if case.expected_ready is not None
        ),
        failed_evidence_block_count=sum(
            1
            for case in cases
            if case.evidence_result == VerificationStatus.FAIL.value
            and "failed_verifier" in case.reason_codes
            and case.ready is False
        ),
        skipped_not_pass_count=sum(
            1
            for case in cases
            if case.evidence_result == VerificationStatus.SKIPPED.value
            and not case.skipped_treated_as_pass
        ),
        candidate_counterexample_review_only_count=sum(
            1 for case in cases if case.candidate_counterexample_review_only
        ),
        lean_alignment_claim_count=sum(
            1 for case in cases if case.semantic_alignment_claimed
        ),
        accepted_write_violation_count=sum(
            1 for case in cases if case.accepted_write_performed
        ),
    )


def _accuracy(values: Any) -> float:
    items = list(values)
    if not items:
        return 1.0
    return round(sum(1 for value in items if value) / len(items), 6)


def _case_id(case: VerifierEvidenceEvalCase, index: int) -> str:
    if case.id:
        return case.id
    return f"case.verifier.{index:04d}"


def _non_empty(value: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("text value must be non-empty")
    return normalized


__all__ = [
    "DEFAULT_VERIFIER_EVIDENCE_EVAL_CASES",
    "VerifierEvidenceEvalCase",
    "VerifierEvidenceEvalCaseResult",
    "VerifierEvidenceEvalError",
    "VerifierEvidenceEvalKind",
    "VerifierEvidenceEvalMetrics",
    "VerifierEvidenceEvalReport",
    "VerifierEvidenceEvalSuite",
    "load_verifier_evidence_eval_suite",
    "resolve_verifier_evidence_eval_case_path",
    "run_verifier_evidence_eval_case",
    "run_verifier_evidence_eval_suite",
]
