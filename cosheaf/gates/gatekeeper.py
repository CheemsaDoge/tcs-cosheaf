"""Thin repository validation orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cosheaf.gates.dependency_gate import (
    validate_dependencies,
    validate_id_uniqueness,
)
from cosheaf.gates.schema_gate import (
    ValidationFailure,
    load_schema_valid_record,
    load_schema_valid_records,
    sort_failures,
)
from cosheaf.gates.status_gate import (
    validate_evidence_paths,
    validate_status_paths,
)
from cosheaf.storage.loader import LoadedRecord
from cosheaf.storage.repo import RepoContext


@dataclass(frozen=True)
class ValidationReport:
    """Validation result for a repository or a single artifact file."""

    records: tuple[LoadedRecord, ...]
    failures: tuple[ValidationFailure, ...]

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def checked_count(self) -> int:
        return len(self.records)


def validate_repository(context: RepoContext) -> ValidationReport:
    """Validate a repository checkout using the implemented MVP gates."""
    schema_result = load_schema_valid_records(context)
    records = schema_result.records
    failures: list[ValidationFailure] = list(schema_result.failures)
    failures.extend(validate_id_uniqueness(records))
    failures.extend(validate_status_paths(records))
    failures.extend(validate_dependencies(records))
    failures.extend(validate_evidence_paths(context, records))

    return ValidationReport(records=records, failures=sort_failures(failures))


def validate_artifact_file(context: RepoContext, path: Path) -> ValidationReport:
    """Validate one YAML file with file-local checks."""
    schema_result = load_schema_valid_record(context, path)
    records = schema_result.records
    failures: list[ValidationFailure] = list(schema_result.failures)
    failures.extend(validate_status_paths(records))
    failures.extend(validate_evidence_paths(context, records))

    return ValidationReport(records=records, failures=sort_failures(failures))

