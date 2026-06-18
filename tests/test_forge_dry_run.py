from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _issue_data(issue_id: str = "issue.fixture.forge") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Forge issue preview fixture",
        "status": "open",
        "summary": "Preview a GitHub issue without creating one.",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "labels": ["forge", "dry-run"],
        "related_artifacts": [],
        "related_sources": [],
        "scope": "private",
    }


def _repo_files(repo_root: Path) -> set[str]:
    return {
        path.relative_to(repo_root).as_posix()
        for path in repo_root.rglob("*")
        if path.is_file()
    }


def test_forge_models_serialize_authority_boundaries() -> None:
    from cosheaf.forge import (
        ForgeActionResult,
        ForgePreviewResult,
        GitHubIssuePlan,
        GitHubPrPlan,
        LocalGitPlan,
    )

    local_plan = LocalGitPlan(
        repo_root=".",
        base="main",
        head="feature",
    )
    issue_plan = GitHubIssuePlan(
        source_path="issues/open/issue.fixture.forge.yaml",
        issue_id="issue.fixture.forge",
        title="Forge issue preview fixture",
        body="Preview a GitHub issue without creating one.",
        labels=["forge"],
    )
    pr_plan = GitHubPrPlan(
        base="main",
        head="feature",
        title="Merge feature into main",
        body="Dry-run PR preview.",
    )
    preview = ForgePreviewResult(
        kind="github_pr",
        local_git_plan=local_plan,
        github_issue_plan=issue_plan,
        github_pr_plan=pr_plan,
    )
    action = ForgeActionResult(action="preview")

    payload = preview.to_dict()
    assert payload["schema_version"] == 1
    assert payload["dry_run_only"] is True
    assert payload["network_calls_performed"] is False
    assert payload["git_writes_performed"] is False
    assert payload["github_writes_performed"] is False
    assert "dry-run" in payload["authority_warning"]
    assert action.to_dict()["action_performed"] is False


def test_forge_status_json_is_dry_run_only(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["forge", "status", "--repo-root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["kind"] == "status"
    assert payload["dry_run_only"] is True
    assert payload["network_calls_performed"] is False
    assert payload["git_writes_performed"] is False
    assert payload["github_writes_performed"] is False
    assert "dry-run" in payload["authority_warning"]


def test_forge_issue_preview_from_local_issue_is_read_only(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    issue_path = _write_yaml(
        tmp_path,
        "issues/open/issue.fixture.forge.yaml",
        _issue_data(),
    )
    before = _repo_files(tmp_path)

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("forge issue preview must not shell out")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "issue",
            "preview",
            "--from",
            str(issue_path.relative_to(tmp_path)),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert _repo_files(tmp_path) == before
    payload = json.loads(result.output)
    assert payload["kind"] == "github_issue"
    assert payload["network_calls_performed"] is False
    assert payload["github_writes_performed"] is False
    plan = payload["github_issue_plan"]
    assert plan["source_path"] == "issues/open/issue.fixture.forge.yaml"
    assert plan["issue_id"] == "issue.fixture.forge"
    assert plan["title"] == "Forge issue preview fixture"
    assert plan["labels"] == ["forge", "dry-run"]
    assert plan["github_issue_created"] is False
    assert "dry-run" in payload["authority_warning"]


def test_forge_pr_preview_is_read_only(tmp_path: Path, monkeypatch: Any) -> None:
    before = _repo_files(tmp_path)

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("forge PR preview must not shell out")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "pr",
            "preview",
            "--base",
            "main",
            "--head",
            "arch-forge-dry-run",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert _repo_files(tmp_path) == before
    payload = json.loads(result.output)
    assert payload["kind"] == "github_pr"
    assert payload["network_calls_performed"] is False
    assert payload["git_writes_performed"] is False
    assert payload["github_writes_performed"] is False
    assert payload["github_pr_plan"]["base"] == "main"
    assert payload["github_pr_plan"]["head"] == "arch-forge-dry-run"
    assert payload["github_pr_plan"]["github_pr_created"] is False
    assert payload["local_git_plan"]["commit_performed"] is False
    assert payload["local_git_plan"]["push_performed"] is False
    assert "dry-run" in payload["authority_warning"]
