from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
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
from cosheaf.verification.counterexample_evidence import (
    CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
)

runner = CliRunner()

CONTROLLED_TOOL_NAMES = [
    "draft_artifact_create_or_update",
    "source_note_draft_create",
    "worker_bundle_validate",
    "worker_bundle_stage",
    "review_request_from_bundle",
    "checked_counterexample_evidence_validate",
    "checked_counterexample_evidence_stage",
    "failure_log_add_draft",
    "research_run_start",
    "research_run_append_command",
    "research_run_append_artifact",
    "research_run_append_output",
    "research_run_finalize",
    "research_run_export_review_dry_run",
    "research_run_export_review",
    "strategy_update_from_run",
    "strategy_export_review_dry_run",
    "strategy_export_review",
]


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


def _draft_artifact_request(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "artifact_id": "claim.fixture.mcp-draft",
        "artifact_type": "claim",
        "title": "MCP draft claim",
        "domain": ["testing"],
        "status": "draft",
        "statement": "A controlled MCP draft claim.",
        "authors": ["tester"],
        "tags": ["mcp"],
        "depends_on": ["claim.fixture.mcp-public"],
        "supersedes": [],
        "target_surface": "draft",
    }
    data.update(overrides)
    return data


def _source_note_request(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "source_id": "source.fixture.mcp",
        "kind": "paper",
        "title": "MCP Source Note",
        "authors": ["A. Maintainer"],
        "year": 2026,
        "notes": "Controlled source-note fixture.",
    }
    data.update(overrides)
    return data


def _worker_bundle_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "bundle_id": "bundle.issue.fixture.mcp.reasoner.0001",
        "task_id": "task.issue.fixture.mcp.reasoner",
        "worker_role": "reasoner",
        "created_at": "2026-06-16T08:00:00Z",
        "summary": "Drafted one reviewable claim for MCP tests.",
        "used_artifacts": ["claim.fixture.mcp-public"],
        "used_sources": ["sources/notes/source.fixture.mcp.yaml"],
        "claims": ["The MCP fixture claim remains draft until review."],
        "proposed_artifacts": [
            {
                "path": "kb/private/draft/claims/claim.fixture.bundle-output.yaml",
                "summary": "Draft claim proposed by the worker bundle.",
            }
        ],
        "assumptions": ["Fixture assumption."],
        "uncertainty": ["No human review was performed."],
        "verification_requests": ["Run validation and gate before review."],
        "failed_attempts": ["A direct proof attempt did not close the claim."],
        "counterexamples": ["Candidate remains unchecked."],
        "counterexample_candidates": [
            {
                "candidate_id": "candidate.fixture.mcp.0001",
                "target_claim": "claim.fixture.mcp-private",
                "construction_summary": "A tiny unchecked candidate.",
                "evidence_paths": [".cosheaf/evidence/candidate.json"],
                "verifier_request_ids": ["verifier.request.fixture.mcp.0001"],
                "status": "proposed",
                "limitations": "Not checked by a verifier or reviewer.",
            }
        ],
        "failures_or_counterexamples": ["No machine proof was performed."],
        "dependency_questions": ["Should another definition be cited?"],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Request human review before promotion."],
        "confidence": "medium",
    }
    data.update(overrides)
    return data


def _write_worker_bundle(
    repo_root: Path,
    *,
    relative_path: str = "outputs/bundle.yaml",
    **overrides: Any,
) -> str:
    _write_yaml(repo_root, relative_path, _worker_bundle_data(**overrides))
    return relative_path


def _checked_evidence_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "evidence_id": (
            "checked-counterexample.claim.fixture.mcp.candidate.0001.habc123"
        ),
        "target_artifact_id": "claim.fixture.mcp-private",
        "candidate_id": "candidate.fixture.mcp.0001",
        "candidate_source": "worker_bundle",
        "check_method": "verifier_result",
        "checked_result": "checked_refutes",
        "verifier_evidence_ids": ["verifier-evidence.claim.fixture.mcp.habc123"],
        "review_record_paths": [],
        "evidence_paths": [".cosheaf/evidence/candidate-check.json"],
        "created_at": "2026-06-16T08:00:00Z",
        "checker": "mcp-test-checker",
        "limitations": [
            "Checked counterexample evidence is evidence for review only.",
            CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
        ],
    }
    data.update(overrides)
    return data


