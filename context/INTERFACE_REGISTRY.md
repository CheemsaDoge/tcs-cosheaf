# Interface Registry

## Current Public Python Interfaces

### CLI Entry Point

- Entry point: `cosheaf`
- Implementation: `cosheaf.cli:app`
- Framework: Typer

### CLI Commands

- `cosheaf --help`: shows CLI help.
- `cosheaf version`: prints the package version.
- `cosheaf workspace info`: shows the active workspace name, configured/legacy
  mode, repository root, and KB roots.
- `cosheaf workspace info --repo-root <path>`: shows workspace configuration for
  an explicit repository root.
- `cosheaf validate`: validates repository YAML records discovered under the
  active workspace KB roots plus `issues/` and `examples/`. Without
  `cosheaf.toml`, the KB root remains `kb/`.
- `cosheaf validate --repo-root <path>`: validates a repository rooted at `<path>`.
- `cosheaf validate --debug`: shows tracebacks for unexpected validation errors.
- `cosheaf artifact validate <path>`: validates one YAML file with file-local checks.
- `cosheaf artifact validate <path> --repo-root <path>`: resolves the artifact path against an explicit repository root.
- `cosheaf artifact validate <path> --debug`: shows tracebacks for unexpected validation errors.
- `cosheaf artifact create --id <artifact-id> --type <artifact-type> --title <title> --domain <domain> --status <status> --statement <statement>`: creates a deterministic artifact YAML record under the lifecycle tree and validates it before reporting success. In configured workspaces, it writes to the writable private KB root by default.
- `cosheaf artifact create ... --repo-root <path>`: creates the artifact for an explicit repository root.
- `cosheaf artifact create ... --author <author>`: records one author value; repeat for multiple authors.
- `cosheaf artifact create ... --tag <tag>`: records one tag value; repeat for multiple tags.
- `cosheaf artifact create ... --depends-on <artifact-id>`: records one dependency; repeat for multiple dependencies.
- `cosheaf artifact create ... --supersedes <artifact-id>`: records one superseded artifact ID; repeat for multiple IDs.
- `cosheaf artifact create ... --created-at <timestamp>`: sets `created_at` and `updated_at`; defaults to current UTC if omitted.
- `cosheaf artifact move-status <artifact-id> <new-status>`: moves a unique artifact ID through a non-accepted lifecycle status transition after status/path and repository validation. In configured workspaces, it refuses artifacts loaded from readonly KB roots.
- `cosheaf artifact move-status <artifact-id> <new-status> --repo-root <path>`: moves the artifact status for an explicit repository root.
- `cosheaf index rebuild`: rebuilds `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json`.
- `cosheaf index rebuild --repo-root <path>`: rebuilds index outputs for an explicit repository root.
- `cosheaf graph show`: prints the directed artifact dependency graph.
- `cosheaf graph show --repo-root <path>`: prints the graph for an explicit repository root.
- `cosheaf gate`: runs the gatekeeper with default options and writes reports under `.cosheaf/reports/`.
- `cosheaf gate --repo-root <path>`: runs the gatekeeper for an explicit repository root.
- `cosheaf gate --persist-review`: also persists report copies under `reviews/gatekeeper/`.
- `cosheaf gate run`: explicit gatekeeper run command.
- `cosheaf gate run --repo-root <path>`: runs the gatekeeper for an explicit repository root.
- `cosheaf gate run --persist-review`: also persists report copies under `reviews/gatekeeper/`.
- `cosheaf context build <issue-id>`: builds a bounded deterministic context pack under `context/TASKS/<issue-id>/`.
- `cosheaf context build <issue-id> --repo-root <path>`: builds a context pack for an explicit repository root.
- `cosheaf context show <issue-id>`: builds the context pack and prints `CONTEXT.md`.
- `cosheaf context show <issue-id> --repo-root <path>`: shows context for an explicit repository root.
- `cosheaf task create --issue <issue-id> --worker <worker-type>`: creates an open local agent task under `.cosheaf/tasks/` after confirming the issue exists.
- `cosheaf task create --issue <issue-id> --worker <worker-type> --repo-root <path>`: creates the task for an explicit repository root.
- `cosheaf task list`: lists local task records in deterministic task ID order.
- `cosheaf task list --repo-root <path>`: lists local task records for an explicit repository root.
- `cosheaf task complete <task-id> --bundle <path>`: validates a local worker output bundle and marks the task completed without merging accepted knowledge.
- `cosheaf task complete <task-id> --bundle <path> --repo-root <path>`: completes the task for an explicit repository root.

