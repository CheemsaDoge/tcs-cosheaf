"""Orchestrator FSM CLI commands."""
import json
from pathlib import Path
from typing import Annotated
import typer
from rich.console import Console
from cosheaf.orchestrator_fsm.fsm import create_orchestrator, transition_state, next_action, FSMState, FSM_AUTHORITY_NOTICE
console = Console()
fsm_app = typer.Typer(no_args_is_help=True, add_completion=False, short_help="Durable orchestrator FSM for issue workflows.")

@fsm_app.command("start")
def fsm_start(issue: Annotated[str, typer.Option("--issue", help="Issue ID")], json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    orch = create_orchestrator(issue)
    if json_output:
        console.print_json(json.dumps(orch.model_dump(mode="json"), default=str))
    else:
        console.print(f"Orchestrator {orch.orch_id} created (state: {orch.state.value})")

@fsm_app.command("transition")
def fsm_transition(orch_id: Annotated[str, typer.Argument()], event: Annotated[str, typer.Option("--event")], json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    console.print(f"FSM transition not yet persisted for {orch_id} -> {event}")

@fsm_app.command("next")
def fsm_next(orch_id: Annotated[str, typer.Argument()], json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    console.print(f"Next action not yet persisted for {orch_id}")
