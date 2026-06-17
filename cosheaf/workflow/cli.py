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
from cosheaf.workflow.handoff import (
    WORKFLOW_HANDOFF_AUTHORITY_NOTICE,
    build_workflow_handoff,
    export_workflow_handoff,
    load_workflow_handoff,
    scan_workflow_handoff,
)
from cosheaf.workflow.proposal import write_draft_proposal

console = Console()
workflow_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    short_help="Reviewable research workflow engine.",
)
handoff_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    short_help="Build and scan workflow review handoffs.",
)
workflow_app.add_typer(handoff_app, name="handoff")


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


@workflow_app.command("draft-proposal")
def wf_draft_proposal(
    workflow_id: Annotated[str, typer.Argument()],
    out: Annotated[Path | None, typer.Option("--out")] = None,
    private_root: Annotated[Path | None, typer.Option("--private-root")] = None,
    artifact_id: Annotated[str | None, typer.Option("--artifact-id")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", is_flag=True)] = False,
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Build or write a review-only draft proposal from workflow output."""
    try:
        result = write_draft_proposal(
            RepoContext(repo_root),
            workflow_id,
            out=out,
            private_root=private_root,
            artifact_id=artifact_id,
            dry_run=dry_run,
        )
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    mode = "dry-run" if result.dry_run else "written"
    console.print(f"Draft proposal {mode}: {workflow_id}")
    if result.target_path:
        console.print(f"- target: {result.target_path}")
    console.print("- accepted_write: false")


@handoff_app.command("build")
def wf_handoff_build(
    workflow_id: Annotated[str, typer.Argument()],
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Build a runtime review handoff packet from workflow output."""
    try:
        result = build_workflow_handoff(RepoContext(repo_root), workflow_id)
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Workflow handoff built: {result.handoff.handoff_id}")
    console.print(f"- workflow: {result.handoff.workflow_id}")
    console.print(f"- path: {result.relative_path.as_posix()}")
    console.print(f"- authority: {WORKFLOW_HANDOFF_AUTHORITY_NOTICE}")


@handoff_app.command("show")
def wf_handoff_show(
    handoff_id: Annotated[str, typer.Argument()],
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Show one runtime workflow handoff packet."""
    try:
        result = load_workflow_handoff(RepoContext(repo_root), handoff_id)
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Workflow handoff: {result.handoff.handoff_id}")
    console.print(f"- workflow: {result.handoff.workflow_id}")
    console.print(f"- path: {result.relative_path.as_posix()}")
    console.print(f"- authority: {WORKFLOW_HANDOFF_AUTHORITY_NOTICE}")


@handoff_app.command("scan")
def wf_handoff_scan(
    handoff_id: Annotated[str, typer.Argument()],
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Scan a workflow handoff packet and runtime inputs for blockers."""
    try:
        result = scan_workflow_handoff(RepoContext(repo_root), handoff_id)
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        if result.handoff_blocked:
            raise typer.Exit(1)
        return
    console.print(f"Workflow handoff scan: {result.handoff_id}")
    console.print(f"- findings: {result.finding_count}")
    console.print(f"- blockers: {result.blocking_finding_count}")
    console.print(f"- report: {result.report_path}")
    console.print(f"- authority: {WORKFLOW_HANDOFF_AUTHORITY_NOTICE}")
    if result.handoff_blocked:
        raise typer.Exit(1)


@handoff_app.command("export")
def wf_handoff_export(
    handoff_id: Annotated[str, typer.Argument()],
    dry_run: Annotated[bool, typer.Option("--dry-run", is_flag=True)] = False,
    repo_root: Annotated[Path, typer.Option("--repo-root")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False,
) -> None:
    """Export one workflow handoff as explicit review-context YAML."""
    try:
        result = export_workflow_handoff(
            RepoContext(repo_root),
            handoff_id,
            dry_run=dry_run,
        )
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    action = "dry-run" if result.dry_run else "written"
    console.print(f"Workflow handoff export {action}: {result.handoff_id}")
    console.print(f"- target: {result.target_path}")
    console.print(f"- authority: {WORKFLOW_HANDOFF_AUTHORITY_NOTICE}")
