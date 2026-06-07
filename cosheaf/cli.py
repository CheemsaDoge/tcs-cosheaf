from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console

from cosheaf import __version__
from cosheaf.agent.context_pack import (
    ContextPackError,
    build_context_pack,
    show_context_pack,
)
from cosheaf.agent.local_runner import (
    LocalWorkerRunConfig,
    LocalWorkerRunError,
    LocalWorkerRunner,
)
from cosheaf.agent.orchestrator_stub import OrchestratorStub, TaskHarnessError
from cosheaf.agent.task import WorkerType
from cosheaf.config.workspace import KbRootConfig, WorkspaceConfigError
from cosheaf.core.artifact import BaseArtifact, is_external_dependency_ref
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import lifecycle_artifact_path
from cosheaf.core.status import (
    ArtifactStatus,
    ArtifactType,
    expected_status_for_path,
    is_preaccepted_status,
)
from cosheaf.gates.gatekeeper import (
    GatekeeperRunResult,
    ValidationReport,
    run_gatekeeper,
    validate_artifact_file,
    validate_repository,
)
from cosheaf.gates.source_metadata_gate import missing_required_source_metadata
from cosheaf.graph.claim_graph import DependencyGraph, build_dependency_graph
from cosheaf.memory import (
    MEMORY_GRAPH_SIDECAR,
    ArtifactCardStatus,
    MemoryCardError,
    MemoryGraphError,
    MemorySearchError,
    build_artifact_cards,
    build_memory_graph,
    compute_global_pagerank,
    load_memory_graph_snapshot,
    search_artifact_cards,
)
from cosheaf.storage.index import rebuild_index
from cosheaf.storage.loader import LoadedRecord, LoadError, load_artifacts
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

app = typer.Typer(
    add_completion=False,
    help="TCS-Cosheaf research knowledge base harness.",
    no_args_is_help=True,
)
artifact_app = typer.Typer(
    add_completion=False,
    help="Artifact commands.",
    no_args_is_help=True,
)
index_app = typer.Typer(
    add_completion=False,
    help="Index commands.",
    no_args_is_help=True,
)
graph_app = typer.Typer(
    add_completion=False,
    help="Graph commands.",
    no_args_is_help=True,
)
gate_app = typer.Typer(
    add_completion=False,
    help="Gatekeeper commands.",
)
context_app = typer.Typer(
    add_completion=False,
    help="Context pack commands.",
    no_args_is_help=True,
)
task_app = typer.Typer(
    add_completion=False,
    help="Agent task commands.",
    no_args_is_help=True,
)
workspace_app = typer.Typer(
    add_completion=False,
    help="Workspace configuration commands.",
    no_args_is_help=True,
)
memory_app = typer.Typer(
    add_completion=False,
    help="Deterministic memory/card commands.",
    no_args_is_help=True,
)
memory_graph_app = typer.Typer(
    add_completion=False,
    help="Deterministic memory graph commands.",
    no_args_is_help=True,
)
app.add_typer(artifact_app, name="artifact")
app.add_typer(index_app, name="index")
app.add_typer(graph_app, name="graph")
app.add_typer(gate_app, name="gate")
app.add_typer(context_app, name="context")
app.add_typer(task_app, name="task")
app.add_typer(workspace_app, name="workspace")
app.add_typer(memory_app, name="memory")
memory_app.add_typer(memory_graph_app, name="graph")


@app.command()
def version() -> None:
    """Print the TCS-Cosheaf version."""
    Console().print(f"tcs-cosheaf {__version__}")


