"""Local action CLI commands for the deterministic action registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from cosheaf.actions.builtins import build_default_registry
from cosheaf.actions.registry import (
    LOCAL_ACTION_AUTHORITY_NOTICE,
    LocalActionPolicy,
    LocalActionRunRequest,
    LocalActionStatus,
)

console = Console()
action_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    short_help="Run deterministic local actions through the action registry.",
)


@action_app.command("list")
def action_list(
    json_output: Annotated[
        bool, typer.Option("--json", is_flag=True, help="Output JSON")
    ] = False,
) -> None:
    """List registered local actions."""
    registry = build_default_registry()
    specs = registry.list_actions()
    if json_output:
        data = [s.model_dump(mode="json") for s in specs]
        console.print_json(json.dumps(data, default=str))
        return

    console.print("[bold]Registered local actions:[/bold]")
    for s in specs:
        console.print(f"  [cyan]{s.action_id}[/cyan] - {s.description}")
    console.print()
    console.print(f"[dim]{LOCAL_ACTION_AUTHORITY_NOTICE}[/dim]")


@action_app.command("describe")
def action_describe(
    action_id: Annotated[str, typer.Argument(help="Action identifier")],
    json_output: Annotated[
        bool, typer.Option("--json", is_flag=True, help="Output JSON")
    ] = False,
) -> None:
    """Describe a specific local action."""
    registry = build_default_registry()
    spec = registry.get_spec(action_id)
    if spec is None:
        console.print(f"[red]Unknown action: {action_id!r}[/red]")
        raise typer.Exit(1)

    if json_output:
        console.print_json(json.dumps(spec.model_dump(mode="json"), default=str))
        return

    console.print(f"[bold]{spec.action_id}[/bold]")
    console.print(f"  {spec.description}")
    console.print(f"  Input refs: {', '.join(spec.allowed_input_refs) if spec.allowed_input_refs else 'none'}")
    console.print(f"  Max timeout: {spec.max_timeout_seconds}s")
    console.print(f"[dim]{spec.authority_notice}[/dim]")


@action_app.command("run")
def action_run(
    action_id: Annotated[str, typer.Argument(help="Action identifier")],
    input_json: Annotated[
        str | None, typer.Option("--input-json", help="Path to JSON input file")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", is_flag=True, help="Preview only, do not execute")
    ] = False,
    mode: Annotated[
        str, typer.Option("--mode", help="Policy mode: public_only or private_research")
    ] = "private_research",
) -> None:
    """Run a whitelisted local action."""
    registry = build_default_registry()

    input_refs: dict[str, str] = {}
    if input_json:
        try:
            input_refs = json.loads(Path(input_json).read_text(encoding="utf-8"))
        except Exception as exc:
            console.print(f"[red]Failed to read input JSON: {exc}[/red]")
            raise typer.Exit(1)

    request = LocalActionRunRequest(
        action_id=action_id,
        input_refs=input_refs,
        dry_run=dry_run,
    )
    policy = LocalActionPolicy(
        mode=mode,  # type: ignore[arg-type]
    )

    repo_root = Path.cwd()
    result = registry.run(request, policy, repo_root)

    json_str = json.dumps(result.model_dump(mode="json"), default=str)
    console.print_json(json_str)

    if result.status in (
        LocalActionStatus.ERROR,
        LocalActionStatus.FAILED,
        LocalActionStatus.BLOCKED,
    ):
        raise typer.Exit(1)
