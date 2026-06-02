# Project State

## Current State After Task 014

TCS-Cosheaf is in pre-MVP scaffold state. The repository contains project governance documentation, a short README, a Python-oriented `.gitignore`, the durable documentation skeleton, the minimal Python project scaffold, the initial repository directory layout, initial JSON Schema files, example YAML artifacts, initial Pydantic v2 core artifact models, filesystem-backed storage loading utilities, initial repository validation gates, an artifact dependency graph, deterministic repository index rebuilds, gatekeeper report generation, issue-scoped context pack generation, the initial verifier adapter interface, a Python checker verifier adapter, optional-tool SAT/SMT/Lean verifier skeleton adapters, GitHub Actions CI, and GitHub collaboration templates.

The Python scaffold defines a `cosheaf` package, a Typer-based `cosheaf` CLI entry point, development dependencies, Makefile targets, a Dockerfile for reproducible local development, and smoke tests for import and CLI help/version behavior.

The filesystem layout now includes accepted and draft knowledge-base directories, refuted and obsolete artifact areas, issue directories, experiment directories, and review directories. The initial schemas live under `schemas/`, and examples live under `examples/`.

The core model layer now defines artifact type and status enums, base artifact data models, artifact ID validation, timestamp validation, risk/evidence/review value objects, and pure status/path helper functions.

The storage layer defines `RepoContext`, YAML discovery under `kb/`, `issues/`, and `examples/`, typed YAML loading into `BaseArtifact`, `IssueRecord`, or `ReviewRecord`, repository-relative source paths on loaded records, deterministic ordering by path then ID, clear load errors, and deterministic YAML writing helpers.

The validation CLI implements repository validation for YAML parse/model parse, ID uniqueness, status/path consistency, dependency existence, accepted-artifact-to-draft-artifact dependencies, and local evidence path existence. Expected validation failures produce concise Rich output and nonzero exit codes without stack traces unless `--debug` is used.

The graph layer builds directed dependency edges from artifact to dependency, detects missing dependencies, detects directed cycles, and reports accepted artifacts depending on draft or otherwise pre-accepted artifacts.

The index rebuild command writes `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json` from scratch. The SQLite index stores artifact ID, type, status, path, title, and domain, plus deterministic dependency rows. The manifest ordering is deterministic and stable across delete-and-rebuild cycles.

The gatekeeper command runs G1-G5 implemented gates, the G6 verifier gate, and
G7-G8 placeholder gates. It writes JSON and Markdown reports to
`.cosheaf/reports/` by default, can persist copies under `reviews/gatekeeper/`
with `--persist-review`, and exits nonzero when blocking issues exist.
Placeholder gates are reported as skipped and do not pretend to pass.

The agent harness layer now builds bounded deterministic context packs for issue IDs. Context packs are written under `context/TASKS/<issue-id>/` and include `CONTEXT.md`, `ACCEPTANCE.md`, `RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`, and `COMMANDS.md`. Relevant artifacts are selected from the issue's related artifacts plus one dependency hop; draft artifacts are visibly labeled.

The verification layer now defines the `VerifierAdapter` protocol, normalized `VerificationResult` model, `VerificationStatus` enum, instance-local `VerifierRegistry`, and `PythonCheckerAdapter`. Verification results distinguish `pass`, `fail`, `error`, and `skipped`; command-backed results record command and working directory metadata.

The Python checker adapter runs `kind: python_checker` evidence from the repository root, enforces a timeout, writes stdout/stderr logs under `.cosheaf/logs/`, and records command metadata in `VerificationResult`. The gatekeeper G6 verifier gate now runs the default verifier registry and reports Python checker results. G6 is skipped only when no verifier adapters are applicable.

The SAT, SMT, and Lean adapters are optional-tool skeletons. They check for configured solver/tool availability, return `skipped` when the tool is unavailable, and do not add hard dependencies on Lean, Z3, cvc5, Sage, or PySAT. They are registered in the default verifier registry but do not run unless an artifact has matching SAT, SMT, or Lean evidence.

No real SAT, SMT, or Lean verification execution exists yet.

GitHub Actions CI is configured to run on pull requests and pushes to `main`
with Python 3.11. It installs the package with development dependencies and
runs `make lint`, `make typecheck`, `make test`, `make validate`, and
`make gate` as separate status checks. The CI workflow does not install
optional external formal tools.

GitHub issue templates now cover feature tasks, bug tasks, and research issues.
The pull request template requires summary, changed files, tests run, risks,
interface changes, documentation changes, artifact/schema changes, and the
gatekeeper result.

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
- Context pack generation in `cosheaf/agent/context_pack.py`.
- Context pack CLI commands `cosheaf context build <issue-id>` and `cosheaf context show <issue-id>`.
- Context pack tests in `tests/test_context_pack.py`.
- Verifier adapter protocol in `cosheaf/verification/base.py`.
- Normalized verification result model in `cosheaf/verification/result.py`.
- Instance-local verifier registry in `cosheaf/verification/registry.py`.
- Verification result and registry tests in `tests/test_verification_result.py`.
- Python checker verifier adapter in `cosheaf/verification/python_checker.py`.
- Python checker evaluator example in `experiments/evaluators/check_graph_example.py`.
- Python checker tests in `tests/test_python_checker.py`.
- Gatekeeper G6 verifier gate execution for the default Python checker registry.
- SAT verifier skeleton in `cosheaf/verification/sat_adapter.py`.
- SMT verifier skeleton in `cosheaf/verification/smt_adapter.py`.
- Lean verifier skeleton in `cosheaf/verification/lean_adapter.py`.
- Optional verifier skeleton tests in `tests/test_optional_verifier_skeletons.py`.
- GitHub Actions CI in `.github/workflows/ci.yml`.
- Feature task, bug task, and research issue forms under `.github/ISSUE_TEMPLATE/`.
- Pull request template in `.github/pull_request_template.md`.

## Not Implemented Yet

- SQLite-backed query API beyond deterministic index rebuild output.
- Real SAT, SMT, and Lean solver invocation and result parsing.
- Reproducibility metadata gate and PR checklist gate beyond skipped placeholders.
- Advanced relevance ranking beyond issue-related artifacts plus one dependency hop.
