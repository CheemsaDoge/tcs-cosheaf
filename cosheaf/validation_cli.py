"""Validation and gate CLI commands backed by the app facade."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError
from rich.console import Console

from cosheaf.app import open_app
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import repo_relative_posix
from cosheaf.gates.gatekeeper import GatekeeperRunResult, ValidationReport
from cosheaf.services.models import ErrorResult, GateRunResult, ValidateResult
from cosheaf.storage.repo import RepoContext

gate_app = typer.Typer(
    add_completion=False,
    help="Gatekeeper commands.",
)


def register_validation_commands(root_app: typer.Typer) -> None:
    """Register top-level validation commands on the root CLI app."""
    root_app.command()(validate)


def validate(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to validate.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show tracebacks for unexpected validation errors.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Validate repository YAML records and implemented invariants."""
    app = open_app(repo_root)
    run_validation(
        report_factory=app.validate_repository,
        success_message="Validation passed",
        failure_message="Validation failed",
        debug=debug,
        json_output=json_output,
    )


@gate_app.callback(invoke_without_command=True)
def gate(
    ctx: typer.Context,
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to gate.",
    ),
    persist_review: bool = typer.Option(
        False,
        "--persist-review",
        help="Also persist reports under reviews/gatekeeper/.",
    ),
    pr_checklist: Path | None = typer.Option(
        None,
        "--pr-checklist",
        help="Local PR checklist markdown file to validate with G8.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Run the gatekeeper when no gate subcommand is provided."""
    if ctx.invoked_subcommand is None:
        run_gatekeeper_cli(
            repo_root=repo_root,
            persist_review=persist_review,
            pr_checklist=pr_checklist,
            json_output=json_output,
        )


@gate_app.command("run")
def gate_run(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to gate.",
    ),
    persist_review: bool = typer.Option(
        False,
        "--persist-review",
        help="Also persist reports under reviews/gatekeeper/.",
    ),
    pr_checklist: Path | None = typer.Option(
        None,
        "--pr-checklist",
        help="Local PR checklist markdown file to validate with G8.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Run gatekeeper checks and write JSON/Markdown reports."""
    run_gatekeeper_cli(
        repo_root=repo_root,
        persist_review=persist_review,
        pr_checklist=pr_checklist,
        json_output=json_output,
    )


def run_validation(
    *,
    report_factory: Callable[[], ValidationReport],
    success_message: str,
    failure_message: str,
    debug: bool,
    json_output: bool = False,
) -> None:
    console = Console(width=120)
    try:
        report = report_factory()
    except Exception:
        if json_output and not debug:
            emit_error(
                ErrorResult(
                    code="validation_unexpected_error",
                    message="Unexpected validation error.",
                    remediation="Rerun without --json and with --debug for traceback.",
                    blocking=True,
                )
            )
            raise typer.Exit(code=2) from None
        if debug:
            console.print_exception()
        else:
            console.print(
                "[bold red]Unexpected validation error.[/bold red] "
                "Rerun with --debug for traceback."
            )
        raise typer.Exit(code=2) from None

    if json_output:
        emit_model(validation_report_to_result(report))
        if not report.ok:
            raise typer.Exit(code=1)
        return

    print_validation_report(
        console=console,
        report=report,
        success_message=success_message,
        failure_message=failure_message,
    )
    if not report.ok:
        raise typer.Exit(code=1)


def run_gatekeeper_cli(
    repo_root: Path,
    persist_review: bool,
    pr_checklist: Path | None,
    json_output: bool = False,
) -> None:
    console = Console(width=120)
    app = open_app(repo_root)
    result = app.run_gate(
        persist_review=persist_review,
        pr_checklist_path=pr_checklist,
    )
    if json_output:
        emit_model(gate_run_to_result(app.context, result))
        if result.report.blocking_issues:
            raise typer.Exit(code=1)
        return

    print_gatekeeper_result(console, result)
    if result.report.blocking_issues:
        raise typer.Exit(code=1)


def emit_model(model: ErrorResult | GateRunResult | ValidateResult) -> None:
    typer.echo(model.to_json(), nl=False)


def emit_error(error: ErrorResult) -> None:
    emit_model(error)


def validation_report_to_result(report: ValidationReport) -> ValidateResult:
    return ValidateResult(
        ok=report.ok,
        checked_count=report.checked_count,
        failures=[validation_failure_to_error(failure) for failure in report.failures],
    )


def validation_failure_to_error(failure: Any) -> ErrorResult:
    return ErrorResult(
        code="validation_failed",
        message=f"{failure.gate}: {failure.message}",
        remediation="Fix the referenced YAML record and rerun validation.",
        blocking=True,
        related_path=valid_related_path(failure.source_path),
        related_artifact=valid_related_artifact(failure.artifact_id),
        details={"gate": failure.gate},
    )


def gate_run_to_result(
    context: RepoContext,
    result: GatekeeperRunResult,
) -> GateRunResult:
    return GateRunResult(
        verdict=result.report.verdict,
        report_json_path=repo_relative_posix(context.repo_root, result.json_path),
        report_markdown_path=repo_relative_posix(
            context.repo_root,
            result.markdown_path,
        ),
        blocking_issues=[
            gate_issue_to_error(issue) for issue in result.report.blocking_issues
        ],
        nonblocking_issues=[
            gate_issue_to_error(issue) for issue in result.report.nonblocking_issues
        ],
    )


def gate_issue_to_error(issue: Any) -> ErrorResult:
    return ErrorResult(
        code="gate_issue",
        message=f"{issue.gate_id} {issue.gate_name}: {issue.message}",
        remediation="Fix the gate issue and rerun `cosheaf gate run`.",
        blocking=issue.severity == "blocking",
        related_path=valid_related_path(issue.source_path),
        related_artifact=valid_related_artifact(issue.artifact_id),
        details={
            "gate_id": issue.gate_id,
            "gate_name": issue.gate_name,
            "severity": issue.severity,
        },
    )


def valid_related_path(value: str | None) -> str | None:
    if not value:
        return None
    try:
        ErrorResult(
            code="path_probe",
            message="Path probe.",
            remediation="Path probe.",
            blocking=False,
            related_path=value,
        )
    except ValidationError:
        return None
    return value


def valid_related_artifact(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return validate_artifact_id(value.strip())
    except ValueError:
        return None


def print_validation_report(
    *,
    console: Console,
    report: ValidationReport,
    success_message: str,
    failure_message: str,
) -> None:
    if report.ok:
        console.print(
            f"[bold green]{success_message}[/bold green]: "
            f"checked {report.checked_count} YAML record(s)."
        )
        return

    console.print(
        f"[bold red]{failure_message}[/bold red]: "
        f"{len(report.failures)} failure(s) across "
        f"{report.checked_count} loaded YAML record(s)."
    )
    for failure in report.failures:
        source_path = failure.source_path or "-"
        artifact_id = failure.artifact_id or "-"
        console.print(
            f"- {failure.gate} | {source_path} | {artifact_id} | {failure.message}"
        )


def print_gatekeeper_result(
    console: Console,
    result: GatekeeperRunResult,
) -> None:
    report = result.report
    console.print(f"Gate verdict: {report.verdict}")
    console.print(f"JSON report: {result.json_path}")
    console.print(f"Markdown report: {result.markdown_path}")
    for issue in report.blocking_issues:
        source_path = issue.source_path or "-"
        artifact_id = issue.artifact_id or "-"
        console.print(
            f"- {issue.gate_id} {issue.gate_name} | "
            f"{source_path} | {artifact_id} | {issue.message}"
        )


__all__ = [
    "gate_app",
    "register_validation_commands",
    "run_validation",
]