### Python API

#### Workspace Configuration

- `cosheaf.config.workspace.KbRootConfig`: Pydantic v2 model for one KB root
  with `name`, repository-relative `path`, `readonly`, and `priority`.
- `cosheaf.config.workspace.WorkspacePolicy`: Pydantic v2 model for workspace
  policy fields `private_can_depend_on_public`,
  `public_can_depend_on_private`, and `accepted_requires_source`.
- `cosheaf.config.workspace.WorkspaceConfig`: Pydantic v2 model for workspace
  configuration with `name`, `kb`, `policy`, and `configured` fields.
- `cosheaf.config.workspace.WorkspaceConfig.legacy(repo_root: Path) -> WorkspaceConfig`:
  returns the no-config default with one writable `kb` root.
- `cosheaf.config.workspace.WorkspaceConfig.ordered_kb -> tuple[KbRootConfig, ...]`:
  returns KB roots sorted by `(priority, name, path)`.
- `cosheaf.config.workspace.WorkspaceConfig.root_by_name(name: str) -> KbRootConfig | None`:
  returns one KB root by name when configured.
- `cosheaf.config.workspace.WorkspaceConfigError`: expected config load or
  validation error.
- `cosheaf.config.workspace.load_workspace_config(repo_root: str | Path) -> WorkspaceConfig`:
  loads `cosheaf.toml`, or returns legacy single-root config when absent.

`cosheaf.toml` uses:

- `[workspace]`
- `workspace.name`
- `[[kb]]`
- `kb.name`
- `kb.path`
- `kb.readonly`
- `kb.priority`
- `[policy]`
- `policy.private_can_depend_on_public`
- `policy.public_can_depend_on_private`
- `policy.accepted_requires_source`

#### Core Models

- `cosheaf.core.artifact.BaseArtifact`: Pydantic v2 base model for typed artifacts.
- `cosheaf.core.artifact.Evidence`: Pydantic v2 model for evidence references.
- `cosheaf.core.artifact.Risk`: Pydantic v2 model for artifact risk metadata.
- `cosheaf.core.artifact.ReviewRef`: Pydantic v2 model for inline review state.
- `cosheaf.core.task.AgentTask`: Pydantic v2 model for local task records, re-exported through `cosheaf.agent.task.AgentTask`.

#### Core Enums

- `cosheaf.core.status.ArtifactType`: artifact type enum.
- `cosheaf.core.status.ArtifactStatus`: artifact lifecycle status enum.
- `cosheaf.core.task.WorkerType`: protocol worker type enum, re-exported through `cosheaf.agent.task.WorkerType`.
- `cosheaf.core.task.TaskStatus`: task lifecycle status enum, re-exported through `cosheaf.agent.task.TaskStatus`.

#### Core Helpers

- `cosheaf.core.ids.validate_artifact_id(value: str) -> str`
  - IDs are dot-separated. The first segment must be a lowercase slug; later
    segments may be lowercase slugs or numeric version/index segments such as
    `0001`.
- `cosheaf.core.paths.normalize_repo_path(path: str | Path) -> str`
- `cosheaf.core.paths.repo_relative_path(repo_root: Path, path: Path) -> Path`
- `cosheaf.core.paths.repo_relative_posix(repo_root: Path, path: Path) -> str`
- `cosheaf.core.paths.is_yaml_path(path: Path) -> bool`
- `cosheaf.core.paths.ARTIFACT_TYPE_DIRECTORIES`: mapping from lifecycle artifact type enums to knowledge-base directory names.
- `cosheaf.core.paths.artifact_type_directory(artifact_type: ArtifactType) -> str`
- `cosheaf.core.paths.lifecycle_artifact_path(artifact_type: ArtifactType, status: ArtifactStatus, artifact_id: str) -> Path`
- `cosheaf.core.status.is_terminal_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.is_preaccepted_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.is_accepted_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.expected_status_for_path(path: str) -> frozenset[ArtifactStatus]`
- `cosheaf.core.task.create_task_id(issue_id: str, worker_type: WorkerType | str) -> str`

