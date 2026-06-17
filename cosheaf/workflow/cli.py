"""Workflow CLI commands."""
import json
from pathlib import Path
from typing import Annotated
import typer
from rich.console import Console
from cosheaf.workflow.engine import (
    start_workflow, append_step, assess_readiness, WorkflowStep, WorkflowStatus, WORKFLOW_AUTHORITY_NOTICE,
)
console = Console()
workflow_app = typer.Typer(no_args_is_help=True, add_completion=False, short_help="Reviewable research workflow engine.")

@workflow_app.command("start")
def wf_start(issue: Annotated[str, typer.Option("--issue")], query: Annotated[str, typer.Option("--query")] = "", json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    rec = start_workflow(issue, query)
    if json_output:
        console.print_json(json.dumps(rec.model_dump(mode="json"), default=str))
    else:
        console.print(f"Workflow {rec.workflow_id} started (issue: {issue})")

@workflow_app.command("step")
def wf_step(workflow_id: Annotated[str, typer.Argument()], action: Annotated[str, typer.Option("--action")] = "memory.search", status: Annotated[str, typer.Option("--status")] = "success", json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    step = WorkflowStep(step_number=0, action=action, status=status, warnings=[])
    console.print(f"Step {action}: {status} (ephemeral, not persisted)")

@workflow_app.command("readiness")
def wf_readiness(workflow_id: Annotated[str, typer.Argument()], json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    console.print(f"Readiness for {workflow_id}: not yet assessable from persisted state")
