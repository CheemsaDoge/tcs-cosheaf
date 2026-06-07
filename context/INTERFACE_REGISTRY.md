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
- `cosheaf artifact promote <artifact-id>`: promotes an eligible lifecycle artifact into `kb/accepted/<type-dir>/<artifact-id>.yaml` after repository validation, gatekeeper, target verifier, dependency, review, readonly-root, and accepted-public source metadata checks.
- `cosheaf artifact promote <artifact-id> --repo-root <path>`: promotes the artifact for an explicit repository root.
- `cosheaf index rebuild`: rebuilds `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json`.
- `cosheaf index rebuild --repo-root <path>`: rebuilds index outputs for an explicit repository root.
- `cosheaf graph show`: prints the directed artifact dependency graph.
- `cosheaf graph show --repo-root <path>`: prints the graph for an explicit repository root.
- `cosheaf gate`: runs the gatekeeper with default options and writes reports under `.cosheaf/reports/`.
- `cosheaf gate --repo-root <path>`: runs the gatekeeper for an explicit repository root.
- `cosheaf gate --persist-review`: also persists report copies under `reviews/gatekeeper/`.
- `cosheaf gate --pr-checklist <path>`: validates a local PR checklist markdown file through G8 when running the default gate command.
- `cosheaf gate run`: explicit gatekeeper run command.
- `cosheaf gate run --repo-root <path>`: runs the gatekeeper for an explicit repository root.
- `cosheaf gate run --persist-review`: also persists report copies under `reviews/gatekeeper/`.
- `cosheaf gate run --pr-checklist <path>`: validates a local PR checklist markdown file through G8 without using GitHub API or network access.
- `cosheaf context build <issue-id>`: builds a bounded deterministic context pack under `context/TASKS/<issue-id>/`.
- `cosheaf context build <issue-id> --repo-root <path>`: builds a context pack for an explicit repository root.
- `cosheaf context show <issue-id>`: builds the context pack and prints `CONTEXT.md`.
- `cosheaf context show <issue-id> --repo-root <path>`: shows context for an explicit repository root.
- `cosheaf memory cards`: builds deterministic artifact cards from existing
  repository metadata. Default output is compact text lines, not full artifact
  YAML or statements.
- `cosheaf memory cards --repo-root <path>`: builds cards for an explicit
  repository root.
- `cosheaf memory cards --issue <issue-id>`: limits cards to the issue record's
  direct `related_artifacts`, after scope/status filters.
- `cosheaf memory cards --status <status>`: filters cards by artifact-card
  lifecycle/trust status, such as `accepted` or `draft`.
- `cosheaf memory cards --json`: emits deterministic JSON card DTOs.
- `cosheaf memory search <query>`: searches deterministic artifact cards with
  local SQLite FTS5/BM25 when available, deterministic lexical fallback
  otherwise, and issue-conditioned graph ranking signals. Default text output
  prints compact card lines with total score, not full artifact YAML or
  statements.
- `cosheaf memory search <query> --repo-root <path>`: searches cards for an
  explicit repository root.
- `cosheaf memory search <query> --issue <issue-id>`: uses the issue and its
  direct `related_artifacts` as Personalized PageRank seeds after
  scope/status filters, without granting accepted-promotion authority.
- `cosheaf memory search <query> --seed-artifact <artifact-id>`: adds an
  explicit artifact seed to personalized ranking; repeat for multiple seeds.
- `cosheaf memory search <query> --pin-artifact <artifact-id>`: adds a
  stronger pinned artifact seed to personalized ranking; repeat for multiple
  pins.
- `cosheaf memory search <query> --status <status>`: filters search candidates
  by artifact-card lifecycle/trust status.
- `cosheaf memory search <query> --include-refuted`: includes refuted cards
  with an explicit score penalty.
- `cosheaf memory search <query> --include-obsolete`: includes obsolete and
  superseded cards with an explicit score penalty.
- `cosheaf memory search <query> --explain`: prints score component
  breakdowns and relevance reasons in text output.
- `cosheaf memory search <query> --json`: emits a deterministic
  `RetrievalResult` JSON payload with card hits, score breakdowns, and audit
  metadata.
- `cosheaf memory graph build`: rebuilds
  `.cosheaf/memory/graph_snapshot.json` from repository YAML plus optional
  local sidecar signals such as gate reports and task run records.
- `cosheaf memory graph build --repo-root <path>`: rebuilds the memory graph
  sidecar for an explicit repository root.
- `cosheaf memory graph build --json`: emits a deterministic JSON build
  summary with the graph fingerprint, node count, edge count, sidecar path,
  and warnings.
- `cosheaf memory graph pagerank`: computes deterministic weighted global
  PageRank from an existing `.cosheaf/memory/graph_snapshot.json` sidecar.
