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


@dataclass(frozen=True)
class FormalizationQueryRow:
    """One formalization reference loaded from `.cosheaf/index.sqlite`."""

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
class FormalPolicyQueryRow:
    """One artifact formal policy row loaded from `.cosheaf/index.sqlite`."""

    artifact_id: str
    alignment_status: str
    alignment_reviewer: str
    verification_level: str
    require_formal_link: bool
    require_lean_check: bool
    require_alignment_review: bool


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

    def list_formalizations(self) -> tuple[FormalizationQueryRow, ...]:
        """List formalization references in deterministic order."""
        return self._fetch_formalizations(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            ORDER BY artifact_id, formalization_id
            """,
            (),
        )

    def list_formalizations_for_artifact(
        self,
        artifact_id: str,
    ) -> tuple[FormalizationQueryRow, ...]:
        """List formalization references attached to one artifact."""
        return self._fetch_formalizations(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            WHERE artifact_id = ?
            ORDER BY formalization_id
            """,
            (artifact_id,),
        )

    def list_formalizations_by_library(
        self,
        library: str,
    ) -> tuple[FormalizationQueryRow, ...]:
        """List formalization references for one formal library."""
        return self._fetch_formalizations(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            WHERE library = ?
            ORDER BY artifact_id, formalization_id
            """,
            (library,),
        )

    def list_formalizations_by_symbol(
        self,
        symbol: str,
    ) -> tuple[FormalizationQueryRow, ...]:
        """List formalization references for one declaration symbol."""
        return self._fetch_formalizations(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            WHERE symbol = ?
            ORDER BY artifact_id, formalization_id
            """,
            (symbol,),
        )

    def list_formalizations_by_status(
        self,
        status: str,
    ) -> tuple[FormalizationQueryRow, ...]:
        """List formalization references with one formal-link status."""
        return self._fetch_formalizations(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            WHERE status = ?
            ORDER BY artifact_id, formalization_id
            """,
            (status,),
        )

    def list_formalizations_by_import(
        self,
        import_path: str,
    ) -> tuple[FormalizationQueryRow, ...]:
        """List formalization references for one Lean import path."""
        return self._fetch_formalizations(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            WHERE import_path = ?
            ORDER BY artifact_id, formalization_id
            """,
            (import_path,),
        )

    def get_formal_policy(self, artifact_id: str) -> FormalPolicyQueryRow | None:
        """Return one artifact's formal policy row, or `None` when absent."""
        policies = self._fetch_formal_policies(
            """
            SELECT artifact_id, alignment_status, alignment_reviewer,
                   verification_level, require_formal_link, require_lean_check,
                   require_alignment_review
            FROM artifact_formal_policy
            WHERE artifact_id = ?
            ORDER BY artifact_id
            """,
            (artifact_id,),
        )
        return policies[0] if policies else None

    def list_artifacts_requiring_formal_link(
        self,
    ) -> tuple[FormalPolicyQueryRow, ...]:
        """List artifacts whose policy requires a formal link."""
        return self._fetch_formal_policies(
            """
            SELECT artifact_id, alignment_status, alignment_reviewer,
                   verification_level, require_formal_link, require_lean_check,
                   require_alignment_review
            FROM artifact_formal_policy
            WHERE require_formal_link = 1
            ORDER BY artifact_id
            """,
            (),
        )

    def list_artifacts_requiring_lean_check(
        self,
    ) -> tuple[FormalPolicyQueryRow, ...]:
        """List artifacts whose policy requires Lean checking metadata."""
        return self._fetch_formal_policies(
            """
            SELECT artifact_id, alignment_status, alignment_reviewer,
                   verification_level, require_formal_link, require_lean_check,
                   require_alignment_review
            FROM artifact_formal_policy
            WHERE require_lean_check = 1
            ORDER BY artifact_id
            """,
            (),
        )

    def list_artifacts_requiring_alignment_review(
        self,
    ) -> tuple[FormalPolicyQueryRow, ...]:
        """List artifacts whose policy requires human alignment review."""
        return self._fetch_formal_policies(
            """
            SELECT artifact_id, alignment_status, alignment_reviewer,
                   verification_level, require_formal_link, require_lean_check,
                   require_alignment_review
            FROM artifact_formal_policy
            WHERE require_alignment_review = 1
            ORDER BY artifact_id
            """,
            (),
        )

    def _fetch_artifacts(
        self,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[ArtifactQueryRow, ...]:
        rows = _read_rows(self.sqlite_path, sql, parameters)
        return tuple(_artifact_from_row(row) for row in rows)

    def _fetch_dependencies(
        self,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[DependencyQueryRow, ...]:
        rows = _read_rows(self.sqlite_path, sql, parameters)
        return tuple(
            DependencyQueryRow(source_id=str(row[0]), target_id=str(row[1]))
            for row in rows
        )

    def _fetch_formalizations(
        self,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[FormalizationQueryRow, ...]:
        rows = _read_rows(self.sqlite_path, sql, parameters)
        return tuple(_formalization_from_row(row) for row in rows)

    def _fetch_formal_policies(
        self,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[FormalPolicyQueryRow, ...]:
        rows = _read_rows(self.sqlite_path, sql, parameters)
        return tuple(_formal_policy_from_row(row) for row in rows)


def _read_rows(
    sqlite_path: Path,
    sql: str,
    parameters: tuple[object, ...],
) -> list[tuple[Any, ...]]:
    try:
        with closing(_connect_readonly(sqlite_path)) as connection:
            rows = connection.execute(sql, parameters).fetchall()
    except sqlite3.DatabaseError as exc:
        raise IndexQueryError(f"index query failed: {exc}") from exc
    return rows


def _connect_readonly(sqlite_path: Path) -> sqlite3.Connection:
    uri = f"{sqlite_path.resolve().as_uri()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


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


def _formalization_from_row(row: tuple[Any, ...]) -> FormalizationQueryRow:
    if len(row) != 12:
        raise IndexQueryError(f"formalization row has wrong width: {len(row)}")
    return FormalizationQueryRow(
        artifact_id=str(row[0]),
        formalization_id=str(row[1]),
        system=str(row[2]),
        library=str(row[3]),
        library_ref=str(row[4]),
        import_path=str(row[5]),
        symbol=str(row[6]),
        declaration_kind=str(row[7]),
        status=str(row[8]),
        check_mode=str(row[9]),
        expected_type=str(row[10]),
        notes=str(row[11]),
    )


def _formal_policy_from_row(row: tuple[Any, ...]) -> FormalPolicyQueryRow:
    if len(row) != 7:
        raise IndexQueryError(f"formal policy row has wrong width: {len(row)}")
    return FormalPolicyQueryRow(
        artifact_id=str(row[0]),
        alignment_status=str(row[1]),
        alignment_reviewer=str(row[2]),
        verification_level=str(row[3]),
        require_formal_link=_parse_sqlite_bool(row[4], "require_formal_link"),
        require_lean_check=_parse_sqlite_bool(row[5], "require_lean_check"),
        require_alignment_review=_parse_sqlite_bool(
            row[6],
            "require_alignment_review",
        ),
    )


def _parse_sqlite_bool(raw: object, column: str) -> bool:
    if raw == 0:
        return False
    if raw == 1:
        return True
    raise IndexQueryError(f"formal policy column {column} is not boolean: {raw!r}")


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
