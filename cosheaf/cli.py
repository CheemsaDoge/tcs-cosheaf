from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

import typer
from pydantic import ValidationError
from rich.console import Console

from cosheaf import __version__
from cosheaf.agent.context_pack import (
    ContextPackError,
)
from cosheaf.agent.local_runner import (
    LocalWorkerRunError,
)
from cosheaf.agent.model_provider import ProviderName
from cosheaf.agent.orchestrator_planner import (
    OrchestratorPlannerError,
    plan_for_issue,
)
from cosheaf.agent.orchestrator_runner import (
    OrchestratorLocalRunConfig,
    OrchestratorLocalRunError,
    OrchestratorLocalRunner,
)
from cosheaf.agent.orchestrator_stub import TaskHarnessError
from cosheaf.agent.providers import (
    ProviderConfig,
    ProviderError,
    ProviderGatewayRequest,
    ProviderMode,
)
from cosheaf.agent.task import WorkerType
from cosheaf.config.workspace import KbRootConfig, WorkspaceConfigError
from cosheaf.core.artifact import BaseArtifact, is_external_dependency_ref
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import lifecycle_artifact_path, repo_relative_posix
from cosheaf.core.status import (
    ArtifactStatus,
    ArtifactType,
    expected_status_for_path,
    is_preaccepted_status,
)
from cosheaf.evals import (
    DEFAULT_CONTEXT_EVAL_CASES,
    DEFAULT_RETRIEVAL_EVAL_CASES,
    ContextEvalError,
    RetrievalEvalError,
    load_context_eval_suite,
    load_retrieval_eval_suite,
    resolve_context_eval_case_path,
    resolve_retrieval_eval_case_path,
    run_context_eval_suite,
    run_retrieval_eval_suite,
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
from cosheaf.ingest import IngestError, MarkItDownIngestAdapter
from cosheaf.mcp import READ_ONLY_TOOL_NAMES, serve_stdio
from cosheaf.memory import (
    MEMORY_GRAPH_SIDECAR,
    ArtifactCardStatus,
    MemoryCardError,
    MemoryGraphError,
    MemoryRootScope,
    MemorySearchError,
    RetrievalRole,
    build_memory_graph,
    compute_global_pagerank,
    load_memory_graph_snapshot,
)
from cosheaf.services import (
    BundleValidationService,
    ContextPackService,
    ContextSendPolicyService,
    ControlledWriteResult,
    DraftWriteService,
    DraftWriteServiceError,
    GateService,
    MemorySearchService,
    ServiceError,
    TaskService,
    ValidationService,
    WorkspaceService,
)
from cosheaf.services.model_calls import ModelCallService
from cosheaf.services.models import (
    AgentAccessModel,
    AgentKbRoot,
    ContextBuildRequest,
    ContextBuildResult,
    ContextPolicyMode,
    DraftArtifactWriteRequest,
    ErrorResult,
    GateRunResult,
    KbRootPolicy,
    ModelCallResult,
    ProviderConsent,
    ValidateResult,
    WorkerBundleSubmitRequest,
)
from cosheaf.services.models import (
    WorkspaceInfoResult as AgentWorkspaceInfoResult,
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
draft_app = typer.Typer(
    add_completion=False,
    help="Controlled draft/staging write commands.",
    no_args_is_help=True,
)
bundle_app = typer.Typer(
    add_completion=False,
    help="Worker bundle review-submission commands.",
    no_args_is_help=True,
)
review_app = typer.Typer(
    add_completion=False,
    help="Controlled review request commands.",
    no_args_is_help=True,
)
orchestrator_app = typer.Typer(
    add_completion=False,
    help="Deterministic local orchestrator commands.",
    no_args_is_help=True,
)
workspace_app = typer.Typer(
    add_completion=False,
    help="Workspace configuration commands.",
    no_args_is_help=True,
)
ingest_app = typer.Typer(
    add_completion=False,
    help="Source ingestion commands.",
    no_args_is_help=True,
)
eval_app = typer.Typer(
    add_completion=False,
    help="Deterministic local evaluation commands.",
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
mcp_app = typer.Typer(
    add_completion=False,
    help="Read-only MCP server commands.",
    no_args_is_help=True,
)
provider_app = typer.Typer(
    add_completion=False,
    help="Provider gateway preview and fake-run commands.",
    no_args_is_help=True,
)
app.add_typer(artifact_app, name="artifact")
app.add_typer(index_app, name="index")
app.add_typer(graph_app, name="graph")
app.add_typer(gate_app, name="gate")
app.add_typer(context_app, name="context")
app.add_typer(task_app, name="task")
app.add_typer(draft_app, name="draft")
app.add_typer(bundle_app, name="bundle")
app.add_typer(review_app, name="review")
app.add_typer(orchestrator_app, name="orchestrator")
app.add_typer(workspace_app, name="workspace")
app.add_typer(ingest_app, name="ingest")
app.add_typer(eval_app, name="eval")
app.add_typer(memory_app, name="memory")
app.add_typer(mcp_app, name="mcp")
app.add_typer(provider_app, name="provider")
memory_app.add_typer(memory_graph_app, name="graph")

_SUPPORTED_PROVIDER_CLI_NAMES = (ProviderName.FAKE, ProviderName.OPENAI)


@app.command()
def version(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Print the TCS-Cosheaf version."""
    if json_output:
        _emit_json(
            {
                "schema_version": 1,
                "package": "tcs-cosheaf",
                "version": __version__,
            }
        )
        return
    Console().print(f"tcs-cosheaf {__version__}")


@workspace_app.command("info")
def workspace_info(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Show workspace configuration and KB roots."""
    console = Console(width=120, markup=False)
    try:
        context = RepoContext(repo_root)
    except WorkspaceConfigError as exc:
        if json_output:
            _emit_error(
                ErrorResult(
                    code="workspace_config_failed",
                    message=str(exc),
                    remediation="Fix cosheaf.toml and rerun workspace info.",
                    blocking=True,
                    related_path="cosheaf.toml",
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"Workspace config failed: {exc}")
        raise typer.Exit(code=1) from None

    info = WorkspaceService(context).info()
    if json_output:
        _emit_model(_workspace_info_to_agent_result(context, info))
        return
    console.print(f"Workspace: {info.name}")
    console.print(f"- repo_root: {info.repo_root}")
    console.print(f"- mode: {info.mode}")
    console.print("KB roots:")
    for root in info.kb_roots:
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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Validate repository YAML records and implemented invariants."""
    context = RepoContext(repo_root)
    _run_validation(
        report_factory=lambda: ValidationService(context).validate_repository(),
        success_message="Validation passed",
        failure_message="Validation failed",
        debug=debug,
        json_output=json_output,
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
        report_factory=lambda: ValidationService(context).validate_artifact_file(path),
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
        result = DraftWriteService(RepoContext(repo_root)).create_artifact(
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
    except DraftWriteServiceError as exc:
        console.print(f"Artifact create failed: {exc}")
        raise typer.Exit(code=1) from None

    artifact = result.artifact
    relative_path = result.relative_path
    console.print(f"Artifact created: {relative_path.as_posix()}")
    console.print(f"- id: {artifact.id}")
    console.print(f"- status: {artifact.status.value}")


@draft_app.command("write-artifact")
def draft_write_artifact(
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="JSON request for a draft artifact write.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for controlled draft writes.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate and report target paths without writing files.",
    ),
) -> None:
    """Write or preview a controlled draft artifact request."""
    console = Console(width=120, markup=False)
    raw = _read_input_json_or_exit(input_json, json_output=json_output)
    if str(raw.get("status", "")).strip() == ArtifactStatus.ACCEPTED.value:
        _exit_with_error(
            ErrorResult(
                code="accepted_write_forbidden",
                message="draft write-artifact cannot target accepted knowledge",
                remediation=(
                    "Use draft status and the explicit promotion workflow after "
                    "review and gates."
                ),
                blocking=True,
            ),
            json_output=json_output,
            console=console,
        )

    try:
        request = DraftArtifactWriteRequest.model_validate(raw)
        result = DraftWriteService(RepoContext(repo_root)).write_artifact_request(
            request,
            dry_run=dry_run,
        )
    except (DraftWriteServiceError, ValidationError) as exc:
        _exit_with_error(
            _exception_to_error_result(exc, default_code="draft_write_failed"),
            json_output=json_output,
            console=console,
        )

    _emit_controlled_write(result, json_output=json_output, console=console)


@draft_app.command("write-source-note")
def draft_write_source_note(
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="JSON request for a staged source note.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for controlled source-note writes.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate and report target paths without writing files.",
    ),
) -> None:
    """Write or preview a staged draft source note."""
    console = Console(width=120, markup=False)
    raw = _read_input_json_or_exit(input_json, json_output=json_output)
    try:
        result = DraftWriteService(RepoContext(repo_root)).write_source_note(
            raw,
            dry_run=dry_run,
        )
    except DraftWriteServiceError as exc:
        _exit_with_error(
            exc.to_error_result(),
            json_output=json_output,
            console=console,
        )

    _emit_controlled_write(result, json_output=json_output, console=console)


@review_app.command("request")
def review_request(
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="JSON request for a draft review request record.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for controlled review requests.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate and report target paths without writing files.",
    ),
) -> None:
    """Write or preview a draft informational review request."""
    console = Console(width=120, markup=False)
    raw = _read_input_json_or_exit(input_json, json_output=json_output)
    status = str(raw.get("status", "")).strip()
    if status in {"human_reviewed", "accepted"}:
        _exit_with_error(
            ErrorResult(
                code="human_review_forbidden",
                message="review request cannot mark human review complete",
                remediation=(
                    "Use status=draft and decision=informational. Human review "
                    "must be recorded explicitly by a reviewer."
                ),
                blocking=True,
            ),
            json_output=json_output,
            console=console,
        )

    try:
        result = DraftWriteService(RepoContext(repo_root)).write_review_request(
            raw,
            dry_run=dry_run,
        )
    except DraftWriteServiceError as exc:
        _exit_with_error(
            exc.to_error_result(),
            json_output=json_output,
            console=console,
        )

    _emit_controlled_write(result, json_output=json_output, console=console)


@bundle_app.command("submit")
def bundle_submit(
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="JSON request for worker bundle review submission.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for bundle submission.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate and report without changing task state.",
    ),
) -> None:
    """Validate a worker bundle for review without promotion."""
    console = Console(width=120, markup=False)
    raw = _read_input_json_or_exit(input_json, json_output=json_output)
    try:
        request = WorkerBundleSubmitRequest.model_validate(raw)
        result = BundleValidationService(RepoContext(repo_root)).submit(
            request,
            dry_run=dry_run,
        )
    except (ServiceError, ValidationError) as exc:
        _exit_with_error(
            _exception_to_error_result(exc, default_code="bundle_submit_failed"),
            json_output=json_output,
            console=console,
        )

    if json_output:
        _emit_model(result)
        return

    console.print(f"Bundle accepted for review: {result.bundle_id}")
    console.print("- accepted knowledge merge: not performed")


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


@ingest_app.command("convert")
def ingest_convert(
    path: Path = typer.Argument(..., help="Repository-local source file to convert."),
    out_dir: Path = typer.Option(
        Path(".cosheaf/ingest"),
        "--out",
        help="Repository-local staging directory for Markdown and metadata output.",
    ),
    metadata_json: bool = typer.Option(
        False,
        "--metadata-json",
        help="Emit deterministic provenance metadata JSON.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used to resolve source and output paths.",
    ),
) -> None:
    """Convert a local source file into staged Markdown with provenance."""
    console = Console(width=120, markup=False)
    try:
        result = MarkItDownIngestAdapter().convert(
            RepoContext(repo_root),
            path,
            out_dir=out_dir,
        )
    except IngestError as exc:
        console.print(f"Ingest failed: {exc}")
        raise typer.Exit(code=1) from None

    if metadata_json:
        typer.echo(result.to_json(), nl=False)
    else:
        console.print(f"Ingest status: {result.status}")
        if result.output_path is not None:
            console.print(f"- output: {result.output_path}")
        if result.metadata_path is not None:
            console.print(f"- metadata: {result.metadata_path}")
        if result.message:
            console.print(f"- note: {result.message}")

    if result.status == "unavailable":
        raise typer.Exit(code=1)


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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Run the gatekeeper when no gate subcommand is provided."""
    if ctx.invoked_subcommand is None:
        _run_gatekeeper_cli(
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
    _run_gatekeeper_cli(
        repo_root=repo_root,
        persist_review=persist_review,
        pr_checklist=pr_checklist,
        json_output=json_output,
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
    context = RepoContext(repo_root)
    try:
        result = ContextPackService(context).build(
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )
    except ContextPackError as exc:
        if json_output:
            _emit_error(
                ErrorResult(
                    code="context_build_failed",
                    message=str(exc),
                    remediation="Check the issue ID and repository records.",
                    blocking=True,
                    related_artifact=_valid_related_artifact(issue_id),
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"Context pack failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        _emit_model(_context_build_to_result(context, result, public_only=public_only))
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
    context = RepoContext(repo_root)
    try:
        service = ContextPackService(context)
        rendered = service.show(
            issue_id,
            role=role,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            public_only=public_only,
        )
    except ContextPackError as exc:
        if json_output:
            _emit_error(
                ErrorResult(
                    code="context_show_failed",
                    message=str(exc),
                    remediation="Check the issue ID and repository records.",
                    blocking=True,
                    related_artifact=_valid_related_artifact(issue_id),
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"Context pack failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        task_dir = context.repo_root / "context" / "TASKS" / issue_id
        files = [
            repo_relative_posix(context.repo_root, task_dir / filename)
            for filename in ("CONTEXT.md",)
        ]
        _emit_json(
            {
                "schema_version": 1,
                "issue_id": issue_id,
                "task_dir": repo_relative_posix(context.repo_root, task_dir),
                "files": files,
                "public_only": public_only,
                "private_context_included": _context_private_included(task_dir),
                "content": rendered,
            }
        )
        return

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
        cards = MemorySearchService(RepoContext(repo_root)).cards(
            issue_id=issue,
            status=status,
        )
    except MemoryCardError as exc:
        if json_output:
            _emit_error(
                ErrorResult(
                    code="memory_cards_failed",
                    message=str(exc),
                    remediation=(
                        "Check the issue ID, status filter, and repository "
                        "records."
                    ),
                    blocking=True,
                    related_artifact=_valid_related_artifact(issue),
                )
            )
            raise typer.Exit(code=1) from None
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
        result = MemorySearchService(RepoContext(repo_root)).search(
            query,
            issue_id=issue,
            status=status,
            seed_artifacts=tuple(seed_artifact or ()),
            pinned_artifacts=tuple(pin_artifact or ()),
            include_refuted=include_refuted,
            include_obsolete=include_obsolete,
        )
    except MemorySearchError as exc:
        if json_output:
            _emit_error(
                ErrorResult(
                    code="memory_search_failed",
                    message=str(exc),
                    remediation=(
                        "Check the query, issue ID, filters, and repository "
                        "records."
                    ),
                    blocking=True,
                    related_artifact=_valid_related_artifact(issue),
                )
            )
            raise typer.Exit(code=1) from None
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


@eval_app.command("retrieval")
def eval_retrieval(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    cases: Path = typer.Option(
        DEFAULT_RETRIEVAL_EVAL_CASES,
        "--cases",
        help="Repository-local YAML retrieval eval case file.",
    ),
    k: int = typer.Option(
        5,
        "--k",
        min=1,
        help="Top-k cutoff used for hit@k.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text summary.",
    ),
) -> None:
    """Run deterministic retrieval regression cases."""
    console = Console(width=120, markup=False)
    try:
        context = RepoContext(repo_root)
        case_path = resolve_retrieval_eval_case_path(context, cases)
        suite = load_retrieval_eval_suite(case_path)
        report = run_retrieval_eval_suite(context, suite, k=k)
    except RetrievalEvalError as exc:
        console.print(f"Retrieval eval failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(report.to_json(), nl=False)
        return

    verdict = "pass" if report.passed else "fail"
    console.print(f"Retrieval eval verdict: {verdict}")
    console.print(f"- cases: {report.case_count}")
    console.print(f"- hit@{k}: {report.metrics.hit_at_k:.6f}")
    console.print(f"- forbidden_hit_count: {report.metrics.forbidden_hit_count}")
    console.print(
        f"- accepted_priority_score: {report.metrics.accepted_priority_score:.6f}"
    )
    console.print(f"- private_leakage_count: {report.metrics.private_leakage_count}")
    for case in report.cases:
        console.print(
            f"- {case.id}: hit@{k}={case.hit_at_k:.6f} "
            f"forbidden={case.forbidden_hit_count} "
            f"private_leakage={case.private_leakage_count} "
            f"returned={','.join(case.returned_artifacts) or '-'}"
        )

    if not report.passed:
        raise typer.Exit(code=1)


@eval_app.command("context")
def eval_context(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    cases: Path = typer.Option(
        DEFAULT_CONTEXT_EVAL_CASES,
        "--cases",
        help="Repository-local YAML context eval case file.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text summary.",
    ),
) -> None:
    """Run deterministic context-pack regression cases."""
    console = Console(width=120, markup=False)
    try:
        context = RepoContext(repo_root)
        case_path = resolve_context_eval_case_path(context, cases)
        suite = load_context_eval_suite(case_path)
        report = run_context_eval_suite(context, suite)
    except ContextEvalError as exc:
        console.print(f"Context eval failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        typer.echo(report.to_json(), nl=False)
        return

    verdict = "pass" if report.passed else "fail"
    console.print(f"Context eval verdict: {verdict}")
    console.print(f"- cases: {report.case_count}")
    console.print(f"- max_cards: {report.metrics.max_cards}")
    console.print(f"- max_full_artifacts: {report.metrics.max_full_artifacts}")
    console.print(f"- token_estimate: {report.metrics.token_estimate}")
    console.print(f"- accepted_ratio: {report.metrics.accepted_ratio:.6f}")
    console.print(f"- draft_ratio: {report.metrics.draft_ratio:.6f}")
    console.print(f"- private_leakage_count: {report.metrics.private_leakage_count}")
    console.print(
        f"- required_artifact_hit: {report.metrics.required_artifact_hit:.6f}"
    )
    for case in report.cases:
        failures = ",".join(case.failures) if case.failures else "-"
        console.print(
            f"- {case.id}: cards={case.metrics.max_cards} "
            f"full={case.metrics.max_full_artifacts} "
            f"private_leakage={case.metrics.private_leakage_count} "
            f"required_hit={case.metrics.required_artifact_hit:.6f} "
            f"failures={failures}"
        )

    if not report.passed:
        raise typer.Exit(code=1)


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


@provider_app.command("list")
def provider_list(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """List provider gateway modes available to agent callers."""
    providers = [
        {
            "provider": ProviderName.FAKE.value,
            "mode": ProviderMode.FAKE.value,
            "enabled_by_default": True,
            "network": "not_used",
            "api_key_required": False,
            "fake_run_cli": True,
            "real_run_cli": False,
        },
        {
            "provider": ProviderName.OPENAI.value,
            "mode": ProviderMode.OPENAI_COMPATIBLE.value,
            "enabled_by_default": False,
            "network": "explicit_config_only",
            "api_key_required": True,
            "fake_run_cli": False,
            "real_run_cli": False,
        },
    ]
    if json_output:
        _emit_json({"schema_version": 1, "providers": providers})
        return

    console = Console(width=120, markup=False)
    for provider in providers:
        console.print(
            f"{provider['provider']} | mode={provider['mode']} | "
            f"network={provider['network']} | real_run_cli=false"
        )


@provider_app.command("config-check")
def provider_config_check(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    provider: ProviderName = typer.Option(
        ProviderName.FAKE,
        "--provider",
        help="Provider identifier to check.",
    ),
    api_key_env: str | None = typer.Option(
        None,
        "--api-key-env",
        help="Environment variable name for provider API key presence checks.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Check provider configuration without revealing secret values."""
    console = Console(width=120, markup=False)
    _ensure_supported_provider_cli(provider, json_output=json_output, console=console)
    try:
        RepoContext(repo_root)
    except WorkspaceConfigError as exc:
        _exit_with_error(
            ErrorResult(
                code="workspace_config_failed",
                message=str(exc),
                remediation="Fix cosheaf.toml and rerun provider config-check.",
                blocking=True,
                related_path="cosheaf.toml",
            ),
            json_output=json_output,
            console=console,
        )

    env_name = api_key_env or _default_provider_api_key_env(provider)
    api_key_present = bool(env_name and os.environ.get(env_name))
    payload = {
        "schema_version": 1,
        "provider": provider.value,
        "mode": _provider_mode(provider).value,
        "enabled": provider is ProviderName.FAKE,
        "api_key_env": env_name,
        "api_key_present": api_key_present,
        "api_key_value": "<redacted>" if api_key_present else "missing",
        "real_run_cli": False,
        "network": "not_used"
        if provider is ProviderName.FAKE
        else "explicit_config_only",
    }
    if json_output:
        _emit_json(payload)
        return

    console.print(f"provider: {payload['provider']}")
    console.print(f"mode: {payload['mode']}")
    console.print(f"api_key_present: {str(api_key_present).lower()}")
    api_key_value = "<redacted>" if api_key_present else "missing"
    console.print(f"api_key_value: {api_key_value}")
    console.print("real_run_cli: false")


@provider_app.command("preview-send")
def provider_preview_send(
    issue: str = typer.Option(..., "--issue", help="Issue ID to preview."),
    provider: ProviderName = typer.Option(
        ProviderName.FAKE,
        "--provider",
        help="Provider identifier for preview metadata.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
    include_private: bool = typer.Option(
        False,
        "--include-private",
        help="Preview private context. Requires private policy and consent.",
    ),
    policy_mode: ContextPolicyMode = typer.Option(
        ContextPolicyMode.PUBLIC,
        "--policy-mode",
        help="Context policy mode.",
    ),
    allow_private_context: bool = typer.Option(
        False,
        "--allow-private-context",
        help="Confirm private-context preview for private research mode.",
    ),
    max_cards: int = typer.Option(
        20,
        "--max-cards",
        help="Maximum preview cards.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Preview provider-send context shape without sending artifact text."""
    console = Console(width=120, markup=False)
    _ensure_supported_provider_cli(provider, json_output=json_output, console=console)
    try:
        request = ContextBuildRequest(
            issue_id=issue,
            max_cards=max_cards,
            max_full_artifacts=0,
            policy_mode=policy_mode,
            public_only=not include_private,
            allow_private_context=allow_private_context,
        )
        preview = ContextSendPolicyService(RepoContext(repo_root)).provider_preview(
            request
        )
    except (ValidationError, WorkspaceConfigError) as exc:
        _exit_with_error(
            _exception_to_error_result(
                exc,
                default_code="provider_context_preview_failed",
            ),
            json_output=json_output,
            console=console,
        )

    if isinstance(preview, ErrorResult):
        _exit_with_error(preview, json_output=json_output, console=console)

    preview_payload = preview.to_dict()
    payload = {
        "schema_version": 1,
        "provider": provider.value,
        "mode": _provider_mode(provider).value,
        "real_run_performed": False,
        "preview": preview_payload,
        "payload_shape": {
            "artifact_count": len(preview.artifact_ids),
            "root_scopes": preview_payload["root_scopes"],
            "estimated_tokens": preview.estimated_tokens,
            "private_context_included": preview.private_context_included,
            "risk_flags": preview.risk_flags,
        },
    }
    if json_output:
        _emit_json(payload)
        return

    console.print(f"provider: {provider.value}")
    console.print(f"artifact_count: {len(preview.artifact_ids)}")
    console.print(f"root_scopes: {', '.join(preview_payload['root_scopes'])}")
    console.print(f"estimated_tokens: {preview.estimated_tokens}")


@provider_app.command("fake-run")
def provider_fake_run(
    input_json: Path = typer.Option(
        ...,
        "--input-json",
        help="JSON request for a fake provider run.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root for provider run logs.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON instead of text output.",
    ),
) -> None:
    """Run the deterministic fake provider; no hosted API call is performed."""
    console = Console(width=120, markup=False)
    context = RepoContext(repo_root)
    raw = _read_input_json_or_exit(input_json, json_output=json_output)
    raw["provider"] = ProviderName.FAKE.value
    raw.setdefault("model", "fake-deterministic")
    raw.setdefault(
        "consent",
        ProviderConsent(
            consent_required=False,
            consent_granted=False,
            allow_private_context=False,
            policy_scope=ContextPolicyMode.PUBLIC,
        ).to_dict(),
    )
    try:
        request = ProviderGatewayRequest.model_validate(raw)
        result = ModelCallService(context).call(
            request,
            config=ProviderConfig(
                provider=ProviderName.FAKE,
                mode=ProviderMode.FAKE,
                model=request.model,
                enabled=True,
            ),
        )
    except (ValidationError, WorkspaceConfigError) as exc:
        _exit_with_error(
            _exception_to_error_result(exc, default_code="provider_fake_run_failed"),
            json_output=json_output,
            console=console,
        )

    if isinstance(result, ProviderError):
        _exit_with_error(
            ErrorResult(
                code=result.code,
                message=result.message,
                remediation=result.remediation,
                blocking=result.blocking,
                details=result.details,
            ),
            json_output=json_output,
            console=console,
        )

    provider_log = _provider_log_payload(context, result)
    payload = result.to_dict()
    payload["provider_log"] = provider_log
    if json_output:
        _emit_json(payload)
        return

    console.print(f"provider: {result.provider.value}")
    console.print(f"status: {result.status.value}")
    if result.provider_run.log_path:
        console.print(f"log_path: {result.provider_run.log_path}")


@mcp_app.command("list-tools")
def mcp_list_tools(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for command consistency.",
    ),
) -> None:
    """List read-only MCP tool names."""
    RepoContext(repo_root)
    for tool_name in READ_ONLY_TOOL_NAMES:
        typer.echo(tool_name)


@mcp_app.command("serve")
def mcp_serve(
    stdio: bool = typer.Option(
        False,
        "--stdio",
        help="Serve line-delimited JSON-RPC over stdio.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to expose through read-only MCP tools.",
    ),
) -> None:
    """Serve the read-only MCP JSON-RPC surface."""
    if not stdio:
        Console(width=120, markup=False).print("MCP serve failed: --stdio is required")
        raise typer.Exit(code=1)
    serve_stdio(RepoContext(repo_root))


@orchestrator_app.command("plan")
def orchestrator_plan(
    issue: str = typer.Option(..., "--issue", help="Issue ID to plan for."),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit deterministic JSON for the plan.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Create a deterministic task-DAG plan without executing workers."""
    console = Console(width=120, markup=False)
    try:
        plan = plan_for_issue(RepoContext(repo_root), issue)
    except OrchestratorPlannerError as exc:
        if json_output:
            _emit_error(
                ErrorResult(
                    code="orchestrator_plan_failed",
                    message=str(exc),
                    remediation="Check the issue ID and repository records.",
                    blocking=True,
                    related_artifact=_valid_related_artifact(issue),
                )
            )
            raise typer.Exit(code=1) from None
        console.print(f"Orchestrator plan failed: {exc}")
        raise typer.Exit(code=1) from None

    if json_output:
        _emit_json({"schema_version": 1, **plan.to_dict()})
        return

    console.print(f"Plan: {plan.plan_id}")
    console.print(f"- issue: {plan.issue_id}")
    console.print(f"- objective: {plan.objective}")
    console.print("- execution: not performed")
    console.print("- accepted knowledge writes: not performed")
    console.print("Task DAG:")
    for node in plan.task_dag.nodes:
        depends_on = ", ".join(node.depends_on) if node.depends_on else "-"
        console.print(
            f"- {node.node_id} | {node.worker_type.value} | depends_on={depends_on}"
        )


@orchestrator_app.command("run")
def orchestrator_run(
    issue: str = typer.Option(..., "--issue", help="Issue ID to run locally."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Run deterministic dry-run workers only.",
    ),
    local_only: bool = typer.Option(
        False,
        "--local-only",
        help="Require local-only execution with no hosted LLM or network.",
    ),
    timeout_seconds: int = typer.Option(
        60,
        "--timeout-seconds",
        help="Maximum runtime for each local worker command in seconds.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root to inspect.",
    ),
) -> None:
    """Run a deterministic local-only orchestrator dry-run for an issue."""
    console = Console(width=120, markup=False)
    if not dry_run:
        console.print("Orchestrator run failed: --dry-run is required")
        raise typer.Exit(code=1)
    if not local_only:
        console.print("Orchestrator run failed: --local-only is required")
        raise typer.Exit(code=1)

    try:
        result = OrchestratorLocalRunner(RepoContext(repo_root)).run_issue(
            OrchestratorLocalRunConfig(
                issue_id=issue,
                timeout_seconds=timeout_seconds,
            )
        )
    except OrchestratorLocalRunError as exc:
        console.print(f"Orchestrator run failed: {exc}")
        raise typer.Exit(code=1) from None

    console.print(f"Orchestrator run: {result.run.run_id}")
    console.print(f"- issue: {result.run.issue_id}")
    console.print(f"- state: {result.run.state.value}")
    console.print("- local_only: true")
    console.print("- hosted_llm: not used")
    console.print("- network: not used")
    console.print("- accepted_writes: not performed")
    console.print(f"- run_record: {result.record_path}")
    console.print(f"- worker_calls: {len(result.run.worker_calls)}")
    console.print(f"- reducer_results: {len(result.run.reducer_results)}")
    for stop in result.run.stop_conditions:
        console.print(f"- stop: {stop.reason} | {stop.description}")

    if result.run.state.value != "completed":
        raise typer.Exit(code=1)


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
        task = TaskService(RepoContext(repo_root)).create_task(
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
        tasks = TaskService(RepoContext(repo_root)).list_tasks()
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
        result = TaskService(RepoContext(repo_root)).complete_task(
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
        service = TaskService(context)
        result = service.run_task(
            task_id,
            command=command,
            timeout_seconds=timeout_seconds,
            cwd=cwd,
            bundle_path=bundle_path,
        )
    except LocalWorkerRunError as exc:
        console.print(f"Task run failed: {exc}")
        raise typer.Exit(code=1) from None

    task_completed = False
    if result.status == "completed" and complete_with_bundle is not None:
        try:
            service.complete_task(
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
    json_output: bool = False,
) -> None:
    console = Console(width=120)
    try:
        report = report_factory()
    except Exception:
        if json_output and not debug:
            _emit_error(
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
        _emit_model(_validation_report_to_result(report))
        if not report.ok:
            raise typer.Exit(code=1)
        return

    _print_validation_report(
        console=console,
        report=report,
        success_message=success_message,
        failure_message=failure_message,
    )
    if not report.ok:
        raise typer.Exit(code=1)


def _emit_json(payload: dict[str, Any] | list[Any]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=True, indent=2))


def _emit_model(model: AgentAccessModel) -> None:
    typer.echo(model.to_json(), nl=False)


def _emit_error(error: ErrorResult) -> None:
    _emit_model(error)


def _read_input_json_or_exit(
    input_json: Path,
    *,
    json_output: bool,
) -> dict[str, Any]:
    try:
        raw = json.loads(input_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        _exit_with_error(
            ErrorResult(
                code="invalid_input_json",
                message=f"invalid input JSON: {exc}",
                remediation="Provide a readable JSON object via --input-json.",
                blocking=True,
                related_path=_valid_related_path(str(input_json)),
            ),
            json_output=json_output,
            console=Console(width=120, markup=False),
        )
    if not isinstance(raw, dict):
        _exit_with_error(
            ErrorResult(
                code="invalid_input_json",
                message="input JSON must be an object",
                remediation="Provide a JSON object at the input document root.",
                blocking=True,
                related_path=_valid_related_path(str(input_json)),
            ),
            json_output=json_output,
            console=Console(width=120, markup=False),
        )
    return dict(raw)


def _exit_with_error(
    error: ErrorResult,
    *,
    json_output: bool,
    console: Console,
) -> NoReturn:
    if json_output:
        _emit_error(error)
    else:
        console.print(f"{error.code}: {error.message}")
        console.print(f"remediation: {error.remediation}")
    raise typer.Exit(code=1)


def _exception_to_error_result(
    exc: Exception,
    *,
    default_code: str,
) -> ErrorResult:
    if isinstance(exc, ServiceError):
        return exc.to_error_result()
    if isinstance(exc, ValidationError):
        return ErrorResult(
            code=default_code,
            message=_format_pydantic_errors(exc),
            remediation="Fix the input JSON fields and retry.",
            blocking=True,
        )
    return ErrorResult(
        code=default_code,
        message=str(exc),
        remediation="Fix the request and retry.",
        blocking=True,
    )


def _emit_controlled_write(
    result: ControlledWriteResult,
    *,
    json_output: bool,
    console: Console,
) -> None:
    if json_output:
        _emit_json(
            {
                "schema_version": 1,
                "kind": result.kind,
                "path": result.relative_path.as_posix(),
                "written_paths": [
                    path.as_posix() for path in result.written_paths
                ],
                "dry_run": result.dry_run,
                "accepted_write_performed": result.accepted_write_performed,
                "record_id": result.record_id,
            }
        )
        return

    action = "would write" if result.dry_run else "wrote"
    console.print(f"{result.kind}: {action} {result.relative_path.as_posix()}")
    console.print("- accepted knowledge merge: not performed")


def _provider_mode(provider: ProviderName) -> ProviderMode:
    if provider is ProviderName.OPENAI:
        return ProviderMode.OPENAI_COMPATIBLE
    if provider is ProviderName.FAKE:
        return ProviderMode.FAKE
    msg = f"provider CLI does not support {provider.value!r}"
    raise ValueError(msg)


def _ensure_supported_provider_cli(
    provider: ProviderName,
    *,
    json_output: bool,
    console: Console,
) -> None:
    if provider in _SUPPORTED_PROVIDER_CLI_NAMES:
        return
    supported = ",".join(provider.value for provider in _SUPPORTED_PROVIDER_CLI_NAMES)
    _exit_with_error(
        ErrorResult(
            code="provider_unsupported",
            message=f"Provider CLI does not support {provider.value!r}.",
            remediation=(
                "Use `cosheaf provider list --json` to inspect currently "
                "supported provider CLI modes."
            ),
            blocking=True,
            details={"supported_providers": supported},
        ),
        json_output=json_output,
        console=console,
    )


def _default_provider_api_key_env(provider: ProviderName) -> str | None:
    if provider is ProviderName.OPENAI:
        return "OPENAI_API_KEY"
    return None


def _provider_log_payload(
    context: RepoContext,
    result: ModelCallResult,
) -> dict[str, Any]:
    log_path = result.provider_run.log_path
    if log_path is None:
        return {}
    raw = json.loads(context.resolve(Path(log_path)).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return dict(raw)


def _workspace_info_to_agent_result(
    context: RepoContext,
    info: Any,
) -> AgentWorkspaceInfoResult:
    return AgentWorkspaceInfoResult(
        workspace_name=info.name,
        repo_root=str(context.repo_root),
        mode=info.mode,
        kb_roots=[
            AgentKbRoot(
                name=root.name,
                path=root.path,
                scope=_kb_root_scope(root),
                readonly=root.readonly,
                priority=root.priority,
            )
            for root in info.kb_roots
        ],
        policy=KbRootPolicy(
            private_can_depend_on_public=(
                context.workspace_config.policy.private_can_depend_on_public
            ),
            public_can_depend_on_private=(
                context.workspace_config.policy.public_can_depend_on_private
            ),
            accepted_requires_source=(
                context.workspace_config.policy.accepted_requires_source
            ),
        ),
    )


def _kb_root_scope(root: KbRootConfig) -> MemoryRootScope:
    name = root.name.lower()
    if name == "public":
        return MemoryRootScope.PUBLIC
    if name == "private":
        return MemoryRootScope.PRIVATE
    if name == "framework":
        return MemoryRootScope.FRAMEWORK
    return MemoryRootScope.WORKSPACE


def _validation_report_to_result(report: ValidationReport) -> ValidateResult:
    return ValidateResult(
        ok=report.ok,
        checked_count=report.checked_count,
        failures=[
            _validation_failure_to_error(failure)
            for failure in report.failures
        ],
    )


def _validation_failure_to_error(failure: Any) -> ErrorResult:
    return ErrorResult(
        code="validation_failed",
        message=f"{failure.gate}: {failure.message}",
        remediation="Fix the referenced YAML record and rerun validation.",
        blocking=True,
        related_path=_valid_related_path(failure.source_path),
        related_artifact=_valid_related_artifact(failure.artifact_id),
        details={"gate": failure.gate},
    )


def _gate_run_to_result(
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
            _gate_issue_to_error(issue)
            for issue in result.report.blocking_issues
        ],
        nonblocking_issues=[
            _gate_issue_to_error(issue)
            for issue in result.report.nonblocking_issues
        ],
    )


def _gate_issue_to_error(issue: Any) -> ErrorResult:
    return ErrorResult(
        code="gate_issue",
        message=f"{issue.gate_id} {issue.gate_name}: {issue.message}",
        remediation="Fix the gate issue and rerun `cosheaf gate run`.",
        blocking=issue.severity == "blocking",
        related_path=_valid_related_path(issue.source_path),
        related_artifact=_valid_related_artifact(issue.artifact_id),
        details={
            "gate_id": issue.gate_id,
            "gate_name": issue.gate_name,
            "severity": issue.severity,
        },
    )


def _context_build_to_result(
    context: RepoContext,
    result: Any,
    *,
    public_only: bool,
) -> ContextBuildResult:
    return ContextBuildResult(
        issue_id=result.issue_id,
        task_dir=repo_relative_posix(context.repo_root, result.task_dir),
        files=[
            repo_relative_posix(context.repo_root, path)
            for path in result.files
        ],
        public_only=public_only,
        private_context_included=_context_private_included(result.task_dir),
    )


def _context_private_included(task_dir: Path) -> bool:
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
        pull.get("root_scope") == MemoryRootScope.PRIVATE.value
        for pull in pulls
    )


def _valid_related_path(value: str | None) -> str | None:
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


def _valid_related_artifact(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return validate_artifact_id(value.strip())
    except ValueError:
        return None


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
    json_output: bool = False,
) -> None:
    console = Console(width=120)
    context = RepoContext(repo_root)
    result = GateService(context).run(
        persist_review=persist_review,
        pr_checklist_path=pr_checklist,
    )
    if json_output:
        _emit_model(_gate_run_to_result(context, result))
        if result.report.blocking_issues:
            raise typer.Exit(code=1)
        return

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
