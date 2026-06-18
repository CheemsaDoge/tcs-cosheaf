from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.storage.loader import IssueRecord, load_artifacts
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _modern_issue_data(issue_id: str = "issue.fixture.local") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Local issue fixture",
        "status": "open",
        "summary": "Exercise the local issue model.",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "labels": ["local-issue"],
        "related_artifacts": [],
        "related_sources": ["source.fixture.local"],
        "scope": "public",
    }


def _legacy_issue_data(issue_id: str = "issue.fixture.legacy") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Legacy issue fixture",
        "status": "open",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Legacy description text.",
        "related_artifacts": [],
        "tags": ["legacy-label"],
    }


def _draft_artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.issue-close",
        "type": "claim",
        "title": "Issue close draft claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["issue-close"],
        "statement": "A draft claim that must stay draft.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def test_issue_create_show_list_and_close_json(tmp_path: Path) -> None:
    created = runner.invoke(
        app,
        [
            "issue",
            "create",
            "--id",
            "issue.fixture.local-cli",
            "--title",
            "Local issue CLI",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert created.exit_code == 0, created.output
    created_payload = json.loads(created.output)
    assert created_payload["schema_version"] == 1
    assert created_payload["path"] == "issues/open/issue.fixture.local-cli.yaml"
    assert created_payload["github_issue_created"] is False
    assert created_payload["artifact_status_changed"] is False
    assert created_payload["issue"]["id"] == "issue.fixture.local-cli"
    assert created_payload["issue"]["status"] == "open"
    assert created_payload["issue"]["summary"] == "Local issue CLI"
    assert created_payload["issue"]["labels"] == []
    assert created_payload["issue"]["related_sources"] == []
    assert created_payload["issue"]["scope"] == "private"

    source = tmp_path / "issues" / "open" / "issue.fixture.local-cli.yaml"
    assert source.is_file()
    source_data = _read_yaml(source)
    assert source_data["summary"] == "Local issue CLI"
    assert "description" not in source_data
    assert "tags" not in source_data

    shown = runner.invoke(
        app,
        [
            "issue",
            "show",
            "issue.fixture.local-cli",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    listed = runner.invoke(
        app,
        [
            "issue",
            "list",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)["issue"]["id"] == "issue.fixture.local-cli"
    assert listed.exit_code == 0, listed.output
    listed_payload = json.loads(listed.output)
    assert [item["id"] for item in listed_payload["issues"]] == [
        "issue.fixture.local-cli"
    ]

    closed = runner.invoke(
        app,
        [
            "issue",
            "close",
            "issue.fixture.local-cli",
            "--reason",
            "Finished the local issue fixture.",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert closed.exit_code == 0, closed.output
    closed_payload = json.loads(closed.output)
    assert closed_payload["path"] == "issues/closed/issue.fixture.local-cli.yaml"
    assert closed_payload["artifact_status_changed"] is False
    assert not source.exists()
    target = tmp_path / "issues" / "closed" / "issue.fixture.local-cli.yaml"
    assert target.is_file()
    target_data = _read_yaml(target)
    assert target_data["status"] == "closed"
    assert target_data["close_reason"] == "Finished the local issue fixture."


def test_issue_close_does_not_change_related_artifact_status(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path,
        "issues/open/issue.fixture.close-artifact.yaml",
        {
            **_modern_issue_data("issue.fixture.close-artifact"),
            "related_artifacts": ["claim.fixture.issue-close"],
        },
    )
    artifact_path = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.issue-close.yaml",
        _draft_artifact_data(),
    )

    result = runner.invoke(
        app,
        [
            "issue",
            "close",
            "issue.fixture.close-artifact",
            "--reason",
            "Issue workflow done; artifact remains draft.",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["artifact_status_changed"] is False
    assert artifact_path.is_file()
    assert _read_yaml(artifact_path)["status"] == "draft"
    assert not (tmp_path / "kb" / "accepted").exists()
    assert not (tmp_path / "kb" / "refuted").exists()


def test_issue_model_accepts_modern_and_legacy_yaml(tmp_path: Path) -> None:
    _write_yaml(tmp_path, "issues/blocked/modern.yaml", _modern_issue_data())
    _write_yaml(tmp_path, "issues/open/legacy.yaml", _legacy_issue_data())

    records = load_artifacts(RepoContext(tmp_path))
    issues = {
        loaded.id: loaded.record
        for loaded in records
        if isinstance(loaded.record, IssueRecord)
    }

    modern = issues["issue.fixture.local"]
    legacy = issues["issue.fixture.legacy"]
    assert modern.status == "open"
    assert modern.summary == "Exercise the local issue model."
    assert modern.description == modern.summary
    assert modern.labels == ["local-issue"]
    assert modern.tags == modern.labels
    assert modern.related_sources == ["source.fixture.local"]
    assert modern.scope == "public"
    assert legacy.summary == "Legacy description text."
    assert legacy.labels == ["legacy-label"]
    assert legacy.scope == "private"


def test_validate_rejects_invalid_issue_status(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path,
        "issues/open/bad.yaml",
        {
            **_modern_issue_data("issue.fixture.bad-status"),
            "status": "in_progress",
        },
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path), "--json"])

    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["failures"][0]["code"] == "validation_failed"
    assert payload["failures"][0]["related_path"] == "issues/open/bad.yaml"
    assert "status" in payload["failures"][0]["message"]
    assert "Traceback" not in result.output