- `cosheaf memory graph pagerank --repo-root <path>`: computes PageRank for an
  explicit repository root.
- `cosheaf memory graph pagerank --json`: emits a deterministic
  `PageRankResult` JSON payload.
- `cosheaf task create --issue <issue-id> --worker <worker-type>`: creates an open local agent task under `.cosheaf/tasks/` after confirming the issue exists.
- `cosheaf task create --issue <issue-id> --worker <worker-type> --repo-root <path>`: creates the task for an explicit repository root.
- `cosheaf task list`: lists local task records in deterministic task ID order.
- `cosheaf task list --repo-root <path>`: lists local task records for an explicit repository root.
- `cosheaf task complete <task-id> --bundle <path>`: validates a local worker output bundle and marks the task completed without merging accepted knowledge.
- `cosheaf task complete <task-id> --bundle <path> --repo-root <path>`: completes the task for an explicit repository root.
- `cosheaf task run <task-id> -- <command> [args...]`: runs an explicit local argv command for an existing task, logs stdout/stderr and run metadata under `.cosheaf/tasks/<task-id>/runs/<run-id>/`, and does not complete the task by default.
- `cosheaf task run <task-id> --timeout-seconds <seconds> -- <command> [args...]`: enforces a positive command timeout.
- `cosheaf task run <task-id> --cwd <repo-local-path> -- <command> [args...]`: runs from an optional repository-local working directory. Paths outside the repository are rejected.
- `cosheaf task run <task-id> --bundle <path> -- <command> [args...]`: requires a repository-local bundle path, validates a worker output bundle after a successful command without completing the task, and accepts either a YAML manifest or a directory containing `bundle.yaml`.
- `cosheaf task run <task-id> --complete-with-bundle <path> -- <command> [args...]`: requires a repository-local bundle path, validates a worker output bundle after a successful command, accepts either a YAML manifest or a directory containing `bundle.yaml`, and delegates task completion to the existing orchestrator stub.
- `cosheaf task run <task-id> ... --repo-root <path> -- <command> [args...]`: runs the local worker command for an explicit repository root.

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
- `cosheaf.core.artifact.SourceMetadata`: Pydantic v2 model for structured source/citation metadata.
- `cosheaf.core.artifact.FormalizationRef`: Pydantic v2 model for one external
  formal declaration reference.
- `cosheaf.core.artifact.AlignmentReview`: Pydantic v2 model for semantic
  alignment review between an informal artifact statement and a formal
  declaration.
- `cosheaf.core.artifact.VerificationPolicy`: Pydantic v2 model for
  per-artifact formal-link, Lean-check, and alignment-review expectations.
- `cosheaf.core.task.AgentTask`: Pydantic v2 model for local task records, re-exported through `cosheaf.agent.task.AgentTask`.

`BaseArtifact` fields include:

- `sources: list[SourceMetadata]`
- `formalizations: list[FormalizationRef]`
- `alignment: AlignmentReview`
- `verification_policy: VerificationPolicy`

`SourceMetadata` fields are:

- `kind`: `paper`, `book`, `survey`, `lecture_note`, `website`,
  `internal_note`, or `other`
- `title`
- `authors`
- `year`
- `doi`
- `arxiv`
- `url`
- `theorem_number`
- `page`
- `notes`

`FormalizationRef` fields are:

- `id`
- `system`: currently `lean4`
- `library`
- `library_ref`
- `import_path`
- `symbol`
- `declaration_kind`: `definition`, `theorem`, `lemma`, `instance`,
  `structure`, or `other`
- `status`: `planned`, `linked`, `checked`, `broken`, or `deprecated`
- `check_mode`: `external_library_ref` or `local_file`
- `expected_type`: optional, defaults to an empty string
- `notes`: optional, defaults to an empty string

Formalization reference IDs use the same dot-separated lowercase slug format
as artifact IDs. `library`, `library_ref`, `import_path`, and `symbol` are
required non-empty strings.

`AlignmentReview` fields are:

- `status`: `none`, `requested`, `human_reviewed`, or `rejected`
- `reviewer`
- `reviewed_at`
- `convention_notes`
- `limitations`

Alignment statuses `human_reviewed` and `rejected` require a non-empty
`reviewer`. `reviewed_at`, when present, must include timezone information.

`VerificationPolicy` fields are:

- `level`: `source_reviewed`, `source_reviewed_with_formal_link`,
  `machine_checked`, or `lean_required`
- `require_formal_link`
- `require_lean_check`
- `require_alignment_review`

`source_reviewed_with_formal_link` requires `require_formal_link: true`.
`lean_required` requires both `require_formal_link: true` and
`require_lean_check: true`.

