from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pytest import MonkeyPatch
from typer.testing import CliRunner

import cosheaf.memory.search as memory_search_module
from cosheaf.cli import app

runner = CliRunner()


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str,
    status: str = "draft",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Fixture statement.",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": title,
        "domain": domain or ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or [],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    artifact_type: str = "claim",
    title: str,
    status: str = "draft",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Fixture statement.",
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            _artifact_data(
                artifact_id,
                artifact_type=artifact_type,
                title=title,
                status=status,
                domain=domain,
                tags=tags,
                depends_on=depends_on,
                statement=statement,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_issue(
    repo_root: Path,
    *,
    issue_id: str,
    related_artifacts: list[str],
) -> None:
    path = repo_root / "issues" / "open" / f"{issue_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "id": issue_id,
                "type": "issue",
                "title": "Memory search issue",
                "status": "open",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "severity": "medium",
                "description": "Issue for memory search filtering.",
                "related_artifacts": related_artifacts,
                "tags": ["memory-search"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "memory-search-workspace"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
                "[policy]",
                "private_can_depend_on_public = true",
                "public_can_depend_on_private = false",
                "accepted_requires_source = true",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_memory_search_json_returns_ranked_cards_with_audit(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/planar.yaml",
        artifact_id="definition.fixture.planar-separator",
        artifact_type="definition",
        title="Planar separator theorem",
        status="accepted",
        domain=["graph-theory"],
        tags=["planar", "separator"],
        statement="SECRET FULL STATEMENT SHOULD NOT APPEAR",
    )
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/tree.yaml",
        artifact_id="definition.fixture.tree",
        artifact_type="definition",
        title="Tree",
        status="accepted",
        domain=["graph-theory"],
        tags=["tree"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "planar separator",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["request_id"].startswith("retrieval.memory.search.")
    assert payload["index_fingerprint"].startswith("sha256:")
    assert payload["audit"]["filters_applied"][:2] == [
        "scope:public,workspace,framework",
        "status:accepted,human_reviewed,machine_checked,locally_tested",
    ]
    assert payload["cards"][0]["card"]["id"] == (
        "definition.fixture.planar-separator"
    )
    assert payload["cards"][0]["score_breakdown"]["retrieval_hybrid"] > 0
    assert payload["cards"][0]["score_breakdown"]["total"] > 0
    assert "lexical" in " ".join(payload["cards"][0]["why_relevant"]).lower() or (
        "fts" in " ".join(payload["cards"][0]["why_relevant"]).lower()
    )
    assert "SECRET FULL STATEMENT" not in result.output
    assert not (tmp_path / ".cosheaf" / "memory").exists()


def test_memory_search_status_filter_excludes_draft(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph foundation",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/draft.yaml",
        artifact_id="claim.fixture.graph-draft",
        title="Graph draft",
        status="draft",
        domain=["graph-theory"],
        tags=["graph"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--status",
            "accepted",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.graph"
    ]
    assert "claim.fixture.graph-draft" not in [
        hit["card"]["id"] for hit in payload["cards"]
    ]
    assert payload["audit"]["excluded"] == [
        {
            "artifact_id": "claim.fixture.graph-draft",
            "reason": "status excluded: draft not in accepted",
        }
    ]


def test_memory_search_text_output_is_compact(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
        statement="SECRET FULL STATEMENT SHOULD NOT APPEAR",
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "definition.fixture.graph | score=" in result.output
    assert "Graph | accepted | workspace | kb/accepted/definitions/graph.yaml" in (
        result.output
    )
    assert "SECRET FULL STATEMENT" not in result.output


def test_memory_search_issue_filter_and_private_default_scope(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Public graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/walk.yaml",
        artifact_id="definition.fixture.walk",
        artifact_type="definition",
        title="Walk",
        status="accepted",
        domain=["graph-theory"],
        tags=["walk"],
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        title="Private graph conjecture",
        status="draft",
        domain=["graph-theory"],
        tags=["graph"],
        depends_on=["definition.fixture.graph"],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.search",
        related_artifacts=["definition.fixture.graph", "claim.fixture.private"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.search",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.graph"
    ]
    assert "definition.fixture.walk" not in result.output
    assert "claim.fixture.private" not in result.output
    assert payload["audit"]["excluded"] == []


def test_memory_search_json_output_is_deterministic(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )

    args = [
        "memory",
        "search",
        "graph",
        "--repo-root",
        str(tmp_path),
        "--json",
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert first.output == second.output


def test_memory_search_falls_back_when_sqlite_fts_is_unavailable(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        domain=["graph-theory"],
        tags=["graph"],
    )

    class _BrokenFtsConnection:
        def execute(self, *_args: object, **_kwargs: object) -> None:
            raise sqlite3.DatabaseError("no fts5")

        def close(self) -> None:
            return None

    def _broken_connect(_database: str) -> _BrokenFtsConnection:
        return _BrokenFtsConnection()

    monkeypatch.setattr(memory_search_module.sqlite3, "connect", _broken_connect)

    result = runner.invoke(
        app,
        [
            "memory",
            "search",
            "graph",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [hit["card"]["id"] for hit in payload["cards"]] == [
        "definition.fixture.graph"
    ]
    assert any(
        "lexical fallback used" in warning
        for warning in payload["audit"]["warnings"]
    )
