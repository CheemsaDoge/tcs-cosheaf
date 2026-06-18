"""CLI for dry-run forge planning previews."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cosheaf.forge.models import ForgePreviewResult
from cosheaf.forge.service import ForgePreviewError, ForgeService
from cosheaf.services.models import ErrorResult
from cosheaf.storage.repo import RepoContext

forge_app = typer.Typer(
    add_completion=False,
    help="Dry-run forge planning commands.",
    no_args_is_help=True,
)
forge_issue_app = typer.Typer(
    add_completion=False,
    help="Dry-run GitHub issue planning commands.",
    no_args_is_help=True,
)
forge_pr_app = typer.Typer(
    add_completion=False,
    help="Dry-run GitHub pull request planning commands.",
    no_args_is_help=True,
)

forge_app.add_typer(forge_issue_app, name="issue")
forge_app.add_typer(forge_pr_app, name="pr")


@forge_app.command("status")
def forge_status(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Show dry-run forge status without token lookup or git mutation."""
    _emit_preview_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).status(),
        json_output=json_output,
    )


@forge_issue_app.command("preview")
def forge_issue_preview(
    source_path: Path = typer.Option(
        ...,
        "--from",
        help="Repository-local issue YAML path.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Preview GitHub issue creation without creating a GitHub issue."""
    _emit_preview_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).issue_preview(source_path),
        json_output=json_output,
    )


@forge_pr_app.command("preview")
def forge_pr_preview(
    base: str = typer.Option(
        ...,
        "--base",
        help="Base branch for the dry-run PR plan.",
    ),
    head: str = typer.Option(
        ...,
        "--head",
        help="Head branch for the dry-run PR plan.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Preview GitHub PR creation without git or GitHub writes."""
    _emit_preview_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).pr_preview(
            base=base,
            head=head,
        ),
        json_output=json_output,
    )


def _emit_preview_or_exit(
    run: Callable[[], ForgePreviewResult],
    *,
    json_output: bool,
) -> None:
    console = Console(width=120, markup=False)
    try:
        result = run()
    except ForgePreviewError as exc:
        error = ErrorResult(
            code="forge_preview_failed",
            message=str(exc),
            remediation="Fix the forge preview inputs and retry.",
            blocking=True,
        )
        if json_output:
            typer.echo(error.to_json(), nl=False)
        else:
            console.print(f"Forge preview failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(result.to_json(), nl=False)
        return
    console.print(f"Forge preview: {result.kind}")
    console.print(f"- dry_run_only: {str(result.dry_run_only).lower()}")
    console.print(
        f"- network_calls_performed: {str(result.network_calls_performed).lower()}"
    )
    console.print(f"- git_writes_performed: {str(result.git_writes_performed).lower()}")
    console.print(
        f"- github_writes_performed: {str(result.github_writes_performed).lower()}"
    )
    console.print(f"- authority: {result.authority_warning}")


__all__ = ["forge_app"]
