"""Worker bundle v2 and deterministic reducer helpers.

This module defines the Phase 4.3 worker-output surface. It is intentionally
pure: validation and reduction do not execute workers, call hosted services,
write files, request human review, merge outputs, or promote accepted
knowledge.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Self

import yaml  # type: ignore[import-untyped]
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from yaml import YAMLError

from cosheaf.agent.orchestrator_state import ReducerResult
from cosheaf.agent.task import WorkerType
from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.gates.schema_gate import load_schema_valid_record
from cosheaf.storage.loader import LoadedRecord
from cosheaf.storage.repo import RepoContext


class WorkerBundleV2Error(ValueError):
    """Raised when a worker bundle v2 record is unsafe or invalid."""


class WorkerBundleConfidence(StrEnum):
    """Coarse confidence label supplied by a worker."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CounterexampleCandidateStatus(StrEnum):
    """Review lifecycle label for a proposed counterexample candidate."""

    PROPOSED = "proposed"
    NEEDS_CHECK = "needs_check"
    CHECKED_FALSE = "checked_false"
    CHECKED_TRUE = "checked_true"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ProposedArtifact(BaseModel):
    """One proposed repository-local artifact output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    summary: str

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return _validate_repo_local_path(value)

    @field_validator("summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="proposed artifact summary")


class CounterexampleCandidate(BaseModel):
    """One typed counterexample candidate preserved for review.

    This record is evidence-routing metadata. It does not refute accepted
    knowledge, create verifier results, create human review, or promote
    artifacts.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    target_claim: str | None = None
    construction_summary: str
    evidence_paths: list[str]
    verifier_request_ids: list[str]
    status: CounterexampleCandidateStatus
    limitations: str

    @field_validator("candidate_id")
    @classmethod
    def _validate_candidate_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("target_claim")
    @classmethod
    def _validate_target_claim(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        return validate_artifact_id(stripped)

    @field_validator("construction_summary")
    @classmethod
    def _validate_construction_summary(cls, value: str) -> str:
        return _validate_non_empty_text(
            value,
            field_name="counterexample construction summary",
        )

    @field_validator("evidence_paths")
    @classmethod
    def _validate_evidence_paths(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_repo_local_path(value) for value in values
        )

    @field_validator("verifier_request_ids")
    @classmethod
    def _validate_verifier_request_ids(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            validate_artifact_id(value.strip()) for value in values
        )

    @field_validator("limitations")
    @classmethod
    def _validate_limitations(cls, value: str) -> str:
        return _validate_non_empty_text(
            value,
            field_name="counterexample limitations",
        )

    @model_validator(mode="after")
    def _checked_candidates_need_evidence(self) -> Self:
        if (
            self.status
            in {
                CounterexampleCandidateStatus.CHECKED_FALSE,
                CounterexampleCandidateStatus.CHECKED_TRUE,
            }
            and not self.evidence_paths
        ):
            raise ValueError(f"{self.status.value} requires evidence_paths")
        return self


class WorkerBundleV2(BaseModel):
    """Strict Phase 4.3 worker-output bundle.

    Workers may propose draft artifacts, assumptions, uncertainty, verification
    requests, failed attempts, counterexample candidates, dependency questions,
    risks, and next steps. They may not create review authority or accepted
    knowledge.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    bundle_id: str
    task_id: str
    worker_role: WorkerType
    created_at: datetime
    summary: str
    used_artifacts: list[str] = Field(default_factory=list)
    used_sources: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    proposed_artifacts: list[ProposedArtifact] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    verification_requests: list[str] = Field(default_factory=list)
    failed_attempts: list[str] = Field(default_factory=list)
    counterexamples: list[str] = Field(default_factory=list)
    counterexample_candidates: list[CounterexampleCandidate] = Field(
        default_factory=list
    )
    failures_or_counterexamples: list[str] = Field(default_factory=list)
    dependency_questions: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    confidence: WorkerBundleConfidence

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic machine-readable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this bundle."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"

    @field_validator("bundle_id", "task_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("created_at")
    @classmethod
    def _validate_created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information")
        return value.astimezone(UTC).replace(microsecond=0)

    @field_validator("summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="summary")

    @field_validator("used_artifacts")
    @classmethod
    def _validate_used_artifacts(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            validate_artifact_id(value.strip()) for value in values
        )

    @field_validator(
        "used_sources",
        "claims",
        "assumptions",
        "uncertainty",
        "verification_requests",
        "failed_attempts",
        "counterexamples",
        "failures_or_counterexamples",
        "dependency_questions",
        "risk_flags",
        "next_steps",
    )
    @classmethod
    def _normalize_text_list(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_non_empty_text(value, field_name="bundle text field")
            for value in values
        )


def validate_worker_bundle_v2(
    context: RepoContext,
    bundle_path: str | Path,
) -> WorkerBundleV2:
    """Load and validate a worker bundle v2 manifest."""
    manifest_path = _resolve_manifest_path(context, bundle_path)
    raw = _read_yaml_mapping(manifest_path)
    try:
        bundle = WorkerBundleV2.model_validate(raw)
    except ValidationError as exc:
        message = _format_errors(exc)
        raise WorkerBundleV2Error(f"invalid worker bundle v2: {message}") from exc

    for proposed in bundle.proposed_artifacts:
        _validate_proposed_artifact(context, proposed)

    return bundle


def reduce_worker_bundle_v2(
    context: RepoContext,
    bundle_path: str | Path,
    *,
    reducer_id: str,
) -> ReducerResult:
    """Validate and reduce a bundle v2 manifest into a deterministic result."""
    bundle = validate_worker_bundle_v2(context, bundle_path)
    return ReducerResult(
        reducer_id=reducer_id,
        status="accepted_for_review",
        summary=bundle.summary,
        output_paths=[artifact.path for artifact in bundle.proposed_artifacts],
        warnings=worker_bundle_review_warnings(bundle),
    )


def worker_bundle_review_warnings(bundle: WorkerBundleV2) -> list[str]:
    """Return reducer/review warnings while preserving non-authoritative output.

    Verification requests stay explicitly labeled as requests, and
    counterexamples stay candidate review evidence. This function does not
    create verifier results, refute accepted knowledge, or promote artifacts.
    """
    return _dedupe_preserving_order(
        [
            *(f"assumption: {item}" for item in bundle.assumptions),
            *(f"uncertainty: {item}" for item in bundle.uncertainty),
            *(
                f"verification_request: {item}"
                for item in bundle.verification_requests
            ),
            *(f"failed_attempt: {item}" for item in bundle.failed_attempts),
            *(
                f"counterexample_candidate: {item}"
                for item in bundle.counterexamples
            ),
            *(
                _counterexample_candidate_warning(candidate)
                for candidate in bundle.counterexample_candidates
            ),
            *bundle.failures_or_counterexamples,
            *(
                f"dependency_question: {item}"
                for item in bundle.dependency_questions
            ),
            *(f"risk: {flag}" for flag in bundle.risk_flags),
            f"confidence: {bundle.confidence.value}",
        ]
    )


def _counterexample_candidate_warning(candidate: CounterexampleCandidate) -> str:
    target = f" target={candidate.target_claim}" if candidate.target_claim else ""
    evidence = (
        ",".join(candidate.evidence_paths) if candidate.evidence_paths else "none"
    )
    verifier_requests = (
        ",".join(candidate.verifier_request_ids)
        if candidate.verifier_request_ids
        else "none"
    )
    return (
        "counterexample_candidate: "
        f"{candidate.candidate_id} status={candidate.status.value}{target} "
        f"evidence_paths={evidence} "
        f"verifier_request_ids={verifier_requests} "
        f"summary={candidate.construction_summary} "
        f"limitations={candidate.limitations}"
    )


def _resolve_manifest_path(context: RepoContext, bundle_path: str | Path) -> Path:
    path = Path(bundle_path)
    resolved = path.resolve() if path.is_absolute() else context.resolve(path)
    if resolved.is_dir():
        resolved = resolved / "bundle.yaml"

    try:
        resolved.relative_to(context.repo_root)
    except ValueError:
        raise WorkerBundleV2Error(
            "worker bundle v2 must be inside the repository"
        ) from None

    if not resolved.is_file():
        raise WorkerBundleV2Error(f"worker bundle v2 not found: {resolved}")
    return resolved


def _read_yaml_mapping(path: Path) -> dict[str, object]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except YAMLError as exc:
        raise WorkerBundleV2Error(f"invalid worker bundle v2 YAML: {exc}") from exc
    except OSError as exc:
        raise WorkerBundleV2Error(f"cannot read worker bundle v2: {exc}") from exc

    if not isinstance(raw, dict):
        raise WorkerBundleV2Error("worker bundle v2 must be a YAML mapping")
    return raw


def _validate_proposed_artifact(
    context: RepoContext,
    proposed: ProposedArtifact,
) -> None:
    relative_path = Path(proposed.path)
    resolved = context.resolve(relative_path)
    try:
        resolved.relative_to(context.repo_root)
    except ValueError:
        raise WorkerBundleV2Error(
            f"proposed artifact path must be repository-local: {proposed.path}"
        ) from None

    _reject_accepted_knowledge_path(proposed.path)

    if not resolved.exists():
        return

    gate_result = load_schema_valid_record(context, relative_path)
    if gate_result.failures:
        messages = "; ".join(failure.message for failure in gate_result.failures)
        raise WorkerBundleV2Error(
            f"proposed artifact did not pass schema gate: {proposed.path}: {messages}"
        )

    record = _single_loaded_record(gate_result.records, proposed.path)
    if isinstance(record.record, BaseArtifact) and record.record.review.state in {
        "human_reviewed",
        "accepted",
    }:
        raise WorkerBundleV2Error(
            "worker bundle v2 must not create human_reviewed or accepted "
            f"review state: {proposed.path}"
        )


def _single_loaded_record(
    records: tuple[LoadedRecord, ...],
    path: str,
) -> LoadedRecord:
    if len(records) != 1:
        raise WorkerBundleV2Error(f"expected exactly one loaded record for {path}")
    return records[0]


def _validate_repo_local_path(value: str) -> str:
    normalized = normalize_repo_path(value)
    is_absolute = Path(value).is_absolute() or PureWindowsPath(value).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or is_absolute
        or normalized == ".."
        or normalized.startswith("../")
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    _reject_accepted_knowledge_path(normalized)
    return normalized


def _reject_accepted_knowledge_path(path: str) -> None:
    parts = PurePosixPath(normalize_repo_path(path)).parts
    if "accepted" in parts and (
        parts[0] == "kb" or (len(parts) >= 2 and parts[0] == "kb")
    ):
        raise WorkerBundleV2Error(
            "worker bundle v2 must not target accepted knowledge: "
            f"{normalize_repo_path(path)}"
        )


def _validate_non_empty_text(value: str, *, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must be non-empty")
    return stripped


def _dedupe_preserving_order(values: Any) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _format_errors(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
