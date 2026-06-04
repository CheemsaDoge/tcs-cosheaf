"""Reproducibility metadata gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cosheaf.core.artifact import BaseArtifact, Evidence
from cosheaf.gates.schema_gate import ValidationFailure, sort_failures
from cosheaf.storage.loader import LoadedRecord
from cosheaf.verification.result import VerificationResult, VerificationStatus

EXECUTABLE_EVIDENCE_KINDS = frozenset(
    {
        "python_checker",
        "sat",
        "sat_solver",
        "sat_checker",
        "smt",
        "smt_solver",
        "smt_checker",
        "lean",
        "lean4",
        "lean_checker",
        "lean_proof",
    }
)

REQUIRED_EXECUTED_METADATA = (
    "command",
    "cwd",
    "timeout_seconds",
    "input_paths",
    "stdout_path",
    "stderr_path",
    "output_paths",
    "tool_name",
)

REQUIRED_SKIPPED_METADATA = (
    "command",
    "cwd",
    "evidence_paths",
    "tool_name",
)

RANDOMNESS_MARKERS = (
    "random",
    "randomized",
    "randomised",
    "randomness",
    "stochastic",
    "monte carlo",
)

CheckStatus = Literal["pass", "fail", "not_applicable"]


@dataclass(frozen=True)
class ReproducibilityCheck:
    """One artifact/evidence reproducibility metadata check."""

    artifact_id: str
    source_path: str
    evidence_kind: str
    evidence_path: str
    status: CheckStatus
    required_metadata: tuple[str, ...]
    missing_metadata: tuple[str, ...] = ()
    randomized: bool = False
    seed_recorded: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "source_path": self.source_path,
            "evidence_kind": self.evidence_kind,
            "evidence_path": self.evidence_path,
            "status": self.status,
            "required_metadata": list(self.required_metadata),
            "missing_metadata": list(self.missing_metadata),
            "randomized": self.randomized,
            "seed_recorded": self.seed_recorded,
        }


@dataclass(frozen=True)
class ReproducibilityMetadataResult:
    """Aggregate result for the reproducibility metadata gate."""

    checks: tuple[ReproducibilityCheck, ...]
    failures: tuple[ValidationFailure, ...]

    @property
    def applicable_count(self) -> int:
        return sum(1 for check in self.checks if check.status != "not_applicable")

    @property
    def ok(self) -> bool:
        return not self.failures


def validate_reproducibility_metadata(
    records: tuple[LoadedRecord, ...],
    verification_results: tuple[VerificationResult, ...],
) -> ReproducibilityMetadataResult:
    """Check executable evidence has enough metadata to reproduce verifier runs."""
    checks: list[ReproducibilityCheck] = []
    failures: list[ValidationFailure] = []
    results_by_artifact = _results_by_artifact(verification_results)

    for loaded in records:
        artifact = loaded.record
        if not isinstance(artifact, BaseArtifact):
            continue
        if not artifact.evidence:
            checks.append(_not_applicable_check(loaded, "", ""))
            continue
        for evidence in artifact.evidence:
            if evidence.kind not in EXECUTABLE_EVIDENCE_KINDS:
                checks.append(
                    _not_applicable_check(loaded, evidence.kind, evidence.path)
                )
                continue
            matching_results = _matching_results(
                results_by_artifact.get(artifact.id, ()),
                evidence,
            )
            if not matching_results:
                check = ReproducibilityCheck(
                    artifact_id=artifact.id,
                    source_path=loaded.source_path.as_posix(),
                    evidence_kind=evidence.kind,
                    evidence_path=evidence.path,
                    status="fail",
                    required_metadata=REQUIRED_EXECUTED_METADATA,
                    missing_metadata=("verification_result",),
                    randomized=_is_randomized(artifact, evidence),
                    seed_recorded=False,
                )
                checks.append(check)
                failures.append(_failure_from_check(check))
                continue
            check = _check_evidence_result(
                loaded=loaded,
                evidence=evidence,
                result=matching_results[0],
            )
            checks.append(check)
            if check.status == "fail":
                failures.append(_failure_from_check(check))

    return ReproducibilityMetadataResult(
        checks=tuple(sorted(checks, key=_check_sort_key)),
        failures=sort_failures(failures),
    )


def _results_by_artifact(
    results: tuple[VerificationResult, ...],
) -> dict[str, tuple[VerificationResult, ...]]:
    grouped: dict[str, list[VerificationResult]] = {}
    for result in results:
        grouped.setdefault(result.artifact_id, []).append(result)
    return {
        artifact_id: tuple(sorted(values, key=_result_sort_key))
        for artifact_id, values in grouped.items()
    }


def _matching_results(
    results: tuple[VerificationResult, ...],
    evidence: Evidence,
) -> tuple[VerificationResult, ...]:
    matching = [
        result
        for result in results
        if evidence.path in result.evidence_paths
        or evidence.path in result.input_paths
        or not result.evidence_paths
    ]
    return tuple(sorted(matching, key=_result_sort_key))


def _check_evidence_result(
    *,
    loaded: LoadedRecord,
    evidence: Evidence,
    result: VerificationResult,
) -> ReproducibilityCheck:
    artifact = loaded.record
    if not isinstance(artifact, BaseArtifact):
        raise TypeError("loaded record is not an artifact")

    required = (
        REQUIRED_SKIPPED_METADATA
        if result.status is VerificationStatus.SKIPPED
        else REQUIRED_EXECUTED_METADATA
    )
    missing = list(_missing_metadata(result, required))
    randomized = _is_randomized(artifact, evidence)
    seed_recorded = bool(result.seed)
    if randomized and not seed_recorded:
        missing.append("seed")

    return ReproducibilityCheck(
        artifact_id=artifact.id,
        source_path=loaded.source_path.as_posix(),
        evidence_kind=evidence.kind,
        evidence_path=evidence.path,
        status="fail" if missing else "pass",
        required_metadata=required,
        missing_metadata=tuple(sorted(dict.fromkeys(missing))),
        randomized=randomized,
        seed_recorded=seed_recorded,
    )


def _missing_metadata(
    result: VerificationResult,
    required: tuple[str, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in required:
        value = getattr(result, field_name)
        if value is None:
            missing.append(field_name)
        elif isinstance(value, tuple) and not value:
            missing.append(field_name)
        elif isinstance(value, str) and not value.strip():
            missing.append(field_name)

    if result.status in {VerificationStatus.PASS, VerificationStatus.FAIL}:
        if result.exit_code is None:
            missing.append("exit_code")

    return tuple(missing)


def _failure_from_check(check: ReproducibilityCheck) -> ValidationFailure:
    message = (
        "randomized evidence requires seed metadata"
        if check.missing_metadata == ("seed",)
        else "missing reproducibility metadata: "
        + ", ".join(check.missing_metadata)
    )
    if "seed" in check.missing_metadata and len(check.missing_metadata) > 1:
        message += "; randomized evidence requires seed metadata"
    return ValidationFailure(
        gate="reproducibility metadata",
        source_path=check.source_path,
        artifact_id=check.artifact_id,
        message=message,
    )


def _not_applicable_check(
    loaded: LoadedRecord,
    evidence_kind: str,
    evidence_path: str,
) -> ReproducibilityCheck:
    artifact_id = loaded.id
    return ReproducibilityCheck(
        artifact_id=artifact_id,
        source_path=loaded.source_path.as_posix(),
        evidence_kind=evidence_kind,
        evidence_path=evidence_path,
        status="not_applicable",
        required_metadata=(),
    )


def _is_randomized(artifact: BaseArtifact, evidence: Evidence) -> bool:
    text = " ".join(
        [
            artifact.type.value,
            artifact.statement,
            " ".join(artifact.tags),
            evidence.kind,
            evidence.summary,
        ]
    ).lower()
    return any(marker in text for marker in RANDOMNESS_MARKERS)


def _check_sort_key(check: ReproducibilityCheck) -> tuple[str, str, str]:
    return (check.source_path, check.artifact_id, check.evidence_path)


def _result_sort_key(result: VerificationResult) -> tuple[str, str, str]:
    return (result.artifact_id, result.verifier, result.message)