def _failure_log_entry(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "failure_id": "failure.fixture.mcp.0001",
        "attempted_at": "2026-06-16T08:00:00Z",
        "recorded_by": "mcp-test",
        "origin": "agent",
        "attempt_kind": "proof_attempt",
        "target": "claim.fixture.mcp-private",
        "direction": "Try a direct proof.",
        "summary": "The direct proof attempt failed.",
        "failed_because": "The fixture needs a smaller lemma.",
        "evidence_paths": [],
        "related_verifier_results": [],
        "related_counterexample_candidates": [],
        "next_possible_directions": ["Try a smaller lemma."],
        "status": "open",
        "limitations": "Failure memory only; not proof or review evidence.",
    }
    data.update(overrides)
    return data


def _command_record(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "argv": ["python", "-m", "pytest"],
        "cwd": ".",
        "started_at": "2026-06-16T08:01:00Z",
        "ended_at": "2026-06-16T08:02:00Z",
        "exit_code": 0,
        "status": "completed",
    }
    data.update(overrides)
    return data


def _output_ref(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "kind": "controlled_write",
        "path": "kb/private/draft/claims/claim.fixture.mcp-draft.yaml",
        "identifier": "claim.fixture.mcp-draft",
        "status": "completed",
        "summary": "controlled draft artifact write",
    }
    data.update(overrides)
    return data


def _tool_payload(response: dict[str, Any]) -> dict[str, Any]:
    assert "error" not in response
    result = response["result"]
    assert isinstance(result, dict)
    assert result["isError"] is False
    payload = result["structuredContent"]
    assert isinstance(payload, dict)
    assert payload["accepted_write_performed"] is False
    return payload


def _tool_error_code(response: dict[str, Any]) -> str:
    if "error" in response:
        return str(response["error"]["data"]["code"])
    result = response["result"]
    assert result["isError"] is True
    return str(result["structuredContent"]["code"])


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


def test_mcp_tools_list_exposes_controlled_write_core(tmp_path: Path) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(_request("tools/list"))

    tool_names = [tool["name"] for tool in response["result"]["tools"]]
    for name in CONTROLLED_TOOL_NAMES:
        assert name in tool_names
    assert "write_accepted" not in tool_names
    assert "promote_artifact" not in tool_names
    assert "mark_human_reviewed" not in tool_names
    assert "run_hosted_provider_by_default" not in tool_names
    assert "arbitrary_shell" not in tool_names


