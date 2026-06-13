from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

import cosheaf
from cosheaf.cli import app
from cosheaf.mcp.server import (
    READ_ONLY_PROMPT_NAMES,
    READ_ONLY_TOOL_NAMES,
    ReadOnlyMcpServer,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "mcp-fixture"',
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


def _source_fixture() -> dict[str, Any]:
    return {
        "kind": "paper",
        "title": "MCP Fixture Source",
        "authors": ["A. Maintainer"],
        "year": 2026,
        "doi": "10.1145/mcp-fixture",
        "arxiv": "",
        "url": "",
        "theorem_number": "Definition 1",
        "page": "1",
        "notes": "Deterministic MCP fixture.",
    }


def _artifact_data(
    artifact_id: str,
    *,
    title: str,
    status: str,
    tags: list[str],
    sources: list[dict[str, Any]] | None = None,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-09T00:00:00Z",
        "updated_at": "2026-06-09T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags,
        "statement": f"{title}.",
        "evidence": [],
        "sources": sources or [],
        "review": {"state": "requested", "notes": "MCP fixture review."},
        "risk": {"level": "low", "notes": "MCP fixture risk."},
    }


def _issue_data() -> dict[str, Any]:
    return {
        "id": "issue.fixture.mcp",
        "type": "issue",
        "title": "MCP read-only fixture",
        "status": "open",
        "created_at": "2026-06-09T00:00:00Z",
        "updated_at": "2026-06-09T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise read-only MCP tools without leaking private data.",
        "related_artifacts": [
            "claim.fixture.mcp-public",
            "claim.fixture.mcp-private",
        ],
        "tags": ["mcp", "private-secret"],
    }


def _fixture_repo(repo_root: Path) -> RepoContext:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.mcp-public",
            title="MCP public claim",
            status="accepted",
            tags=["mcp"],
            sources=[_source_fixture()],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.mcp-private",
            title="private-secret draft claim",
            status="draft",
            tags=["private-secret"],
            depends_on=["claim.fixture.mcp-public"],
        ),
    )
    _write_yaml(repo_root, "issues/open/mcp.yaml", _issue_data())
    return RepoContext(repo_root)


def _request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}


def test_mcp_initialize_reports_package_version(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(_request("initialize"))

    assert response["result"]["serverInfo"] == {
        "name": "tcs-cosheaf-readonly",
        "version": cosheaf.__version__,
    }


def test_mcp_tools_list_exposes_read_only_whitelist(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(_request("tools/list"))

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    tool_names = [tool["name"] for tool in response["result"]["tools"]]
    assert tool_names == list(READ_ONLY_TOOL_NAMES)
    assert "draft_write" not in tool_names
    assert "artifact_promote" not in tool_names
    assert "shell" not in tool_names


def test_mcp_tool_call_returns_structured_workspace_info(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(
        _request("tools/call", {"name": "workspace_info", "arguments": {}})
    )

    result = response["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["mode"] == "configured"
    assert [root["name"] for root in result["structuredContent"]["kb_roots"]] == [
        "public",
        "private",
    ]


def test_mcp_resource_reads_respect_public_scope(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    public_response = server.handle(
        _request(
            "resources/read",
            {"uri": "cosheaf://artifacts/claim.fixture.mcp-public/card"},
        )
    )
    private_response = server.handle(
        _request(
            "resources/read",
            {"uri": "cosheaf://artifacts/claim.fixture.mcp-private/card"},
        )
    )

    public_payload = json.loads(public_response["result"]["contents"][0]["text"])
    assert public_payload["artifact_id"] == "claim.fixture.mcp-public"
    assert public_payload["root_scope"] == "public"
    assert private_response["error"]["code"] == -32000
    assert private_response["error"]["data"]["code"] == "private_resource_denied"


def test_mcp_memory_search_does_not_return_private_hits(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(
        _request(
            "tools/call",
            {
                "name": "memory_search",
                "arguments": {
                    "query": "private-secret",
                    "issue_id": "issue.fixture.mcp",
                },
            },
        )
    )

    payload = response["result"]["structuredContent"]
    assert payload["cards"] == []
    assert "claim.fixture.mcp-private" not in json.dumps(payload)


def test_mcp_context_build_is_public_only(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(
        _request(
            "tools/call",
            {
                "name": "context_build",
                "arguments": {"issue_id": "issue.fixture.mcp"},
            },
        )
    )

    payload = response["result"]["structuredContent"]
    assert payload["public_only"] is True
    assert payload["accepted_writes"] is False
    assert "claim.fixture.mcp-private" not in (
        tmp_path
        / "context"
        / "TASKS"
        / "issue.fixture.mcp"
        / "RETRIEVAL_AUDIT.json"
    ).read_text(encoding="utf-8")


def test_mcp_prompts_list_and_get_governance_safe_templates(
    tmp_path: Path,
) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    list_response = server.handle(_request("prompts/list"))

    prompt_names = [prompt["name"] for prompt in list_response["result"]["prompts"]]
    assert prompt_names == list(READ_ONLY_PROMPT_NAMES)

    get_response = server.handle(
        _request(
            "prompts/get",
            {
                "name": "start_issue_work",
                "arguments": {"issue_id": "issue.fixture.mcp"},
            },
        )
    )

    text = get_response["result"]["messages"][0]["content"]["text"]
    assert "accepted" in text
    assert "draft" in text
    assert "artifact IDs" in text
    assert "Do not write accepted knowledge" in text
    assert "make validate" in text
    assert "make gate" in text
    assert "make test" in text
    assert "private-secret" not in text
    assert "claim.fixture.mcp-private" not in text


def test_mcp_resources_list_scope_aware_templates(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(_request("resources/list"))

    uris = [resource["uri"] for resource in response["result"]["resources"]]
    assert "cosheaf://workspace" in uris
    assert "cosheaf://artifacts/public/{artifact_id}/card" in uris
    assert "cosheaf://artifacts/private/{artifact_id}/card" in uris
    assert "cosheaf://context/public/{issue_id}" in uris
    assert "cosheaf://context/private/{issue_id}" in uris


def test_mcp_private_scoped_resources_require_policy_permission(
    tmp_path: Path,
) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    artifact_response = server.handle(
        _request(
            "resources/read",
            {"uri": "cosheaf://artifacts/private/claim.fixture.mcp-private/card"},
        )
    )
    context_response = server.handle(
        _request(
            "resources/read",
            {"uri": "cosheaf://context/private/issue.fixture.mcp"},
        )
    )

    assert artifact_response["error"]["data"]["code"] == "private_resource_denied"
    assert context_response["error"]["data"]["code"] == "private_resource_denied"


def test_mcp_cli_list_tools_and_stdio_tools_list(tmp_path: Path) -> None:
    _fixture_repo(tmp_path)

    list_result = runner.invoke(
        app,
        ["mcp", "list-tools", "--repo-root", str(tmp_path)],
    )
    assert list_result.exit_code == 0, list_result.output
    assert "workspace_info" in list_result.output
    assert "artifact_promote" not in list_result.output

    request_line = json.dumps(_request("tools/list")) + "\n"
    serve_result = runner.invoke(
        app,
        ["mcp", "serve", "--stdio", "--repo-root", str(tmp_path)],
        input=request_line,
    )
    assert serve_result.exit_code == 0, serve_result.output
    response = json.loads(serve_result.output)
    assert [tool["name"] for tool in response["result"]["tools"]] == list(
        READ_ONLY_TOOL_NAMES
    )
