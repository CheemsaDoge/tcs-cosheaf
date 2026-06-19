from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.app import open_app
from cosheaf.server import ReadOnlySiteApi


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _audit_entries(repo_root: Path) -> list[dict[str, Any]]:
    audit_path = repo_root / ".cosheaf" / "audit" / "web-actions.jsonl"
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.issue-workbench",
        "type": "claim",
        "title": "Issue workbench draft claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["issue-workbench"],
        "statement": "A draft claim that must stay draft.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _issue_data(issue_id: str = "issue.fixture.issue-workbench") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Issue workbench fixture",
        "status": "open",
        "summary": "Exercise web issue workbench actions.",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "labels": ["issue-workbench"],
        "related_artifacts": ["claim.fixture.issue-workbench"],
        "related_sources": [],
        "scope": "private",
    }


def _fixture_workspace(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "kb/draft/claims/claim.fixture.issue-workbench.yaml",
        _artifact_data(),
    )
    _write_yaml(
        repo_root,
        "issues/open/issue.fixture.issue-workbench.yaml",
        _issue_data(),
    )


def test_web_issue_preview_create_then_create_updates_live_list(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))
    payload = {
        "issue_id": "issue.fixture.web-created",
        "title": "Web-created issue",
        "summary": "Created through the local web issue workbench.",
        "authors": ["web-user"],
        "labels": ["web", "issue-workbench"],
        "related_artifacts": ["claim.fixture.issue-workbench"],
        "related_sources": [],
        "scope": "public",
    }

    preview = api.handle(
        "POST",
        "/api/issues/preview-create",
        json.dumps(payload),
    )

    assert preview.status == 200
    assert preview.payload["kind"] == "issue_create_preview"
    assert preview.payload["dry_run_only"] is True
    assert preview.payload["repo_writes_performed"] is False
    assert preview.payload["planned_files"] == [
        "issues/open/issue.fixture.web-created.yaml"
    ]
    assert "diff" in preview.payload
    assert not (tmp_path / "issues/open/issue.fixture.web-created.yaml").exists()

    blocked = api.handle(
        "POST",
        "/api/issues/create",
        json.dumps(payload),
    )
    assert blocked.status == 400
    assert blocked.payload["code"] == "confirm_required"

    created = api.handle(
        "POST",
        "/api/issues/create",
        json.dumps({**payload, "confirm": True}),
    )

    assert created.status == 200
    assert created.payload["kind"] == "issue_create"
    assert created.payload["repo_writes_performed"] is True
    assert created.payload["issue"]["id"] == "issue.fixture.web-created"
    assert (tmp_path / "issues/open/issue.fixture.web-created.yaml").is_file()

    listed = api.handle("GET", "/api/issues/live")
    assert listed.status == 200
    assert "issue.fixture.web-created" in [
        issue["id"] for issue in listed.payload["issues"]
    ]

    entries = _audit_entries(tmp_path)
    assert [entry["action"] for entry in entries] == [
        "issue.create",
        "issue.create",
        "issue.create",
    ]
    assert entries[0]["preview_only"] is True
    assert entries[1]["result_status"] == "confirm_required"
    assert entries[2]["repo_writes_performed"] is True


def test_web_issue_preview_update_then_update_preserves_identity_and_created_at(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))
    issue_path = tmp_path / "issues/open/issue.fixture.issue-workbench.yaml"
    before = _read_yaml(issue_path)
    payload = {
        "title": "Updated issue workbench fixture",
        "summary": "Updated through the web workbench.",
        "authors": ["tester", "web-user"],
        "labels": ["updated"],
        "related_artifacts": ["claim.fixture.issue-workbench"],
        "related_sources": [],
        "scope": "private",
    }

    preview = api.handle(
        "POST",
        "/api/issues/issue.fixture.issue-workbench/preview-update",
        json.dumps(payload),
    )

    assert preview.status == 200
    assert preview.payload["kind"] == "issue_update_preview"
    assert preview.payload["dry_run_only"] is True
    assert _read_yaml(issue_path) == before
    assert "-title: Issue workbench fixture" in preview.payload["diff"]
    assert "+title: Updated issue workbench fixture" in preview.payload["diff"]

    updated = api.handle(
        "POST",
        "/api/issues/issue.fixture.issue-workbench/update",
        json.dumps({**payload, "confirm": True}),
    )

    assert updated.status == 200
    assert updated.payload["kind"] == "issue_update"
    after = _read_yaml(issue_path)
    assert after["id"] == "issue.fixture.issue-workbench"
    assert after["created_at"] == before["created_at"]
    assert after["title"] == "Updated issue workbench fixture"
    assert after["labels"] == ["updated"]


def test_web_issue_preview_close_then_close_preserves_artifact_status(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))
    artifact_path = tmp_path / "kb/draft/claims/claim.fixture.issue-workbench.yaml"

    preview = api.handle(
        "POST",
        "/api/issues/issue.fixture.issue-workbench/preview-close",
        json.dumps({"reason": "Issue workflow done; artifact stays draft."}),
    )

    assert preview.status == 200
    assert preview.payload["kind"] == "issue_close_preview"
    assert preview.payload["dry_run_only"] is True
    assert preview.payload["artifact_status_changed"] is False
    assert (tmp_path / "issues/open/issue.fixture.issue-workbench.yaml").is_file()
    assert not (tmp_path / "issues/closed/issue.fixture.issue-workbench.yaml").exists()
    assert _read_yaml(artifact_path)["status"] == "draft"

    blocked = api.handle(
        "POST",
        "/api/issues/issue.fixture.issue-workbench/close",
        json.dumps({"reason": "Missing confirm."}),
    )
    assert blocked.status == 400
    assert blocked.payload["code"] == "confirm_required"

    closed = api.handle(
        "POST",
        "/api/issues/issue.fixture.issue-workbench/close",
        json.dumps(
            {
                "reason": "Issue workflow done; artifact stays draft.",
                "confirm": True,
            }
        ),
    )

    assert closed.status == 200
    assert closed.payload["kind"] == "issue_close"
    assert closed.payload["artifact_status_changed"] is False
    assert not (tmp_path / "issues/open/issue.fixture.issue-workbench.yaml").exists()
    closed_path = tmp_path / "issues/closed/issue.fixture.issue-workbench.yaml"
    assert closed_path.is_file()
    closed_issue = _read_yaml(closed_path)
    assert closed_issue["status"] == "closed"
    assert closed_issue["close_reason"] == "Issue workflow done; artifact stays draft."
    assert _read_yaml(artifact_path)["status"] == "draft"

    shown = api.handle("GET", "/api/issues/issue.fixture.issue-workbench")
    assert shown.status == 200
    assert shown.payload["issue"]["status"] == "closed"