def test_mcp_controlled_write_tools_wrap_safe_services(tmp_path: Path) -> None:
    context = _fixture_repo(tmp_path)
    server = ReadOnlyMcpServer(context)
    bundle_path = _write_worker_bundle(tmp_path)

    draft_dry = server.handle(
        _request(
            "tools/call",
            {
                "name": "draft_artifact_create_or_update",
                "arguments": {"request": _draft_artifact_request(), "dry_run": True},
            },
        )
    )
    assert _tool_payload(draft_dry)["dry_run"] is True
    assert not (
        tmp_path / "kb/private/draft/claims/claim.fixture.mcp-draft.yaml"
    ).exists()

    draft_write = server.handle(
        _request(
            "tools/call",
            {
                "name": "draft_artifact_create_or_update",
                "arguments": {"request": _draft_artifact_request()},
            },
        )
    )
    draft_payload = _tool_payload(draft_write)
    assert draft_payload["kind"] == "draft_artifact"
    assert draft_payload["written_paths"] == [
        "kb/private/draft/claims/claim.fixture.mcp-draft.yaml"
    ]

    source_write = server.handle(
        _request(
            "tools/call",
            {
                "name": "source_note_draft_create",
                "arguments": {"request": _source_note_request()},
            },
        )
    )
    source_payload = _tool_payload(source_write)
    assert source_payload["kind"] == "source_note"
    assert source_payload["path"] == "sources/notes/source.fixture.mcp.yaml"

    bundle_validate = server.handle(
        _request(
            "tools/call",
            {
                "name": "worker_bundle_validate",
                "arguments": {"bundle_path": bundle_path},
            },
        )
    )
    assert _tool_payload(bundle_validate)["bundle_id"] == (
        "bundle.issue.fixture.mcp.reasoner.0001"
    )

    bundle_stage = server.handle(
        _request(
            "tools/call",
            {
                "name": "worker_bundle_stage",
                "arguments": {
                    "task_id": "task.issue.fixture.mcp.reasoner",
                    "bundle_path": bundle_path,
                    "dry_run": True,
                },
            },
        )
    )
    assert _tool_payload(bundle_stage)["accepted_for_review"] is True

    review_request = server.handle(
        _request(
            "tools/call",
            {
                "name": "review_request_from_bundle",
                "arguments": {"bundle_path": bundle_path},
            },
        )
    )
    review_payload = _tool_payload(review_request)
    assert review_payload["kind"] == "review_request"
    assert review_payload["written_paths"] == [
        "reviews/requests/review.request.bundle.issue.fixture.mcp.reasoner.0001.yaml"
    ]

    checked_validate = server.handle(
        _request(
            "tools/call",
            {
                "name": "checked_counterexample_evidence_validate",
                "arguments": {"evidence": _checked_evidence_data()},
            },
        )
    )
    assert _tool_payload(checked_validate)["valid"] is True

    checked_stage = server.handle(
        _request(
            "tools/call",
            {
                "name": "checked_counterexample_evidence_stage",
                "arguments": {"evidence": _checked_evidence_data(), "dry_run": True},
            },
        )
    )
    assert _tool_payload(checked_stage)["dry_run"] is True

    failure_write = server.handle(
        _request(
            "tools/call",
            {
                "name": "failure_log_add_draft",
                "arguments": {
                    "artifact_id": "claim.fixture.mcp-private",
                    "entry": _failure_log_entry(),
                },
            },
        )
    )
    assert _tool_payload(failure_write)["kind"] == "artifact_failure_log_entry"

    run_start = server.handle(
        _request(
            "tools/call",
            {
                "name": "research_run_start",
                "arguments": {
                    "issue_id": "issue.fixture.mcp",
                    "operator_kind": "external",
                    "operator_label": "MCP test",
                    "run_id": "run.issue.fixture.mcp.controlled",
                },
            },
        )
    )
    run_id = _tool_payload(run_start)["run_id"]

    for name, arguments in [
        (
            "research_run_append_command",
            {"run_id": run_id, "command": _command_record()},
        ),
        (
            "research_run_append_artifact",
            {
                "run_id": run_id,
                "artifact_id": "claim.fixture.mcp-private",
                "mode": "read",
            },
        ),
        (
            "research_run_append_output",
            {"run_id": run_id, "output": _output_ref()},
        ),
    ]:
        response = server.handle(
            _request("tools/call", {"name": name, "arguments": arguments})
        )
        _tool_payload(response)

    finalize = server.handle(
        _request(
            "tools/call",
            {
                "name": "research_run_finalize",
                "arguments": {
                    "run_id": run_id,
                    "status": "completed",
                    "stop_reason": "MCP controlled-write smoke completed.",
                },
            },
        )
    )
    assert _tool_payload(finalize)["status"] == "completed"

    run_export_dry = server.handle(
        _request(
            "tools/call",
            {
                "name": "research_run_export_review_dry_run",
                "arguments": {"run_id": run_id},
            },
        )
    )
    assert _tool_payload(run_export_dry)["dry_run"] is True

    run_export = server.handle(
        _request(
            "tools/call",
            {
                "name": "research_run_export_review",
                "arguments": {"run_id": run_id},
            },
        )
    )
    assert _tool_payload(run_export)["written_paths"] == [
        f"reviews/runs/{run_id}.yaml"
    ]

    plan_response = server.handle(
        _request(
            "tools/call",
            {"name": "strategy_plan", "arguments": {"issue_id": "issue.fixture.mcp"}},
        )
    )
    plan_id = _tool_payload(plan_response)["plan_id"]

    strategy_update = server.handle(
        _request(
            "tools/call",
            {
                "name": "strategy_update_from_run",
                "arguments": {"plan_id": plan_id, "run_id": run_id},
            },
        )
    )
    assert _tool_payload(strategy_update)["plan_id"] == plan_id

    strategy_export_dry = server.handle(
        _request(
            "tools/call",
            {
                "name": "strategy_export_review_dry_run",
                "arguments": {"plan_id": plan_id},
            },
        )
    )
    assert _tool_payload(strategy_export_dry)["dry_run"] is True

    strategy_export = server.handle(
        _request(
            "tools/call",
            {
                "name": "strategy_export_review",
                "arguments": {"plan_id": plan_id},
            },
        )
    )
    assert _tool_payload(strategy_export)["written_paths"] == [
        f"reviews/strategy/{plan_id}.yaml"
    ]


