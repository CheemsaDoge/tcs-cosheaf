from __future__ import annotations

import json
import subprocess
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.request import Request, urlopen

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.app import open_app
from cosheaf.cli import app
from cosheaf.server import READONLY_SERVER_HOST, ReadOnlySiteApi, make_handler

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.readonly-server",
        "type": "claim",
        "title": "Read-only server fixture claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["readonly-server"],
        "statement": "The local server can expose read-only site payloads.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _issue_data() -> dict[str, Any]:
    return {
        "id": "issue.fixture.readonly-server",
        "type": "issue",
        "title": "Read-only server fixture issue",
        "status": "open",
        "summary": "Exercise read-only local API routing.",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "labels": ["readonly-server"],
        "related_artifacts": ["claim.fixture.readonly-server"],
        "related_sources": [],
        "scope": "public",
    }


def _fixture_workspace(repo_root: Path) -> None:
    _write_yaml(
        repo_root,
        "kb/draft/claims/readonly-server.yaml",
        _artifact_data(),
    )
    _write_yaml(
        repo_root,
        "issues/open/readonly-server.yaml",
        _issue_data(),
    )


def test_readonly_site_api_routes_export_payloads_without_cli_subprocess(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _fixture_workspace(tmp_path)

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("read-only server must not shell out to CLI")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    api = ReadOnlySiteApi(open_app(tmp_path))

    health = api.handle("GET", "/api/health")
    assert health.status == 200
    assert health.payload["readonly"] is True
    assert health.payload["host"] == "127.0.0.1"

    workspace = api.handle("GET", "/api/workspace")
    assert workspace.status == 200
    assert workspace.payload["kind"] == "workspace"

    artifacts = api.handle("GET", "/api/artifacts")
    assert artifacts.status == 200
    assert artifacts.payload["artifacts"][0]["id"] == "claim.fixture.readonly-server"

    context = api.handle("GET", "/api/context/issue.fixture.readonly-server")
    assert context.status == 200
    assert context.payload["issue_id"] == "issue.fixture.readonly-server"
    assert context.payload["context_pack"]["related_artifacts"] == [
        "claim.fixture.readonly-server"
    ]

    missing = api.handle("GET", "/api/context/issue.missing")
    assert missing.status == 404
    assert missing.payload["code"] == "context_pack_not_found"

    refused_write = api.handle("POST", "/api/artifacts")
    assert refused_write.status == 405
    assert refused_write.payload["code"] == "method_not_allowed"


def test_preview_endpoints_plan_actions_without_repo_or_github_writes(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _fixture_workspace(tmp_path)

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("preview endpoints must not run git, gh, or CLI")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    api = ReadOnlySiteApi(open_app(tmp_path))

    local_issue = api.handle(
        "POST",
        "/api/forge/local-issues/preview",
        json.dumps(
            {
                "issue_id": "issue.fixture.web-preview",
                "title": "Preview a local issue",
                "summary": "Show the exact local issue file before writing.",
                "authors": ["tester"],
                "labels": ["website-preview"],
                "related_artifacts": ["claim.fixture.readonly-server"],
                "related_sources": [],
                "scope": "private",
            }
        ),
    )
    assert local_issue.status == 200
    assert local_issue.payload["kind"] == "local_issue_preview"
    assert local_issue.payload["dry_run_only"] is True
    assert local_issue.payload["repo_writes_performed"] is False
    assert local_issue.payload["github_writes_performed"] is False
    assert local_issue.payload["planned_files"] == [
        "issues/open/issue.fixture.web-preview.yaml"
    ]
    assert not (tmp_path / "issues/open/issue.fixture.web-preview.yaml").exists()

    github_issue = api.handle(
        "POST",
        "/api/forge/issues/preview",
        json.dumps({"source_path": "issues/open/readonly-server.yaml"}),
    )
    assert github_issue.status == 200
    assert github_issue.payload["kind"] == "github_issue_preview"
    assert github_issue.payload["network_calls_performed"] is False
    assert github_issue.payload["github_writes_performed"] is False
    assert github_issue.payload["planned_files"] == [
        "issues/open/readonly-server.yaml"
    ]

    github_pr = api.handle(
        "POST",
        "/api/forge/prs/preview",
        json.dumps({"base": "main", "head": "website-preview-actions"}),
    )
    assert github_pr.status == 200
    assert github_pr.payload["kind"] == "github_pr_preview"
    assert github_pr.payload["planned_actions"] == [
        "create GitHub pull request preview"
    ]
    assert github_pr.payload["github_pr_plan"]["head"] == "website-preview-actions"

    review_packet = api.handle(
        "POST",
        "/api/forge/review-packets/preview",
        json.dumps({"issue_id": "issue.fixture.readonly-server"}),
    )
    assert review_packet.status == 200
    assert review_packet.payload["kind"] == "review_packet_preview"
    assert review_packet.payload["planned_files"] == [
        "reviews/website/issue.fixture.readonly-server-review-packet.md"
    ]
    assert review_packet.payload["repo_writes_performed"] is False
    assert not (
        tmp_path
        / "reviews/website/issue.fixture.readonly-server-review-packet.md"
    ).exists()


def test_http_preview_endpoints_allow_localhost_browser_preflight(
    tmp_path: Path,
) -> None:
    _fixture_workspace(tmp_path)
    api = ReadOnlySiteApi(open_app(tmp_path))
    server = HTTPServer((READONLY_SERVER_HOST, 0), make_handler(api))
    port = server.server_port
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        preflight = Request(
            f"http://{READONLY_SERVER_HOST}:{port}/api/forge/prs/preview",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:4321",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        with urlopen(preflight, timeout=5) as response:
            assert response.status == 204
            assert response.headers["Access-Control-Allow-Origin"] == (
                "http://localhost:4321"
            )
            assert "POST" in response.headers["Access-Control-Allow-Methods"]

        request = Request(
            f"http://{READONLY_SERVER_HOST}:{port}/api/forge/prs/preview",
            data=json.dumps(
                {"base": "main", "head": "website-preview-actions"}
            ).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Origin": "http://localhost:4321",
            },
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert response.headers["Access-Control-Allow-Origin"] == (
                "http://localhost:4321"
            )
            assert payload["kind"] == "github_pr_preview"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_server_cli_registers_readonly_localhost_command(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    fake_app = object()
    seen: dict[str, object] = {}

    def fake_open_app(repo_root: Path) -> object:
        seen["repo_root"] = repo_root
        return fake_app

    def fake_serve_readonly_api(app_obj: object, *, host: str, port: int) -> None:
        seen["app"] = app_obj
        seen["host"] = host
        seen["port"] = port

    monkeypatch.setattr("cosheaf.server.cli.open_app", fake_open_app)
    monkeypatch.setattr(
        "cosheaf.server.cli.serve_readonly_api",
        fake_serve_readonly_api,
    )
    result = runner.invoke(
        app,
        [
            "server",
            "serve",
            "--readonly",
            "--port",
            "8765",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert seen == {
        "repo_root": tmp_path,
        "app": fake_app,
        "host": "127.0.0.1",
        "port": 8765,
    }


def test_server_cli_requires_readonly_guard(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "server",
            "serve",
            "--port",
            "8765",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "pass --readonly" in result.output
