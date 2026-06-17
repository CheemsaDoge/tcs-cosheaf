"""Tests for persistent reviewable workflow runtime storage and CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from cosheaf.actions.registry import (
    LocalActionPolicy,
    LocalActionRegistry,
    LocalActionResult,
    LocalActionRunRequest,
    LocalActionSpec,
    LocalActionStatus,
)
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WORKFLOW_AUTHORITY_NOTICE,
    ReadinessClass,
    WorkflowStep,
    assess_readiness,
    load_workflow,
    start_workflow,
    step_workflow,
    workflow_events_path,
    workflow_path,
)

runner = CliRunner()


def _json(output: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(output))


def test_start_persists_workflow_record_and_events(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)

    result = start_workflow(
        context,
        issue_id="issue.workflow.fixture",
        query="find a small graph lemma",
        workflow_id="workflow.fixture",
    )

    assert result.workflow.workflow_id == "workflow.fixture"
    assert result.relative_path == Path(
        ".cosheaf/workflows/workflow.fixture/workflow.json"
    )
    assert (tmp_path / workflow_path("workflow.fixture")).exists()
    assert (tmp_path / workflow_events_path("workflow.fixture")).exists()

    loaded = load_workflow(context, "workflow.fixture")
    assert loaded.issue_id == "issue.workflow.fixture"
    assert loaded.query == "find a small graph lemma"
    assert loaded.authority_notice == WORKFLOW_AUTHORITY_NOTICE

    events = (tmp_path / workflow_events_path("workflow.fixture")).read_text(
        encoding="utf-8"
    )
    assert "workflow_started" in events


def test_step_persists_workflow_state_and_event(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(
        context,
        issue_id="issue.workflow.fixture",
        workflow_id="workflow.fixture",
    )

    result = step_workflow(
        context,
        "workflow.fixture",
        action_id="workspace.info",
        execute_local_action=False,
    )

    assert result.workflow.steps[0].action == "workspace.info"
    assert result.workflow.steps[0].status == "planned"
    loaded = load_workflow(context, "workflow.fixture")
    assert len(loaded.steps) == 1

    events = (tmp_path / workflow_events_path("workflow.fixture")).read_text(
        encoding="utf-8"
    )
    assert "workflow_step" in events


def test_planned_only_workflow_readiness_is_inconclusive(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(
        context,
        issue_id="issue.workflow.fixture",
        workflow_id="workflow.fixture",
    )
    result = step_workflow(
        context,
        "workflow.fixture",
        action_id="workspace.info",
        execute_local_action=False,
    )

    readiness = assess_readiness(result.workflow)

    assert readiness.classification == ReadinessClass.INCONCLUSIVE
    assert "planned" in " ".join(readiness.blocker_details)


def test_local_action_step_rejects_non_whitelisted_action(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(
        context,
        issue_id="issue.workflow.fixture",
        workflow_id="workflow.fixture",
    )

    result = step_workflow(
        context,
        "workflow.fixture",
        action_id="not.registered",
        execute_local_action=True,
    )

    step = result.workflow.steps[-1]
    assert step.status == "blocked"
    assert step.output_refs["error_code"] == "UNKNOWN_ACTION"
    assert result.workflow.readiness == ReadinessClass.BLOCKED_EVIDENCE


def test_local_action_step_blocks_accepted_write_action(tmp_path: Path) -> None:
    context = RepoContext(tmp_path)
    start_workflow(
        context,
        issue_id="issue.workflow.fixture",
        workflow_id="workflow.fixture",
    )
    registry = LocalActionRegistry()

    def _blocked_action(
        request: LocalActionRunRequest,
        policy: LocalActionPolicy,
        repo_root: Path,
    ) -> LocalActionResult:
        raise AssertionError("accepted-write action must be blocked before execution")

    registry.register(
        LocalActionSpec(
            action_id="accepted.write",
            description="unsafe accepted write fixture",
            writes_accepted=True,
        ),
        _blocked_action,
    )

    result = step_workflow(
        context,
        "workflow.fixture",
        action_id="accepted.write",
        execute_local_action=True,
        registry=registry,
    )

    step = result.workflow.steps[-1]
    assert step.status == "blocked"
    assert step.output_refs["action_status"] == LocalActionStatus.BLOCKED.value
    assert step.output_refs["error_code"] == "ACCEPTED_WRITE_BLOCKED"
    assert result.workflow.readiness == ReadinessClass.BLOCKED_SCANNER


def test_workflow_cli_start_show_step_run_and_readiness(tmp_path: Path) -> None:
    start = runner.invoke(
        app,
        [
            "workflow",
            "start",
            "--issue",
            "issue.workflow.fixture",
            "--query",
            "demo query",
            "--workflow-id",
            "workflow.fixture",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert start.exit_code == 0, start.output
    start_payload = _json(start.output)
    assert start_payload["workflow"]["workflow_id"] == "workflow.fixture"

    show = runner.invoke(
        app,
        [
            "workflow",
            "show",
            "workflow.fixture",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    assert _json(show.output)["workflow_id"] == "workflow.fixture"

    step = runner.invoke(
        app,
        [
            "workflow",
            "step",
            "workflow.fixture",
            "--action",
            "workspace.info",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert step.exit_code == 0, step.output
    assert _json(step.output)["workflow"]["steps"][0]["status"] == "planned"

    run = runner.invoke(
        app,
        [
            "workflow",
            "run",
            "workflow.fixture",
            "--max-steps",
            "1",
            "--execute-local-actions",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert run.exit_code == 0, run.output
    run_payload = _json(run.output)
    assert run_payload["steps_requested"] == 1
    assert run_payload["steps_executed"] == 1
    assert len(run_payload["workflow"]["steps"]) == 2
    assert run_payload["workflow"]["steps"][-1]["status"] in {
        "success",
        "failed",
        "error",
        "blocked",
    }

    readiness = runner.invoke(
        app,
        [
            "workflow",
            "readiness",
            "workflow.fixture",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert readiness.exit_code == 0, readiness.output
    readiness_payload = _json(readiness.output)
    assert readiness_payload["workflow_id"] == "workflow.fixture"
    assert "classification" in readiness_payload


def test_workflow_step_rejects_accepted_output_reference() -> None:
    try:
        WorkflowStep(
            step_number=1,
            action="unsafe",
            status="success",
            output_refs={"target": "kb/accepted/claims/claim.bad.yaml"},
        )
    except ValueError as exc:
        assert "accepted KB paths" in str(exc)
    else:
        raise AssertionError("accepted output references must be rejected")
