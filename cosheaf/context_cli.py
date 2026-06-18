"""Context-pack CLI commands backed by the app facade."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from cosheaf.agent.context_pack import ContextPackError
from cosheaf.app import open_app
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import repo_relative_posix
from cosheaf.memory import MemoryRootScope, RetrievalRole
from cosheaf.services.models import AgentAccessModel, ContextBuildResult, ErrorResult
from cosheaf.storage.repo import RepoContext

context_app = typer.Typer(
    add_completion=False,
    help="Context pack commands.",
    no_args_is_help=True,
)


@context_app.command("build")
def context_build(
    issue_id: str = typer.Argument(..., help="Issue ID to build context for."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    role: RetrievalRole = typer.Option(
        RetrievalRole.ORCHESTRATOR,
        "--role",
        help="Retrieval role used for context-pack budgets.",
    ),
    max_cards: int = typer.Option(
        20,
        "--max-cards",
        min=1,
        help="Maximum artifact cards to include before issue-local filtering.",
    ),
    max_full_artifacts: int = typer.Option(
        0,
        "--max-full-artifacts",
        min=0,
        help="Explicit full artifact pull budget; defaults to cards only.",
    ),
    public_only: bool = typer.Option(
        False,
        "--public-only",
        help="Exclude private cards and private artifact IDs from audit output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Build a bounded deterministic context pack for an issue."""
    console = Console(width=120, markup=False)
    app = open_app(repo_root)
    try:
        result = app.build_context(
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )
    except ContextPackError as exc:
        if json_output:
            emit_error(
                ErrorResult(
                    code="context_build_failed",
                    message=str(exc),
                    remediation="Check the issue ID and repository records.",
                    blocking=True,
                    related_artifact=valid_related_artifact(issue_id),
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"Context pack failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        emit_model(
            context_build_to_result(
                app.context,
                result,
                public_only=public_only,
            )
        )
        return

    console.print(f"Context pack built: {result.task_dir}")
    for path in result.files:
        console.print(f"- {path}")


@context_app.command("show")
def context_show(
    issue_id: str = typer.Argument(..., help="Issue ID to show context for."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    role: RetrievalRole = typer.Option(
        RetrievalRole.ORCHESTRATOR,
        "--role",
        help="Retrieval role used for context-pack budgets.",
    ),
    max_cards: int = typer.Option(
        20,
        "--max-cards",
        min=1,
        help="Maximum artifact cards to include before issue-local filtering.",
    ),
    max_full_artifacts: int = typer.Option(
        0,
        "--max-full-artifacts",
        min=0,
        help="Explicit full artifact pull budget; defaults to cards only.",
    ),
    public_only: bool = typer.Option(
        False,
        "--public-only",
        help="Exclude private cards and private artifact IDs from audit output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Build and print the main context document for an issue."""
    console = Console(width=120, markup=False)
    app = open_app(repo_root)
    try:
        rendered = app.show_context(
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )
    except ContextPackError as exc:
        if json_output:
            emit_error(
                ErrorResult(
                    code="context_show_failed",
                    message=str(exc),
                    remediation="Check the issue ID and repository records.",
                    blocking=True,
                    related_artifact=valid_related_artifact(issue_id),
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"Context pack failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        task_dir = app.context.repo_root / "context" / "TASKS" / issue_id
        files = [
            repo_relative_posix(app.context.repo_root, task_dir / filename)
            for filename in ("CONTEXT.md",)
        ]
        emit_json(
            {
                "schema_version": 1,
                "issue_id": issue_id,
                "task_dir": repo_relative_posix(app.context.repo_root, task_dir),
                "files": files,
                "public_only": public_only,
                "private_context_included": context_private_included(task_dir),
                "content": rendered,
            }
        )
        return

    typer.echo(rendered, nl=False)


def emit_json(payload: dict[str, Any] | list[Any]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=True, indent=2))


def emit_model(model: AgentAccessModel) -> None:
    typer.echo(model.to_json(), nl=False)


def emit_error(error: ErrorResult) -> None:
    emit_model(error)


def context_build_to_result(
    context: RepoContext,
    result: Any,
    *,
    public_only: bool,
) -> ContextBuildResult:
    payload_counts = context_payload_counts(result.task_dir)
    return ContextBuildResult(
        issue_id=result.issue_id,
        task_dir=repo_relative_posix(context.repo_root, result.task_dir),
        files=[repo_relative_posix(context.repo_root, path) for path in result.files],
        public_only=public_only,
        private_context_included=context_private_included(result.task_dir),
        card_count=payload_counts["card_count"],
        full_artifact_count=payload_counts["full_artifact_count"],
        content_mode=payload_counts["content_mode"],
    )


def context_payload_counts(task_dir: Path) -> dict[str, Any]:
    audit_path = task_dir / "RETRIEVAL_AUDIT.json"
    try:
        payload = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "card_count": 0,
            "full_artifact_count": 0,
            "content_mode": "cards_only",
        }

    context_payload = payload.get("context_payload")
    if isinstance(context_payload, dict):
        card_count = context_payload.get("card_count", 0)
        full_artifact_count = context_payload.get("full_artifact_count", 0)
        content_mode = context_payload.get("content_mode", "cards_only")
        if isinstance(card_count, int) and isinstance(full_artifact_count, int):
            if content_mode in {"cards_only", "cards_with_full_artifacts"}:
                return {
                    "card_count": card_count,
                    "full_artifact_count": full_artifact_count,
                    "content_mode": content_mode,
                }

    cards = payload.get("retrieval", {}).get("cards", [])
    pulls = payload.get("full_artifact_pulls", [])
    card_count = len(cards) if isinstance(cards, list) else 0
    full_artifact_count = len(pulls) if isinstance(pulls, list) else 0
    return {
        "card_count": card_count,
        "full_artifact_count": full_artifact_count,
        "content_mode": "cards_with_full_artifacts"
        if full_artifact_count
        else "cards_only",
    }


def context_private_included(task_dir: Path) -> bool:
    audit_path = task_dir / "RETRIEVAL_AUDIT.json"
    try:
        payload = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    cards = payload.get("retrieval", {}).get("cards", [])
    if any(card.get("root_scope") == MemoryRootScope.PRIVATE.value for card in cards):
        return True
    pulls = payload.get("full_artifact_pulls", [])
    return any(
        pull.get("root_scope") == MemoryRootScope.PRIVATE.value for pull in pulls
    )


def valid_related_artifact(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return validate_artifact_id(value.strip())
    except ValueError:
        return None


__all__ = [
    "context_app",
]