Formalization links are metadata references to external declarations. They are
not copied Lean proof bodies and are not stored in `evidence`. G10 statically
checks consistency between `formalizations`, `alignment`, and
`verification_policy`, but it does not execute Lean, inspect CSLib/mathlib
libraries, prove informal/formal alignment, or change accepted promotion
semantics beyond ordinary gatekeeper blocking behavior.

#### Memory/Retrieval Models

- `cosheaf.memory.ArtifactCard`: Pydantic v2 model for compact retrieval cards
  derived from existing repository metadata.
- `cosheaf.memory.ScoreBreakdown`: Pydantic v2 model for inspectable retrieval
  score components.
- `cosheaf.memory.RetrievalRequest`: Pydantic v2 model for bounded local
  retrieval requests.
- `cosheaf.memory.RetrievedArtifactCard`: Pydantic v2 model pairing an
  `ArtifactCard` with a `ScoreBreakdown` and relevance reasons.
- `cosheaf.memory.FullArtifactPull`: Pydantic v2 audit entry for explicit full
  artifact pulls beyond card metadata.
- `cosheaf.memory.RetrievalExclusion`: Pydantic v2 audit entry for records
  excluded by scope, status, or policy.
- `cosheaf.memory.RetrievalAudit`: Pydantic v2 model for retrieval filters,
  exclusions, and warnings.
- `cosheaf.memory.RetrievalResult`: Pydantic v2 model for ordered retrieved
  cards, full-artifact pull audit entries, and retrieval audit metadata.
- `cosheaf.memory.RetrievalScoreWeights`: frozen dataclass for configurable
  retrieval formula weights. Defaults are `0.50` retrieval hybrid, `0.20`
  personalized PageRank, `0.15` global PageRank, `0.10` quality prior, and
  `0.05` freshness. Penalty is always subtracted after weighted components.
- `cosheaf.memory.MemoryGraphNode`: Pydantic v2 model for one deterministic
  memory graph node.
- `cosheaf.memory.MemoryGraphEdge`: Pydantic v2 model for one weighted memory
  graph edge.
- `cosheaf.memory.MemoryGraphSnapshot`: Pydantic v2 model for the rebuildable
  `.cosheaf/memory/graph_snapshot.json` sidecar.
- `cosheaf.memory.PageRankRow`: Pydantic v2 model for one global PageRank row.
- `cosheaf.memory.PageRankResult`: Pydantic v2 model for deterministic
  weighted global PageRank output.
- `cosheaf.memory.MemoryCardError`: expected error for card-builder failures,
  such as an unknown issue ID or a repository load failure.
- `cosheaf.memory.MemorySearchError`: expected error for memory-search
  failures, such as invalid query text or card-builder errors.
- `cosheaf.memory.MemoryGraphError`: expected error for memory graph build,
  sidecar read, or PageRank failures.

All memory models are strict (`extra="forbid"`), frozen, preserve enum values as
enum instances in Python, and expose:

- `to_dict() -> dict[str, Any]`: deterministic `model_dump(mode="json")`.
- `to_json() -> str`: deterministic indented JSON with a trailing newline.

`ArtifactCard` fields are:

- `id`
- `path`
- `root_scope`
- `type`
- `status`
- `title`
- `summary`
- `domain`
- `tags`
- `depends_on`
- `sources`
- `review_state`
- `verifier_state`
- `formalization_state`
- `trust_score`
- `retrieval_score`
- `why_relevant`
- `risk_flags`
- `can_pull_full`

`RetrievalRequest` fields are:

- `schema_version`
- `query`
- `issue_id`
- `seed_artifacts`
- `pinned_artifacts`
- `allowed_scopes`
- `allowed_statuses`
- `include_refuted`
- `include_obsolete`
- `max_cards`
- `max_full_artifacts`
- `role`

`RetrievalResult` fields are:

- `schema_version`
- `request_id`
- `generated_at`
- `index_fingerprint`
- `cards`
- `full_artifact_pulls`
- `audit`

`MemoryGraphSnapshot` fields are:

- `schema_version`
- `generated_at`
- `graph_fingerprint`
- `nodes`
- `edges`
- `warnings`

`MemoryGraphNode` fields are:

- `node_id`
- `kind`
- `record_id`
- `path`
- `title`
- `status`
- `metadata`

`MemoryGraphEdge` fields are:

- `source`
- `target`
- `kind`
- `weight`
- `evidence`

`PageRankResult` fields are:

- `schema_version`
- `algorithm`
- `damping`
- `iterations`
- `graph_fingerprint`
- `rows`
- `warnings`

The memory package also exposes:

- `cosheaf.memory.build_artifact_cards(context: RepoContext, *, issue_id: str | None = None, status: ArtifactCardStatus | str | None = None, allowed_scopes: Iterable[MemoryRootScope | str] = DEFAULT_CARD_SCOPES) -> tuple[ArtifactCard, ...]`:
  builds deterministic cards from loaded repository YAML metadata.
