"""Checked counterexample evidence records.

Checked counterexample evidence is durable review evidence. It does not mark an
artifact refuted, create human review, or authorize accepted promotion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, Self

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from yaml import YAMLError

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path, repo_relative_posix
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE = (
    "Checked counterexample evidence is evidence for review only; it is not "
    "human review, accepted refutation, accepted status, or promotion authority."
)
SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION = (
    "Skipped checked counterexample evidence is not pass evidence."
)
CHECKED_COUNTEREXAMPLE_EVIDENCE_ROOT = Path(
    "reviews"
) / "evidence" / "checked-counterexamples"
AUTHORITY_CLAIM_FIELDS = frozenset(
    {
        "accepted",
        "artifact_status",
        "human_reviewed",
        "promote",
        "review_state",
    }
)


class CheckedCounterexampleEvidenceError(ValueError):
    """Expected checked-evidence service failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        remediation: str,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.remediation = remediation
        self.details = dict(details or {})


class CandidateSource(StrEnum):
    """Where a counterexample candidate originated."""

    WORKER_BUNDLE = "worker_bundle"
    FAILURE_LOG = "failure_log"
    ARTIFACT = "artifact"
    MANUAL_NOTE = "manual_note"
    VERIFIER = "verifier"


class CheckMethod(StrEnum):
    """How a candidate was checked."""

    VERIFIER_RESULT = "verifier_result"
    MANUAL_REVIEW_REFERENCE = "manual_review_reference"
    EXECUTABLE_CHECK = "executable_check"
    PROOF_SKETCH_REVIEW = "proof_sketch_review"
    OTHER = "other"


class CheckedResult(StrEnum):
    """Outcome of a checked counterexample evidence record."""

    CHECKED_REFUTES = "checked_refutes"
    CHECKED_DOES_NOT_REFUTE = "checked_does_not_refute"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"
    SKIPPED = "skipped"


class CheckedCounterexampleEvidenceRecord(BaseModel):
    """Durable v1 checked counterexample evidence record."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    schema_version: Literal[1] = 1
    evidence_id: str
    target_artifact_id: str
    candidate_id: str
    candidate_source: CandidateSource
    check_method: CheckMethod
    checked_result: CheckedResult
    verifier_evidence_ids: tuple[str, ...] = ()
    review_record_paths: tuple[str, ...] = ()
    evidence_paths: tuple[str, ...] = ()
    created_at: datetime
    checker: str
    limitations: tuple[str, ...]

    @field_validator("evidence_id", "target_artifact_id", "candidate_id")
    @classmethod
    def _artifact_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("verifier_evidence_ids", mode="before")
    @classmethod
    def _verifier_evidence_ids(cls, value: Any) -> tuple[str, ...]:
        return tuple(validate_artifact_id(item) for item in _text_items(value))

    @field_validator("review_record_paths", "evidence_paths", mode="before")
    @classmethod
    def _repo_paths(cls, value: Any) -> tuple[str, ...]:
        return tuple(
            _validate_repo_local_nonaccepted_path(item)
            for item in _text_items(value)
        )

    @field_validator("created_at")
    @classmethod
    def _created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information")
        return value

    @field_validator("checker")
    @classmethod
    def _checker(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("checker must be non-empty")
        return normalized

    @field_validator("limitations", mode="before")
    @classmethod
    def _limitations(cls, value: Any) -> tuple[str, ...]:
        normalized = tuple(dict.fromkeys(_text_items(value)))
        if not normalized:
            raise ValueError("limitations must contain at least one item")
        return normalized

    @model_validator(mode="after")
    def _record_consistency(self) -> Self:
        support_count = (
            len(self.verifier_evidence_ids)
            + len(self.review_record_paths)
            + len(self.evidence_paths)
        )
        if self.checked_result is CheckedResult.CHECKED_REFUTES and support_count == 0:
            raise ValueError(
                "checked_refutes requires verifier evidence, review record, "
                "or evidence path support"
            )
        if (
            self.checked_result is CheckedResult.SKIPPED
            and SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION not in self.limitations
        ):
            raise ValueError("skipped is not pass for checked counterexample evidence")
        if CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE not in self.limitations:
            raise ValueError(
                "limitations must include the checked-evidence authority notice"
            )
        return self

    @property
    def is_checked_refutation(self) -> bool:
        """Return whether this record says the checked candidate refutes the target."""
        return self.checked_result is CheckedResult.CHECKED_REFUTES

    @property
    def is_skipped(self) -> bool:
        """Return whether this record is an honest skipped check."""
        return self.checked_result is CheckedResult.SKIPPED

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this record."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


@dataclass(frozen=True)
class CheckedCounterexampleEvidenceStagingResult:
    """Result of staging or previewing checked counterexample evidence."""

    record: CheckedCounterexampleEvidenceRecord
    relative_path: Path
    written_paths: tuple[Path, ...]
    dry_run: bool
    accepted_write_performed: Literal[False] = False

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable CLI payload fields."""
        return {
            "schema_version": 1,
            "kind": "checked_counterexample_evidence",
            "path": self.relative_path.as_posix(),
            "written_paths": [path.as_posix() for path in self.written_paths],
            "dry_run": self.dry_run,
            "accepted_write_performed": self.accepted_write_performed,
            "record_id": self.record.evidence_id,
            "authority_notice": CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
            "evidence": self.record.to_dict(),
        }


