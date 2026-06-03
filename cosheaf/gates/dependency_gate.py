"""ID uniqueness and dependency gates."""

from __future__ import annotations

from collections import defaultdict

from cosheaf.core.artifact import BaseArtifact
from cosheaf.core.status import ArtifactStatus, is_preaccepted_status
from cosheaf.gates.schema_gate import ValidationFailure
from cosheaf.storage.loader import LoadedRecord


def validate_id_uniqueness(
    records: tuple[LoadedRecord, ...],
) -> list[ValidationFailure]:
    """Validate global uniqueness for loaded record IDs."""
    paths_by_id: defaultdict[str, list[str]] = defaultdict(list)
    for loaded in records:
        paths_by_id[loaded.id].append(loaded.source_path.as_posix())

    failures: list[ValidationFailure] = []
    for artifact_id in sorted(paths_by_id):
        paths = sorted(paths_by_id[artifact_id])
        if len(paths) <= 1:
            continue
        failures.append(
            ValidationFailure(
                gate="id uniqueness",
                source_path=paths[0],
                artifact_id=artifact_id,
                message=f"duplicate id {artifact_id}: {', '.join(paths)}",
            )
        )
    return failures


def validate_dependencies(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]:
    """Validate dependency existence and accepted-to-draft dependency rules."""
    artifact_records = [
        loaded for loaded in records if isinstance(loaded.record, BaseArtifact)
    ]
    artifacts_by_id = {
        loaded.id: loaded for loaded in sorted(artifact_records, key=_record_sort_key)
    }

    failures: list[ValidationFailure] = []
    for loaded in sorted(artifact_records, key=_record_sort_key):
        artifact = loaded.record
        if not isinstance(artifact, BaseArtifact):
            continue
        for dependency_id in artifact.depends_on:
            dependency = artifacts_by_id.get(dependency_id)
            if dependency is None:
                failures.append(
                    ValidationFailure(
                        gate="dependency",
                        source_path=loaded.source_path.as_posix(),
                        artifact_id=artifact.id,
                        message=f"missing dependency: {dependency_id}",
                    )
                )
                continue

            dependency_record = dependency.record
            if not isinstance(dependency_record, BaseArtifact):
                continue
            if _public_depends_on_private(loaded, dependency):
                failures.append(
                    ValidationFailure(
                        gate="dependency",
                        source_path=loaded.source_path.as_posix(),
                        artifact_id=artifact.id,
                        message=(
                            "public artifact depends on private artifact: "
                            f"{dependency_id} at {dependency.source_path.as_posix()}"
                        ),
                    )
                )
            if (
                artifact.status is ArtifactStatus.ACCEPTED
                and is_preaccepted_status(dependency_record.status)
            ):
                failures.append(
                    ValidationFailure(
                        gate="dependency",
                        source_path=loaded.source_path.as_posix(),
                        artifact_id=artifact.id,
                        message=(
                            "accepted artifact depends on draft artifact: "
                            f"{dependency_id} at {dependency.source_path.as_posix()}"
                        ),
                    )
                )

    return failures


def _public_depends_on_private(source: LoadedRecord, dependency: LoadedRecord) -> bool:
    return source.kb_root_name == "public" and dependency.kb_root_name == "private"


def _record_sort_key(record: LoadedRecord) -> tuple[str, str]:
    return (record.source_path.as_posix(), record.id)

