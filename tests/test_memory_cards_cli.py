from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str = "Test artifact",
    status: str = "draft",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Test statement.",
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
    title: str = "Test artifact",
    status: str = "draft",
    domain: list[str] | None = None,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
    statement: str = "Test statement.",
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
                "title": "Card builder issue",
                "status": "open",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "severity": "medium",
                "description": "Issue for memory card filtering.",
                "related_artifacts": related_artifacts,
                "tags": ["memory-cards"],
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
                'name = "memory-card-workspace"',
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


def test_memory_cards_cli_outputs_cards_without_full_text(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
        statement="SECRET FULL STATEMENT SHOULD NOT APPEAR",
    )

    result = runner.invoke(app, ["memory", "cards", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert (
        "definition.fixture.graph | Graph | accepted | workspace | "
        "kb/accepted/definitions/graph.yaml"
    ) in result.output
    assert "SECRET FULL STATEMENT" not in result.output
    assert not (tmp_path / ".cosheaf" / "memory").exists()


def test_memory_cards_json_status_filter_excludes_draft(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/definitions/graph.yaml",
        artifact_id="definition.fixture.graph",
        artifact_type="definition",
        title="Graph",
        status="accepted",
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/draft.yaml",
        artifact_id="claim.fixture.draft",
        title="Draft claim",
        status="draft",
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "cards",
            "--repo-root",
            str(tmp_path),
            "--status",
            "accepted",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    cards = json.loads(result.output)
    assert [card["id"] for card in cards] == ["definition.fixture.graph"]
    assert cards[0]["status"] == "accepted"
    assert "statement" not in cards[0]
    assert "Draft claim" not in result.output


def test_memory_cards_issue_filter_uses_direct_related_artifacts(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/draft/claims/related.yaml",
        artifact_id="claim.fixture.related",
        title="Related claim",
        status="draft",
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/unrelated.yaml",
        artifact_id="claim.fixture.unrelated",
        title="Unrelated claim",
        status="draft",
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.cards",
        related_artifacts=["claim.fixture.related"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "cards",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.cards",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    cards = json.loads(result.output)
    assert [card["id"] for card in cards] == ["claim.fixture.related"]
    assert "claim.fixture.unrelated" not in result.output


def test_memory_cards_default_excludes_private_workspace_cards(
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
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        title="Private claim",
        status="draft",
        depends_on=["definition.fixture.graph"],
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.private",
        related_artifacts=["definition.fixture.graph", "claim.fixture.private"],
    )

    result = runner.invoke(
        app,
        [
            "memory",
            "cards",
            "--repo-root",
            str(tmp_path),
            "--issue",
            "issue.fixture.private",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    cards = json.loads(result.output)
    assert [card["id"] for card in cards] == ["definition.fixture.graph"]
    assert cards[0]["root_scope"] == "public"
    assert "claim.fixture.private" not in result.output
    assert "Private claim" not in result.output
    assert not (tmp_path / ".cosheaf" / "memory").exists()
