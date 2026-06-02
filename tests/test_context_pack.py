from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.agent.context_pack import ContextPackError, build_context_pack
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_context_docs(repo_root: Path) -> None:
    context_dir = repo_root / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / "PROJECT_STATE.md").write_text(
        "# Project State\n\nCurrent state for tests.\n",
        encoding="utf-8",
    )
    (context_dir / "INTERFACE_REGISTRY.md").write_text(
        "# Interface Registry\n\n- `cosheaf context build <issue-id>`\n",
        encoding="utf-8",
    )


def _artifact_data(
    artifact_id: str,
    *,
    status: str,
    title: str | None = None,
    depends_on: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title or f"Claim {artifact_id}",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or [],
        "statement": "A bounded context-pack fixture.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _issue_data(
    issue_id: str = "issue.fixture.context",
    related_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Build a bounded context pack",
        "status": "open",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": (
            "The task needs a short, deterministic handoff.\n"
            "- Include accepted background before draft material.\n"
            "- Mark draft artifacts visibly.\n"
        ),
        "related_artifacts": related_artifacts or [
            "claim.fixture.accepted",
            "claim.fixture.draft",
            "claim.fixture.refuted",
        ],
        "tags": ["context-pack"],
    }


def _write_repo(repo_root: Path) -> None:
    _write_context_docs(repo_root)
    _write_yaml(repo_root, "issues/open/issue.yaml", _issue_data())
    _write_yaml(
        repo_root,
        "kb/accepted/claims/accepted.yaml",
        _artifact_data(
            "claim.fixture.accepted",
            status="accepted",
            title="Accepted claim",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/draft/claims/draft.yaml",
        _artifact_data("claim.fixture.draft", status="draft", title="Draft claim"),
    )
    _write_yaml(
        repo_root,
        "kb/refuted/refuted.yaml",
        _artifact_data(
            "claim.fixture.refuted",
            status="refuted",
            title="Refuted claim",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/draft/claims/unrelated.yaml",
        _artifact_data(
            "claim.fixture.unrelated",
            status="draft",
            title="Unrelated claim",
        ),
    )


def test_context_pack_files_created(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    assert result.issue_id == "issue.fixture.context"
    assert result.task_dir == tmp_path / "context" / "TASKS" / "issue.fixture.context"
    expected_names = {
        "CONTEXT.md",
        "ACCEPTANCE.md",
        "RELEVANT_ARTIFACTS.md",
        "KNOWN_FAILURES.md",
        "COMMANDS.md",
    }
    assert {path.name for path in result.files} == expected_names
    for path in result.files:
        assert path.exists()


def test_context_pack_output_is_deterministic(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    first = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")
    first_contents = {
        path.name: path.read_text(encoding="utf-8") for path in first.files
    }
    second = build_context_pack(RepoContext(tmp_path), "issue.fixture.context")
    second_contents = {
        path.name: path.read_text(encoding="utf-8") for path in second.files
    }

    assert second_contents == first_contents


def test_missing_issue_fails_with_clear_error(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    with pytest.raises(
        ContextPackError,
        match="issue not found: issue.fixture.missing",
    ):
        build_context_pack(RepoContext(tmp_path), "issue.fixture.missing")

    result = runner.invoke(
        app,
        ["context", "build", "issue.fixture.missing", "--repo-root", str(tmp_path)],
    )

    assert result.exit_code != 0
    assert "issue not found: issue.fixture.missing" in result.output
    assert "Traceback" not in result.output


def test_accepted_and_draft_labels_are_clear(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    context_md = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "CONTEXT.md"
    ).read_text(encoding="utf-8")
    relevant_md = (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.context"
        / "RELEVANT_ARTIFACTS.md"
    ).read_text(encoding="utf-8")

    assert "## Relevant Accepted Artifacts" in context_md
    assert "- claim.fixture.accepted | Accepted claim" in context_md
    assert "## Relevant Draft Artifacts" in context_md
    assert "[DRAFT] claim.fixture.draft | Draft claim" in context_md
    assert "claim.fixture.accepted | Accepted claim | accepted" in relevant_md
    assert "[DRAFT] claim.fixture.draft | Draft claim | draft" in relevant_md
    assert "claim.fixture.unrelated" not in context_md
    assert "claim.fixture.unrelated" not in relevant_md


def test_known_failures_and_commands_are_written(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    build_context_pack(RepoContext(tmp_path), "issue.fixture.context")

    task_dir = tmp_path / "context" / "TASKS" / "issue.fixture.context"
    known_failures = (task_dir / "KNOWN_FAILURES.md").read_text(encoding="utf-8")
    commands = (task_dir / "COMMANDS.md").read_text(encoding="utf-8")

    assert "claim.fixture.refuted | Refuted claim | refuted" in known_failures
    for command in (
        "make lint",
        "make typecheck",
        "make test",
        "make validate",
        "make gate",
    ):
        assert f"- `{command}`" in commands


def test_context_show_prints_context_pack(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        ["context", "show", "issue.fixture.context", "--repo-root", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "# Context Pack: issue.fixture.context" in result.output
    assert "claim.fixture.accepted" in result.output
    assert "[DRAFT] claim.fixture.draft" in result.output
