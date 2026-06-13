from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.evals.agent_workflow import (
    DEFAULT_AGENT_WORKFLOW_EVAL_CASES,
    AgentWorkflowEvalCase,
    AgentWorkflowEvalKind,
    AgentWorkflowEvalSuite,
    AgentWorkflowEvalSurface,
    load_agent_workflow_eval_suite,
    run_agent_workflow_eval_suite,
)
from cosheaf.storage.repo import RepoContext

ROOT = Path(__file__).resolve().parents[1]


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "agent-workflow-eval-fixture"',
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


def _artifact_data(
    artifact_id: str,
    *,
    title: str,
    status: str,
    statement: str,
    tags: list[str] | None = None,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags or ["agent-workflow-eval"],
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Eval fixture review."},
        "risk": {"level": "low", "notes": "Eval fixture risk."},
    }


def _issue_data(issue_id: str = "issue.fixture.agent-workflow") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Evaluate agent workflow fixture",
        "status": "open",
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": (
            "Evaluate public CLI-agent and provider-worker boundaries without "
            "leaking private-secret-eval."
        ),
        "related_artifacts": [
            "claim.fixture.agent-public",
            "claim.fixture.agent-private",
        ],
        "tags": ["agent-workflow-eval", "private-secret-eval"],
    }


def _write_fixture_repo(repo_root: Path) -> None:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.agent-public",
            title="Public agent workflow fixture",
            status="accepted",
            statement="Public context for agent workflow eval.",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.agent-private",
            title="private-secret-eval private fixture",
            status="draft",
            statement="Private context containing sk-private-eval-secret.",
            tags=["agent-workflow-eval", "private-secret-eval"],
            depends_on=["claim.fixture.agent-public"],
        ),
    )
    _write_yaml(repo_root, "issues/open/agent-workflow.yaml", _issue_data())


def _accepted_artifact_request() -> dict[str, Any]:
    return {
        "artifact_id": "claim.fixture.accepted-write",
        "artifact_type": "claim",
        "title": "Accepted write should be rejected",
        "domain": ["testing"],
        "status": "accepted",
        "statement": "This must not be written.",
        "authors": ["tester"],
        "tags": ["agent-workflow-eval"],
        "depends_on": [],
        "supersedes": [],
    }


def _fake_provider_request() -> dict[str, Any]:
    return {
        "model": "fake-deterministic",
        "worker_role": "reasoner",
        "prompt": "Use sk-provider-eval-secret only as a redaction fixture.",
        "context_artifact_ids": ["claim.fixture.agent-public"],
        "root_scopes": ["public"],
        "output_kind": "text",
        "expected_output_paths": ["kb/private/draft/claims/provider-eval.yaml"],
    }


def _malformed_bundle() -> dict[str, Any]:
    return {
        "bundle_id": "bundle.issue.fixture.agent-workflow.reasoner.0001",
        "task_id": "task.issue.fixture.agent-workflow.reasoner",
        "worker_role": "reasoner",
        "created_at": "2026-06-10T00:00:00Z",
        "summary": "Malformed bundle is missing required confidence.",
        "used_artifacts": ["claim.fixture.agent-public"],
        "used_sources": [],
        "claims": ["Review-only malformed bundle."],
        "proposed_artifacts": [],
        "verification_requests": [],
        "failures_or_counterexamples": [],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Fix the bundle."],
    }