- `cosheaf.memory.artifact_card_from_loaded_record(loaded: LoadedRecord) -> ArtifactCard`:
  builds one card from a loaded lifecycle artifact record.
- `cosheaf.memory.DEFAULT_CARD_SCOPES`: default public-output scope set,
  containing `public`, `workspace`, and `framework`, excluding `private`.
- `cosheaf.memory.search_artifact_cards(context: RepoContext, *, query: str, issue_id: str | None = None, status: ArtifactCardStatus | str | None = None, max_cards: int = 20, allowed_scopes: tuple[MemoryRootScope, ...] | None = None, seed_artifacts: tuple[str, ...] = (), pinned_artifacts: tuple[str, ...] = (), include_refuted: bool = False, include_obsolete: bool = False, score_weights: RetrievalScoreWeights = RetrievalScoreWeights()) -> RetrievalResult`:
  searches deterministic artifact cards with SQLite FTS5/BM25 when available,
  deterministic lexical fallback otherwise, and in-memory Personalized
  PageRank/global PageRank/freshness/penalty scoring. It does not write memory
  sidecars.
- `cosheaf.memory.build_memory_graph(context: RepoContext, *, persist: bool = False) -> MemoryGraphSnapshot`:
  builds the deterministic memory graph from repository YAML plus optional
  local sidecar signals. With `persist=True`, it writes the rebuildable
  `.cosheaf/memory/graph_snapshot.json` sidecar.
- `cosheaf.memory.load_memory_graph_snapshot(context: RepoContext) -> MemoryGraphSnapshot`:
  loads the existing graph sidecar and fails clearly if users need to run
  `cosheaf memory graph build` first.
- `cosheaf.memory.compute_global_pagerank(graph: MemoryGraphSnapshot, *, damping: float = 0.85, max_iterations: int = 50, tolerance: float = 1e-12) -> PageRankResult`:
  computes deterministic weighted global PageRank rows from the memory graph.
- `cosheaf.memory.write_memory_graph_snapshot(context: RepoContext, snapshot: MemoryGraphSnapshot) -> Path`:
  writes the deterministic rebuildable graph sidecar.
- `cosheaf.memory.MEMORY_GRAPH_SIDECAR`: repository-relative graph sidecar path,
  `.cosheaf/memory/graph_snapshot.json`.

The card builder and search read existing YAML records through the storage
loader. Search uses an in-memory SQLite FTS5 table and in-memory memory graph
ranking when available and does not write `.cosheaf/memory/` sidecars. Memory
graph build writes only the rebuildable graph snapshot sidecar, and PageRank
reads that sidecar without implicitly rebuilding it. The memory package does
not add embeddings, context-pack v2 behavior, hosted LLM workers,
accepted-promotion shortcuts, formal checking, or artifact schema changes. By
default, configured private KB roots are excluded from `cosheaf memory cards`
and `cosheaf memory search`; callers must not treat memory output as accepted
knowledge or human review.

#### Core Enums

- `cosheaf.core.status.ArtifactType`: artifact type enum.
- `cosheaf.core.status.ArtifactStatus`: artifact lifecycle status enum.
- `cosheaf.core.task.WorkerType`: protocol worker type enum, re-exported through `cosheaf.agent.task.WorkerType`.
- `cosheaf.core.task.TaskStatus`: task lifecycle status enum, re-exported through `cosheaf.agent.task.TaskStatus`.
- `cosheaf.memory.MemoryRootScope`: memory root scope enum with values
  `public`, `private`, `workspace`, and `framework`.
- `cosheaf.memory.ArtifactCardType`: artifact-card type enum with values
  `definition`, `theorem`, `claim`, `conjecture`, `proof`, `proof_attempt`,
  `construction`, `algorithm`, `reduction`, `counterexample`, `experiment`,
  `review`, `verifier`, `issue`, and `source_note`.
- `cosheaf.memory.ArtifactCardStatus`: artifact-card lifecycle/trust status enum
  with values `raw`, `draft`, `locally_tested`, `adversarially_tested`,
  `machine_checked`, `human_reviewed`, `accepted`, `refuted`, `obsolete`, and
  `superseded`.
- `cosheaf.memory.RetrievalRole`: retrieval caller role enum with values
  `librarian`, `orchestrator`, `reasoner`, `verifier`, `formalizer`,
  `literature_scout`, `counterexampleer`, and `construction_searcher`.

#### Core Helpers

- `cosheaf.core.ids.validate_artifact_id(value: str) -> str`
  - IDs are dot-separated. The first segment must be a lowercase slug; later
    segments may be lowercase slugs or numeric version/index segments such as
    `0001`.
- `cosheaf.core.artifact.is_external_dependency_ref(value: str) -> bool`
- `cosheaf.core.artifact.validate_dependency_ref(value: str) -> str`
  - Dependency references are either local artifact IDs or explicit external
    references beginning with `external:`.
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

