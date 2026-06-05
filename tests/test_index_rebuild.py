from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.storage.index import rebuild_index
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    title: str,
    depends_on: list[str] | None = None,
    formalizations: list[dict[str, Any]] | None = None,
    alignment: dict[str, Any] | None = None,
    verification_policy: dict[str, Any] | None = None,
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": [],
        "statement": "Test statement.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Test review."},
        "risk": {"level": "low", "notes": "Test risk."},
    }
    if formalizations is not None:
        data["formalizations"] = formalizations
    if alignment is not None:
        data["alignment"] = alignment
    if verification_policy is not None:
        data["verification_policy"] = verification_policy
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _formalization_fixture(
    *,
    formalization_id: str = "cslib.fixture.link",
    status: str = "planned",
) -> dict[str, Any]:
    return {
        "id": formalization_id,
        "system": "lean4",
        "library": "CSLib",
        "library_ref": "cslib-main",
        "import_path": "CSLib.Graph.Basic",
        "symbol": "CSLib.Graph.Basic.fixture_symbol",
        "declaration_kind": "theorem",
        "status": status,
        "check_mode": "external_library_ref",
        "expected_type": "Fixture Lean type.",
        "notes": "Fixture formalization link.",
    }


def _formal_link_policy(
    *,
    level: str = "source_reviewed_with_formal_link",
    require_formal_link: bool = True,
    require_lean_check: bool = False,
    require_alignment_review: bool = False,
) -> dict[str, Any]:
    return {
        "level": level,
        "require_formal_link": require_formal_link,
        "require_lean_check": require_lean_check,
        "require_alignment_review": require_alignment_review,
    }


def test_rebuild_index_creates_sqlite_and_manifest(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/b.yaml",
        artifact_id="claim.fixture.b",
        title="B",
    )
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        title="A",
        depends_on=["claim.fixture.b"],
    )

    result = rebuild_index(RepoContext(tmp_path))

    assert result.sqlite_path == tmp_path / ".cosheaf" / "index.sqlite"
    assert result.manifest_path == tmp_path / ".cosheaf" / "artifact_manifest.json"
    assert result.sqlite_path.exists()
    assert result.manifest_path.exists()

    with closing(sqlite3.connect(result.sqlite_path)) as connection:
        rows = connection.execute(
            "SELECT id, type, status, path, title, domain FROM artifacts ORDER BY id"
        ).fetchall()

    assert rows == [
        (
            "claim.fixture.a",
            "claim",
            "draft",
            "examples/claims/a.yaml",
            "A",
            '["testing"]',
        ),
        (
            "claim.fixture.b",
            "claim",
            "draft",
            "examples/claims/b.yaml",
            "B",
            '["testing"]',
        ),
    ]


def test_manifest_is_deterministic_after_delete_and_rebuild(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/b.yaml",
        artifact_id="claim.fixture.b",
        title="B",
    )
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        title="A",
        depends_on=["claim.fixture.b"],
    )

    first = rebuild_index(RepoContext(tmp_path))
    first_manifest = first.manifest_path.read_text(encoding="utf-8")

    first.sqlite_path.unlink()
    first.manifest_path.unlink()

    second = rebuild_index(RepoContext(tmp_path))
    second_manifest = second.manifest_path.read_text(encoding="utf-8")

    assert first_manifest == second_manifest
    manifest_ids = [
        artifact["id"] for artifact in json.loads(second_manifest)["artifacts"]
    ]
    assert manifest_ids == [
        "claim.fixture.a",
        "claim.fixture.b",
    ]


