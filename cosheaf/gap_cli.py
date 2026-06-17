"""Typer CLI for workflow proof-obligation gap reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, NoReturn

import typer
from rich.console import Console

from cosheaf.services.models import ErrorResult
from cosheaf.storage.repo import RepoContext
from cosheaf.workflow.crosscheck import build_gap_report, export_gap_report
from cosheaf.workflow.engine import WorkflowError

gap_app = typer.Typer(
    add_completion=False,
    help="Workflow proof/source/formalization gap commands.",
    no_args_is_help=True,
)


@gap_app.command("list")
def gap_list(
    workflow_id: str = typer.Argument(..., help="Workflow ID to inspect."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """List review-guidance gaps for one workflow."""
    try:
        report = build_gap_report(RepoContext(repo_root), workflow_id)
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(report.to_dict())
        return
    console = Console(width=120, markup=False)
    console.print(f"Workflow gaps: {report.workflow_id}")
    for gap in report.gaps:
        console.print(f"- {gap.kind.value}: {gap.description}")
    console.print("- gaps_are_defects: false")


@gap_app.command("export")
def gap_export(
    workflow_id: str = typer.Argument(..., help="Workflow ID to inspect."),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Repository-local JSON output path under reviews/workflow/.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON.",
    ),
) -> None:
    """Export review-guidance gaps for one workflow."""
    try:
        result = export_gap_report(RepoContext(repo_root), workflow_id, out)
    except Exception as exc:
        _exit_with_error(exc, json_output=json_output)
    if json_output:
        _emit_json(result.to_dict())
        return
    Console(width=120, markup=False).print(
        f"Workflow gaps exported: {result.target_path}"
    )


def _emit_json(payload: dict[str, Any] | list[Any]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=True, indent=2))


def _exit_with_error(exc: Exception, *, json_output: bool) -> NoReturn:
    if isinstance(exc, WorkflowError):
        error = ErrorResult(
            code=exc.code,
            message=str(exc),
            remediation=exc.remediation,
            blocking=True,
            details=exc.details,
        )
    else:
        error = ErrorResult(
            code="workflow_gap_error",
            message=str(exc),
            remediation="Inspect workflow runtime and gap export input.",
            blocking=True,
        )
    if json_output:
        typer.echo(error.to_json(), nl=False)
    else:
        Console(width=120, markup=False).print(
            f"{error.code}: {error.message}\n{error.remediation}"
        )
    raise typer.Exit(1)


__all__ = ["gap_app"]