These helpers are pure validation, path-formatting, status-classification, or deterministic ID/reference helpers. They do not scan the repository, use SQLite, or run gatekeeper behavior.

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
ID, type, status, path, title, domain, source KB root, dependency rows,
formalization rows, and artifact formal-policy rows. The manifest is ordered
deterministically by artifact ID and dependency tuple.

SQLite tables:

- `artifacts(id, type, status, path, title, domain, kb_root)`
- `dependencies(source_id, target_id)`
- `formalizations(artifact_id, formalization_id, system, library, library_ref,
  import_path, symbol, declaration_kind, status, check_mode, expected_type,
  notes)`
- `artifact_formal_policy(artifact_id, alignment_status, alignment_reviewer,
  verification_level, require_formal_link, require_lean_check,
  require_alignment_review)`

`formalizations` has a primary key on `(artifact_id, formalization_id)` and
indexes on `symbol`, `library`, `status`, and `import_path`. The manifest
includes per-artifact `formalizations`, `alignment_status`, and
`verification_policy` fields. These are metadata-only generated surfaces; they
do not run Lean or check external library symbol existence.

#### Storage Query

- `cosheaf.storage.query.ArtifactQueryRow`: immutable row with `id`, `type`,
  `status`, `path`, `title`, `domain`, and `kb_root`.
- `cosheaf.storage.query.DependencyQueryRow`: immutable dependency edge row
  with `source_id` and `target_id`.
- `cosheaf.storage.query.FormalizationQueryRow`: immutable formalization row
  with `artifact_id`, `formalization_id`, `system`, `library`, `library_ref`,
  `import_path`, `symbol`, `declaration_kind`, `status`, `check_mode`,
  `expected_type`, and `notes`.
- `cosheaf.storage.query.FormalPolicyQueryRow`: immutable formal policy row
  with `artifact_id`, `alignment_status`, `alignment_reviewer`,
  `verification_level`, `require_formal_link`, `require_lean_check`, and
  `require_alignment_review`.
- `cosheaf.storage.query.IndexQueryError`: expected query-layer error.
- `cosheaf.storage.query.ArtifactIndexQuery(sqlite_path: str | Path)`: read-only
  SQLite query facade over `.cosheaf/index.sqlite`.