These helpers are pure validation, path-formatting, status-classification, or deterministic ID helpers. They do not scan the repository, use SQLite, or run gatekeeper behavior.

#### Storage Models and Context

- `cosheaf.storage.repo.RepoContext`: immutable filesystem repository context
  with `repo_root` and loaded `workspace_config`.
- `cosheaf.storage.repo.RepoContext.discovery_roots() -> tuple[str, ...]`:
  returns active repository-relative YAML discovery roots. The roots are
  configured KB root paths plus `issues` and `examples`; in legacy mode this is
  `kb`, `issues`, and `examples`.
- `cosheaf.storage.repo.RepoContext.kb_root_for_path(path: str | Path) -> KbRootConfig | None`:
  returns the configured KB root containing a repository-relative path.
- `cosheaf.storage.repo.RepoContext.kb_relative_path(path: str | Path) -> Path | None`:
  returns a path relative to its configured KB root when applicable.
- `cosheaf.storage.loader.IssueRecord`: Pydantic v2 model for issue YAML records loaded by storage.
- `cosheaf.storage.loader.ReviewRecord`: Pydantic v2 model for review YAML records loaded by storage.
- `cosheaf.storage.loader.LoadedRecord`: loaded record wrapper with repository-relative `source_path`, typed `record`, and optional KB root metadata (`kb_root_name`, `kb_root_path`, `kb_root_readonly`, `kb_relative_path`).

#### Storage Loader

- `cosheaf.storage.loader.discover_yaml_paths(context: RepoContext) -> list[Path]`
- `cosheaf.storage.loader.load_yaml_file(context: RepoContext, path: Path) -> LoadedRecord`
- `cosheaf.storage.loader.load_artifacts(context: RepoContext) -> list[LoadedRecord]`

The loader discovers `.yaml` and `.yml` files under the active workspace KB
roots plus `issues/` and `examples/`, parses YAML without swallowing parse
errors, and returns loaded records in deterministic order by source path then
ID. Without `cosheaf.toml`, the active KB root is the legacy `kb/` path. Loaded
models currently include `BaseArtifact`, `IssueRecord`, `ReviewRecord`, and
`AgentTask` example records. Runtime task records under `.cosheaf/tasks/` are
not part of repository discovery.

#### Storage Writer

- `cosheaf.storage.writer.dump_yaml_deterministic(data: Any) -> str`
- `cosheaf.storage.writer.write_yaml_deterministic(path: Path, data: Any) -> None`

The writer preserves mapping insertion order by disabling YAML key sorting.

#### Storage Errors

- `cosheaf.storage.loader.LoadError`
- `cosheaf.storage.loader.UnsupportedArtifactTypeError`

The storage loader and writer do not use SQLite and do not implement gatekeeper
behavior.

#### Storage Index

- `cosheaf.storage.index.IndexRebuildResult`: paths and counts produced by an index rebuild.
- `cosheaf.storage.index.rebuild_index(context: RepoContext) -> IndexRebuildResult`

The index rebuild writes `.cosheaf/index.sqlite` and
`.cosheaf/artifact_manifest.json` from scratch. The SQLite index stores artifact
ID, type, status, path, title, domain, source KB root, and dependency rows. The
manifest is ordered deterministically by artifact ID and dependency tuple.

#### Dependency Graph

- `cosheaf.graph.claim_graph.GraphNode`: deterministic artifact graph node.
- `cosheaf.graph.claim_graph.GraphEdge`: directed dependency edge from artifact to dependency.
- `cosheaf.graph.claim_graph.GraphIssue`: deterministic graph issue row.
- `cosheaf.graph.claim_graph.DependencyGraph`: graph nodes, edges, and detected issues.
- `cosheaf.graph.claim_graph.build_dependency_graph(records: Iterable[LoadedRecord]) -> DependencyGraph`

Graph edge direction is artifact-to-dependency, for example
`claim.example.a -> claim.example.b` means artifact `a` depends on artifact `b`.
The graph reports missing dependencies, directed cycles, and accepted artifacts
depending on draft or otherwise pre-accepted artifacts.

