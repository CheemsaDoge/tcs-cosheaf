"""Deterministic SQLite and manifest index rebuilds."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.loader import LoadedRecord, load_artifacts
from cosheaf.storage.repo import RepoContext


@dataclass(frozen=True)
class IndexRebuildResult:
    """Paths and counts produced by an index rebuild."""

    sqlite_path: Path
    manifest_path: Path
    artifact_count: int
    edge_count: int


@dataclass(frozen=True)
class _IndexedArtifact:
    """Normalized artifact row for deterministic index output."""

    artifact_id: str
    artifact_type: str
    status: str
    path: str
    title: str
    domain: tuple[str, ...]


@dataclass(frozen=True)
class _IndexedDependency:
    """Normalized dependency row for deterministic index output."""

    source_id: str
    target_id: str


def rebuild_index(context: RepoContext) -> IndexRebuildResult:
    """Rebuild `.cosheaf` index outputs from loaded repository artifacts."""
    records = tuple(load_artifacts(context))
    artifacts = _indexed_artifacts(records)
    dependencies = _indexed_dependencies(records)

    output_dir = context.resolve(".cosheaf")
    output_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = output_dir / "index.sqlite"
    manifest_path = output_dir / "artifact_manifest.json"

    if sqlite_path.exists():
        sqlite_path.unlink()

    _write_sqlite(sqlite_path, artifacts, dependencies)
    _write_manifest(manifest_path, artifacts, dependencies)

    return IndexRebuildResult(
        sqlite_path=sqlite_path,
        manifest_path=manifest_path,
        artifact_count=len(artifacts),
        edge_count=len(dependencies),
    )


def _indexed_artifacts(
    records: tuple[LoadedRecord, ...],
) -> tuple[_IndexedArtifact, ...]:
    artifacts: list[_IndexedArtifact] = []
    for loaded in records:
        record = loaded.record
        if not isinstance(record, BaseArtifact):
            continue
        artifacts.append(
            _IndexedArtifact(
                artifact_id=record.id,
                artifact_type=record.type.value,
                status=record.status.value,
                path=loaded.source_path.as_posix(),
                title=record.title,
                domain=tuple(record.domain),
            )
        )
    return tuple(sorted(artifacts, key=lambda artifact: artifact.artifact_id))


def _indexed_dependencies(
    records: tuple[LoadedRecord, ...],
) -> tuple[_IndexedDependency, ...]:
    dependencies: list[_IndexedDependency] = []
    for loaded in records:
        record = loaded.record
        if not isinstance(record, BaseArtifact):
            continue
        dependencies.extend(
            _IndexedDependency(source_id=record.id, target_id=dependency_id)
            for dependency_id in record.depends_on
        )
    return tuple(
        sorted(
            dependencies,
            key=lambda dependency: (dependency.source_id, dependency.target_id),
        )
    )


def _write_sqlite(
    sqlite_path: Path,
    artifacts: tuple[_IndexedArtifact, ...],
    dependencies: tuple[_IndexedDependency, ...],
) -> None:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE artifacts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                path TEXT NOT NULL,
                title TEXT NOT NULL,
                domain TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE dependencies (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                PRIMARY KEY (source_id, target_id)
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO artifacts (id, type, status, path, title, domain)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    artifact.artifact_id,
                    artifact.artifact_type,
                    artifact.status,
                    artifact.path,
                    artifact.title,
                    json.dumps(list(artifact.domain), ensure_ascii=True),
                )
                for artifact in artifacts
            ],
        )
        connection.executemany(
            """
            INSERT INTO dependencies (source_id, target_id)
            VALUES (?, ?)
            """,
            [
                (dependency.source_id, dependency.target_id)
                for dependency in dependencies
            ],
        )
        connection.commit()


def _write_manifest(
    manifest_path: Path,
    artifacts: tuple[_IndexedArtifact, ...],
    dependencies: tuple[_IndexedDependency, ...],
) -> None:
    manifest = {
        "artifacts": [
            {
                "id": artifact.artifact_id,
                "type": artifact.artifact_type,
                "status": artifact.status,
                "path": artifact.path,
                "title": artifact.title,
                "domain": list(artifact.domain),
            }
            for artifact in artifacts
        ],
        "dependencies": [
            {
                "source_id": dependency.source_id,
                "target_id": dependency.target_id,
            }
            for dependency in dependencies
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
