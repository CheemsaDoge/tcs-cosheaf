# Interface Registry

## Current Public Python Interfaces

### CLI Entry Point

- Entry point: `cosheaf`
- Implementation: `cosheaf.cli:app`
- Framework: Typer

### CLI Commands

- `cosheaf --help`: shows CLI help.
- `cosheaf version`: prints the package version.
- `cosheaf validate`: scaffold-only placeholder. It reports that artifact schema validation is not implemented yet and that no artifacts were checked.
- `cosheaf gate`: scaffold-only placeholder. It reports that gatekeeper enforcement is not implemented yet and that no repository gates were enforced.

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

Storage does not use SQLite and does not implement gatekeeper behavior.

### Makefile Targets

- `make lint`: runs `python -m ruff check .`
- `make typecheck`: runs `python -m mypy cosheaf tests`
- `make test`: runs `python -m pytest`
- `make validate`: runs the scaffold-only CLI validation placeholder.
- `make gate`: runs the scaffold-only CLI gate placeholder.

## Registration Rule

Future public interface changes must be recorded here. Public interfaces include CLI commands, Python APIs, artifact schemas, gate result formats, verifier adapter contracts, context pack formats, and documented file layouts.