#### Validation Gates

- `cosheaf.gates.schema_gate.ValidationFailure`: deterministic validation failure row.
- `cosheaf.gates.schema_gate.SchemaGateResult`: schema/model loading result.
- `cosheaf.gates.schema_gate.load_schema_valid_records(context: RepoContext) -> SchemaGateResult`
- `cosheaf.gates.schema_gate.load_schema_valid_record(context: RepoContext, path: Path) -> SchemaGateResult`
- `cosheaf.gates.schema_gate.sort_failures(failures: Iterable[ValidationFailure]) -> tuple[ValidationFailure, ...]`
- `cosheaf.gates.status_gate.validate_status_paths(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.status_gate.validate_evidence_paths(context: RepoContext, records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.dependency_gate.validate_id_uniqueness(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.dependency_gate.validate_dependencies(records: tuple[LoadedRecord, ...]) -> list[ValidationFailure]`
- `cosheaf.gates.reproducibility_gate.ReproducibilityCheck`: one executable evidence metadata check row.
- `cosheaf.gates.reproducibility_gate.ReproducibilityMetadataResult`: aggregate reproducibility metadata gate result.
- `cosheaf.gates.reproducibility_gate.validate_reproducibility_metadata(records: tuple[LoadedRecord, ...], verification_results: tuple[VerificationResult, ...]) -> ReproducibilityMetadataResult`
- `cosheaf.gates.gatekeeper.ValidationReport`: validation report with loaded records and failures.
- `cosheaf.gates.gatekeeper.validate_repository(context: RepoContext) -> ValidationReport`
- `cosheaf.gates.gatekeeper.validate_artifact_file(context: RepoContext, path: Path) -> ValidationReport`
- `cosheaf.gates.gatekeeper.GateIssue`: blocking or nonblocking gatekeeper issue row.
- `cosheaf.gates.gatekeeper.GateResult`: one gate result in a gatekeeper run, including optional machine-readable `details`.
- `cosheaf.gates.gatekeeper.GatekeeperReport`: machine-readable gatekeeper report.
- `cosheaf.gates.gatekeeper.GatekeeperRunResult`: report and written report paths.
- `cosheaf.gates.gatekeeper.GateStatus`: gate status literal type.
- `cosheaf.gates.gatekeeper.GateVerdict`: gatekeeper verdict literal type.
- `cosheaf.gates.gatekeeper.run_gatekeeper(context: RepoContext, *, persist_review: bool = False, timestamp: str | None = None) -> GatekeeperRunResult`

The dependency gate validates missing dependencies, accepted-to-draft
dependencies across KB roots, and public-artifact-to-private-artifact
dependencies.

The validation orchestrator is deterministic and filesystem-backed.
`validate_repository` does not run verifier adapters. `run_gatekeeper` runs
G1-G5 validation gates, runs the G6 verifier gate through the default verifier
registry, runs the G7 reproducibility metadata gate over executable evidence
and verifier results, and records G8 as a skipped placeholder. It writes JSON
and Markdown reports under `.cosheaf/reports/` by default.

#### Agent Context Packs

- `cosheaf.agent.context_pack.ContextPackError`: expected context pack generation error, such as a missing issue ID.
- `cosheaf.agent.context_pack.ContextPackResult`: written context pack metadata with issue ID, task directory, and file paths.
- `cosheaf.agent.context_pack.build_context_pack(context: RepoContext, issue_id: str) -> ContextPackResult`
- `cosheaf.agent.context_pack.show_context_pack(context: RepoContext, issue_id: str) -> str`

Context pack generation loads repository YAML records, finds an issue by ID,
selects and ranks artifacts from direct `related_artifacts`, one-hop dependency
neighbors, artifact domains that match issue text or tags, and artifact tags
that match issue tags. Ranking is deterministic and each listed artifact
includes explainable `reasons`. Accepted artifacts are preferred over draft
artifacts within the same relevance class. Draft artifacts are visibly labeled
as `[DRAFT]`; refuted, obsolete, and superseded artifacts are included only when
relevant and are labeled with their terminal status. Context pack files are
written under `context/TASKS/<issue-id>/`.