@pytest.mark.parametrize(
    ("tool_name", "arguments", "expected_code"),
    [
        (
            "draft_artifact_create_or_update",
            {"request": _draft_artifact_request(status="accepted")},
            "accepted_write_forbidden",
        ),
        (
            "source_note_draft_create",
            {
                "request": _source_note_request(
                    target_path="kb/public/accepted/sources/source.fixture.bad.yaml"
                )
            },
            "accepted_write_forbidden",
        ),
        (
            "worker_bundle_validate",
            {"bundle_path": "missing/bundle.yaml"},
            "worker_bundle_validate_failed",
        ),
        (
            "worker_bundle_stage",
            {
                "task_id": "task.issue.fixture.mcp.reasoner",
                "bundle_path": "missing/bundle.yaml",
            },
            "bundle_submit_failed",
        ),
        (
            "review_request_from_bundle",
            {"bundle_path": "missing/bundle.yaml"},
            "review_request_failed",
        ),
        (
            "checked_counterexample_evidence_validate",
            {"evidence": {**_checked_evidence_data(), "human_reviewed": True}},
            "authority_claim_forbidden",
        ),
        (
            "checked_counterexample_evidence_stage",
            {"evidence": {**_checked_evidence_data(), "promote": True}},
            "authority_claim_forbidden",
        ),
        (
            "failure_log_add_draft",
            {
                "artifact_id": "claim.fixture.mcp-public",
                "entry": _failure_log_entry(),
            },
            "accepted_write_forbidden",
        ),
        (
            "research_run_start",
            {
                "issue_id": "issue.fixture.mcp",
                "operator_kind": "external",
                "operator_label": "MCP test",
                "run_id": "not a valid run id",
            },
            "research_run_validation_failed",
        ),
        (
            "research_run_append_command",
            {
                "run_id": "run.missing",
                "command": {**_command_record(), "human_reviewed": True},
            },
            "authority_claim_forbidden",
        ),
        (
            "research_run_append_artifact",
            {
                "run_id": "run.missing",
                "artifact_id": "claim.fixture.mcp-private",
                "mode": "accepted",
            },
            "research_run_not_found",
        ),
        (
            "research_run_append_output",
            {
                "run_id": "run.missing",
                "output": {**_output_ref(), "promotion_authority": True},
            },
            "authority_claim_forbidden",
        ),
        (
            "research_run_finalize",
            {
                "run_id": "run.missing",
                "status": "completed",
                "stop_reason": "missing run",
            },
            "research_run_not_found",
        ),
        (
            "research_run_export_review_dry_run",
            {"run_id": "run.missing"},
            "research_run_not_found",
        ),
        (
            "research_run_export_review",
            {"run_id": "run.missing"},
            "research_run_not_found",
        ),
        (
            "strategy_update_from_run",
            {"plan_id": "strategy.issue.missing.plan", "run_id": "run.missing"},
            "strategy_plan_not_found",
        ),
        (
            "strategy_export_review_dry_run",
            {"plan_id": "strategy.issue.missing.plan"},
            "strategy_plan_not_found",
        ),
        (
            "strategy_export_review",
            {"plan_id": "strategy.issue.missing.plan"},
            "strategy_plan_not_found",
        ),
    ],
)
def test_mcp_controlled_write_tools_return_expected_errors(
    tmp_path: Path,
    tool_name: str,
    arguments: dict[str, Any],
    expected_code: str,
) -> None:
    server = ReadOnlyMcpServer(_fixture_repo(tmp_path))

    response = server.handle(
        _request("tools/call", {"name": tool_name, "arguments": arguments})
    )

    assert _tool_error_code(response) == expected_code


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
