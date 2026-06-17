"""Librarian CLI commands."""
import json
from pathlib import Path
from typing import Annotated
import typer
from rich.console import Console
from cosheaf.librarian.retrieval import rank as librarian_rank, LIBRARIAN_AUTHORITY_NOTICE
console = Console()
librarian_app = typer.Typer(no_args_is_help=True, add_completion=False, short_help="Deterministic retrieval policy engine.")

@librarian_app.command("rank")
def rank_cmd(query: Annotated[str, typer.Option("--query", help="Search query")] = "", issue: Annotated[str, typer.Option("--issue", help="Issue ID")] = "", json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    """Rank artifacts by retrieval policy."""
    # Use a minimal in-process artifact list from the existing validate surface
    try:
        result = librarian_rank([], query=query, issue_id=issue)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)
    if json_output:
        console.print_json(json.dumps(result.model_dump(mode="json"), default=str))
        return
    console.print(f"[bold]Librarian rank[/bold] (query: {query!r}) - {len(result.candidates)} hot candidates")
    for c in result.candidates:
        console.print(f"  [cyan]{c.artifact_id}[/cyan] score={c.score:.3f} temp={c.temperature}")

@librarian_app.command("explain")
def explain_cmd(query_id: Annotated[str, typer.Argument()], json_output: Annotated[bool, typer.Option("--json", is_flag=True)] = False) -> None:
    console.print(f"Trace for {query_id}: not yet persisted.")
