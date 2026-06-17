"""Workflow CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console

from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.engine import (
    WorkflowError,
    assess_readiness,
    load_workflow,
    run_workflow,
    start_workflow,
    step_workflow,
)

console = Console()
workflow_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    short_help="Reviewable research workflow engine.",
)


def _emit_json(payload: dict) -> None:
    console.print_json(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def _error_payload(exc: Exception) -> dict:
    if isinstance(exc, WorkflowError):
        return {
            "ok": False,
            "error": {
                "code": exc.code,
                "message": str(exc),
                "remediation": exc.remediation,
                "details": exc.details,
            },
        }
    return {
        "ok": False,
        "error": {
            "code": "WORKFLOW_ERROR",
            "message": str(exc),
            "remediation": "Inspect workflow input and runtime files.",
            "details": {},
        },
    }


def _exit_with_error(exc: Exception, *, json_output: bool) -> NoReturn:
    if json_output:
        _emit_json(_error_payload(exc))
    else:
        console.print(f"Workflow error: {exc}")
    raise typer.Exit(1)


@workflow_app.command("start")
def wf_start(
    issue: Annotated[str, typer.Option("--issue")],
    query: Annotated[str, typer.Option("--query")] = "",
    workflow_id: Annotated[str | None, typer.Option("--workflow-id")] = None,
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Start and persist one reviewable workflow record."""
    try:
        result = start_workflow(
            RepoContext(repo_root),
            issue_id=issue,
            query=query,
            workflow_id=workflow_id,
        )
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
    else:
        console.print(
            f"Workflow {result.workflow.workflow_id} started (issue: {issue})"
        )
        console.print(f"- path: {result.relative_path.as_posix()}")


@workflow_app.command("show")
def wf_show(
    workflow_id: Annotated[str, typer.Argument()],
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Show one persisted reviewable workflow record."""
    try:
        workflow = load_workflow(RepoContext(repo_root), workflow_id)
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(workflow.to_dict())
    else:
        console.print(f"Workflow: {workflow.workflow_id}")
        console.print(f"- issue: {workflow.issue_id}")
        console.print(f"- status: {workflow.status.value}")
        console.print(f"- steps: {len(workflow.steps)}")


@workflow_app.command("step")
def wf_step(
    workflow_id: Annotated[str, typer.Argument()],
    action: Annotated[str | None, typer.Option("--action")] = None,
    execute_local_action: Annotated[
        bool,
        typer.Option(
            "--execute-local-action",
            help="Execute the selected action through the whitelisted registry.",
        ),
    ] = False,
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Append one deterministic workflow step."""
    try:
        result = step_workflow(
            RepoContext(repo_root),
            workflow_id,
            action_id=action,
            execute_local_action=execute_local_action,
        )
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Step {result.step.action}: {result.step.status}")
    console.print(f"- event_written: {str(result.event_written).lower()}")


@workflow_app.command("run")
def wf_run(
    workflow_id: Annotated[str, typer.Argument()],
    max_steps: Annotated[int, typer.Option("--max-steps")] = 1,
    execute_local_actions: Annotated[
        bool,
        typer.Option(
            "--execute-local-actions",
            help="Execute only whitelisted local actions from the action registry.",
        ),
    ] = False,
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Run a bounded sequence of deterministic workflow steps."""
    try:
        result = run_workflow(
            RepoContext(repo_root),
            workflow_id,
            max_steps=max_steps,
            execute_local_actions=execute_local_actions,
        )
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Workflow run: {result.workflow.workflow_id}")
    console.print(f"- steps_executed: {result.steps_executed}")
    console.print(
        f"- execute_local_actions: {str(result.execute_local_actions).lower()}"
    )


@workflow_app.command("readiness")
def wf_readiness(
    workflow_id: Annotated[str, typer.Argument()],
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Assess one persisted workflow's draft-proposal readiness."""
    try:
        report = assess_readiness(load_workflow(RepoContext(repo_root), workflow_id))
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(report.to_dict())
        return
    console.print(f"Readiness for {workflow_id}: {report.classification.value}")