Generated context pack files are:

- `CONTEXT.md`
- `ACCEPTANCE.md`
- `RELEVANT_ARTIFACTS.md`
- `KNOWN_FAILURES.md`
- `COMMANDS.md`

`RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`, and the artifact sections inside
`CONTEXT.md` use lines containing artifact ID, title, status, source path, and
ranking reasons.

#### Agent Tasks

- `cosheaf.agent.task.WorkerType`: protocol worker type enum with values `reasoner`, `verifier`, `counterexampleer`, `construction_searcher`, `formalizer`, `literature_scout`, and `orchestrator`.
- `cosheaf.agent.task.TaskStatus`: task status enum with values `open`, `in_progress`, `blocked`, `completed`, `failed`, and `cancelled`.
- `cosheaf.agent.task.AgentTask`: Pydantic v2 model for local task records with fields `task_id`, `issue_id`, `worker_type`, `status`, `input_context`, `budget`, `expected_outputs`, `created_at`, and `updated_at`.
- `cosheaf.agent.task.create_task_id(issue_id: str, worker_type: WorkerType | str) -> str`: deterministic default task ID helper. It returns `task.<issue-id>.<worker-type-slug>`, with underscores in worker type values rendered as hyphens.
- `cosheaf.agent.worker_contract.WorkerOutputKind`: output kind enum with values `artifact`, `review`, `evidence`, and `report`.
- `cosheaf.agent.worker_contract.WorkerOutput`: Pydantic v2 model for one repository-local output reference.
- `cosheaf.agent.worker_contract.WorkerOutputBundle`: Pydantic v2 model for a local worker output bundle manifest.
- `cosheaf.agent.worker_contract.OutputBundleError`: expected worker output bundle validation error.
- `cosheaf.agent.worker_contract.validate_output_bundle(context: RepoContext, bundle_path: str | Path, *, task: AgentTask | None = None) -> WorkerOutputBundle`: validates a local bundle manifest and referenced output paths without merging accepted knowledge.
- `cosheaf.agent.orchestrator_stub.OrchestratorStub`: local filesystem task harness stub. It creates, lists, loads, and completes task records without LLM calls, network calls, concrete worker execution, or accepted knowledge merges.
- `cosheaf.agent.orchestrator_stub.TaskHarnessError`: expected task harness error.
- `cosheaf.agent.orchestrator_stub.AcceptedKnowledgeMergeProhibitedError`: raised when a caller asks the stub to merge accepted knowledge.
- `cosheaf.agent.orchestrator_stub.TaskCompletionResult`: completed task, validated bundle, and task path.

Task records are written under:

- `.cosheaf/tasks/<task-id>.yaml`

Worker output bundles may be passed as a YAML file path or as a directory
containing `bundle.yaml`. Bundle manifests use:

- `schema_version`
- `task_id`
- `worker_type`
- `outputs`
- `notes`

Artifact and review outputs must point to repository-local YAML records that
pass the schema gate. Outputs under `kb/accepted/` are rejected.

#### Verification

- `cosheaf.verification.base.VerifierAdapter`: protocol for verifier adapters.
- `cosheaf.verification.result.VerificationStatus`: normalized result status enum with `pass`, `fail`, `error`, and `skipped`.
- `cosheaf.verification.result.VerificationResult`: Pydantic v2 model for normalized verifier output.
- `cosheaf.verification.registry.VerifierRegistry`: instance-local verifier adapter registry.
- `cosheaf.verification.registry.VerifierRegistryError`: registry registration error.
- `cosheaf.verification.registry.default_verifier_registry() -> VerifierRegistry`
- `cosheaf.verification.python_checker.PythonCheckerAdapter`: verifier adapter for `kind: python_checker` evidence.
- `cosheaf.verification.python_checker.PythonCheckerSpec`: normalized Python checker evidence command specification.
- `cosheaf.verification.sat_adapter.SatAdapter`: optional SAT solver skeleton adapter.
- `cosheaf.verification.smt_adapter.SmtAdapter`: optional SMT solver skeleton adapter.
- `cosheaf.verification.lean_adapter.LeanAdapter`: optional Lean skeleton adapter.

`VerifierAdapter` requires:

- `name: str`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