@dataclass(frozen=True)
class CheckedCounterexampleEvidenceLoadResult:
    """One loaded checked evidence record and its repository path."""

    record: CheckedCounterexampleEvidenceRecord
    relative_path: Path

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-serializable CLI payload fields."""
        return {
            "schema_version": 1,
            "kind": "checked_counterexample_evidence",
            "path": self.relative_path.as_posix(),
            "accepted_write_performed": False,
            "authority_notice": CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
            "evidence": self.record.to_dict(),
        }


def reject_authority_claim_fields(payload: dict[str, Any]) -> None:
    """Reject top-level authority spoofing fields before model validation."""
    present = sorted(AUTHORITY_CLAIM_FIELDS.intersection(payload))
    if not present:
        return
    raise CheckedCounterexampleEvidenceError(
        "checked counterexample evidence input cannot claim review, accepted, "
        "or promotion authority",
        code="authority_claim_forbidden",
        remediation=(
            "Remove authority fields. Checked counterexample evidence is review "
            "evidence only and cannot mark human review, accepted status, or "
            "promotion."
        ),
        details={"forbidden_fields": ",".join(present)},
    )


def validate_checked_counterexample_evidence_payload(
    payload: dict[str, Any],
) -> CheckedCounterexampleEvidenceRecord:
    """Validate one checked counterexample evidence payload."""
    reject_authority_claim_fields(payload)
    return CheckedCounterexampleEvidenceRecord.model_validate(payload)


def stage_checked_counterexample_evidence(
    context: RepoContext,
    payload: dict[str, Any],
    *,
    dry_run: bool = False,
) -> CheckedCounterexampleEvidenceStagingResult:
    """Write or preview a checked counterexample evidence record."""
    record = validate_checked_counterexample_evidence_payload(payload)
    relative_path = checked_counterexample_evidence_path(record.evidence_id)
    target = context.resolve(relative_path)
    _ensure_repo_local_target(context, target)
    if target.exists():
        raise CheckedCounterexampleEvidenceError(
            "checked counterexample evidence path already exists: "
            f"{relative_path.as_posix()}",
            code="checked_evidence_path_exists",
            remediation="Choose a new evidence_id or inspect the existing record.",
            details={"path": relative_path.as_posix()},
        )
    if dry_run:
        return CheckedCounterexampleEvidenceStagingResult(
            record=record,
            relative_path=relative_path,
            written_paths=(),
            dry_run=True,
        )
    write_yaml_deterministic(target, record)
    return CheckedCounterexampleEvidenceStagingResult(
        record=record,
        relative_path=relative_path,
        written_paths=(relative_path,),
        dry_run=False,
    )


def checked_counterexample_evidence_path(evidence_id: str) -> Path:
    """Return the controlled staging path for an evidence ID."""
    validate_artifact_id(evidence_id)
    return CHECKED_COUNTEREXAMPLE_EVIDENCE_ROOT / f"{evidence_id}.yaml"


def show_checked_counterexample_evidence(
    context: RepoContext,
    evidence: str,
) -> CheckedCounterexampleEvidenceLoadResult:
    """Load checked evidence by repository-local path or evidence ID."""
    relative_path = _resolve_evidence_reference(context, evidence)
    if relative_path is None:
        raise CheckedCounterexampleEvidenceError(
            f"checked counterexample evidence not found: {evidence}",
            code="checked_evidence_not_found",
            remediation="Stage the evidence first or provide a repository-local path.",
            details={"evidence": evidence},
        )
    record = _load_record(context, relative_path)
    return CheckedCounterexampleEvidenceLoadResult(
        record=record,
        relative_path=relative_path,
    )


def load_checked_counterexample_evidence(
    context: RepoContext,
) -> tuple[CheckedCounterexampleEvidenceLoadResult, ...]:
    """Load all staged checked counterexample evidence records."""
    root = context.resolve(CHECKED_COUNTEREXAMPLE_EVIDENCE_ROOT)
    if not root.exists():
        return ()
    results: list[CheckedCounterexampleEvidenceLoadResult] = []
    for path in sorted(root.glob("*.yaml")):
        try:
            relative_path = Path(repo_relative_posix(context.repo_root, path))
            record = _load_record(context, relative_path)
        except (OSError, ValueError, CheckedCounterexampleEvidenceError):
            continue
        results.append(
            CheckedCounterexampleEvidenceLoadResult(
                record=record,
                relative_path=relative_path,
            )
        )
    return tuple(results)


def _resolve_evidence_reference(context: RepoContext, evidence: str) -> Path | None:
    value = evidence.strip()
    if not value:
        return None
    path_like = any(separator in value for separator in ("/", "\\")) or value.endswith(
        (".yaml", ".yml")
    )
    if path_like:
        normalized = _validate_repo_local_nonaccepted_path(value)
        relative_path = Path(normalized)
        target = context.resolve(relative_path)
        return relative_path if target.is_file() else None

    evidence_id = validate_artifact_id(value)
    relative_path = checked_counterexample_evidence_path(evidence_id)
    target = context.resolve(relative_path)
    return relative_path if target.is_file() else None


def _load_record(
    context: RepoContext,
    relative_path: Path,
) -> CheckedCounterexampleEvidenceRecord:
    path = context.resolve(relative_path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, YAMLError) as exc:
        raise CheckedCounterexampleEvidenceError(
            f"cannot read checked counterexample evidence: {exc}",
            code="checked_evidence_not_found",
            remediation="Provide a readable checked evidence YAML file.",
            details={"path": relative_path.as_posix()},
        ) from exc
    if not isinstance(raw, dict):
        raise CheckedCounterexampleEvidenceError(
            "checked counterexample evidence YAML must be a mapping",
            code="checked_evidence_validation_failed",
            remediation="Fix the staged checked evidence YAML file.",
            details={"path": relative_path.as_posix()},
        )
    return validate_checked_counterexample_evidence_payload(dict(raw))


def _validate_repo_local_nonaccepted_path(value: str) -> str:
    raw = str(value).strip()
    normalized = normalize_repo_path(raw)
    is_absolute = Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or normalized == "."
        or normalized == ".."
        or normalized.startswith("../")
        or normalized.startswith("/")
        or is_absolute
        or ".." in parts
    ):
        raise ValueError("path must be repository-local")
    if parts and parts[0] == "kb" and "accepted" in parts:
        raise ValueError(
            "checked counterexample evidence cannot reference accepted KB paths"
        )
    return normalized


def _text_items(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    values: tuple[str, ...]
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(str(item) for item in value)
        except TypeError as exc:
            raise ValueError("field must be a sequence of strings") from exc
    return tuple(item.strip() for item in values if item.strip())


def _ensure_repo_local_target(context: RepoContext, target: Path) -> None:
    try:
        target.resolve().relative_to(context.repo_root.resolve())
    except ValueError as exc:
        raise CheckedCounterexampleEvidenceError(
            "checked counterexample evidence target must stay repository-local",
            code="invalid_staging_path",
            remediation="Use the controlled checked evidence staging path.",
        ) from exc


__all__ = [
    "AUTHORITY_CLAIM_FIELDS",
    "CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE",
    "CHECKED_COUNTEREXAMPLE_EVIDENCE_ROOT",
    "SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION",
    "CandidateSource",
    "CheckMethod",
    "CheckedCounterexampleEvidenceError",
    "CheckedCounterexampleEvidenceLoadResult",
    "CheckedCounterexampleEvidenceRecord",
    "CheckedCounterexampleEvidenceStagingResult",
    "CheckedResult",
    "checked_counterexample_evidence_path",
    "load_checked_counterexample_evidence",
    "reject_authority_claim_fields",
    "show_checked_counterexample_evidence",
    "stage_checked_counterexample_evidence",
    "validate_checked_counterexample_evidence_payload",
]
