from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.mcp.server import ReadOnlyMcpServer, tool_definitions
from cosheaf.operator_session import (
    OperatorPolicyMode,
    OperatorToolCallStatus,
    load_operator_session_events,
    start_operator_session,
)
from cosheaf.storage.repo import RepoContext


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "operator-session-mcp-fixture"',
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
        "title": "Operator Session MCP Fixture Source",
        "authors": ["A. Maintainer"],
        "year": 2026,
        "doi": "10.1145/operator-session-mcp-fixture",
        "arxiv": "",
        "url": "",
        "theorem_number": "Definition 1",
        "page": "1",
        "notes": "Deterministic operator-session MCP fixture.",
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
        "created_at": "2026-06-16T00:00:00Z",
        "updated_at": "2026-06-16T00:00:00Z",
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
        "id": "issue.fixture.mcp-session",
        "type": "issue",
        "title": "MCP session recording fixture",
        "status": "open",
        "created_at": "2026-06-16T00:00:00Z",
        "updated_at": "2026-06-16T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise MCP session recording without private leakage.",
        "related_artifacts": [
            "claim.fixture.mcp-session-public",
            "claim.fixture.mcp-session-private",
        ],
        "tags": ["mcp", "private-secret"],
    }


def _fixture_repo(repo_root: Path) -> RepoContext:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.mcp-session-public",
            title="MCP session public claim",
            status="accepted",
            tags=["mcp"],
            sources=[_source_fixture()],
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.mcp-session-private",
            title="private-secret draft claim",
            status="draft",
            tags=["private-secret"],
            depends_on=["claim.fixture.mcp-session-public"],
        ),
    )
    _write_yaml(repo_root, "issues/open/mcp-session.yaml", _issue_data())
    return RepoContext(repo_root)


def _request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}


def _start_session(
    context: RepoContext,
    *,
    policy_mode: OperatorPolicyMode = OperatorPolicyMode.PUBLIC_ONLY,
    session_id: str = "session.issue.fixture.mcp-session.0001",
) -> str:
    result = start_operator_session(
        context,
        issue_id="issue.fixture.mcp-session",
        policy_mode=policy_mode,
        operator_label="mcp test operator",
        session_id=session_id,
        now=datetime(2026, 6, 16, 8, 0, tzinfo=UTC),
    )
    return result.session.session_id


def _tool_error_code(response: dict[str, Any]) -> str:
    if "error" in response:
        return str(response["error"]["data"]["code"])
    return str(response["result"]["structuredContent"]["code"])


def test_mcp_tool_call_with_session_id_records_bounded_event(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(
        context,
        policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
    )
    server = ReadOnlyMcpServer(context)

    response = server.handle(
        _request(
            "tools/call",
            {"name": "workspace_info", "arguments": {"session_id": session_id}},
        )
    )

    assert response["result"]["isError"] is False
    events = load_operator_session_events(context, session_id)
    assert len(events) == 1
    event = events[0]
    assert event.event_kind == "tool_call"
    assert event.event["tool_name"] == "workspace_info"
    assert event.event["status"] == OperatorToolCallStatus.COMPLETED.value
    assert event.event["input_metadata"] == {
        "argument_count": "0",
        "argument_names": "none",
        "mcp_mode": "public_adapter",
        "session_mode": "private_research",
    }
    assert event.event["result_summary"] == "completed tool call: workspace_info"

    serialized = json.dumps(event.to_dict())
    assert "kb_roots" not in serialized
    assert "private-secret" not in serialized
    assert "claim.fixture.mcp-session-private" not in serialized


def test_mcp_tool_call_without_session_id_preserves_no_recording_behavior(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(context)
    server = ReadOnlyMcpServer(context)

    response = server.handle(
        _request("tools/call", {"name": "workspace_info", "arguments": {}})
    )

    assert response["result"]["isError"] is False
    assert load_operator_session_events(context, session_id) == ()


def test_mcp_denied_tool_call_with_session_id_is_recorded(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(context)
    server = ReadOnlyMcpServer(context)

    response = server.handle(
        _request(
            "tools/call",
            {
                "name": "promote_artifact",
                "arguments": {
                    "session_id": session_id,
                    "artifact_id": "claim.fixture.mcp-session-public",
                },
            },
        )
    )

    assert _tool_error_code(response) == "tool_not_found"
    events = load_operator_session_events(context, session_id)
    assert len(events) == 1
    event = events[0].event
    assert event["tool_name"] == "promote_artifact"
    assert event["status"] == OperatorToolCallStatus.DENIED.value
    assert event["warning_codes"] == ["tool_not_found"]
    assert event["result_summary"] == (
        "denied tool call: promote_artifact; code=tool_not_found"
    )


def test_mcp_failed_tool_call_with_session_id_is_recorded(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(context)
    server = ReadOnlyMcpServer(context)

    response = server.handle(
        _request(
            "tools/call",
            {"name": "gate_pr_checklist", "arguments": {"session_id": session_id}},
        )
    )

    assert _tool_error_code(response) == "invalid_arguments"
    events = load_operator_session_events(context, session_id)
    assert len(events) == 1
    event = events[0].event
    assert event["tool_name"] == "gate_pr_checklist"
    assert event["status"] == OperatorToolCallStatus.FAILED.value
    assert event["warning_codes"] == ["invalid_arguments"]
    assert event["input_metadata"] == {
        "argument_count": "0",
        "argument_names": "none",
        "mcp_mode": "public_adapter",
        "session_mode": "public_only",
    }


def test_mcp_public_only_session_recording_does_not_store_private_query_text(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    session_id = _start_session(context)
    server = ReadOnlyMcpServer(context)

    response = server.handle(
        _request(
            "tools/call",
            {
                "name": "memory_search",
                "arguments": {
                    "session_id": session_id,
                    "query": "private-secret",
                    "issue_id": "issue.fixture.mcp-session",
                },
            },
        )
    )

    assert response["result"]["isError"] is False
    assert response["result"]["structuredContent"]["cards"] == []
    serialized_response = json.dumps(response)
    assert "claim.fixture.mcp-session-private" not in serialized_response

    events = load_operator_session_events(context, session_id)
    assert len(events) == 1
    serialized_event = json.dumps(events[0].to_dict())
    assert "private-secret" not in serialized_event
    assert "claim.fixture.mcp-session-private" not in serialized_event
    assert "query" in events[0].event["input_metadata"]["argument_names"]


def test_mcp_tool_definitions_accept_optional_session_id() -> None:
    schemas = {
        tool["name"]: tool["inputSchema"]
        for tool in tool_definitions()
        if tool["name"] in {"workspace_info", "memory_search", "gate_pr_checklist"}
    }

    assert schemas["workspace_info"]["properties"]["session_id"] == {
        "type": "string",
        "description": "Optional operator-session ID for bounded tool-call recording.",
    }
    assert "session_id" in schemas["memory_search"]["properties"]
    assert schemas["memory_search"]["required"] == ["query"]
    assert "session_id" in schemas["gate_pr_checklist"]["properties"]
    assert schemas["gate_pr_checklist"]["required"] == ["pr_checklist"]
