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


class _FakeCredentialProvider:
    def __init__(self, *, has_token: bool = True) -> None:
        self.has_token = has_token
        self.calls = 0
        self.secret = "secret-token-value"

    def provider_name(self) -> str:
        return "fake-provider"

    def has_github_token(self) -> bool:
        self.calls += 1
        return self.has_token


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


def _audit_entries(repo_root: Path) -> list[dict[str, Any]]:
    audit_path = repo_root / ".cosheaf" / "audit" / "website-forge-actions.jsonl"
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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


def test_preview_endpoints_do_not_use_backend_credentials(tmp_path: Path) -> None:
    _fixture_workspace(tmp_path)
    credentials = _FakeCredentialProvider()
    api = ReadOnlySiteApi(open_app(tmp_path), credential_provider=credentials)

    response = api.handle(
        "POST",
        "/api/forge/prs/preview",
        json.dumps({"base": "main", "head": "website-authenticated-forge-actions"}),
    )

    assert response.status == 200
    assert response.payload["kind"] == "github_pr_preview"
    assert credentials.calls == 0


def test_authenticated_create_endpoints_require_auth_and_confirm(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _fixture_workspace(tmp_path)

    def fail_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("unauthorized or unconfirmed create must not run gh")

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    no_auth_api = ReadOnlySiteApi(open_app(tmp_path))
    no_auth = no_auth_api.handle(
        "POST",
        "/api/forge/prs/create",
        json.dumps(
            {
                "base": "main",
                "head": "website-authenticated-forge-actions",
                "confirm": True,
            }
        ),
    )
    assert no_auth.status == 401
    assert no_auth.payload["code"] == "auth_required"

    credentials = _FakeCredentialProvider()
    authed_api = ReadOnlySiteApi(open_app(tmp_path), credential_provider=credentials)
    no_confirm = authed_api.handle(
        "POST",
        "/api/forge/prs/create",
        json.dumps({"base": "main", "head": "website-authenticated-forge-actions"}),
    )
    assert no_confirm.status == 400
    assert no_confirm.payload["code"] == "confirm_required"

    audit = _audit_entries(tmp_path)
    assert [entry["result_status"] for entry in audit] == [
        "auth_required",
        "confirm_required",
    ]


def test_authenticated_create_endpoints_call_forge_and_write_redacted_audit(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _fixture_workspace(tmp_path)
    credentials = _FakeCredentialProvider()
    calls: list[list[str]] = []

    def fake_subprocess_run(
        args: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if args[:3] == ["gh", "issue", "create"]:
            stdout = "https://github.com/CheemsaDoge/tcs-cosheaf/issues/1001\n"
        elif args[:3] == ["gh", "pr", "create"]:
            stdout = "https://github.com/CheemsaDoge/tcs-cosheaf/pull/1002\n"
        else:
            raise AssertionError(f"unexpected subprocess call: {args}")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout)

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    api = ReadOnlySiteApi(open_app(tmp_path), credential_provider=credentials)
    issue_response = api.handle(
        "POST",
        "/api/forge/issues/create",
        json.dumps(
            {
                "source_path": "issues/open/readonly-server.yaml",
                "confirm": True,
            }
        ),
    )
    pr_response = api.handle(
        "POST",
        "/api/forge/prs/create",
        json.dumps(
            {
                "base": "main",
                "head": "website-authenticated-forge-actions",
                "draft": True,
                "confirm": True,
            }
        ),
    )

    assert issue_response.status == 200
    assert issue_response.payload["kind"] == "github_issue_create"
    assert issue_response.payload["forge_action"]["github_issue_created"] is True
    assert pr_response.status == 200
    assert pr_response.payload["kind"] == "github_pr_create"
    assert pr_response.payload["forge_action"]["github_pr_created"] is True
    assert credentials.calls == 2
    assert calls[0][:3] == ["gh", "issue", "create"]
    assert calls[1][:3] == ["gh", "pr", "create"]

    response_text = json.dumps(
        [issue_response.payload, pr_response.payload],
        sort_keys=True,
    )
    assert credentials.secret not in response_text
    assert "token" not in response_text.lower()

    audit_path = tmp_path / ".cosheaf" / "audit" / "website-forge-actions.jsonl"
    audit_text = audit_path.read_text(encoding="utf-8")
    assert credentials.secret not in audit_text
    entries = _audit_entries(tmp_path)
    assert [entry["action"] for entry in entries] == [
        "github_issue_create",
        "github_pr_create",
    ]
    assert [entry["credential_provider"] for entry in entries] == [
        "fake-provider",
        "fake-provider",
    ]
    assert all(entry["explicit_confirm"] is True for entry in entries)
    assert all(entry["github_writes_performed"] is True for entry in entries)


def test_authenticated_create_failures_write_redacted_audit(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _fixture_workspace(tmp_path)
    credentials = _FakeCredentialProvider()

    def fail_subprocess_run(
        args: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr=f"gh failed with token {credentials.secret}",
        )

    monkeypatch.setattr(subprocess, "run", fail_subprocess_run)

    api = ReadOnlySiteApi(open_app(tmp_path), credential_provider=credentials)
    response = api.handle(
        "POST",
        "/api/forge/prs/create",
        json.dumps(
            {
                "base": "main",
                "head": "website-authenticated-forge-actions",
                "confirm": True,
            }
        ),
    )

    assert response.status == 400
    assert response.payload["code"] == "forge_github_failed"
    response_text = json.dumps(response.payload, sort_keys=True)
    assert credentials.secret not in response_text
    assert "token" not in response_text.lower()

    entries = _audit_entries(tmp_path)
    assert len(entries) == 1
    assert entries[0]["action"] == "github_pr_create"
    assert entries[0]["result_status"] == "forge_github_failed"
    assert entries[0]["credential_provider"] == "fake-provider"
    assert entries[0]["explicit_confirm"] is True
    assert entries[0]["github_writes_performed"] is False


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
