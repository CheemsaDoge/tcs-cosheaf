"""SQLite-backed artifact queries over deterministic index rebuild output."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.storage.repo import RepoContext


@dataclass(frozen=True)
class ArtifactQueryRow:
    """One artifact row loaded from `.cosheaf/index.sqlite`."""

    id: str
    type: str
    status: str
    path: str
    title: str
    domain: tuple[str, ...]
    kb_root: str


@dataclass(frozen=True)
class DependencyQueryRow:
    """One dependency edge loaded from `.cosheaf/index.sqlite`."""

    source_id: str
    target_id: str


class IndexQueryError(ValueError):
    """Raised when an index query cannot be served from SQLite output."""


class ArtifactIndexQuery:
    """Read-only query facade for the deterministic SQLite artifact index."""

    def __init__(self, sqlite_path: str | Path) -> None:
        self.sqlite_path = Path(sqlite_path)
        if not self.sqlite_path.is_file():
            raise IndexQueryError(
                f"index sqlite file does not exist: {self.sqlite_path}"
            )

    @classmethod
    def from_context(cls, context: RepoContext) -> Self:
        """Open the `.cosheaf/index.sqlite` output for a repository context."""
        return cls(context.resolve(".cosheaf/index.sqlite"))

    @classmethod
    def from_repo_root(cls, repo_root: str | Path) -> Self:
        """Open the `.cosheaf/index.sqlite` output under a repository root."""
        return cls.from_context(RepoContext(repo_root))

    def list_artifacts(self) -> tuple[ArtifactQueryRow, ...]:
        """List indexed artifacts in deterministic artifact ID order."""
        return self._fetch_artifacts(
            """
            SELECT id, type, status, path, title, domain, kb_root
            FROM artifacts
            ORDER BY id
            """,
            (),
        )

    def get_artifact(self, artifact_id: str) -> ArtifactQueryRow | None:
        """Return one indexed artifact by ID, or `None` when it is absent."""
        artifacts = self._fetch_artifacts(
            """
            SELECT id, type, status, path, title, domain, kb_root
            FROM artifacts
            WHERE id = ?
            ORDER BY id
            """,
            (artifact_id,),
        )
        return artifacts[0] if artifacts else None

    def list_artifacts_by_status(
        self,
        status: ArtifactStatus | str,
    ) -> tuple[ArtifactQueryRow, ...]:
        """List artifacts with the given lifecycle status."""
        return self._fetch_artifacts(
            """
            SELECT id, type, status, path, title, domain, kb_root
            FROM artifacts
            WHERE status = ?
            ORDER BY id
            """,
            (_status_value(status),),
        )

    def list_artifacts_by_type(
        self,
        artifact_type: ArtifactType | str,
    ) -> tuple[ArtifactQueryRow, ...]:
        """List artifacts with the given artifact type."""
        return self._fetch_artifacts(
            """
            SELECT id, type, status, path, title, domain, kb_root
            FROM artifacts
            WHERE type = ?
            ORDER BY id
            """,
            (_type_value(artifact_type),),
        )

    def list_artifacts_by_domain(self, domain: str) -> tuple[ArtifactQueryRow, ...]:
        """List artifacts whose indexed domain list contains `domain`."""
        return tuple(
            artifact
            for artifact in self.list_artifacts()
            if domain in artifact.domain
        )

    def list_dependencies(self, artifact_id: str) -> tuple[DependencyQueryRow, ...]:
        """List dependency edges from `artifact_id` to its dependencies."""
        return self._fetch_dependencies(
            """
            SELECT source_id, target_id
            FROM dependencies
            WHERE source_id = ?
            ORDER BY target_id
            """,
            (artifact_id,),
        )

    def list_reverse_dependencies(
        self,
        artifact_id: str,
    ) -> tuple[DependencyQueryRow, ...]:
        """List dependency edges from artifacts that depend on `artifact_id`."""
        return self._fetch_dependencies(
            """
            SELECT source_id, target_id
            FROM dependencies
            WHERE target_id = ?
            ORDER BY source_id
            """,
            (artifact_id,),
        )

    def _fetch_artifacts(
        self,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[ArtifactQueryRow, ...]:
        with closing(sqlite3.connect(self.sqlite_path)) as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return tuple(_artifact_from_row(row) for row in rows)

    def _fetch_dependencies(
        self,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[DependencyQueryRow, ...]:
        with closing(sqlite3.connect(self.sqlite_path)) as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return tuple(
            DependencyQueryRow(source_id=str(row[0]), target_id=str(row[1]))
            for row in rows
        )


def _artifact_from_row(row: tuple[Any, ...]) -> ArtifactQueryRow:
    domain = _parse_domain(row[5])
    return ArtifactQueryRow(
        id=str(row[0]),
        type=str(row[1]),
        status=str(row[2]),
        path=str(row[3]),
        title=str(row[4]),
        domain=domain,
        kb_root=str(row[6]),
    )


def _parse_domain(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, str):
        raise IndexQueryError(f"indexed artifact domain is not text: {raw!r}")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise IndexQueryError(f"invalid indexed artifact domain JSON: {raw}") from exc
    if not isinstance(decoded, list) or not all(
        isinstance(item, str) for item in decoded
    ):
        raise IndexQueryError(f"indexed artifact domain is not a string list: {raw}")
    return tuple(decoded)


def _status_value(status: ArtifactStatus | str) -> str:
    return status.value if isinstance(status, ArtifactStatus) else status


def _type_value(artifact_type: ArtifactType | str) -> str:
    return (
        artifact_type.value
        if isinstance(artifact_type, ArtifactType)
        else artifact_type
    )