def test_rebuild_index_records_formalizations_and_policy(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/formal.yaml",
        artifact_id="claim.fixture.formal",
        title="Formal",
        formalizations=[_formalization_fixture()],
        alignment={
            "status": "requested",
            "reviewer": "",
            "reviewed_at": None,
            "convention_notes": ["Fixture convention note."],
            "limitations": "Fixture alignment limitation.",
        },
        verification_policy=_formal_link_policy(
            require_alignment_review=True,
        ),
    )
    _write_artifact(
        tmp_path,
        "examples/claims/plain.yaml",
        artifact_id="claim.fixture.plain",
        title="Plain",
    )

    result = rebuild_index(RepoContext(tmp_path))

    with closing(sqlite3.connect(result.sqlite_path)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        formalization_rows = connection.execute(
            """
            SELECT artifact_id, formalization_id, system, library, library_ref,
                   import_path, symbol, declaration_kind, status, check_mode,
                   expected_type, notes
            FROM formalizations
            ORDER BY artifact_id, formalization_id
            """
        ).fetchall()
        policy_rows = connection.execute(
            """
            SELECT artifact_id, alignment_status, alignment_reviewer,
                   verification_level, require_formal_link, require_lean_check,
                   require_alignment_review
            FROM artifact_formal_policy
            ORDER BY artifact_id
            """
        ).fetchall()
        indexes = {
            row[1]
            for row in connection.execute(
                "PRAGMA index_list('formalizations')"
            ).fetchall()
        }

    assert {"formalizations", "artifact_formal_policy"} <= tables
    assert formalization_rows == [
        (
            "claim.fixture.formal",
            "cslib.fixture.link",
            "lean4",
            "CSLib",
            "cslib-main",
            "CSLib.Graph.Basic",
            "CSLib.Graph.Basic.fixture_symbol",
            "theorem",
            "planned",
            "external_library_ref",
            "Fixture Lean type.",
            "Fixture formalization link.",
        )
    ]
    assert policy_rows == [
        (
            "claim.fixture.formal",
            "requested",
            "",
            "source_reviewed_with_formal_link",
            1,
            0,
            1,
        ),
        (
            "claim.fixture.plain",
            "none",
            "",
            "source_reviewed",
            0,
            0,
            0,
        ),
    ]
    assert {
        "idx_formalizations_symbol",
        "idx_formalizations_library",
        "idx_formalizations_status",
        "idx_formalizations_import_path",
    } <= indexes

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    formal_artifact = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["id"] == "claim.fixture.formal"
    )
    plain_artifact = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["id"] == "claim.fixture.plain"
    )
    assert formal_artifact["formalizations"] == [
        {
            "id": "cslib.fixture.link",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "cslib-main",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.Basic.fixture_symbol",
            "declaration_kind": "theorem",
            "status": "planned",
            "check_mode": "external_library_ref",
        }
    ]
    assert formal_artifact["alignment_status"] == "requested"
    assert formal_artifact["verification_policy"] == {
        "level": "source_reviewed_with_formal_link",
        "require_formal_link": True,
        "require_lean_check": False,
        "require_alignment_review": True,
    }
    assert plain_artifact["formalizations"] == []
    assert plain_artifact["alignment_status"] == "none"
    assert plain_artifact["verification_policy"] == {
        "level": "source_reviewed",
        "require_formal_link": False,
        "require_lean_check": False,
        "require_alignment_review": False,
    }


def test_formal_index_outputs_are_deterministic_after_delete_and_rebuild(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/formal.yaml",
        artifact_id="claim.fixture.formal",
        title="Formal",
        formalizations=[
            _formalization_fixture(formalization_id="cslib.fixture.z"),
            _formalization_fixture(formalization_id="cslib.fixture.a"),
        ],
        verification_policy=_formal_link_policy(),
    )

    first = rebuild_index(RepoContext(tmp_path))
    first_manifest = first.manifest_path.read_text(encoding="utf-8")
    with closing(sqlite3.connect(first.sqlite_path)) as connection:
        first_rows = connection.execute(
            """
            SELECT artifact_id, formalization_id
            FROM formalizations
            ORDER BY artifact_id, formalization_id
            """
        ).fetchall()

    first.sqlite_path.unlink()
    first.manifest_path.unlink()

    second = rebuild_index(RepoContext(tmp_path))
    second_manifest = second.manifest_path.read_text(encoding="utf-8")
    with closing(sqlite3.connect(second.sqlite_path)) as connection:
        second_rows = connection.execute(
            """
            SELECT artifact_id, formalization_id
            FROM formalizations
            ORDER BY artifact_id, formalization_id
            """
        ).fetchall()

    assert first_manifest == second_manifest
    assert first_rows == second_rows == [
        ("claim.fixture.formal", "cslib.fixture.a"),
        ("claim.fixture.formal", "cslib.fixture.z"),
    ]


def test_index_rebuild_cli_creates_outputs(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        title="A",
    )

    result = runner.invoke(app, ["index", "rebuild", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Index rebuilt" in result.output
    assert (tmp_path / ".cosheaf" / "index.sqlite").exists()
    assert (tmp_path / ".cosheaf" / "artifact_manifest.json").exists()


def test_graph_show_cli_reports_edges(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        title="A",
        depends_on=["claim.fixture.b"],
    )
    _write_artifact(
        tmp_path,
        "examples/claims/b.yaml",
        artifact_id="claim.fixture.b",
        title="B",
    )

    result = runner.invoke(app, ["graph", "show", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "claim.fixture.a -> claim.fixture.b" in result.output