@workspace_app.command("info")
def workspace_info(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Show workspace configuration and KB roots."""
    console = Console(width=120, markup=False)
    try:
        context = RepoContext(repo_root)
    except WorkspaceConfigError as exc:
        console.print(f"Workspace config failed: {exc}")
        raise typer.Exit(code=1) from None

    config = context.workspace_config
    mode = "configured" if config.configured else "legacy"
    console.print(f"Workspace: {config.name}")
    console.print(f"- repo_root: {context.repo_root}")
    console.print(f"- mode: {mode}")
    console.print("KB roots:")
    for root in config.ordered_kb:
        readonly = str(root.readonly).lower()
        console.print(
            f"- {root.name} | {root.path} | "
            f"readonly={readonly} | priority={root.priority}"
        )


@app.command()
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
) -> None:
    """Validate repository YAML records and implemented invariants."""
    context = RepoContext(repo_root)
    _run_validation(
        report_factory=lambda: validate_repository(context),
        success_message="Validation passed",
        failure_message="Validation failed",
        debug=debug,
    )


@artifact_app.command("validate")
def artifact_validate(
    path: Path = typer.Argument(..., help="Repository-local artifact YAML path."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used to resolve the artifact path.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show tracebacks for unexpected validation errors.",
    ),
) -> None:
    """Validate one artifact YAML file with file-local checks."""
    context = RepoContext(repo_root)
    _run_validation(
        report_factory=lambda: validate_artifact_file(context, path),
        success_message="Artifact validation passed",
        failure_message="Artifact validation failed",
        debug=debug,
    )


@artifact_app.command("create")
def artifact_create(
    artifact_id: str = typer.Option(..., "--id", help="Globally unique artifact ID."),
    artifact_type: ArtifactType = typer.Option(..., "--type", help="Artifact type."),
    title: str = typer.Option(..., "--title", help="Artifact title."),
    domain: list[str] = typer.Option(
        ...,
        "--domain",
        help="Artifact domain. Repeat for multiple domains.",
    ),
    status: ArtifactStatus = typer.Option(
        ...,
        "--status",
        help="Initial artifact lifecycle status.",
    ),
    statement: str = typer.Option(..., "--statement", help="Artifact statement."),
    author: list[str] | None = typer.Option(
        None,
        "--author",
        help="Artifact author. Repeat for multiple authors.",
    ),
    tag: list[str] | None = typer.Option(
        None,
        "--tag",
        help="Artifact tag. Repeat for multiple tags.",
    ),
    depends_on: list[str] | None = typer.Option(
        None,
        "--depends-on",
        help="Artifact dependency ID. Repeat for multiple dependencies.",
    ),
    supersedes: list[str] | None = typer.Option(
        None,
        "--supersedes",
        help="Superseded artifact ID. Repeat for multiple IDs.",
    ),
    created_at: str | None = typer.Option(
        None,
        "--created-at",
        help="UTC timestamp for created_at/updated_at; defaults to current UTC.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for artifact creation.",
    ),
) -> None:
    """Create a deterministic artifact YAML record in the lifecycle tree."""
    console = Console(width=120, markup=False)
    try:
        artifact, relative_path = _create_artifact_record(
            context=RepoContext(repo_root),
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            title=title,
            domain=domain,
            status=status,
            statement=statement,
            authors=author or [],
            tags=tag or [],
            depends_on=depends_on or [],
            supersedes=supersedes or [],
            created_at=created_at,
        )
    except ArtifactLifecycleError as exc:
        console.print(f"Artifact create failed: {exc}")
        raise typer.Exit(code=1) from None

    console.print(f"Artifact created: {relative_path.as_posix()}")
    console.print(f"- id: {artifact.id}")
    console.print(f"- status: {artifact.status.value}")


@artifact_app.command("move-status")
def artifact_move_status(
    artifact_id: str = typer.Argument(..., help="Artifact ID to move."),
    new_status: ArtifactStatus = typer.Argument(..., help="New lifecycle status."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for status movement.",
    ),
) -> None:
    """Move an artifact through a safe lifecycle status transition."""
    console = Console(width=120, markup=False)
    try:
        old_status, old_path, new_path = _move_artifact_status(
            context=RepoContext(repo_root),
            artifact_id=artifact_id,
            new_status=new_status,
        )
    except ArtifactLifecycleError as exc:
        console.print(f"Artifact move-status failed: {exc}")
        raise typer.Exit(code=1) from None

    console.print(
        f"Artifact moved: {artifact_id} | {old_status.value} -> {new_status.value}"
    )
    console.print(f"- from: {old_path.as_posix()}")
    console.print(f"- to: {new_path.as_posix()}")


@artifact_app.command("promote")
def artifact_promote(
    artifact_id: str = typer.Argument(..., help="Artifact ID to promote."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for accepted promotion.",
    ),
) -> None:
    """Promote an eligible lifecycle artifact into accepted knowledge."""
    console = Console(width=120, markup=False)
    try:
        old_status, old_path, new_path = _promote_artifact(
            context=RepoContext(repo_root),
            artifact_id=artifact_id,
        )
    except ArtifactLifecycleError as exc:
        console.print(f"Artifact promote failed: {exc}")
        raise typer.Exit(code=1) from None

    console.print(
        f"Artifact promoted: {artifact_id} | {old_status.value} -> accepted"
    )
    console.print(f"- from: {old_path.as_posix()}")
    console.print(f"- to: {new_path.as_posix()}")


@index_app.command("rebuild")
def index_rebuild(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to index.",
    ),
) -> None:
    """Rebuild deterministic SQLite and manifest index outputs."""
    console = Console(width=120)
    try:
        result = rebuild_index(RepoContext(repo_root))
    except Exception as exc:
        console.print(f"[bold red]Index rebuild failed[/bold red]: {exc}")
        raise typer.Exit(code=1) from None

    console.print(
        "[bold green]Index rebuilt[/bold green]: "
        f"{result.sqlite_path} and {result.manifest_path} "
        f"({result.artifact_count} artifact(s), {result.edge_count} edge(s))."
    )


@graph_app.command("show")
def graph_show(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Show the directed artifact dependency graph."""
    console = Console(width=120)
    try:
        records = tuple(load_artifacts(RepoContext(repo_root)))
        graph = build_dependency_graph(records)
    except Exception as exc:
        console.print(f"[bold red]Graph load failed[/bold red]: {exc}")
        raise typer.Exit(code=1) from None

    _print_dependency_graph(console, graph)


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
) -> None:
    """Run the gatekeeper when no gate subcommand is provided."""
    if ctx.invoked_subcommand is None:
        _run_gatekeeper_cli(
            repo_root=repo_root,
            persist_review=persist_review,
            pr_checklist=pr_checklist,
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
) -> None:
    """Run gatekeeper checks and write JSON/Markdown reports."""
    _run_gatekeeper_cli(
        repo_root=repo_root,
        persist_review=persist_review,
        pr_checklist=pr_checklist,
    )


