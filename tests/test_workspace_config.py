from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.config.workspace import (
    WorkspaceConfigError,
    load_workspace_config,
)
from cosheaf.storage.index import rebuild_index
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_workspace_config(
    repo_root: Path,
    *,
    public_readonly: bool = True,
    private_readonly: bool = False,
) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "my-tcs-workspace"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                f"readonly = {str(public_readonly).lower()}",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                f"readonly = {str(private_readonly).lower()}",
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


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    title: str = "Test artifact",
    status: str = "draft",
    depends_on: list[str] | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": ["workspace"],
        "statement": "Test statement.",
        "evidence": evidence or [],
        "review": {"state": "requested", "notes": "Test review."},
        "risk": {"level": "low", "notes": "Test risk."},
    }


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    artifact_type: str = "claim",
    title: str = "Test artifact",
    status: str = "draft",
    depends_on: list[str] | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            _artifact_data(
                artifact_id,
                artifact_type=artifact_type,
                title=title,
                status=status,
                depends_on=depends_on,
                evidence=evidence,
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


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
                "title": "Workspace issue",
                "status": "open",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-06-01T00:00:00Z",
                "authors": ["tester"],
                "severity": "medium",
                "description": "Issue for workspace context.",
                "related_artifacts": related_artifacts,
                "tags": ["testing"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_legacy_config_preserves_single_repository_kb_root(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/draft/claims/legacy.yaml",
        artifact_id="claim.fixture.legacy",
    )

    config = load_workspace_config(tmp_path)
    records = load_artifacts(RepoContext(tmp_path))

    assert config.configured is False
    assert config.name == tmp_path.name
    roots = [(root.name, root.path, root.readonly, root.priority) for root in config.kb]
    assert roots == [("default", "kb", False, 0)]
    assert records[0].id == "claim.fixture.legacy"
    assert records[0].kb_root_name == "default"
    kb_relative_path = records[0].kb_relative_path
    assert kb_relative_path is not None
    assert kb_relative_path.as_posix() == "draft/claims/legacy.yaml"


def test_configured_workspace_loads_multiple_kb_roots_with_source_metadata(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/draft/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        title="Public definition",
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        title="Private claim",
        depends_on=["definition.fixture.public"],
    )

    config = load_workspace_config(tmp_path)
    records = {record.id: record for record in load_artifacts(RepoContext(tmp_path))}

    assert config.configured is True
    assert config.name == "my-tcs-workspace"
    roots = [(root.name, root.path, root.readonly, root.priority) for root in config.kb]
    assert roots == [
        ("public", "kb/public", True, 10),
        ("private", "kb/private", False, 20),
    ]
    assert records["definition.fixture.public"].kb_root_name == "public"
    assert records["definition.fixture.public"].kb_root_readonly is True
    public_relative_path = records["definition.fixture.public"].kb_relative_path
    assert public_relative_path is not None
    assert public_relative_path.as_posix() == "draft/definitions/public.yaml"
    assert records["claim.fixture.private"].kb_root_name == "private"
    assert records["claim.fixture.private"].kb_root_readonly is False
    private_relative_path = records["claim.fixture.private"].kb_relative_path
    assert private_relative_path is not None
    assert private_relative_path.as_posix() == "draft/claims/private.yaml"


def test_invalid_workspace_config_reports_clear_error(tmp_path: Path) -> None:
    tmp_path.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "bad"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "../outside"',
                "readonly = true",
                "priority = 10",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(WorkspaceConfigError, match="parent-directory traversal"):
        load_workspace_config(tmp_path)


def test_validate_checks_duplicate_ids_across_configured_roots(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/draft/claims/a.yaml",
        artifact_id="claim.fixture.duplicate",
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/b.yaml",
        artifact_id="claim.fixture.duplicate",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "duplicate id claim.fixture.duplicate" in result.output
    assert "kb/private/draft/claims/b.yaml" in result.output
    assert "kb/public/draft/claims/a.yaml" in result.output


def test_private_artifact_may_depend_on_public_artifact(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        status="accepted",
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        depends_on=["definition.fixture.public"],
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Validation passed" in result.output


def test_public_artifact_must_not_depend_on_private_artifact(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
    )
    _write_artifact(
        tmp_path,
        "kb/public/draft/claims/public.yaml",
        artifact_id="claim.fixture.public",
        depends_on=["claim.fixture.private"],
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "public artifact depends on private artifact" in result.output
    assert "claim.fixture.public" in result.output
    assert "claim.fixture.private" in result.output


def test_accepted_artifact_must_not_depend_on_draft_across_roots(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/draft/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        status="draft",
    )
    _write_artifact(
        tmp_path,
        "kb/private/accepted/claims/private.yaml",
        artifact_id="claim.fixture.private",
        status="accepted",
        depends_on=["definition.fixture.public"],
    )

    result = runner.invoke(app, ["gate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "accepted artifact depends on" in result.output
    assert "draft artifact" in result.output
    assert "definition.fixture.public" in result.output


def test_workspace_status_paths_are_relative_to_kb_root(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        status="draft",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "status/path mismatch" in result.output
    assert "kb/public/accepted/definitions/public.yaml" in result.output


def test_index_rebuild_includes_configured_kb_roots(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        status="accepted",
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        depends_on=["definition.fixture.public"],
    )

    result = rebuild_index(RepoContext(tmp_path))
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert [artifact["id"] for artifact in manifest["artifacts"]] == [
        "claim.fixture.private",
        "definition.fixture.public",
    ]
    assert {artifact["kb_root"] for artifact in manifest["artifacts"]} == {
        "private",
        "public",
    }
    assert manifest["dependencies"] == [
        {
            "source_id": "claim.fixture.private",
            "target_id": "definition.fixture.public",
        }
    ]


def test_workspace_info_cli_reports_configured_roots(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)

    result = runner.invoke(app, ["workspace", "info", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Workspace: my-tcs-workspace" in result.output
    assert "mode: configured" in result.output
    assert "public | kb/public | readonly=true | priority=10" in result.output
    assert "private | kb/private | readonly=false | priority=20" in result.output


def test_workspace_info_cli_reports_legacy_mode(tmp_path: Path) -> None:
    result = runner.invoke(app, ["workspace", "info", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert f"Workspace: {tmp_path.name}" in result.output
    assert "mode: legacy" in result.output
    assert "default | kb | readonly=false | priority=0" in result.output


def test_context_command_uses_configured_kb_roots(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        status="accepted",
        title="Public definition",
    )
    _write_issue(
        tmp_path,
        issue_id="issue.fixture.workspace",
        related_artifacts=["definition.fixture.public"],
    )

    result = runner.invoke(
        app,
        ["context", "show", "issue.fixture.workspace", "--repo-root", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert "definition.fixture.public" in result.output
    assert "kb/public/accepted/definitions/public.yaml" in result.output


def test_graph_command_uses_configured_kb_roots(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/accepted/definitions/public.yaml",
        artifact_id="definition.fixture.public",
        artifact_type="definition",
        status="accepted",
    )
    _write_artifact(
        tmp_path,
        "kb/private/draft/claims/private.yaml",
        artifact_id="claim.fixture.private",
        depends_on=["definition.fixture.public"],
    )

    result = runner.invoke(app, ["graph", "show", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "claim.fixture.private -> definition.fixture.public" in result.output


def test_artifact_create_uses_writable_private_root_in_workspace(
    tmp_path: Path,
) -> None:
    _write_workspace_config(tmp_path)

    result = runner.invoke(
        app,
        [
            "artifact",
            "create",
            "--id",
            "claim.fixture.created",
            "--type",
            "claim",
            "--title",
            "Created private claim",
            "--domain",
            "testing",
            "--status",
            "draft",
            "--statement",
            "A created private draft.",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        "Artifact created: kb/private/draft/claims/claim.fixture.created.yaml"
        in result.output
    )
    assert (
        tmp_path / "kb" / "private" / "draft" / "claims" / "claim.fixture.created.yaml"
    ).is_file()
    assert not (tmp_path / "kb" / "public" / "draft" / "claims").exists()


def test_artifact_move_status_refuses_readonly_kb_root(tmp_path: Path) -> None:
    _write_workspace_config(tmp_path)
    _write_artifact(
        tmp_path,
        "kb/public/draft/claims/public.yaml",
        artifact_id="claim.fixture.public",
        status="draft",
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "move-status",
            "claim.fixture.public",
            "locally_tested",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "readonly KB root cannot be modified: public" in result.output
    assert "Traceback" not in result.output
