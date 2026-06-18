"""CLI commands for repository-local issue records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError
from rich.console import Console

from cosheaf.issues.service import (
    ISSUE_AUTHORITY_NOTICE,
    LocalIssueError,
    LocalIssueService,
)
from cosheaf.services.models import ErrorResult
from cosheaf.storage.loader import LoadError
from cosheaf.storage.repo import RepoContext

issue_app = typer.Typer(
    add_completion=False,
    help="Repository-local issue commands.",
    no_args_is_help=True,
)


@issue_app.command("create")
def issue_create(
    title: str = typer.Option(..., "--title", help="Issue title."),
    issue_id: str = typer.Option(..., "--id", help="Repository-local issue ID."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for local issue storage.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Create an open local issue YAML record without GitHub calls."""
    console = Console(width=120, markup=False)
    try:
        result = LocalIssueService(RepoContext(repo_root)).create(
            issue_id=issue_id,
            title=title,
        )
    except (LocalIssueError, LoadError, ValidationError, ValueError) as exc:
        _exit_with_issue_error(exc, json_output=json_output, console=console)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Issue created: {result.relative_path.as_posix()}")
    console.print(f"- id: {result.issue.id}")
    console.print(f"- authority: {ISSUE_AUTHORITY_NOTICE}")


@issue_app.command("show")
def issue_show(
    issue_id: str = typer.Argument(..., help="Repository-local issue ID."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for local issue storage.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Show one local issue record."""
    console = Console(width=120, markup=False)
    try:
        result = LocalIssueService(RepoContext(repo_root)).show(issue_id)
    except (LocalIssueError, LoadError, ValidationError, ValueError) as exc:
        _exit_with_issue_error(exc, json_output=json_output, console=console)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Issue: {result.issue.id}")
    console.print(f"- title: {result.issue.title}")
    console.print(f"- status: {result.issue.status}")
    console.print(f"- path: {result.relative_path.as_posix()}")
    console.print(f"- authority: {ISSUE_AUTHORITY_NOTICE}")


@issue_app.command("list")
def issue_list(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for local issue storage.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """List local issue records."""
    console = Console(width=120, markup=False)
    try:
        result = LocalIssueService(RepoContext(repo_root)).list()
    except (LoadError, ValidationError, ValueError) as exc:
        _exit_with_issue_error(exc, json_output=json_output, console=console)
    if json_output:
        _emit_json(result.to_dict())
        return
    if not result.issues:
        console.print("No local issues found.")
        return
    for issue, path in zip(result.issues, result.paths, strict=True):
        console.print(f"{issue.id} | {issue.status} | {path.as_posix()}")


@issue_app.command("close")
def issue_close(
    issue_id: str = typer.Argument(..., help="Repository-local issue ID."),
    reason: str = typer.Option(..., "--reason", help="Close reason."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for local issue storage.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Close a local issue without changing artifacts or promotion state."""
    console = Console(width=120, markup=False)
    try:
        result = LocalIssueService(RepoContext(repo_root)).close(
            issue_id,
            reason=reason,
        )
    except (LocalIssueError, LoadError, ValidationError, ValueError) as exc:
        _exit_with_issue_error(exc, json_output=json_output, console=console)
    if json_output:
        _emit_json(result.to_dict())
        return
    console.print(f"Issue closed: {result.issue.id}")
    console.print(f"- path: {result.relative_path.as_posix()}")
    console.print(f"- authority: {ISSUE_AUTHORITY_NOTICE}")


def _emit_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", nl=False)


def _exit_with_issue_error(
    exc: Exception,
    *,
    json_output: bool,
    console: Console,
) -> None:
    error = ErrorResult(
        code="issue_failed",
        message=str(exc),
        remediation="Fix the local issue record and rerun the issue command.",
        blocking=True,
    )
    if json_output:
        typer.echo(error.to_json(), nl=False)
    else:
        console.print(f"Issue command failed: {exc}")
    raise typer.Exit(code=1) from None


__all__ = ["issue_app"]
