from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_issue(repo_root: Path) -> Path:
    path = repo_root / "issues" / "open" / "issue.fixture.github.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "id": "issue.fixture.github",
                "type": "issue",
                "title": "GitHub forge fixture",
                "status": "open",
                "summary": "Create a GitHub issue from local YAML.",
                "created_at": "2026-06-19T00:00:00Z",
                "updated_at": "2026-06-19T00:00:00Z",
                "authors": ["tester"],
                "labels": ["forge", "github"],
                "related_artifacts": [],
                "related_sources": [],
                "scope": "private",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_forge_issue_create_requires_confirm(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    issue_path = _write_issue(tmp_path)

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("unconfirmed GitHub issue create must not run gh")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "issue",
            "create",
            "--from",
            str(issue_path.relative_to(tmp_path)),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_confirm_required"


def test_forge_issue_create_calls_gh_and_links_local_issue(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    issue_path = _write_issue(tmp_path)
    calls: list[list[str]] = []

    def fake_subprocess_run(
        args: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="https://github.com/CheemsaDoge/tcs-cosheaf/issues/999\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "issue",
            "create",
            "--from",
            str(issue_path.relative_to(tmp_path)),
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "github_issue_create"
    assert payload["action_performed"] is True
    assert payload["github_issue_created"] is True
    assert payload["github_writes_performed"] is True
    assert payload["network_calls_performed"] is True
    assert payload["git_writes_performed"] is False
    assert payload["local_issue_closed"] is False
    assert payload["github_issue_url"].endswith("/issues/999")
    assert calls == [
        [
            "gh",
            "issue",
            "create",
            "--title",
            "GitHub forge fixture",
            "--body",
            "Create a GitHub issue from local YAML.",
            "--label",
            "forge",
            "--label",
            "github",
        ]
    ]

    updated = yaml.safe_load(issue_path.read_text(encoding="utf-8"))
    assert updated["status"] == "open"
    assert updated["external_links"] == [
        "https://github.com/CheemsaDoge/tcs-cosheaf/issues/999"
    ]


def test_forge_issue_create_reports_bad_source_as_action_error(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("invalid GitHub issue source must not run gh")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "issue",
            "create",
            "--from",
            "issues/open/missing.yaml",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_invalid_input"
    assert "does not exist" in payload["message"]


def test_forge_pr_create_requires_confirm(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("unconfirmed GitHub PR create must not run gh")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            "feature",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["code"] == "forge_confirm_required"


def test_forge_pr_create_calls_gh_without_push_or_token_storage(
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
            stdout="https://github.com/CheemsaDoge/tcs-cosheaf/pull/1000\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    result = runner.invoke(
        app,
        [
            "forge",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            "feature",
            "--draft",
            "--confirm",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "github_pr_create"
    assert payload["action_performed"] is True
    assert payload["github_pr_created"] is True
    assert payload["github_writes_performed"] is True
    assert payload["network_calls_performed"] is True
    assert payload["git_writes_performed"] is False
    assert payload["push_performed"] is False
    assert payload["github_pr_url"].endswith("/pull/1000")
    assert calls == [
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            "feature",
            "--title",
            "Merge feature into main",
            "--body",
            "Forge-created PR for feature into main.",
            "--draft",
        ]
    ]
    assert not any("token" in path.name.lower() for path in tmp_path.rglob("*"))


def test_forge_sync_is_read_only(tmp_path: Path, monkeypatch: Any) -> None:
    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("forge sync must not call gh in A4.3")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    result = runner.invoke(
        app,
        ["forge", "sync", "--repo-root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "sync"
    assert payload["action_performed"] is False
    assert payload["github_writes_performed"] is False
    assert payload["network_calls_performed"] is False
