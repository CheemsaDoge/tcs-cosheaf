from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Tester")
    _git(repo, "config", "user.email", "tester@example.invalid")
    (repo / ".gitignore").write_text(".cosheaf/\n", encoding="utf-8")
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Initial commit")


def test_forge_branch_create_requires_confirm(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "forge",
            "branch",
            "create",
            "feature.local",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_confirm_required"
    assert _git(tmp_path, "branch", "--show-current") == "main"


def test_forge_branch_create_switches_to_new_branch(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "forge",
            "branch",
            "create",
            "feature.local",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "branch_create"
    assert payload["action_performed"] is True
    assert payload["git_writes_performed"] is True
    assert payload["network_calls_performed"] is False
    assert payload["github_writes_performed"] is False
    assert payload["push_performed"] is False
    assert payload["github_pr_created"] is False
    assert payload["branch"] == "feature.local"
    assert _git(tmp_path, "branch", "--show-current") == "feature.local"


def test_forge_branch_create_refuses_dirty_state(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "scratch.txt").write_text("dirty\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "forge",
            "branch",
            "create",
            "feature.local",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_dirty_state"
    assert "dirty" in payload["message"]
    assert _git(tmp_path, "branch", "--show-current") == "main"


def test_forge_branch_create_refuses_protected_branch(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "forge",
            "branch",
            "create",
            "master",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_protected_branch"
    assert _git(tmp_path, "branch", "--show-current") == "main"


def test_forge_commit_requires_confirm(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "README.md").write_text("changed\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")

    result = runner.invoke(
        app,
        [
            "forge",
            "commit",
            "--message",
            "Update README",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_confirm_required"
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Initial commit"


def test_forge_commit_runs_checks_and_creates_local_commit(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "README.md").write_text("changed\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")

    result = runner.invoke(
        app,
        [
            "forge",
            "commit",
            "--message",
            "Update README",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "commit"
    assert payload["action_performed"] is True
    assert payload["git_writes_performed"] is True
    assert payload["network_calls_performed"] is False
    assert payload["github_writes_performed"] is False
    assert payload["push_performed"] is False
    assert payload["github_pr_created"] is False
    assert payload["validation_performed"] is True
    assert payload["gate_performed"] is True
    assert payload["commit_hash"]
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Update README"


def test_forge_commit_refuses_untracked_ambiguity(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "README.md").write_text("changed\n", encoding="utf-8")
    (tmp_path / "scratch.txt").write_text("untracked\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")

    result = runner.invoke(
        app,
        [
            "forge",
            "commit",
            "--message",
            "Update README",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_dirty_state"
    assert "untracked" in payload["message"]
    assert _git(tmp_path, "log", "-1", "--pretty=%s") == "Initial commit"


def test_forge_push_requires_confirm(tmp_path: Path, monkeypatch: Any) -> None:
    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("unconfirmed forge push must not run git")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "push",
            "--branch",
            "feature.local",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_confirm_required"


def test_forge_push_refuses_protected_branch(tmp_path: Path, monkeypatch: Any) -> None:
    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("protected forge push must not run git")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "push",
            "--branch",
            "main",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_protected_branch"


def test_forge_push_calls_git_push_without_github_api(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    calls: list[list[str]] = []

    def fake_subprocess_run(
        args: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "push",
            "--branch",
            "feature.local",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "push"
    assert payload["action_performed"] is True
    assert payload["git_writes_performed"] is True
    assert payload["network_calls_performed"] is True
    assert payload["github_writes_performed"] is False
    assert payload["push_performed"] is True
    assert payload["branch"] == "feature.local"
    assert payload["head"] == "feature.local"
    assert calls == [["git", "push", "-u", "origin", "feature.local"]]