@context_app.command("build")
def context_build(
    issue_id: str = typer.Argument(..., help="Issue ID to build context for."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Build a bounded deterministic context pack for an issue."""
    console = Console(width=120, markup=False)
    try:
        result = build_context_pack(RepoContext(repo_root), issue_id)
    except ContextPackError as exc:
        console.print(f"Context pack failed: {exc}")
        raise typer.Exit(code=1) from None

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
) -> None:
    """Build and print the main context document for an issue."""
    console = Console(width=120, markup=False)
    try:
        rendered = show_context_pack(RepoContext(repo_root), issue_id)
    except ContextPackError as exc:
        console.print(f"Context pack failed: {exc}")
        raise typer.Exit(code=1) from None

    typer.echo(rendered, nl=False)


@memory_app.command("cards")
def memory_cards(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    issue: str | None = typer.Option(
        None,
        "--issue",
        help="Optional issue ID whose direct related artifacts should be shown.",
    ),
    status: ArtifactCardStatus | None = typer.Option(
        None,
        "--status",
        help="Optional artifact-card status filter.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text lines.",
    ),
) -> None:
    """Build compact artifact cards from existing repository metadata."""
    console = Console(width=120, markup=False)
    try:
        cards = build_artifact_cards(
            RepoContext(repo_root),
            issue_id=issue,
            status=status,
        )
    except MemoryCardError as exc:
        console.print(f"Memory cards failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(
            json.dumps(
                [card.to_dict() for card in cards],
                ensure_ascii=True,
                indent=2,
            )
        )
        return

    if not cards:
        console.print("No memory cards.")
        return

    for card in cards:
        console.print(
            f"{card.id} | {card.title} | {card.status.value} | "
            f"{card.root_scope.value} | {card.path}"
        )


@memory_app.command("search")
def memory_search(
    query: str = typer.Argument(..., help="Search query."),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    issue: str | None = typer.Option(
        None,
        "--issue",
        help="Optional issue ID used as a Personalized PageRank seed.",
    ),
    seed_artifact: list[str] | None = typer.Option(
        None,
        "--seed-artifact",
        help="Explicit artifact ID to seed personalized ranking. Repeatable.",
    ),
    pin_artifact: list[str] | None = typer.Option(
        None,
        "--pin-artifact",
        help="Artifact ID to strongly pin into personalized ranking. Repeatable.",
    ),
    status: ArtifactCardStatus | None = typer.Option(
        None,
        "--status",
        help="Optional artifact-card status filter.",
    ),
    include_refuted: bool = typer.Option(
        False,
        "--include-refuted",
        help="Include refuted cards with an explicit score penalty.",
    ),
    include_obsolete: bool = typer.Option(
        False,
        "--include-obsolete",
        help="Include obsolete or superseded cards with an explicit score penalty.",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Print score component breakdowns in text output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON retrieval result instead of text lines.",
    ),
) -> None:
    """Search compact artifact cards with deterministic local scoring."""
    console = Console(width=120, markup=False)
    try:
        result = search_artifact_cards(
            RepoContext(repo_root),
            query=query,
            issue_id=issue,
            status=status,
            seed_artifacts=tuple(seed_artifact or ()),
            pinned_artifacts=tuple(pin_artifact or ()),
            include_refuted=include_refuted,
            include_obsolete=include_obsolete,
        )
    except MemorySearchError as exc:
        console.print(f"Memory search failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(result.to_json(), nl=False)
        return

    if not result.cards:
        console.print("No memory search results.")
        return

    for hit in result.cards:
        card = hit.card
        console.print(
            f"{card.id} | score={hit.score_breakdown.total:.6f} | "
            f"{card.title} | {card.status.value} | "
            f"{card.root_scope.value} | {card.path}"
        )
        if explain:
            breakdown = hit.score_breakdown
            console.print(
                "  breakdown: "
                f"retrieval_hybrid={breakdown.retrieval_hybrid:.6f} "
                f"personalized_pagerank={breakdown.personalized_pagerank:.6f} "
                f"global_pagerank={breakdown.global_pagerank:.6f} "
                f"quality_prior={breakdown.quality_prior:.6f} "
                f"freshness={breakdown.freshness:.6f} "
                f"penalty={breakdown.penalty:.6f}"
            )
            for reason in hit.why_relevant:
                console.print(f"  why: {reason}")


@memory_graph_app.command("build")
def memory_graph_build(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON summary instead of text lines.",
    ),
) -> None:
    """Build the rebuildable memory graph sidecar."""
    console = Console(width=120, markup=False)
    try:
        context = RepoContext(repo_root)
        snapshot = build_memory_graph(context, persist=True)
    except MemoryGraphError as exc:
        console.print(f"Memory graph build failed: {exc}")
        raise typer.Exit(code=1) from None

    sidecar = MEMORY_GRAPH_SIDECAR.as_posix()
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "schema_version": snapshot.schema_version,
                    "graph_fingerprint": snapshot.graph_fingerprint,
                    "node_count": snapshot.node_count,
                    "edge_count": snapshot.edge_count,
                    "sidecar_path": sidecar,
                    "warnings": snapshot.warnings,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return

    console.print(
        "Memory graph built: "
        f"{sidecar} ({snapshot.node_count} node(s), "
        f"{snapshot.edge_count} edge(s))."
    )
    console.print(f"- fingerprint: {snapshot.graph_fingerprint}")
    for warning in snapshot.warnings:
        console.print(f"- warning: {warning}")


@memory_graph_app.command("pagerank")
def memory_graph_pagerank(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON PageRank output instead of text lines.",
    ),
) -> None:
    """Compute global PageRank from an existing memory graph sidecar."""
    console = Console(width=120, markup=False)
    try:
        snapshot = load_memory_graph_snapshot(RepoContext(repo_root))
        result = compute_global_pagerank(snapshot)
    except MemoryGraphError as exc:
        console.print(f"Memory graph PageRank failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(result.to_json(), nl=False)
        return

    if not result.rows:
        console.print("No memory graph PageRank rows.")
        return

    for row in result.rows:
        console.print(
            f"{row.rank}. {row.node_id} | score={row.score:.12f} | "
            f"{row.kind} | {row.record_id}"
        )


@task_app.command("create")
def task_create(
    issue: str = typer.Option(..., "--issue", help="Issue ID for the task."),
    worker: WorkerType = typer.Option(
        ...,
        "--worker",
        help="Protocol worker type for the task.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Create an open local agent task without invoking a worker."""
    console = Console(width=120, markup=False)
    try:
        task = OrchestratorStub(RepoContext(repo_root)).create_task(
            issue_id=issue,
            worker_type=worker,
        )
    except TaskHarnessError as exc:
        console.print(f"Task create failed: {exc}")
        raise typer.Exit(code=1) from None

    console.print(f"Task created: {task.task_id}")
    console.print(f"- issue: {task.issue_id}")
    console.print(f"- worker: {task.worker_type.value}")
    console.print(f"- status: {task.status.value}")


@task_app.command("list")
def task_list(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """List local agent tasks."""
    console = Console(width=120, markup=False)
    try:
        tasks = OrchestratorStub(RepoContext(repo_root)).list_tasks()
    except TaskHarnessError as exc:
        console.print(f"Task list failed: {exc}")
        raise typer.Exit(code=1) from None

    if not tasks:
        console.print("No tasks.")
        return

    for task in tasks:
        console.print(
            f"{task.task_id} | {task.issue_id} | "
            f"{task.worker_type.value} | {task.status.value}"
        )


@task_app.command("complete")
def task_complete(
    task_id: str = typer.Argument(..., help="Task ID to mark complete."),
    bundle: Path = typer.Option(
        ...,
        "--bundle",
        help="Worker output bundle manifest path or containing directory.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Validate a worker output bundle and mark the task complete."""
    console = Console(width=120, markup=False)
    try:
        result = OrchestratorStub(RepoContext(repo_root)).complete_task(
            task_id=task_id,
            bundle_path=bundle,
        )
    except TaskHarnessError as exc:
        console.print(f"Task complete failed: {exc}")
        raise typer.Exit(code=1) from None

    console.print(f"Task completed: {result.task.task_id}")
    console.print(f"- bundle outputs: {len(result.bundle.outputs)}")
    console.print("- accepted knowledge merge: not performed")


@task_app.command("run")
def task_run(
    task_id: str = typer.Argument(..., help="Task ID to run a local command for."),
    command: list[str] = typer.Argument(
        ...,
        help="Explicit command argv. Separate it from options with '--'.",
    ),
    timeout_seconds: int = typer.Option(
        60,
        "--timeout-seconds",
        help="Maximum command runtime in seconds.",
    ),
    cwd: Path | None = typer.Option(
        None,
        "--cwd",
        help="Optional repository-local working directory.",
    ),
    bundle: Path | None = typer.Option(
        None,
        "--bundle",
        help="Validate a worker output bundle after a successful command.",
    ),
    complete_with_bundle: Path | None = typer.Option(
        None,
        "--complete-with-bundle",
        help=(
            "Validate a worker output bundle after a successful command and "
            "delegate task completion to the orchestrator stub."
        ),
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Run an explicit local command for an existing task."""
    console = Console(width=120, markup=False)
    if bundle is not None and complete_with_bundle is not None:
        console.print("Task run failed: use either --bundle or --complete-with-bundle")
        raise typer.Exit(code=1)

    bundle_path = complete_with_bundle or bundle
    try:
        context = RepoContext(repo_root)
        result = LocalWorkerRunner(context).run_task(
            task_id,
            LocalWorkerRunConfig(
                command=command,
                timeout_seconds=timeout_seconds,
                cwd=cwd,
                bundle_path=bundle_path,
            ),
        )
    except LocalWorkerRunError as exc:
        console.print(f"Task run failed: {exc}")
        raise typer.Exit(code=1) from None

    task_completed = False
    if result.status == "completed" and complete_with_bundle is not None:
        try:
            OrchestratorStub(context).complete_task(
                task_id=task_id,
                bundle_path=complete_with_bundle,
            )
        except TaskHarnessError as exc:
            console.print(f"Task complete failed: {exc}")
            raise typer.Exit(code=1) from None
        task_completed = True

    console.print(f"status: {result.status}")
    console.print(f"returncode: {result.returncode}")
    console.print(f"run_directory: {result.run_dir}")
    if result.bundle_valid is not None:
        console.print(f"bundle_valid: {str(result.bundle_valid).lower()}")
    if complete_with_bundle is not None:
        console.print(f"task_completed: {str(task_completed).lower()}")

    if result.status != "completed":
        raise typer.Exit(code=1)


def _run_validation(
    *,
    report_factory: Callable[[], ValidationReport],
    success_message: str,
    failure_message: str,
    debug: bool,
) -> None:
    console = Console(width=120)
    try:
        report = report_factory()
    except Exception:
        if debug:
            console.print_exception()
        else:
            console.print(
                "[bold red]Unexpected validation error.[/bold red] "
                "Rerun with --debug for traceback."
            )
        raise typer.Exit(code=2) from None

    _print_validation_report(
        console=console,
        report=report,
        success_message=success_message,
        failure_message=failure_message,
    )
    if not report.ok:
        raise typer.Exit(code=1)


def _print_validation_report(
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


def _run_gatekeeper_cli(
    repo_root: Path,
    persist_review: bool,
    pr_checklist: Path | None,
) -> None:
    console = Console(width=120)
    result = run_gatekeeper(
        RepoContext(repo_root),
        persist_review=persist_review,
        pr_checklist_path=pr_checklist,
    )
    _print_gatekeeper_result(console, result)
    if result.report.blocking_issues:
        raise typer.Exit(code=1)


def _print_gatekeeper_result(
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


def _print_dependency_graph(console: Console, graph: DependencyGraph) -> None:
    console.print(
        f"[bold]Dependency graph[/bold]: "
        f"{len(graph.nodes)} node(s), {len(graph.edges)} edge(s)."
    )
    if graph.edges:
        for edge in graph.edges:
            console.print(f"- {edge.source_id} -> {edge.target_id}")
    else:
        console.print("- no dependency edges")

    for issue in graph.missing_dependencies:
        console.print(
            f"[red]- missing dependency[/red] | "
            f"{issue.source_id} -> {issue.target_id} | {issue.source_path}"
        )
    for cycle in graph.cycles:
        console.print(f"[red]- cycle[/red] | {' -> '.join(cycle)}")
    for issue in graph.accepted_draft_violations:
        console.print(
            f"[red]- accepted->draft[/red] | "
            f"{issue.source_id} -> {issue.target_id} | {issue.source_path}"
        )


class ArtifactLifecycleError(ValueError):
    """Raised for expected artifact lifecycle CLI failures."""


PROMOTION_REVIEW_STATES = frozenset({"human_reviewed", "accepted"})
BLOCKING_VERIFIER_STATUSES = frozenset({"fail", "error"})


def _create_artifact_record(
    *,
    context: RepoContext,
    artifact_id: str,
    artifact_type: ArtifactType,
    title: str,
    domain: list[str],
    status: ArtifactStatus,
    statement: str,
    authors: list[str],
    tags: list[str],
    depends_on: list[str],
    supersedes: list[str],
    created_at: str | None,
) -> tuple[BaseArtifact, Path]:
    if not domain:
        raise ArtifactLifecycleError("at least one --domain value is required")
    if status is ArtifactStatus.ACCEPTED:
        raise ArtifactLifecycleError(
            "accepted artifacts must be promoted through a dedicated gate/review "
            "workflow"
        )

    try:
        validate_artifact_id(artifact_id)
    except ValueError as exc:
        raise ArtifactLifecycleError(str(exc)) from exc

    timestamp = _parse_artifact_timestamp(created_at)
    try:
        relative_path = _workspace_lifecycle_artifact_path(
            context=context,
            artifact_type=artifact_type,
            status=status,
            artifact_id=artifact_id,
        )
    except ValueError as exc:
        raise ArtifactLifecycleError(str(exc)) from exc

    _ensure_artifact_id_is_available(context, artifact_id)
    target_path = context.resolve(relative_path)
    if target_path.exists():
        raise ArtifactLifecycleError(
            f"artifact path already exists: {relative_path.as_posix()}"
        )

    try:
        artifact = BaseArtifact.model_validate(
            {
                "id": artifact_id,
                "type": artifact_type,
                "title": title,
                "domain": domain,
                "status": status,
                "created_at": timestamp,
                "updated_at": timestamp,
                "authors": authors,
                "depends_on": depends_on,
                "supersedes": supersedes,
                "tags": tags,
                "statement": statement,
                "evidence": [],
                "review": {"state": "requested", "notes": "Created by CLI."},
                "risk": {"level": "low", "notes": ""},
            }
        )
    except ValidationError as exc:
        raise ArtifactLifecycleError(_format_pydantic_errors(exc)) from exc

    write_yaml_deterministic(target_path, artifact)
    report = validate_artifact_file(context, relative_path)
    if report.ok:
        return artifact, relative_path

    target_path.unlink(missing_ok=True)
    raise ArtifactLifecycleError(_format_report_failures(report))


def _move_artifact_status(
    *,
    context: RepoContext,
    artifact_id: str,
    new_status: ArtifactStatus,
) -> tuple[ArtifactStatus, Path, Path]:
    records = _load_records_for_lifecycle(context)
    loaded = _find_unique_base_artifact(records, artifact_id)
    artifact = loaded.record
    if not isinstance(artifact, BaseArtifact):
        raise AssertionError("unreachable non-artifact lifecycle record")

    _ensure_kb_lifecycle_record(loaded)
    _ensure_current_status_path_consistent(loaded)
    _ensure_loaded_record_is_writable(loaded)

    if new_status is ArtifactStatus.ACCEPTED:
        raise ArtifactLifecycleError(
            "accepted promotion requires a dedicated gate/review workflow; "
            "move-status refuses direct moves into kb/accepted"
        )

    old_status = artifact.status
    old_relative_path = loaded.source_path
    new_relative_path = _workspace_status_move_path(loaded, artifact, new_status)

    if old_status is new_status and old_relative_path == new_relative_path:
        return old_status, old_relative_path, new_relative_path

    _ensure_repository_valid_for_lifecycle_move(context)
    _write_status_move(
        context=context,
        artifact=artifact,
        source_relative_path=old_relative_path,
        target_relative_path=new_relative_path,
        new_status=new_status,
    )
    report = validate_artifact_file(context, new_relative_path)
    if not report.ok:
        raise ArtifactLifecycleError(_format_report_failures(report))
    return old_status, old_relative_path, new_relative_path


def _promote_artifact(
    *,
    context: RepoContext,
    artifact_id: str,
) -> tuple[ArtifactStatus, Path, Path]:
    validation_report = validate_repository(context)
    if not validation_report.ok:
        raise ArtifactLifecycleError(
            "repository validation failed before promotion: "
            f"{_format_report_failures(validation_report)}"
        )

    records = validation_report.records
    loaded = _find_unique_promotable_artifact(records, artifact_id)
    artifact = loaded.record
    if not isinstance(artifact, BaseArtifact):
        raise AssertionError("unreachable non-artifact promotion record")

    _ensure_kb_lifecycle_record(loaded)
    _ensure_current_status_path_consistent(loaded)
    _ensure_loaded_record_is_writable(loaded)
    _ensure_preaccepted_for_promotion(artifact)

    gatekeeper_result = run_gatekeeper(context)
    _ensure_gatekeeper_allows_promotion(gatekeeper_result, artifact_id)
    _ensure_artifact_reviewed_for_promotion(artifact)
    _ensure_promotion_dependencies_accepted(records, artifact)
    _ensure_source_metadata_for_public_promotion(context, loaded, artifact)

    old_status = artifact.status
    old_relative_path = loaded.source_path
    new_relative_path = _workspace_status_move_path(
        loaded,
        artifact,
        ArtifactStatus.ACCEPTED,
    )

    _write_accepted_promotion(
        context=context,
        artifact=artifact,
        source_relative_path=old_relative_path,
        target_relative_path=new_relative_path,
    )
    return old_status, old_relative_path, new_relative_path


def _find_unique_promotable_artifact(
    records: tuple[LoadedRecord, ...],
    artifact_id: str,
) -> LoadedRecord:
    matches = [record for record in records if record.id == artifact_id]
    if not matches:
        raise ArtifactLifecycleError(f"artifact not found: {artifact_id}")
    if len(matches) > 1:
        paths = ", ".join(sorted(record.source_path.as_posix() for record in matches))
        raise ArtifactLifecycleError(f"duplicate artifact id {artifact_id}: {paths}")

    loaded = matches[0]
    if not isinstance(loaded.record, BaseArtifact):
        raise ArtifactLifecycleError(
            f"record is not a promotable lifecycle artifact: {artifact_id}"
        )
    try:
        lifecycle_artifact_path(
            loaded.record.type,
            ArtifactStatus.ACCEPTED,
            loaded.record.id,
        )
    except ValueError as exc:
        raise ArtifactLifecycleError(
            f"record is not a promotable lifecycle artifact: {artifact_id}"
        ) from exc
    return loaded


def _ensure_preaccepted_for_promotion(artifact: BaseArtifact) -> None:
    if artifact.status is ArtifactStatus.ACCEPTED:
        raise ArtifactLifecycleError(f"artifact is already accepted: {artifact.id}")
    if not is_preaccepted_status(artifact.status):
        raise ArtifactLifecycleError(
            "only pre-accepted lifecycle artifacts may be promoted: "
            f"{artifact.id} has status {artifact.status.value}"
        )


def _ensure_gatekeeper_allows_promotion(
    result: GatekeeperRunResult,
    artifact_id: str,
) -> None:
    target_blockers = _target_verifier_blockers(result, artifact_id)
    if target_blockers:
        raise ArtifactLifecycleError(
            "target verifier result blocks promotion: "
            f"{'; '.join(target_blockers)}"
        )
    if result.report.blocking_issues:
        raise ArtifactLifecycleError(
            "gatekeeper blocking issues prevent promotion: "
            f"{_format_gatekeeper_blocking_issues(result)}"
        )


def _target_verifier_blockers(
    result: GatekeeperRunResult,
    artifact_id: str,
) -> list[str]:
    blockers: list[str] = []
    for gate in result.report.gates:
        if gate.gate_id != "G6":
            continue
        for detail in gate.details:
            if detail.get("artifact_id") != artifact_id:
                continue
            status = detail.get("status")
            if status not in BLOCKING_VERIFIER_STATUSES:
                continue
            verifier = str(detail.get("verifier", "verifier"))
            message = str(detail.get("message", "")).strip()
            rendered = f"{verifier} {status}"
            if message:
                rendered = f"{rendered}: {message}"
            blockers.append(rendered)
    if blockers:
        return blockers

    return [
        issue.message
        for issue in result.report.blocking_issues
        if issue.gate_id == "G6" and issue.artifact_id == artifact_id
    ]


def _format_gatekeeper_blocking_issues(result: GatekeeperRunResult) -> str:
    return "; ".join(
        f"{issue.gate_id} | {issue.source_path or '-'} | "
        f"{issue.artifact_id or '-'} | {issue.message}"
        for issue in result.report.blocking_issues
    )


def _ensure_artifact_reviewed_for_promotion(artifact: BaseArtifact) -> None:
    if artifact.review.state in PROMOTION_REVIEW_STATES:
        return
    raise ArtifactLifecycleError(
        "review.state must be human_reviewed or accepted before promotion: "
        f"{artifact.id} has {artifact.review.state}"
    )


def _ensure_promotion_dependencies_accepted(
    records: tuple[LoadedRecord, ...],
    artifact: BaseArtifact,
) -> None:
    artifacts_by_id = {
        record.id: record
        for record in records
        if isinstance(record.record, BaseArtifact)
    }
    for dependency_id in artifact.depends_on:
        if is_external_dependency_ref(dependency_id):
            continue
        dependency = artifacts_by_id.get(dependency_id)
        if dependency is None or not isinstance(dependency.record, BaseArtifact):
            raise ArtifactLifecycleError(f"dependency is missing: {dependency_id}")
        if dependency.record.status is ArtifactStatus.ACCEPTED:
            continue
        raise ArtifactLifecycleError(
            "dependency is not accepted: "
            f"{dependency_id} has status {dependency.record.status.value} "
            f"at {dependency.source_path.as_posix()}"
        )


def _ensure_source_metadata_for_public_promotion(
    context: RepoContext,
    loaded: LoadedRecord,
    artifact: BaseArtifact,
) -> None:
    if not context.workspace_config.policy.accepted_requires_source:
        return
    if loaded.kb_root_name != "public":
        return
    missing = missing_required_source_metadata(artifact)
    if not missing:
        return
    if missing == ("sources",):
        raise ArtifactLifecycleError(
            "accepted public artifact requires source metadata before promotion: "
            f"{artifact.id}"
        )
    raise ArtifactLifecycleError(
        "accepted public artifact has incomplete source metadata before promotion: "
        + ", ".join(missing)
    )


def _write_accepted_promotion(
    *,
    context: RepoContext,
    artifact: BaseArtifact,
    source_relative_path: Path,
    target_relative_path: Path,
) -> None:
    source_path = context.resolve(source_relative_path)
    target_path = context.resolve(target_relative_path)
    if target_path.exists() and source_path != target_path:
        raise ArtifactLifecycleError(
            f"target artifact path already exists: {target_relative_path.as_posix()}"
        )

    original_text = source_path.read_text(encoding="utf-8")
    updated = artifact.model_copy(
        update={
            "status": ArtifactStatus.ACCEPTED,
            "updated_at": datetime.now(UTC).replace(microsecond=0),
        }
    )
    write_yaml_deterministic(source_path, updated)
    if source_path != target_path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            source_path.rename(target_path)
        except OSError:
            source_path.write_text(original_text, encoding="utf-8", newline="\n")
            raise

    report = validate_artifact_file(context, target_relative_path)
    if report.ok:
        return

    _restore_failed_promotion(
        source_path=source_path,
        target_path=target_path,
        original_text=original_text,
    )
    raise ArtifactLifecycleError(_format_report_failures(report))


def _restore_failed_promotion(
    *,
    source_path: Path,
    target_path: Path,
    original_text: str,
) -> None:
    if source_path != target_path and target_path.exists():
        target_path.rename(source_path)
    source_path.write_text(original_text, encoding="utf-8", newline="\n")


def _write_status_move(
    *,
    context: RepoContext,
    artifact: BaseArtifact,
    source_relative_path: Path,
    target_relative_path: Path,
    new_status: ArtifactStatus,
) -> None:
    source_path = context.resolve(source_relative_path)
    target_path = context.resolve(target_relative_path)
    if target_path.exists() and source_path != target_path:
        raise ArtifactLifecycleError(
            f"target artifact path already exists: {target_relative_path.as_posix()}"
        )

    updated = artifact.model_copy(update={"status": new_status})
    original_text = source_path.read_text(encoding="utf-8")
    write_yaml_deterministic(source_path, updated)
    if source_path == target_path:
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        source_path.rename(target_path)
    except OSError:
        source_path.write_text(original_text, encoding="utf-8", newline="\n")
        raise


def _parse_artifact_timestamp(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    try:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ArtifactLifecycleError(
            f"invalid --created-at timestamp: {value}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ArtifactLifecycleError("--created-at must include timezone information")
    return parsed.astimezone(UTC).replace(microsecond=0)


def _ensure_artifact_id_is_available(context: RepoContext, artifact_id: str) -> None:
    records = _load_records_for_lifecycle(context)
    if any(record.id == artifact_id for record in records):
        raise ArtifactLifecycleError(f"artifact already exists: {artifact_id}")


def _load_records_for_lifecycle(context: RepoContext) -> tuple[LoadedRecord, ...]:
    try:
        return tuple(load_artifacts(context))
    except LoadError as exc:
        raise ArtifactLifecycleError(
            f"cannot load repository records: {exc}"
        ) from exc


def _find_unique_base_artifact(
    records: tuple[LoadedRecord, ...],
    artifact_id: str,
) -> LoadedRecord:
    matches = [record for record in records if record.id == artifact_id]
    if not matches:
        raise ArtifactLifecycleError(f"artifact not found: {artifact_id}")
    if len(matches) > 1:
        paths = ", ".join(sorted(record.source_path.as_posix() for record in matches))
        raise ArtifactLifecycleError(f"duplicate artifact id {artifact_id}: {paths}")

    loaded = matches[0]
    if not isinstance(loaded.record, BaseArtifact):
        raise ArtifactLifecycleError(f"record is not an artifact: {artifact_id}")
    return loaded


def _ensure_kb_lifecycle_record(loaded: LoadedRecord) -> None:
    if loaded.kb_relative_path is None:
        raise ArtifactLifecycleError(
            "lifecycle status moves are only supported for records under a KB root: "
            f"{loaded.source_path.as_posix()}"
        )


def _ensure_current_status_path_consistent(loaded: LoadedRecord) -> None:
    artifact = loaded.record
    if not isinstance(artifact, BaseArtifact):
        return
    allowed = expected_status_for_path(_status_path_for_loaded_record(loaded))
    if artifact.status in allowed:
        return
    expected = ", ".join(sorted(status.value for status in allowed))
    raise ArtifactLifecycleError(
        "status/path mismatch: "
        f"{loaded.source_path.as_posix()} has status {artifact.status.value}; "
        f"expected one of {expected}"
    )


def _ensure_loaded_record_is_writable(loaded: LoadedRecord) -> None:
    if not loaded.kb_root_readonly:
        return
    root_name = loaded.kb_root_name or "<unknown>"
    raise ArtifactLifecycleError(f"readonly KB root cannot be modified: {root_name}")


def _workspace_lifecycle_artifact_path(
    *,
    context: RepoContext,
    artifact_type: ArtifactType,
    status: ArtifactStatus,
    artifact_id: str,
) -> Path:
    legacy_path = lifecycle_artifact_path(artifact_type, status, artifact_id)
    if not context.workspace_config.configured:
        return legacy_path
    root = _default_writable_kb_root(context)
    return Path(root.path) / _strip_legacy_kb_prefix(legacy_path)


def _workspace_status_move_path(
    loaded: LoadedRecord,
    artifact: BaseArtifact,
    new_status: ArtifactStatus,
) -> Path:
    legacy_path = lifecycle_artifact_path(artifact.type, new_status, artifact.id)
    if loaded.kb_root_path is None:
        return legacy_path
    return loaded.kb_root_path / _strip_legacy_kb_prefix(legacy_path)


def _default_writable_kb_root(context: RepoContext) -> KbRootConfig:
    writable_roots = [
        root for root in context.workspace_config.kb if not root.readonly
    ]
    if not writable_roots:
        raise ArtifactLifecycleError("no writable KB root is configured")

    private_roots = [root for root in writable_roots if root.name == "private"]
    candidates = private_roots or writable_roots
    return sorted(
        candidates,
        key=lambda root: (-root.priority, root.name, root.path),
    )[0]


def _strip_legacy_kb_prefix(path: Path) -> Path:
    parts = path.parts
    if parts and parts[0] == "kb":
        return Path(*parts[1:])
    return path


def _status_path_for_loaded_record(loaded: LoadedRecord) -> str:
    if loaded.kb_relative_path is None:
        return loaded.source_path.as_posix()
    relative = loaded.kb_relative_path.as_posix()
    return "kb" if not relative else f"kb/{relative}"


def _ensure_repository_valid_for_lifecycle_move(context: RepoContext) -> None:
    report = validate_repository(context)
    if not report.ok:
        raise ArtifactLifecycleError(
            "repository validation failed before status move: "
            f"{_format_report_failures(report)}"
        )


def _format_pydantic_errors(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )


def _format_report_failures(report: ValidationReport) -> str:
    return "; ".join(
        f"{failure.gate} | {failure.source_path} | "
        f"{failure.artifact_id} | {failure.message}"
        for failure in report.failures
    )


if __name__ == "__main__":
    app()
