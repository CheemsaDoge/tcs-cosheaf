"""Schema and model parsing gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from cosheaf.core.paths import is_yaml_path, repo_relative_posix
from cosheaf.storage.loader import (
    LoadedRecord,
    LoadError,
    discover_yaml_paths,
    load_yaml_file,
)
from cosheaf.storage.repo import RepoContext


@dataclass(frozen=True)
class ValidationFailure:
    """A deterministic validation failure row."""

    gate: str
    source_path: str
    artifact_id: str
    message: str


@dataclass(frozen=True)
class SchemaGateResult:
    """Records and failures produced by schema/model loading."""

    records: tuple[LoadedRecord, ...]
    failures: tuple[ValidationFailure, ...]


def sort_failures(
    failures: Iterable[ValidationFailure],
) -> tuple[ValidationFailure, ...]:
    """Return failures in deterministic display order."""
    return tuple(
        sorted(
            failures,
            key=lambda failure: (
                failure.source_path,
                failure.artifact_id,
                failure.gate,
                failure.message,
            ),
        )
    )


def load_schema_valid_records(context: RepoContext) -> SchemaGateResult:
    """Load repository YAML records and collect schema/model failures."""
    records: list[LoadedRecord] = []
    failures: list[ValidationFailure] = []

    for path in discover_yaml_paths(context):
        result = load_schema_valid_record(context, path)
        records.extend(result.records)
        failures.extend(result.failures)

    return SchemaGateResult(
        records=tuple(sorted(records, key=lambda record: _record_sort_key(record))),
        failures=sort_failures(failures),
    )


def load_schema_valid_record(context: RepoContext, path: Path) -> SchemaGateResult:
    """Load a single YAML record and collect expected validation failures."""
    resolved_path = path.resolve() if path.is_absolute() else context.resolve(path)
    display_path = _display_path(context, resolved_path)

    if not is_yaml_path(resolved_path):
        return SchemaGateResult(
            records=(),
            failures=(
                ValidationFailure(
                    gate="schema",
                    source_path=display_path,
                    artifact_id="",
                    message="expected a YAML file with .yaml or .yml suffix",
                ),
            ),
        )

    try:
        resolved_path.relative_to(context.repo_root)
    except ValueError:
        return SchemaGateResult(
            records=(),
            failures=(
                ValidationFailure(
                    gate="schema",
                    source_path=display_path,
                    artifact_id="",
                    message="path is outside the repository root",
                ),
            ),
        )

    try:
        record = load_yaml_file(context, resolved_path)
    except LoadError as exc:
        return SchemaGateResult(
            records=(),
            failures=(
                ValidationFailure(
                    gate="schema",
                    source_path=display_path,
                    artifact_id="",
                    message=str(exc),
                ),
            ),
        )
    except OSError as exc:
        return SchemaGateResult(
            records=(),
            failures=(
                ValidationFailure(
                    gate="schema",
                    source_path=display_path,
                    artifact_id="",
                    message=f"cannot read YAML file: {exc}",
                ),
            ),
        )

    return SchemaGateResult(records=(record,), failures=())


def _record_sort_key(record: LoadedRecord) -> tuple[str, str]:
    return (record.source_path.as_posix(), record.id)


def _display_path(context: RepoContext, path: Path) -> str:
    try:
        return repo_relative_posix(context.repo_root, path)
    except ValueError:
        return str(path)
