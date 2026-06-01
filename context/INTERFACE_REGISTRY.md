# Interface Registry

## Current Public Python Interfaces

### CLI Entry Point

- Entry point: `cosheaf`
- Implementation: `cosheaf.cli:app`
- Framework: Typer

### CLI Commands

- `cosheaf --help`: shows CLI help.
- `cosheaf version`: prints the package version.
- `cosheaf validate`: validates repository YAML records discovered under `kb/`, `issues/`, and `examples/`.
- `cosheaf validate --repo-root <path>`: validates a repository rooted at `<path>`.
- `cosheaf validate --debug`: shows tracebacks for unexpected validation errors.
- `cosheaf artifact validate <path>`: validates one YAML file with file-local checks.
- `cosheaf artifact validate <path> --repo-root <path>`: resolves the artifact path against an explicit repository root.
- `cosheaf artifact validate <path> --debug`: shows tracebacks for unexpected validation errors.
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

### Python API

#### Core Models

- `cosheaf.core.artifact.BaseArtifact`: Pydantic v2 base model for typed artifacts.
- `cosheaf.core.artifact.Evidence`: Pydantic v2 model for evidence references.
- `cosheaf.core.artifact.Risk`: Pydantic v2 model for artifact risk metadata.
- `cosheaf.core.artifact.ReviewRef`: Pydantic v2 model for inline review state.

#### Core Enums

- `cosheaf.core.status.ArtifactType`: artifact type enum.
- `cosheaf.core.status.ArtifactStatus`: artifact lifecycle status enum.

#### Core Helpers

- `cosheaf.core.ids.validate_artifact_id(value: str) -> str`
- `cosheaf.core.paths.normalize_repo_path(path: str | Path) -> str`
- `cosheaf.core.paths.repo_relative_path(repo_root: Path, path: Path) -> Path`
- `cosheaf.core.paths.repo_relative_posix(repo_root: Path, path: Path) -> str`
- `cosheaf.core.paths.is_yaml_path(path: Path) -> bool`
- `cosheaf.core.status.is_terminal_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.is_preaccepted_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.is_accepted_status(status: ArtifactStatus) -> bool`
- `cosheaf.core.status.expected_status_for_path(path: str) -> frozenset[ArtifactStatus]`

These helpers are pure path-classification or path-formatting helpers. They do not scan the repository, use SQLite, or run gatekeeper behavior.

#### Storage Models and Context

- `cosheaf.storage.repo.RepoContext`: immutable filesystem repository context with `repo_root`.
- `cosheaf.storage.loader.IssueRecord`: Pydantic v2 model for issue YAML records loaded by storage.
- `cosheaf.storage.loader.ReviewRecord`: Pydantic v2 model for review YAML records loaded by storage.
- `cosheaf.storage.loader.LoadedRecord`: loaded record wrapper with repository-relative `source_path` and typed `record`.

#### Storage Loader

- `cosheaf.storage.loader.discover_yaml_paths(context: RepoContext) -> list[Path]`
- `cosheaf.storage.loader.load_yaml_file(context: RepoContext, path: Path) -> LoadedRecord`
- `cosheaf.storage.loader.load_artifacts(context: RepoContext) -> list[LoadedRecord]`

The loader discovers `.yaml` and `.yml` files under `kb/`, `issues/`, and `examples/`, parses YAML without swallowing parse errors, and returns loaded records in deterministic order by source path then ID.

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
ID, type, status, path, title, domain, and dependency rows. The manifest is
ordered deterministically by artifact ID and dependency tuple.

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
- `cosheaf.gates.gatekeeper.ValidationReport`: validation report with loaded records and failures.
- `cosheaf.gates.gatekeeper.validate_repository(context: RepoContext) -> ValidationReport`
- `cosheaf.gates.gatekeeper.validate_artifact_file(context: RepoContext, path: Path) -> ValidationReport`
- `cosheaf.gates.gatekeeper.GateIssue`: blocking or nonblocking gatekeeper issue row.
- `cosheaf.gates.gatekeeper.GateResult`: one gate result in a gatekeeper run.
- `cosheaf.gates.gatekeeper.GatekeeperReport`: machine-readable gatekeeper report.
- `cosheaf.gates.gatekeeper.GatekeeperRunResult`: report and written report paths.
- `cosheaf.gates.gatekeeper.GateStatus`: gate status literal type.
- `cosheaf.gates.gatekeeper.GateVerdict`: gatekeeper verdict literal type.
- `cosheaf.gates.gatekeeper.run_gatekeeper(context: RepoContext, *, persist_review: bool = False, timestamp: str | None = None) -> GatekeeperRunResult`

The initial validation orchestrator is deterministic and filesystem-backed. It
does not run verifier adapters. `run_gatekeeper` currently runs G1-G5 gates and
records G6-G8 as skipped placeholders, writing JSON and Markdown reports under
`.cosheaf/reports/` by default.

### Makefile Targets

- `make lint`: runs `python -m ruff check .`
- `make typecheck`: runs `python -m mypy cosheaf tests`
- `make test`: runs `python -m pytest`
- `make validate`: runs `python -m cosheaf.cli validate`.
- `make gate`: runs `python -m cosheaf.cli gate`, which defaults to a real gatekeeper run.

## Registration Rule

Future public interface changes must be recorded here. Public interfaces include CLI commands, Python APIs, artifact schemas, gate result formats, verifier adapter contracts, context pack formats, and documented file layouts.
