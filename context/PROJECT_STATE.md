# Project State

## Current State After Task 009

TCS-Cosheaf is in pre-MVP scaffold state. The repository contains project governance documentation, a short README, a Python-oriented `.gitignore`, the durable documentation skeleton, the minimal Python project scaffold, the initial repository directory layout, initial JSON Schema files, example YAML artifacts, initial Pydantic v2 core artifact models, filesystem-backed storage loading utilities, initial repository validation gates, an artifact dependency graph, deterministic repository index rebuilds, and gatekeeper report generation.

The Python scaffold defines a `cosheaf` package, a Typer-based `cosheaf` CLI entry point, development dependencies, Makefile targets, a Dockerfile for reproducible local development, and smoke tests for import and CLI help/version behavior.

The filesystem layout now includes accepted and draft knowledge-base directories, refuted and obsolete artifact areas, issue directories, experiment directories, and review directories. The initial schemas live under `schemas/`, and examples live under `examples/`.

The core model layer now defines artifact type and status enums, base artifact data models, artifact ID validation, timestamp validation, risk/evidence/review value objects, and pure status/path helper functions.

The storage layer defines `RepoContext`, YAML discovery under `kb/`, `issues/`, and `examples/`, typed YAML loading into `BaseArtifact`, `IssueRecord`, or `ReviewRecord`, repository-relative source paths on loaded records, deterministic ordering by path then ID, clear load errors, and deterministic YAML writing helpers.

The validation CLI implements repository validation for YAML parse/model parse, ID uniqueness, status/path consistency, dependency existence, accepted-artifact-to-draft-artifact dependencies, and local evidence path existence. Expected validation failures produce concise Rich output and nonzero exit codes without stack traces unless `--debug` is used.

The graph layer builds directed dependency edges from artifact to dependency, detects missing dependencies, detects directed cycles, and reports accepted artifacts depending on draft or otherwise pre-accepted artifacts.

The index rebuild command writes `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json` from scratch. The SQLite index stores artifact ID, type, status, path, title, and domain, plus deterministic dependency rows. The manifest ordering is deterministic and stable across delete-and-rebuild cycles.

The gatekeeper command runs G1-G5 implemented gates and G6-G8 placeholder gates. It writes JSON and Markdown reports to `.cosheaf/reports/` by default, can persist copies under `reviews/gatekeeper/` with `--persist-review`, and exits nonzero when blocking issues exist. Placeholder gates are reported as skipped and do not pretend to pass.

No verifier adapters exist yet. No CI configuration exists yet.

## Implemented

- Project-wide engineering rules in `AGENTS.md`.
- Pre-MVP overview in `README.md`.
- Documentation skeleton under `docs/`.
- Initial ADRs under `docs/ADR/`.
- Context skeleton under `context/`.
- Python project metadata in `pyproject.toml`.
- Minimal `cosheaf` package and CLI.
- Makefile targets for `lint`, `typecheck`, `test`, `validate`, and `gate`.
- Implemented `cosheaf validate` repository validation CLI.
- Implemented `cosheaf artifact validate <path>` single-file validation CLI.
- Implemented `cosheaf index rebuild` deterministic repository index rebuild CLI.
- Implemented `cosheaf graph show` dependency graph inspection CLI.
- Implemented `cosheaf gate run` gatekeeper report CLI.
- Implemented `cosheaf gate` default gatekeeper run for the existing `make gate` target.
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
- Initial validation gates under `cosheaf/gates/`.
- Validation CLI tests in `tests/test_validate_cli.py` and `tests/test_status_path_validation.py`.
- Dependency graph utilities under `cosheaf/graph/`.
- Deterministic SQLite and manifest index rebuild in `cosheaf/storage/index.py`.
- Graph and index tests in `tests/test_claim_graph.py` and `tests/test_index_rebuild.py`.
- Gatekeeper reports in `cosheaf/gates/gatekeeper.py`.
- Gatekeeper tests in `tests/test_gatekeeper.py`.

## Not Implemented Yet

- SQLite-backed query API beyond deterministic index rebuild output.
- Verifier adapters.
- Verifier gate, reproducibility metadata gate, and PR checklist gate beyond skipped placeholders.
- CI.