- `cosheaf.storage.query.ArtifactIndexQuery.from_context(context: RepoContext) -> ArtifactIndexQuery`
- `cosheaf.storage.query.ArtifactIndexQuery.from_repo_root(repo_root: str | Path) -> ArtifactIndexQuery`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts() -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.get_artifact(artifact_id: str) -> ArtifactQueryRow | None`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_by_status(status: ArtifactStatus | str) -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_by_type(artifact_type: ArtifactType | str) -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_by_domain(domain: str) -> tuple[ArtifactQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_dependencies(artifact_id: str) -> tuple[DependencyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_reverse_dependencies(artifact_id: str) -> tuple[DependencyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations() -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_for_artifact(artifact_id: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_library(library: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_symbol(symbol: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_status(status: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_formalizations_by_import(import_path: str) -> tuple[FormalizationQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.get_formal_policy(artifact_id: str) -> FormalPolicyQueryRow | None`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_requiring_formal_link() -> tuple[FormalPolicyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_requiring_lean_check() -> tuple[FormalPolicyQueryRow, ...]`
- `cosheaf.storage.query.ArtifactIndexQuery.list_artifacts_requiring_alignment_review() -> tuple[FormalPolicyQueryRow, ...]`

The query API reads the deterministic SQLite output produced by
`rebuild_index`; it does not parse YAML, rebuild indexes implicitly, or modify
repository files. Result ordering is deterministic. `ArtifactQueryRow.kb_root`
contains the indexed source KB root, such as `default`, `public`, or `private`,
and is empty when a row was indexed outside a KB root. Formalization query
methods are metadata-only and do not execute Lean, fetch external libraries, or
check CSLib/mathlib symbol existence.

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
- `cosheaf.gates.source_metadata_gate.SourceMetadataCheck`: one accepted public artifact source metadata check row.
- `cosheaf.gates.source_metadata_gate.SourceMetadataResult`: aggregate source metadata policy gate result.
- `cosheaf.gates.source_metadata_gate.missing_required_source_metadata(artifact: BaseArtifact) -> tuple[str, ...]`: returns missing required source metadata fields for an artifact.
- `cosheaf.gates.source_metadata_gate.validate_source_metadata_policy(context: RepoContext, records: tuple[LoadedRecord, ...]) -> SourceMetadataResult`
- `cosheaf.gates.formal_link_gate.FormalLinkCheck`: one static formal-link metadata check row.
- `cosheaf.gates.formal_link_gate.FormalLinkResult`: aggregate formal-link metadata policy gate result.
- `cosheaf.gates.formal_link_gate.validate_formal_link_policy(records: tuple[LoadedRecord, ...]) -> FormalLinkResult`
- `cosheaf.gates.gatekeeper.ValidationReport`: validation report with loaded records and failures.
- `cosheaf.gates.gatekeeper.validate_repository(context: RepoContext) -> ValidationReport`
- `cosheaf.gates.gatekeeper.validate_artifact_file(context: RepoContext, path: Path) -> ValidationReport`
- `cosheaf.gates.gatekeeper.GateIssue`: blocking or nonblocking gatekeeper issue row.
- `cosheaf.gates.gatekeeper.GateResult`: one gate result in a gatekeeper run, including optional machine-readable `details`.
- `cosheaf.gates.gatekeeper.GatekeeperReport`: machine-readable gatekeeper report.
- `cosheaf.gates.gatekeeper.GatekeeperRunResult`: report and written report paths.
- `cosheaf.gates.gatekeeper.GateStatus`: gate status literal type.
- `cosheaf.gates.gatekeeper.GateVerdict`: gatekeeper verdict literal type.
- `cosheaf.gates.gatekeeper.REQUIRED_PR_CHECKLIST_SECTIONS`: ordered tuple of required G8 PR checklist section names.
- `cosheaf.gates.gatekeeper.run_gatekeeper(context: RepoContext, *, persist_review: bool = False, pr_checklist_path: Path | None = None, timestamp: str | None = None) -> GatekeeperRunResult`

The dependency gate validates missing dependencies, accepted-to-draft
dependencies across KB roots, and public-artifact-to-private-artifact
dependencies.

The validation orchestrator is deterministic and filesystem-backed.
`validate_repository` does not run verifier adapters. It treats dependency
references beginning with `external:` as explicit external references rather
than missing local artifacts. `run_gatekeeper` runs G1-G5 validation gates, runs
the G6 verifier gate through the default verifier registry, runs the G7
reproducibility metadata gate over executable evidence and verifier results,
runs the G8 PR checklist gate, runs the G9 source metadata gate, and runs the
G10 formal link gate. G8 is `skipped` when
`pr_checklist_path`/`--pr-checklist` is omitted, `fail` when the explicit local
markdown checklist is missing required sections, and `pass` when all required
sections are present. G9 is `fail` when accepted artifacts in configured public
KB roots are missing complete source metadata while `accepted_requires_source`
is true, `pass` when applicable accepted public artifacts are complete, and
`not_applicable` for legacy mode, disabled source policy, or no accepted public
artifacts. G10 is `not_applicable` when no artifact has formal-link policy
metadata to check, `fail` when static policy consistency is violated, and
`pass` when applicable formal-link metadata has no blocking issue. G10 warnings
are emitted as nonblocking issues and are not proof failures. It does not call
GitHub, require network access, run Lean, fetch external libraries, or inspect
CSLib/mathlib references recorded in `formalizations`; alignment review remains
separate from Lean checking. It writes JSON and Markdown reports under
`.cosheaf/reports/` by default.

G9 `GateResult.details` entries use:

- `artifact_id`
- `source_path`
- `kb_root`
- `status`
- `source_count`
- `missing_metadata`

G10 `GateResult.details` entries use:

- `artifact_id`
- `source_path`
- `artifact_status`
- `policy_level`
- `require_formal_link`
- `require_lean_check`
- `require_alignment_review`
- `formalization_count`
- `checked_formalization_count`
- `alignment_status`
- `status`
- `blocking_messages`
- `warning_messages`

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
ranking reasons. When a relevant artifact has formal-link metadata or
policy-relevant formal settings, the artifact entry also includes compact
formal-link metadata lines:

- `Formal links:` entries ordered by formalization ID, rendered as
  `<library>@<library_ref>:<import_path>#<symbol> [<kind>, <status>, <mode>]`
- `Alignment: <status>; reviewer=<reviewer-or-dash>`
- `Verification policy: <level>; formal_link=<bool>; lean_check=<bool>;
  alignment_review=<bool>`
- `G10-relevant: yes; ...` static hints derived from artifact metadata

These context-pack lines are metadata-only handoff context. They do not load
gate reports, do not claim the current G10 verdict, and do not claim Lean
verification.

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
- `cosheaf.agent.local_runner.LocalWorkerRunner`: filesystem-backed local runner for existing task records. It executes explicit command argv lists with `shell=False`, rejects `cwd` and `bundle_path` values outside the repository, enforces timeouts, captures stdout/stderr, writes deterministic run records, optionally validates worker output bundles, and never merges outputs or promotes accepted knowledge.
- `cosheaf.agent.local_runner.LocalWorkerRunConfig`: dataclass for one run with fields `command`, `timeout_seconds`, `cwd`, `bundle_path`, `run_id`, and `started_at`.
- `cosheaf.agent.local_runner.LocalWorkerRunResult`: dataclass containing `task`, `run_id`, `status`, `returncode`, `run_dir`, `record_path`, `stdout_path`, `stderr_path`, and `bundle_valid`.
- `cosheaf.agent.local_runner.LocalWorkerRunError`: expected local runner failure, including missing tasks, invalid argv, invalid timeouts, invalid run IDs, `cwd` outside the repository, and `bundle_path` outside the repository.

Task records are written under:

- `.cosheaf/tasks/<task-id>.yaml`

Local worker run records are written under:

- `.cosheaf/tasks/<task-id>/runs/<run-id>/run.yaml`
- `.cosheaf/tasks/<task-id>/runs/<run-id>/stdout.txt`
- `.cosheaf/tasks/<task-id>/runs/<run-id>/stderr.txt`

Local worker run record YAML fields are:

- `schema_version`
- `task_id`
- `worker_type`
- `command`
- `cwd`
- `started_at`
- `finished_at`
- `timeout_seconds`
- `returncode`
- `stdout_path`
- `stderr_path`
- `bundle_path`
- `bundle_valid`
- `status`

Local worker run status values are:

- `completed`
- `failed`
- `timed_out`
- `bundle_invalid`

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
- `cosheaf.verification.sat_adapter.SatBackendResult`: normalized SAT backend invocation result.
- `cosheaf.verification.sat_adapter.SatBackend`: protocol for optional SAT backends.
- `cosheaf.verification.sat_adapter.ExternalSatCommandBackend`: optional external-command SAT backend.
- `cosheaf.verification.sat_adapter.SatAdapter`: optional minimal SAT DIMACS verifier adapter.
- `cosheaf.verification.smt_adapter.SmtBackendResult`: normalized SMT backend invocation result.
- `cosheaf.verification.smt_adapter.SmtBackend`: protocol for optional SMT backends.
- `cosheaf.verification.smt_adapter.ExternalSmtCommandBackend`: optional external-command SMT backend.
- `cosheaf.verification.smt_adapter.SmtAdapter`: optional minimal SMT-LIB verifier adapter.
- `cosheaf.verification.lean_adapter.LeanBackendResult`: normalized Lean backend invocation result.
- `cosheaf.verification.lean_adapter.LeanBackend`: protocol for optional Lean backends.
- `cosheaf.verification.lean_adapter.ExternalLeanCommandBackend`: optional external-command Lean backend.
- `cosheaf.verification.lean_adapter.LeanAdapter`: optional minimal Lean verifier adapter.

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
- `__init__(solver_command: str = "kissat", *, backend: SatBackend | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `sat`, `sat_solver`, and `sat_checker`. It first
requires the SAT evidence path to resolve inside the repository. When no
backend is supplied, it uses `ExternalSatCommandBackend` with the configured
solver command, defaulting to `kissat`. If no supported backend is available,
the adapter returns `skipped`, which is not a pass. If a backend is available,
the adapter runs the backend from the repository root against the DIMACS CNF
evidence, writes stdout and stderr logs under `.cosheaf/logs/`, parses
`sat`/`unsat`/`unknown`, compares against `CHECKER_DATA.expected.satisfiable`
when present, and returns normalized `pass`, `fail`, or `error` results with
command, cwd, timeout, input/output paths, backend metadata, exit code, and
result diagnostics.

`SatBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`
- `result: Literal["sat", "unsat", "unknown"]`

`SatBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(cnf_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(cnf_path: Path, *, cwd: Path, timeout_seconds: float) -> SatBackendResult`

`ExternalSatCommandBackend` exposes:

- `__init__(solver_command: str = "kissat")`
- `name`
- `solver_command`
- `is_available() -> bool`
- `command(cnf_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(cnf_path: Path, *, cwd: Path, timeout_seconds: float) -> SatBackendResult`

The external backend detects availability with PATH lookup, obtains version
metadata from `<solver> --version` when possible, runs the solver with the
repository root as cwd, and parses common SAT solver output or exit codes:
`sat` from output containing SAT or exit code `10`, `unsat` from output
containing UNSAT or exit code `20`, and `unknown` otherwise.

`SmtAdapter` exposes:

- `name = "smt"`
- `__init__(solver_command: str = "z3", *, backend: SmtBackend | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `smt`, `smt_solver`, and `smt_checker`. It first
requires the SMT evidence path to resolve inside the repository. When no
backend is supplied, it uses `ExternalSmtCommandBackend` with the configured
solver command, defaulting to `z3`. If no supported backend is available, the
adapter returns `skipped`, which is not a pass. If a backend is available, the
adapter runs the backend from the repository root against the SMT-LIB evidence,
writes stdout and stderr logs under `.cosheaf/logs/`, parses exact
`sat`/`unsat`/`unknown` status lines, compares against
`CHECKER_DATA.expected.satisfiable` when present, and returns normalized
`pass`, `fail`, or `error` results with command, cwd, timeout, input/output
paths, backend metadata, exit code, and result diagnostics.

`SmtBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`
- `result: Literal["sat", "unsat", "unknown"]`

`SmtBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(smt_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(smt_path: Path, *, cwd: Path, timeout_seconds: float) -> SmtBackendResult`

`ExternalSmtCommandBackend` exposes:

- `__init__(solver_command: str = "z3")`
- `name`
- `solver_command`
- `is_available() -> bool`
- `command(smt_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `solve(smt_path: Path, *, cwd: Path, timeout_seconds: float) -> SmtBackendResult`

The external backend detects availability with PATH lookup, obtains version
metadata from `<solver> --version` when possible, runs `z3 -smt2 <file.smt2>`
style commands with the repository root as cwd, and parses solver output only
from exact status lines: `sat`, `unsat`, or `unknown`.

`LeanAdapter` exposes:

- `name = "lean"`
- `__init__(lean_command: str = "lean", *, backend: LeanBackend | None = None, timeout_seconds: float = 30.0)`
- `can_verify(artifact: BaseArtifact, repo: RepoContext) -> bool`
- `verify(artifact: BaseArtifact, repo: RepoContext) -> VerificationResult`

It recognizes evidence kinds `lean`, `lean4`, `lean_checker`, and
`lean_proof`. It first requires the Lean evidence path to resolve inside the
repository and requires the referenced file to exist. When no backend is
supplied, it uses `ExternalLeanCommandBackend` with the configured Lean command,
defaulting to `lean`. If no supported backend is available, the adapter returns
`skipped`, which is not a pass. If a backend is available, the adapter runs the
backend from the repository root against the plain Lean file, writes stdout and
stderr logs under `.cosheaf/logs/`, and returns normalized `pass`, `fail`, or
`error` results with command, cwd, timeout, input/output paths, backend
metadata, exit code, and diagnostics. Exit code `0` is `pass`, nonzero exit
code is `fail`, and timeout or startup errors are `error`. The adapter does not
autoformalize natural language and does not implement SAT or SMT behavior.

`LeanBackendResult` exposes:

- `exit_code: int | None`
- `stdout: str`
- `stderr: str`

`LeanBackend` requires:

- `name: str`
- `is_available() -> bool`
- `command(lean_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `check(lean_path: Path, *, cwd: Path, timeout_seconds: float) -> LeanBackendResult`

`ExternalLeanCommandBackend` exposes:

- `__init__(lean_command: str = "lean")`
- `name`
- `lean_command`
- `is_available() -> bool`
- `command(lean_path: Path) -> tuple[str, ...]`
- `version() -> str | None`
- `check(lean_path: Path, *, cwd: Path, timeout_seconds: float) -> LeanBackendResult`

The external backend detects availability with PATH lookup, obtains version
metadata from `lean --version` when possible, and runs `lean <file.lean>` with
the repository root as cwd.

### Makefile Targets

- `make lint`: runs `python -m ruff check .`
- `make typecheck`: runs `python -m mypy cosheaf tests`
- `make test`: runs `python -m pytest`
- `make validate`: runs `python -m cosheaf.cli validate`.
- `make gate`: runs `python -m cosheaf.cli gate`, which defaults to a real gatekeeper run.

### Schemas

- `schemas/artifact.schema.json`: artifact YAML schema. Inline
  `review.state` accepts `none`, `requested`, `in_review`, `approved`,
  `changes_requested`, `human_reviewed`, and `accepted`; accepted promotion
  requires `human_reviewed` or `accepted`. Artifact `depends_on` accepts local
  artifact IDs and explicit external references beginning with `external:`.
  Artifact `sources` accepts structured source metadata entries with `kind`,
  `title`, `authors`, `year`, `doi`, `arxiv`, `url`, `theorem_number`, `page`,
  and `notes`. Artifact `formalizations` accepts strict formal declaration
  reference entries with `system`, `library`, `import_path`, `symbol`,
  `declaration_kind`, `status`, `check_mode`, `expected_type`, and `notes`.
  Artifact `alignment` accepts semantic alignment review metadata. Artifact
  `verification_policy` accepts formal-link, Lean-check, and alignment-review
  policy metadata. Formalization references are separate from `evidence`; this
  schema does not add formal-link CLI commands or verifier execution, but G10,
  context packs, and the deterministic index/query surfaces read this metadata.
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
  complete structured source metadata in configured public KB roots.

## Registration Rule

Future public interface changes must be recorded here. Public interfaces include CLI commands, Python APIs, artifact schemas, gate result formats, verifier adapter contracts, context pack formats, and documented file layouts.