`VerificationResult` fields are:

- `verifier`
- `artifact_id`
- `status`
- `started_at`
- `ended_at`
- `command`
- `cwd`
- `exit_code`
- `stdout_path`
- `stderr_path`
- `evidence_paths`
- `timeout_seconds`
- `input_paths`
- `output_paths`
- `tool_name`
- `tool_version`
- `seed`
- `environment`
- `message`

`VerificationResult.to_dict() -> dict[str, Any]` returns a deterministic
machine-readable mapping in model field order. `VerificationResult.to_json() ->
str` returns deterministic JSON for the result. Timestamps are the only expected
run-to-run variation when callers construct results with live clock values.

`VerificationResult` exposes status helpers:

- `is_pass`
- `is_fail`
- `is_error`
- `is_skipped`

`VerifierRegistry` exposes:

- `register(adapter: VerifierAdapter) -> None`
- `get(name: str) -> VerifierAdapter | None`
- `names -> tuple[str, ...]`
- `adapters -> tuple[VerifierAdapter, ...]`

Registry ordering is deterministic by adapter name. Duplicate adapter names
raise `VerifierRegistryError`.

The default verifier registry currently registers `LeanAdapter`,
`PythonCheckerAdapter`, `SatAdapter`, and `SmtAdapter`. Registry ordering is
deterministic by adapter name.

`PythonCheckerAdapter` exposes:

- `name = "python_checker"`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

The adapter runs evidence entries with `kind: python_checker` from the
repository root. With the current artifact evidence model, it derives the command
from the active Python executable, the evidence `path`, and the artifact source
path. It writes stdout and stderr under `.cosheaf/logs/`, records command, cwd,
timeout, input path, output path, tool, tool version, and environment metadata,
returns `pass` for exit code `0`, `fail` for nonzero exit code, and `error` for
timeout or missing checker scripts.

`SatAdapter` exposes:

- `name = "sat"`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `sat`, `sat_solver`, and `sat_checker`. It checks
the configured SAT solver command, defaults to `kissat`, and returns `skipped`
when the solver is unavailable or when real SAT verification is still TODO.

`SmtAdapter` exposes:

- `name = "smt"`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `smt`, `smt_solver`, and `smt_checker`. It checks
the configured SMT solver command, defaults to `z3`, and returns `skipped` when
the solver is unavailable or when real SMT verification is still TODO.

`LeanAdapter` exposes:

- `name = "lean"`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `lean`, `lean4`, and `lean_checker`. It checks the
configured Lean command, defaults to `lean`, and returns `skipped` when Lean is
unavailable or when real Lean verification is still TODO.

### Makefile Targets

- `make lint`: runs `python -m ruff check .`
- `make typecheck`: runs `python -m mypy cosheaf tests`
- `make test`: runs `python -m pytest`
- `make validate`: runs `python -m cosheaf.cli validate`.
- `make gate`: runs `python -m cosheaf.cli gate`, which defaults to a real gatekeeper run.

### Schemas

- `schemas/artifact.schema.json`: artifact YAML schema.
- `schemas/issue.schema.json`: issue YAML schema.
- `schemas/review.schema.json`: review YAML schema.
- `schemas/verifier.schema.json`: verifier result schema.
- `schemas/task.schema.json`: agent task YAML schema.

### Workspace Config Files

- `cosheaf.toml`: optional repository-root workspace configuration file.
  Absence preserves legacy single-root behavior.
- `[workspace] name`: workspace display name.
- `[[kb]] name`: KB root name.
- `[[kb]] path`: repository-relative KB root path.
- `[[kb]] readonly`: whether write commands may modify that root.
- `[[kb]] priority`: integer priority used for deterministic root ordering and
  reporting.
- `[policy] private_can_depend_on_public`: whether private artifacts may depend
  on public artifacts.
- `[policy] public_can_depend_on_private`: whether public artifacts may depend
  on private artifacts.
- `[policy] accepted_requires_source`: whether accepted public artifacts require
  source metadata policy enforcement in future promotion workflows.

## Registration Rule

Future public interface changes must be recorded here. Public interfaces include CLI commands, Python APIs, artifact schemas, gate result formats, verifier adapter contracts, context pack formats, and documented file layouts.
