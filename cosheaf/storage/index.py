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
    kb_root: str
    formalizations: tuple[_IndexedFormalization, ...]
    alignment_status: str
    alignment_reviewer: str
    verification_level: str
    require_formal_link: bool
    require_lean_check: bool
    require_alignment_review: bool


@dataclass(frozen=True)
class _IndexedFormalization:
    """Normalized formalization-reference row for deterministic index output."""

    artifact_id: str
    formalization_id: str
    system: str
    library: str
    library_ref: str
    import_path: str
    symbol: str
    declaration_kind: str
    status: str
    check_mode: str
    expected_type: str
    notes: str


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
                kb_root=loaded.kb_root_name or "",
                formalizations=_indexed_formalizations(record),
                alignment_status=record.alignment.status,
                alignment_reviewer=record.alignment.reviewer,
                verification_level=record.verification_policy.level,
                require_formal_link=record.verification_policy.require_formal_link,
                require_lean_check=record.verification_policy.require_lean_check,
                require_alignment_review=(
                    record.verification_policy.require_alignment_review
                ),
            )
        )
    return tuple(sorted(artifacts, key=lambda artifact: artifact.artifact_id))


def _indexed_formalizations(
    artifact: BaseArtifact,
) -> tuple[_IndexedFormalization, ...]:
    formalizations = [
        _IndexedFormalization(
            artifact_id=artifact.id,
            formalization_id=ref.id,
            system=ref.system,
            library=ref.library,
            library_ref=ref.library_ref,
            import_path=ref.import_path,
            symbol=ref.symbol,
            declaration_kind=ref.declaration_kind,
            status=ref.status,
            check_mode=ref.check_mode,
            expected_type=ref.expected_type,
            notes=ref.notes,
        )
        for ref in artifact.formalizations
    ]
    return tuple(
        sorted(
            formalizations,
            key=lambda formalization: (
                formalization.artifact_id,
                formalization.formalization_id,
            ),
        )
    )


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
    formalizations = tuple(
        formalization
        for artifact in artifacts
        for formalization in artifact.formalizations
    )
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
                domain TEXT NOT NULL,
                kb_root TEXT NOT NULL
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
        connection.execute(
            """
            CREATE TABLE formalizations (
                artifact_id TEXT NOT NULL,
                formalization_id TEXT NOT NULL,
                system TEXT NOT NULL,
                library TEXT NOT NULL,
                library_ref TEXT NOT NULL,
                import_path TEXT NOT NULL,
                symbol TEXT NOT NULL,
                declaration_kind TEXT NOT NULL,
                status TEXT NOT NULL,
                check_mode TEXT NOT NULL,
                expected_type TEXT NOT NULL,
                notes TEXT NOT NULL,
                PRIMARY KEY (artifact_id, formalization_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE artifact_formal_policy (
                artifact_id TEXT PRIMARY KEY,
                alignment_status TEXT NOT NULL,
                alignment_reviewer TEXT NOT NULL,
                verification_level TEXT NOT NULL,
                require_formal_link INTEGER NOT NULL,
                require_lean_check INTEGER NOT NULL,
                require_alignment_review INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX idx_formalizations_symbol ON formalizations (symbol)"
        )
        connection.execute(
            "CREATE INDEX idx_formalizations_library ON formalizations (library)"
        )
        connection.execute(
            "CREATE INDEX idx_formalizations_status ON formalizations (status)"
        )
        connection.execute(
            """
            CREATE INDEX idx_formalizations_import_path
            ON formalizations (import_path)
            """
        )
        connection.executemany(
            """
            INSERT INTO artifacts (id, type, status, path, title, domain, kb_root)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    artifact.artifact_id,
                    artifact.artifact_type,
                    artifact.status,
                    artifact.path,
                    artifact.title,
                    json.dumps(list(artifact.domain), ensure_ascii=True),
                    artifact.kb_root,
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
        connection.executemany(
            """
            INSERT INTO formalizations (
                artifact_id, formalization_id, system, library, library_ref,
                import_path, symbol, declaration_kind, status, check_mode,
                expected_type, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    formalization.artifact_id,
                    formalization.formalization_id,
                    formalization.system,
                    formalization.library,
                    formalization.library_ref,
                    formalization.import_path,
                    formalization.symbol,
                    formalization.declaration_kind,
                    formalization.status,
                    formalization.check_mode,
                    formalization.expected_type,
                    formalization.notes,
                )
                for formalization in formalizations
            ],
        )
        connection.executemany(
            """
            INSERT INTO artifact_formal_policy (
                artifact_id, alignment_status, alignment_reviewer,
                verification_level, require_formal_link, require_lean_check,
                require_alignment_review
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    artifact.artifact_id,
                    artifact.alignment_status,
                    artifact.alignment_reviewer,
                    artifact.verification_level,
                    int(artifact.require_formal_link),
                    int(artifact.require_lean_check),
                    int(artifact.require_alignment_review),
                )
                for artifact in artifacts
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
                "kb_root": artifact.kb_root,
                "formalizations": [
                    {
                        "id": formalization.formalization_id,
                        "system": formalization.system,
                        "library": formalization.library,
                        "library_ref": formalization.library_ref,
                        "import_path": formalization.import_path,
                        "symbol": formalization.symbol,
                        "declaration_kind": formalization.declaration_kind,
                        "status": formalization.status,
                        "check_mode": formalization.check_mode,
                    }
                    for formalization in artifact.formalizations
                ],
                "alignment_status": artifact.alignment_status,
                "verification_policy": {
                    "level": artifact.verification_level,
                    "require_formal_link": artifact.require_formal_link,
                    "require_lean_check": artifact.require_lean_check,
                    "require_alignment_review": (
                        artifact.require_alignment_review
                    ),
                },
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