def _workflow_suite(repo_root: Path) -> AgentWorkflowEvalSuite:
    _write_json(
        repo_root,
        "requests/accepted-write.json",
        _accepted_artifact_request(),
    )
    _write_json(
        repo_root,
        "requests/fake-provider.json",
        _fake_provider_request(),
    )
    _write_yaml(
        repo_root,
        "bundles/malformed.yaml",
        _malformed_bundle(),
    )
    malformed_bundle_request = _write_json(
        repo_root,
        "requests/malformed-bundle-submit.json",
        {
            "task_id": "task.issue.fixture.agent-workflow.reasoner",
            "bundle_path": "bundles/malformed.yaml",
            "complete_task": False,
        },
    )
    return AgentWorkflowEvalSuite(
        cases=[
            AgentWorkflowEvalCase(
                id="case.agent.cli-workflow",
                kind=AgentWorkflowEvalKind.CLI_AGENT_WORKFLOW,
                command=[
                    "context",
                    "build",
                    "issue.fixture.agent-workflow",
                    "--public-only",
                    "--json",
                    "--repo-root",
                    str(repo_root),
                ],
                expect_exit_code=0,
                expect_json=True,
                required_artifacts=["claim.fixture.agent-public"],
                forbidden_substrings=[
                    "claim.fixture.agent-private",
                    "private-secret-eval",
                    "sk-private-eval-secret",
                ],
            ),
            AgentWorkflowEvalCase(
                id="case.agent.context-privacy",
                kind=AgentWorkflowEvalKind.CONTEXT_PRIVACY,
                command=[
                    "provider",
                    "preview-send",
                    "--issue",
                    "issue.fixture.agent-workflow",
                    "--provider",
                    "fake",
                    "--json",
                    "--repo-root",
                    str(repo_root),
                ],
                expect_exit_code=0,
                expect_json=True,
                required_artifacts=["claim.fixture.agent-public"],
                forbidden_substrings=[
                    "claim.fixture.agent-private",
                    "private-secret-eval",
                    "sk-private-eval-secret",
                ],
            ),
            AgentWorkflowEvalCase(
                id="case.agent.provider-fake",
                kind=AgentWorkflowEvalKind.PROVIDER_WORKER_FAKE,
                surface=AgentWorkflowEvalSurface.PROVIDER,
                command=[
                    "provider",
                    "fake-run",
                    "--input-json",
                    "{repo_root}/requests/fake-provider.json",
                    "--json",
                    "--repo-root",
                    str(repo_root),
                ],
                expect_exit_code=0,
                expect_json=True,
                require_provider_redaction=True,
                forbidden_substrings=[
                    "sk-private-eval-secret",
                    "sk-provider-eval-secret",
                ],
            ),
            AgentWorkflowEvalCase(
                id="case.agent.optional-mcp-readonly",
                kind=AgentWorkflowEvalKind.OPTIONAL_MCP_READONLY,
                surface=AgentWorkflowEvalSurface.OPTIONAL_MCP,
                command=[
                    "mcp",
                    "list-tools",
                    "--repo-root",
                    str(repo_root),
                ],
                expect_exit_code=0,
                expect_json=False,
                forbidden_substrings=[
                    "shell",
                    "promote",
                    "accepted-write",
                ],
            ),
            AgentWorkflowEvalCase(
                id="case.agent.accepted-write-rejection",
                kind=AgentWorkflowEvalKind.GATE_REGRESSION,
                command=[
                    "draft",
                    "write-artifact",
                    "--input-json",
                    "{repo_root}/requests/accepted-write.json",
                    "--json",
                    "--repo-root",
                    str(repo_root),
                ],
                expect_exit_code=1,
                expect_json=True,
                expected_error_code="accepted_write_forbidden",
            ),
            AgentWorkflowEvalCase(
                id="case.agent.malformed-bundle-rejection",
                kind=AgentWorkflowEvalKind.BUNDLE_VALIDITY,
                command=[
                    "bundle",
                    "submit",
                    "--input-json",
                    str(malformed_bundle_request),
                    "--json",
                    "--repo-root",
                    str(repo_root),
                ],
                expect_exit_code=1,
                expect_json=True,
                expected_error_code="bundle_submit_failed",
            ),
        ]
    )


def test_agent_workflow_eval_scores_cli_provider_and_safety_cases(
    tmp_path: Path,
) -> None:
    _write_fixture_repo(tmp_path)

    report = run_agent_workflow_eval_suite(
        RepoContext(tmp_path),
        _workflow_suite(tmp_path),
    )

    assert report.passed is True
    assert report.metrics.command_success_rate == 1.0
    assert report.metrics.json_parse_success_rate == 1.0
    assert report.metrics.required_artifact_hit == 1.0
    assert report.metrics.private_leakage_count == 0
    assert report.metrics.accepted_write_rejection_count == 1
    assert report.metrics.malformed_bundle_rejection_count == 1
    assert report.metrics.provider_redaction_pass_count == 1
    assert report.surface_counts == {"cli": 4, "optional_mcp": 1, "provider": 1}
    assert {case.kind for case in report.cases} == {
        AgentWorkflowEvalKind.CLI_AGENT_WORKFLOW,
        AgentWorkflowEvalKind.PROVIDER_WORKER_FAKE,
        AgentWorkflowEvalKind.CONTEXT_PRIVACY,
        AgentWorkflowEvalKind.BUNDLE_VALIDITY,
        AgentWorkflowEvalKind.GATE_REGRESSION,
        AgentWorkflowEvalKind.OPTIONAL_MCP_READONLY,
    }
    assert {case.surface for case in report.cases} == {
        AgentWorkflowEvalSurface.CLI,
        AgentWorkflowEvalSurface.PROVIDER,
        AgentWorkflowEvalSurface.OPTIONAL_MCP,
    }
    assert not (tmp_path / "kb" / "accepted").exists()
    report_json = json.loads(report.to_json())
    assert report_json["metrics"]["command_success_rate"] == 1.0
    assert report_json["surface_counts"] == {
        "cli": 4,
        "optional_mcp": 1,
        "provider": 1,
    }


def test_default_agent_workflow_eval_suite_lists_required_cases() -> None:
    suite = load_agent_workflow_eval_suite(ROOT / DEFAULT_AGENT_WORKFLOW_EVAL_CASES)
    cases_by_id = {case.id: case for case in suite.cases}

    assert set(cases_by_id) == {
        "case.agent.cli-agent-workflow",
        "case.agent.provider-worker-fake",
        "case.agent.context-privacy",
        "case.agent.bundle-validity",
        "case.agent.gate-regression",
        "case.agent.optional-mcp-readonly",
    }
    assert {case.kind for case in suite.cases} == {
        AgentWorkflowEvalKind.CLI_AGENT_WORKFLOW,
        AgentWorkflowEvalKind.PROVIDER_WORKER_FAKE,
        AgentWorkflowEvalKind.CONTEXT_PRIVACY,
        AgentWorkflowEvalKind.BUNDLE_VALIDITY,
        AgentWorkflowEvalKind.GATE_REGRESSION,
        AgentWorkflowEvalKind.OPTIONAL_MCP_READONLY,
    }
    assert {case.surface for case in suite.cases} == {
        AgentWorkflowEvalSurface.CLI,
        AgentWorkflowEvalSurface.PROVIDER,
        AgentWorkflowEvalSurface.OPTIONAL_MCP,
    }
