"""CLI for dry-run forge planning previews."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cosheaf.forge.models import ForgeActionResult, ForgePreviewResult
from cosheaf.forge.service import ForgeActionError, ForgePreviewError, ForgeService
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
forge_branch_app = typer.Typer(
    add_completion=False,
    help="Local git branch commands.",
    no_args_is_help=True,
)

forge_app.add_typer(forge_issue_app, name="issue")
forge_app.add_typer(forge_pr_app, name="pr")
forge_app.add_typer(forge_branch_app, name="branch")


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


@forge_issue_app.command("create")
def forge_issue_create(
    source_path: Path = typer.Option(
        ...,
        "--from",
        help="Repository-local issue YAML path.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm the GitHub issue write.",
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
    """Create a GitHub issue from a local issue file with confirmation."""
    _emit_action_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).github_issue_create(
            source_path,
            confirm=confirm,
        ),
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


@forge_pr_app.command("create")
def forge_pr_create(
    base: str = typer.Option(
        ...,
        "--base",
        help="Base branch for the GitHub PR.",
    ),
    head: str = typer.Option(
        ...,
        "--head",
        help="Head branch for the GitHub PR.",
    ),
    draft: bool = typer.Option(
        False,
        "--draft",
        help="Create the GitHub PR as a draft.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm the GitHub PR write.",
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
    """Create a GitHub PR with explicit confirmation."""
    _emit_action_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).github_pr_create(
            base=base,
            head=head,
            draft=draft,
            confirm=confirm,
        ),
        json_output=json_output,
    )


@forge_branch_app.command("create")
def forge_branch_create(
    branch: str = typer.Argument(..., help="Branch name to create and switch to."),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm the local git branch write.",
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
    """Create and switch to a local branch with explicit confirmation."""
    _emit_action_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).create_branch(
            branch,
            confirm=confirm,
        ),
        json_output=json_output,
    )


@forge_app.command("commit")
def forge_commit(
    message: str = typer.Option(..., "--message", help="Commit message."),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Confirm the local git commit.",
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
    """Run validation/gate and create one local git commit."""
    _emit_action_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).commit(
            message=message,
            confirm=confirm,
        ),
        json_output=json_output,
    )


@forge_app.command("sync")
def forge_sync(
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
    """Show read-only forge sync status."""
    _emit_action_or_exit(
        lambda: ForgeService(RepoContext(repo_root)).sync(),
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


def _emit_action_or_exit(
    run: Callable[[], ForgeActionResult],
    *,
    json_output: bool,
) -> None:
    console = Console(width=120, markup=False)
    try:
        result = run()
    except ForgeActionError as exc:
        error = ErrorResult(
            code=exc.code,
            message=str(exc),
            remediation="Fix the forge action inputs, local state, or GitHub state.",
            blocking=True,
        )
        if json_output:
            typer.echo(error.to_json(), nl=False)
        else:
            console.print(f"Forge action failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(result.to_json(), nl=False)
        return
    payload = result.to_dict()
    console.print(f"Forge action: {payload.get('action', 'unknown')}")
    console.print(f"- action_performed: {str(payload.get('action_performed')).lower()}")
    console.print(
        f"- git_writes_performed: {str(payload.get('git_writes_performed')).lower()}"
    )
    console.print(
        f"- network_calls_performed: "
        f"{str(payload.get('network_calls_performed')).lower()}"
    )
    console.print(
        f"- github_writes_performed: "
        f"{str(payload.get('github_writes_performed')).lower()}"
    )


__all__ = ["forge_app"]
