from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.agent.orchestrator_planner import (
    OrchestratorPlannerError,
    plan_for_issue,
)
from cosheaf.agent.task import WorkerType
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _issue_data(issue_id: str = "issue.fixture.planner") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Plan a local orchestrator workflow",
        "status": "open",
        "created_at": "2026-06-07T00:00:00Z",
        "updated_at": "2026-06-07T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Create an auditable local-only plan from issue metadata.",
        "related_artifacts": ["claim.fixture.planner"],
        "tags": ["orchestrator", "planner"],
    }


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.planner",
        "type": "claim",
        "title": "Planner fixture claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-07T00:00:00Z",
        "updated_at": "2026-06-07T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["planner"],
        "statement": "A fixture claim used only as planner input metadata.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review pending."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _write_repo(repo_root: Path) -> None:
    _write_yaml(repo_root, "issues/open/planner.yaml", _issue_data())
    _write_yaml(repo_root, "kb/draft/claims/planner.yaml", _artifact_data())


def test_plan_for_issue_is_deterministic_and_auditable(tmp_path: Path) -> None:
    _write_repo(tmp_path)
    context = RepoContext(tmp_path)

    first = plan_for_issue(context, "issue.fixture.planner")
    second = plan_for_issue(context, "issue.fixture.planner")

    assert first.to_dict() == second.to_dict()
    assert first.plan_id == "plan.issue.fixture.planner"
    assert first.issue_id == "issue.fixture.planner"
    assert "Plan a local orchestrator workflow" in first.objective
    assert [node.node_id for node in first.task_dag.nodes] == [
        "node.issue.fixture.planner.librarian-retrieval",
        "node.issue.fixture.planner.reasoner-draft",
        "node.issue.fixture.planner.verifier-check",
        "node.issue.fixture.planner.review-request",
    ]
    assert [node.worker_type for node in first.task_dag.nodes] == [
        WorkerType.ORCHESTRATOR,
        WorkerType.REASONER,
        WorkerType.VERIFIER,
        WorkerType.ORCHESTRATOR,
    ]
    assert first.task_dag.nodes[0].input_artifacts == ["claim.fixture.planner"]
    assert first.task_dag.nodes[1].depends_on == [
        "node.issue.fixture.planner.librarian-retrieval"
    ]
    assert first.task_dag.nodes[2].depends_on == [
        "node.issue.fixture.planner.reasoner-draft"
    ]
    assert first.task_dag.nodes[3].depends_on == [
        "node.issue.fixture.planner.verifier-check"
    ]


def test_plan_for_issue_references_context_pack_paths_without_writing(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    plan = plan_for_issue(RepoContext(tmp_path), "issue.fixture.planner")

    assert not (tmp_path / "context" / "TASKS").exists()
    assert plan.task_dag.nodes[0].expected_outputs == [
        "context/TASKS/issue.fixture.planner/CONTEXT.md",
        "context/TASKS/issue.fixture.planner/RETRIEVAL_AUDIT.json",
    ]
    for node in plan.task_dag.nodes:
        for output in node.expected_outputs:
            assert "kb/accepted/" not in output
            assert "kb/public/accepted/" not in output
            assert "kb/private/accepted/" not in output


def test_plan_for_issue_missing_issue_fails_cleanly(tmp_path: Path) -> None:
    with pytest.raises(
        OrchestratorPlannerError,
        match="issue not found: issue.fixture.missing",
    ):
        plan_for_issue(RepoContext(tmp_path), "issue.fixture.missing")


def test_orchestrator_plan_cli_emits_json(tmp_path: Path) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "orchestrator",
            "plan",
            "--issue",
            "issue.fixture.planner",
            "--json",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["plan_id"] == "plan.issue.fixture.planner"
    assert payload["issue_id"] == "issue.fixture.planner"
    assert [node["node_id"] for node in payload["task_dag"]["nodes"]] == [
        "node.issue.fixture.planner.librarian-retrieval",
        "node.issue.fixture.planner.reasoner-draft",
        "node.issue.fixture.planner.verifier-check",
        "node.issue.fixture.planner.review-request",
    ]


def test_orchestrator_plan_cli_missing_issue_exits_nonzero(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "orchestrator",
            "plan",
            "--issue",
            "issue.fixture.missing",
            "--json",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "issue not found: issue.fixture.missing" in result.output
    assert "Traceback" not in result.output
