from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cosheaf import __version__
from cosheaf.agent.context_pack import (
    ContextPackError,
    build_context_pack,
    show_context_pack,
)
from cosheaf.agent.orchestrator_stub import OrchestratorStub, TaskHarnessError
from cosheaf.agent.task import WorkerType
from cosheaf.gates.gatekeeper import (
    GatekeeperRunResult,
    ValidationReport,
    run_gatekeeper,
    validate_artifact_file,
    validate_repository,
)
from cosheaf.graph.claim_graph import DependencyGraph, build_dependency_graph
from cosheaf.storage.index import rebuild_index
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext

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
app.add_typer(artifact_app, name="artifact")
app.add_typer(index_app, name="index")
app.add_typer(graph_app, name="graph")
app.add_typer(gate_app, name="gate")
app.add_typer(context_app, name="context")
app.add_typer(task_app, name="task")


@app.command()
def version() -> None:
    """Print the TCS-Cosheaf version."""
    Console().print(f"tcs-cosheaf {__version__}")


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
) -> None:
    """Run the gatekeeper when no gate subcommand is provided."""
    if ctx.invoked_subcommand is None:
        _run_gatekeeper_cli(repo_root=repo_root, persist_review=persist_review)


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
) -> None:
    """Run gatekeeper checks and write JSON/Markdown reports."""
    _run_gatekeeper_cli(repo_root=repo_root, persist_review=persist_review)


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


def _run_gatekeeper_cli(repo_root: Path, persist_review: bool) -> None:
    console = Console(width=120)
    result = run_gatekeeper(
        RepoContext(repo_root),
        persist_review=persist_review,
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


if __name__ == "__main__":
    app()
