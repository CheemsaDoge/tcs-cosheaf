# Project State

## Current State After Task 006

TCS-Cosheaf is in pre-MVP scaffold state. The repository contains project governance documentation, a short README, a Python-oriented `.gitignore`, the durable documentation skeleton, the minimal Python project scaffold, the initial repository directory layout, initial JSON Schema files, example YAML artifacts, initial Pydantic v2 core artifact models, and filesystem-backed storage loading utilities.

The Python scaffold defines a `cosheaf` package, a Typer-based `cosheaf` CLI entry point, development dependencies, Makefile targets, a Dockerfile for reproducible local development, and smoke tests for import and CLI help/version behavior.

The filesystem layout now includes accepted and draft knowledge-base directories, refuted and obsolete artifact areas, issue directories, experiment directories, and review directories. The initial schemas live under `schemas/`, and examples live under `examples/`.

The core model layer now defines artifact type and status enums, base artifact data models, artifact ID validation, timestamp validation, risk/evidence/review value objects, and pure status/path helper functions.

The storage layer now defines `RepoContext`, YAML discovery under `kb/`, `issues/`, and `examples/`, typed YAML loading into `BaseArtifact`, `IssueRecord`, or `ReviewRecord`, repository-relative source paths on loaded records, deterministic ordering by path then ID, clear load errors, and deterministic YAML writing helpers.

No SQLite storage exists yet. No dependency graph exists yet. No CLI schema validation exists yet. No gatekeeper implementation exists yet. No verifier adapters exist yet. No CI configuration exists yet.

## Implemented

- Project-wide engineering rules in `AGENTS.md`.
- Pre-MVP overview in `README.md`.
- Documentation skeleton under `docs/`.
- Initial ADRs under `docs/ADR/`.
- Context skeleton under `context/`.
- Python project metadata in `pyproject.toml`.
- Minimal `cosheaf` package and CLI.
- Makefile targets for `lint`, `typecheck`, `test`, `validate`, and `gate`.
- Scaffold-only `validate` and `gate` CLI placeholders that explicitly report that full validation and gatekeeper enforcement are not implemented.
- Dockerfile for local development.
- Smoke tests under `tests/`.
- Repository layout under `kb/`, `issues/`, `experiments/`, and `reviews/`.
- JSON Schema files under `schemas/`.
- Example YAML artifacts under `examples/`.
- Schema/example filesystem smoke tests in `tests/test_schema_files_exist.py`.
- Pydantic v2 core models under `cosheaf/core/`.
- Artifact status/path helper functions that do not scan the repository.
- Model tests in `tests/test_artifact_models.py`.
- Repository path helpers in `cosheaf/core/paths.py`.
- Filesystem-backed storage context, loader, and writer under `cosheaf/storage/`.
- Storage loader tests and fixtures in `tests/test_loader.py` and `tests/fixtures/`.

## Not Implemented Yet

- SQLite storage.
- Dependency graph.
- Gatekeeper.
- Verifier adapters.
- CLI schema validation.
- Non-placeholder validation and gate enforcement.
- CI.
