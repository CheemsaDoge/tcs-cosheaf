from __future__ import annotations

import json
from datetime import UTC, datetime
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
from cosheaf.research.run import start_research_run
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
    _write_yaml(
        repo_root,
        "evals/strategy_planner/cases.yaml",
        {
            "cases": [
                {
                    "id": "case.strategy.no-authority",
                    "kind": "no_authority_escalation",
                }
            ]
        },
    )
    _write_yaml(
        repo_root,
        "evals/research_run_loop/cases.yaml",
        {
            "cases": [
                {
                    "id": "case.run.no-authority",
                    "kind": "no_authority_escalation",
                }
            ]
        },
    )
    return RepoContext(repo_root)


def _write_pr_checklist(repo_root: Path) -> Path:
    path = repo_root / ".github" / "pull_request_template.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "## Summary",
                "## Changed Files",
                "## Tests Run",
                "## Risks",
                "## Interface Changes",
                "## Documentation Changes",
                "## Artifact/Schema Changes",
                "## Gatekeeper Result",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _start_research_run_fixture(context: RepoContext) -> str:
    result = start_research_run(
        context,
        issue_id="issue.fixture.mcp",
        operator_kind="external",
        operator_label="mcp test",
        run_id="run.issue.fixture.mcp",
        now=datetime(2026, 6, 16, 8, 0, tzinfo=UTC),
    )
    return result.record.run_id


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


def test_mcp_tools_list_exposes_operator_readonly_core(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(_request("tools/list"))

    tool_names = [tool["name"] for tool in response["result"]["tools"]]
    required_names = [
        "workspace_info",
        "validate",
        "gate",
        "gate_pr_checklist",
        "memory_cards",
        "memory_search",
        "context_build",
        "context_show",
        "strategy_plan",
        "strategy_show",
        "strategy_graph",
        "strategy_next",
        "run_show",
        "run_evidence_report",
        "eval_strategy_planner",
        "eval_research_run_loop",
    ]
    for name in required_names:
        assert name in tool_names
    assert "gate_run" in tool_names
    assert "orchestrator_plan" in tool_names
    assert "write_accepted" not in tool_names
    assert "promote_artifact" not in tool_names
    assert "mark_human_reviewed" not in tool_names
    assert "arbitrary_shell" not in tool_names


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


def test_mcp_gate_tools_return_structured_runtime_reports(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))
    _write_pr_checklist(tmp_path)

    gate_response = server.handle(
        _request("tools/call", {"name": "gate", "arguments": {}})
    )
    checklist_response = server.handle(
        _request(
            "tools/call",
            {
                "name": "gate_pr_checklist",
                "arguments": {
                    "pr_checklist": ".github/pull_request_template.md",
                },
            },
        )
    )

    gate_payload = gate_response["result"]["structuredContent"]
    checklist_payload = checklist_response["result"]["structuredContent"]
    assert gate_payload["verdict"] == "pass"
    assert gate_payload["accepted_writes"] is False
    assert checklist_payload["verdict"] == "pass"
    assert checklist_payload["accepted_writes"] is False
    assert any(
        gate["id"] == "G8" and gate["status"] == "pass"
        for gate in checklist_payload["gates"]
    )


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


def test_mcp_memory_cards_is_public_only(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(
        _request(
            "tools/call",
            {
                "name": "memory_cards",
                "arguments": {"issue_id": "issue.fixture.mcp"},
            },
        )
    )

    payload = response["result"]["structuredContent"]
    assert payload["public_only"] is True
    assert [card["id"] for card in payload["cards"]] == ["claim.fixture.mcp-public"]
    assert "claim.fixture.mcp-private" not in json.dumps(payload)
    assert "private-secret" not in json.dumps(payload)


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


def test_mcp_strategy_tools_are_runtime_only_and_public_scoped(
    tmp_path: Path,
) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    plan_response = server.handle(
        _request(
            "tools/call",
            {
                "name": "strategy_plan",
                "arguments": {"issue_id": "issue.fixture.mcp"},
            },
        )
    )
    plan_payload = plan_response["result"]["structuredContent"]
    plan_id = plan_payload["plan_id"]

    show_response = server.handle(
        _request(
            "tools/call",
            {"name": "strategy_show", "arguments": {"plan_id": plan_id}},
        )
    )
    graph_response = server.handle(
        _request(
            "tools/call",
            {"name": "strategy_graph", "arguments": {"plan_id": plan_id}},
        )
    )
    next_response = server.handle(
        _request(
            "tools/call",
            {"name": "strategy_next", "arguments": {"plan_id": plan_id}},
        )
    )

    for response in (plan_response, show_response, graph_response, next_response):
        payload = response["result"]["structuredContent"]
        serialized = json.dumps(payload)
        assert payload["accepted_write_performed"] is False
        assert payload["public_only"] is True
        assert "claim.fixture.mcp-private" not in serialized
        assert "private-secret" not in serialized
        assert "human_reviewed" not in serialized
        assert "promotion_authority" not in serialized


def test_mcp_run_read_tools_return_provenance_without_authority(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    run_id = _start_research_run_fixture(context)
    server = ReadOnlyMcpServer(context)

    show_response = server.handle(
        _request("tools/call", {"name": "run_show", "arguments": {"run_id": run_id}})
    )
    report_response = server.handle(
        _request(
            "tools/call",
            {
                "name": "run_evidence_report",
                "arguments": {"run_id": run_id},
            },
        )
    )

    show_payload = show_response["result"]["structuredContent"]
    report_payload = report_response["result"]["structuredContent"]
    assert show_payload["accepted_write_performed"] is False
    assert report_payload["accepted_write_performed"] is False
    assert report_payload["command_count"] == 0
    assert "human review" in report_payload["authority_notice"]


def test_mcp_eval_tools_return_deterministic_reports(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    strategy_response = server.handle(
        _request(
            "tools/call",
            {"name": "eval_strategy_planner", "arguments": {}},
        )
    )
    run_response = server.handle(
        _request(
            "tools/call",
            {"name": "eval_research_run_loop", "arguments": {}},
        )
    )

    strategy_payload = strategy_response["result"]["structuredContent"]
    run_payload = run_response["result"]["structuredContent"]
    assert strategy_payload["kind"] == "strategy_planner_eval"
    assert strategy_payload["passed"] is True
    assert strategy_payload["accepted_write_performed"] is False
    assert run_payload["kind"] == "research_run_loop_eval"
    assert run_payload["passed"] is True
    assert run_payload["accepted_write_performed"] is False


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


def test_mcp_forbidden_tools_are_not_exposed(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(
        _request(
            "tools/call",
            {
                "name": "promote_artifact",
                "arguments": {"artifact_id": "claim.fixture.mcp-public"},
            },
        )
    )

    payload = response["error"]["data"]
    assert payload["code"] == "tool_not_found"
    assert "whitelisted" in payload["remediation"]


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
