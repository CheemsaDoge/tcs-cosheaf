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
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


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
