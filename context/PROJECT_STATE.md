# Project State

## Current State After Issue 36

TCS-Cosheaf is in pre-MVP scaffold state. The repository contains project governance documentation, a short README, a Python-oriented `.gitignore`, the durable documentation skeleton, the minimal Python project scaffold, the initial repository directory layout, initial JSON Schema files, example YAML artifacts, initial Pydantic v2 core artifact models including structured source metadata, filesystem-backed storage loading utilities, optional workspace configuration, workspace-aware validation gates including accepted public source metadata enforcement, artifact lifecycle CLI commands including controlled accepted-artifact promotion, an artifact dependency graph, deterministic repository index rebuilds, a read-only SQLite query API over rebuilt index output, gatekeeper report generation, ranked issue-scoped context pack generation, local agent task records, a worker output bundle contract, an orchestrator stub, a local worker command runner, the initial verifier adapter interface, a Python checker verifier adapter, minimal optional SAT DIMACS and SMT-LIB verifier adapters, an optional-tool Lean verifier skeleton adapter, two draft pilot workflows, GitHub Actions CI, and GitHub collaboration templates.

Branch protection and review expectations are now documented in
`docs/REVIEW_POLICY.md`. The documented policy requires protected `main`,
disallows direct pushes to `main`, and routes all changes through issue,
branch, pull request, CI/gate checks, review, and merge.

Issue 20 updates the durable agent operating protocol for the planned
three-repository architecture. `AGENTS.md` and `docs/CODEX_WORKFLOW.md` now
record that `tcs-cosheaf` is the framework repository, `tcs-kb-public` is the
public reusable TCS knowledge base, and `tcs-cosheaf-workspace-template` is the
user-facing workspace template. The documented user model is framework package
plus readonly public KB plus writable private KB overlay; users should not
manually merge framework and KB repositories.

Issue 30 extends the framework user-facing documentation for that
three-repository model. `README.md`, `docs/WORKSPACE.md`, and
`docs/PUBLIC_PRIVATE_KB.md` now name `tcs-cosheaf-workspace-template` as the
recommended user entry point, link the public KB repository, explain that
downstream workspaces should mount public knowledge readonly with private
knowledge writable, and restate that private artifacts may depend on public
artifacts while public artifacts must not depend on private artifacts. This is
documentation-only framework work and does not change code, schemas, or gates.

Issue 33 adds a framework-level integration smoke test for the workspace
template model. The test builds a representative local workspace-template
layout in a temporary directory without cloning remote repositories or requiring
network access. It verifies `cosheaf.toml` public/private KB policy, readonly
public and writable private root metadata, private-to-public dependencies,
`cosheaf workspace info`, `cosheaf validate`, `cosheaf gate run`, explicit
`cosheaf gate run --pr-checklist .github/pull_request_template.md`, and the
negative rule that public artifacts must not depend on private artifacts. This
is test coverage for existing workspace behavior and does not add public
interfaces, schema fields, accepted artifacts, or SAT/SMT/Lean execution.

The durable workflow rules now require nontrivial Codex work to be issue-driven
where possible, with one issue, one focused `codex/<task>` branch, one PR, and
one reviewable increment. They also record repository creation checks through
`gh --version` and `gh auth status`, local issue-draft fallback behavior when
remote issue creation is unavailable, and the rule that repository, branch,
issue, PR, remote push, and check success must never be faked.

`AGENTS.md` now also records the accepted-artifact promotion protocol: accepted
knowledge must enter lifecycle KB roots through
`cosheaf artifact promote <artifact-id>`, with repository validation,
gatekeeper, target verifier, review-state, dependency, readonly-root, and
deterministic-write checks preserved as durable Codex operating rules.

The documented workspace layering policy expects future `cosheaf.toml`
workspaces to support multiple KB roots with public readonly KB and private
writable overlay semantics. Private artifacts may depend on public artifacts,
public artifacts must not depend on private artifacts, accepted artifacts must
not depend on draft artifacts across KB roots, and readonly KB roots must not be
modified by write commands.

The Python scaffold defines a `cosheaf` package, a Typer-based `cosheaf` CLI entry point, development dependencies, Makefile targets, a Dockerfile for reproducible local development, and smoke tests for import and CLI help/version behavior.

The filesystem layout now includes accepted and draft knowledge-base directories, refuted and obsolete artifact areas, issue directories, experiment directories, and review directories. The initial schemas live under `schemas/`, and examples live under `examples/`.

The core model layer now defines artifact type and status enums, base artifact data models, artifact ID and dependency-reference validation, timestamp validation, risk/evidence/source/review value objects, pure status/path helper functions, artifact type directory mapping, and deterministic lifecycle artifact path derivation. Artifact `depends_on` values may reference local artifact IDs or explicit external references beginning with `external:`. Artifact `sources` entries record structured citation metadata with kind, title, authors, year, DOI, arXiv, URL, theorem number, page, and notes fields.

The configuration layer defines optional `cosheaf.toml` workspace loading. A
workspace has a name, public/private policy fields, and one or more KB roots,
each with `name`, path, `readonly`, and `priority`. If no `cosheaf.toml` exists,
TCS-Cosheaf preserves the previous single-repository behavior with one writable
default KB root at `kb/`.

The storage layer defines `RepoContext`, workspace-aware YAML discovery under
configured KB roots plus repository-local `issues/` and `examples/`, typed YAML
loading into `BaseArtifact`, `IssueRecord`, or `ReviewRecord`,
repository-relative source paths on loaded records, source KB root metadata,
deterministic ordering by path then ID, clear load errors, and deterministic
YAML writing helpers.

The validation CLI implements repository validation for YAML parse/model parse, ID uniqueness across all active roots, status/path consistency relative to each KB root, dependency existence, accepted-artifact-to-draft-artifact dependencies across roots, public-artifact-to-private-artifact dependency violations, external dependency references, and local evidence path existence. Expected validation failures produce concise Rich output and nonzero exit codes without stack traces unless `--debug` is used.

The artifact lifecycle CLI now implements `cosheaf artifact create`, `cosheaf artifact move-status`, and `cosheaf artifact promote`. Artifact creation writes deterministic BaseArtifact YAML records under canonical lifecycle paths, refuses duplicate IDs, refuses direct accepted creation, and validates the new file before reporting success. In configured workspaces, creation writes to the writable private root by default. Status movement loads artifacts by unique ID, requires the current file path to match the current status, refuses readonly KB roots, validates the repository before moving, updates YAML deterministically, moves terminal failure statuses to the active KB root's refuted or obsolete area, and refuses direct accepted promotion. Accepted promotion is handled only by `cosheaf artifact promote <artifact-id>`; it validates the repository, runs gatekeeper, refuses blocking gatekeeper issues and target verifier `fail`/`error` results, requires `review.state` to be `human_reviewed` or `accepted`, requires dependencies to be accepted local artifacts or explicit external references, refuses readonly KB roots, requires complete structured source metadata for public KB artifacts when `accepted_requires_source = true`, updates status to `accepted`, refreshes `updated_at`, and writes deterministic YAML under the accepted area of the artifact's KB root.

The workspace CLI now implements `cosheaf workspace info`, which reports the
active workspace name, whether the repository is in configured or legacy mode,
and the configured KB roots with paths, readonly flags, and priorities.

The graph layer builds directed dependency edges from artifact to dependency, detects missing dependencies, detects directed cycles, and reports accepted artifacts depending on draft or otherwise pre-accepted artifacts.

The index rebuild command writes `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json` from scratch. The SQLite index stores artifact ID, type, status, path, title, domain, source KB root, and deterministic dependency rows. The manifest ordering is deterministic and stable across delete-and-rebuild cycles. The SQLite query API reads that rebuilt index without modifying YAML or rebuilding implicitly, and provides deterministic artifact, status, type, domain, dependency, reverse-dependency, and source-KB-root queries.

The gatekeeper command runs G1-G5 implemented gates, the G6 verifier gate, the
G7 reproducibility metadata gate, the G8 PR checklist gate, and the G9 source
metadata gate. It writes JSON and Markdown reports to `.cosheaf/reports/` by
default, can persist copies under `reviews/gatekeeper/` with
`--persist-review`, and exits nonzero when blocking issues exist. G7 reports
`pass`, `fail`, or `not_applicable` depending on executable evidence metadata.
G8 is a local filesystem-only gate: it reports `skipped` when no PR checklist
source is provided, and `cosheaf gate run --pr-checklist <path>` checks a local
markdown PR body for the required checklist sections without GitHub API or
network access. G9 enforces complete structured source metadata for accepted
artifacts in configured public KB roots when `accepted_requires_source = true`;
it is not applicable for draft public artifacts, accepted private artifacts, or
legacy single-root repositories.

The agent harness layer now builds bounded deterministic context packs for issue IDs. Context packs are written under `context/TASKS/<issue-id>/` and include `CONTEXT.md`, `ACCEPTANCE.md`, `RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`, and `COMMANDS.md`. Relevant artifacts are selected and ranked from direct issue references, one-hop dependency neighbors, domain matches against issue text/tags, and artifact tag matches against issue tags. Each selected artifact includes explainable reasons. Draft artifacts are visibly labeled, and refuted/obsolete/superseded artifacts appear only when relevant and are marked as known failures rather than current truth.

The agent task harness now defines protocol worker types for `reasoner`, `verifier`, `counterexampleer`, `construction_searcher`, `formalizer`, `literature_scout`, and `orchestrator`. Task records use deterministic default IDs of the form `task.<issue-id>.<worker-type-slug>`, support lifecycle statuses `open`, `in_progress`, `blocked`, `completed`, `failed`, and `cancelled`, and are written under `.cosheaf/tasks/`. The `cosheaf task create`, `cosheaf task list`, and `cosheaf task complete` CLI commands are local filesystem stubs only: they do not call LLMs, do not make network calls, and do not execute model-provider worker runtimes.

The local worker runner executes explicit repository-local command argv lists for existing task records. `cosheaf task run <task-id> -- <command> [args...]` uses `shell=False`, defaults to the repository root, rejects `--cwd` outside the repository, enforces a timeout, captures stdout/stderr, records return code, and writes run records under `.cosheaf/tasks/<task-id>/runs/<run-id>/` with stdout and stderr stored as separate files. `--bundle <path>` validates an optional worker output bundle without completing the task. `--complete-with-bundle <path>` delegates task completion to the existing orchestrator stub after a successful run and valid bundle. The local runner is not an LLM runtime, does not call hosted APIs or network services, does not merge worker outputs, does not promote artifacts, and does not implement SAT, SMT, or Lean execution.

Worker output bundles are local YAML manifests. `cosheaf task complete` validates the bundle shape, checks that it matches the task, verifies referenced output paths are repository-local, and runs artifact/review YAML outputs through the existing schema gate. Outputs under `kb/accepted/` are rejected, and completion does not merge anything into accepted knowledge.

The verification layer now defines the `VerifierAdapter` protocol, normalized `VerificationResult` model, `VerificationStatus` enum, instance-local `VerifierRegistry`, and `PythonCheckerAdapter`. Verification results distinguish `pass`, `fail`, `error`, and `skipped`; command-backed results record command and working directory metadata.

The Python checker adapter runs `kind: python_checker` evidence from the repository root, enforces a timeout, writes stdout/stderr logs under `.cosheaf/logs/`, and records command metadata, input/output paths, timeout, tool metadata, and environment notes in `VerificationResult`. The gatekeeper G6 verifier gate now runs the default verifier registry and reports Python checker results. G6 is skipped only when no verifier adapters are applicable.

The SAT adapter now supports a minimal optional DIMACS CNF invocation path. It checks repository-local SAT evidence paths, skips clearly when no supported backend is available, and when a backend is available records command, cwd, timeout, input path, stdout/stderr logs, output paths, backend metadata, exit code, and a normalized `sat`/`unsat`/`unknown` result. The default backend is an optional external command backend for `kissat`; tests can inject a fake backend and CI does not require a SAT solver. SAT skipped results are not pass results.

The SMT adapter now supports a minimal optional SMT-LIB invocation path. It checks repository-local SMT evidence paths, skips clearly when no supported backend is available, and when a backend is available records command, cwd, timeout, input path, stdout/stderr logs, output paths, backend metadata, exit code, and a normalized `sat`/`unsat`/`unknown` result. The default backend is an optional external command backend for `z3`; tests can inject a fake backend and CI does not require an SMT solver. SMT skipped results are not pass results.

The Lean adapter remains an optional-tool skeleton. It checks for configured Lean availability, returns `skipped` when Lean is unavailable, and does not add a hard dependency on Lean. No real Lean verification execution exists yet. SAT and SMT support are still intentionally minimal: they execute DIMACS CNF or SMT-LIB evidence only when optional backends are available and are not a full SAT/SMT theorem-proving integration.

The reproducibility metadata gate is now implemented. It checks executable
evidence verifier results for command, working directory, timeout, input paths,
stdout/stderr and output paths, tool metadata, and exit code for pass/fail
results. Randomized evidence requires seed metadata. Non-executable evidence is
reported as not applicable.

The source metadata gate is now implemented for accepted public artifacts in
configured workspaces. Accepted public artifacts must have at least one
`sources` entry; each source must include kind, non-empty title, at least one
author, year, and at least one locator from DOI, arXiv, URL, theorem number, or
page. External dependency references are not accepted as source metadata.
Draft public artifacts and accepted private artifacts may omit formal source
metadata under the current policy, and legacy single-root mode remains
unchanged.

The first graph-theory pilot workflow now exists for
`issue.graph-toy-search.0001`. It adds a finite-combinatorics issue, a
`locally_tested` draft construction artifact for a toy five-cycle graph, a
matching example artifact, and executable Python-checker evidence. The checker
verifies vertex count, edge count, sorted degree sequence, connectedness, and
triangle-freeness. The artifact is not accepted and does not claim a new
theorem or novelty.

The second SAT/CNF pilot workflow now exists for
`issue.sat-smt-gadget.0001`. It adds a satisfiability issue, a `locally_tested`
draft construction artifact for a tiny 3-variable CNF formula, a DIMACS CNF
example, a known satisfying assignment JSON file, optional `sat` evidence, and
executable Python-checker fallback evidence. The SAT adapter reports `skipped`
when no solver backend is available and can execute the tiny DIMACS CNF when a
backend is available; the Python fallback checker verifies the CNF and
assignment locally. The artifact is not accepted and does not claim a new
theorem, novelty, or full SAT/SMT solver integration.

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
- Multi-repository workspace and public/private KB operating rules in
  `AGENTS.md` and `docs/CODEX_WORKFLOW.md`.
- Pre-MVP overview in `README.md`.
- Documentation skeleton under `docs/`.
- Initial ADRs under `docs/ADR/`.
- Context skeleton under `context/`.
- Python project metadata in `pyproject.toml`.
- Minimal `cosheaf` package and CLI.
- Makefile targets for `lint`, `typecheck`, `test`, `validate`, and `gate`.
- Implemented `cosheaf validate` repository validation CLI.
- Implemented `cosheaf artifact validate <path>` single-file validation CLI.
- Implemented `cosheaf artifact create` deterministic artifact lifecycle creation CLI.
- Implemented `cosheaf artifact move-status <artifact-id> <new-status>` safe lifecycle status movement CLI for non-accepted transitions.
- Implemented `cosheaf artifact promote <artifact-id>` controlled accepted-artifact promotion CLI.
- Implemented `cosheaf index rebuild` deterministic repository index rebuild CLI.
- Implemented `cosheaf graph show` dependency graph inspection CLI.
- Implemented `cosheaf gate run` gatekeeper report CLI.
- Implemented `cosheaf gate run --pr-checklist <path>` local G8 PR checklist
  gate input.
- Implemented `cosheaf gate` default gatekeeper run for the existing `make gate` target.
- Implemented G9 source metadata gate for accepted public artifacts in
  configured workspaces.
- Implemented optional `cosheaf.toml` workspace configuration with
  `WorkspaceConfig`, `WorkspacePolicy`, and `KbRootConfig` Pydantic models.
- Implemented workspace-aware storage discovery across multiple configured KB
  roots with source-root metadata on loaded records.
- Implemented public/private dependency validation and accepted-to-draft
  validation across KB roots.
- Implemented readonly KB write refusal and writable private-root default for
  lifecycle artifact creation.
- Implemented `cosheaf workspace info` to inspect the active workspace and KB
  roots.
- Added workspace-template integration smoke tests that exercise a representative
  readonly public KB plus writable private KB fixture without network access.
- Dockerfile for local development.
- Smoke tests under `tests/`.
- Repository layout under `kb/`, `issues/`, `experiments/`, and `reviews/`.
- JSON Schema files under `schemas/`.
- Example YAML artifacts under `examples/`.
- Schema/example filesystem smoke tests in `tests/test_schema_files_exist.py`.
- Pydantic v2 core models under `cosheaf/core/`.
- Structured artifact source metadata model and schema field `sources`.
- Artifact status/path helper functions that do not scan the repository.
- Model tests in `tests/test_artifact_models.py`.
- Repository path helpers in `cosheaf/core/paths.py`.
- Artifact type directory and lifecycle path helpers in `cosheaf/core/paths.py`.
- Filesystem-backed storage context, loader, and writer under `cosheaf/storage/`.
- Storage loader tests and fixtures in `tests/test_loader.py` and `tests/fixtures/`.
- Initial validation gates under `cosheaf/gates/`.
- Validation CLI tests in `tests/test_validate_cli.py` and `tests/test_status_path_validation.py`.
- Dependency graph utilities under `cosheaf/graph/`.
- Deterministic SQLite and manifest index rebuild in `cosheaf/storage/index.py`.
- Read-only SQLite query API in `cosheaf/storage/query.py`.
- Graph and index tests in `tests/test_claim_graph.py` and `tests/test_index_rebuild.py`.
- Query API tests in `tests/test_index_query.py`.
- Gatekeeper reports in `cosheaf/gates/gatekeeper.py`.
- Gatekeeper tests in `tests/test_gatekeeper.py`.
- Ranked context pack generation in `cosheaf/agent/context_pack.py`.
- Context pack CLI commands `cosheaf context build <issue-id>` and `cosheaf context show <issue-id>`.
- Context pack tests in `tests/test_context_pack.py`.
- Agent task model in `cosheaf/agent/task.py`.
- Worker output bundle contract in `cosheaf/agent/worker_contract.py`.
- Local orchestrator stub in `cosheaf/agent/orchestrator_stub.py`.
- Local worker command runner in `cosheaf/agent/local_runner.py`.
- Task CLI commands `cosheaf task create --issue <issue-id> --worker <worker-type>`, `cosheaf task list`, `cosheaf task complete <task-id> --bundle <path>`, and `cosheaf task run <task-id> -- <command> [args...]`.
- Task JSON Schema in `schemas/task.schema.json`.
- Task example YAML in `examples/tasks/task.example.yaml`.
- Task model, local runner, and CLI tests in `tests/test_task_model.py`, `tests/test_local_worker_runner.py`, and `tests/test_task_cli.py`.
- Verifier adapter protocol in `cosheaf/verification/base.py`.
- Normalized verification result model in `cosheaf/verification/result.py`.
- Instance-local verifier registry in `cosheaf/verification/registry.py`.
- Verification result and registry tests in `tests/test_verification_result.py`.
- Python checker verifier adapter in `cosheaf/verification/python_checker.py`.
- Python checker evaluator example in `experiments/evaluators/check_graph_example.py`.
- Python checker tests in `tests/test_python_checker.py`.
- Gatekeeper G6 verifier gate execution for the default Python checker registry.
- Gatekeeper G7 reproducibility metadata gate execution.
- Gatekeeper G9 accepted public source metadata gate execution.
- Minimal optional SAT DIMACS verifier adapter in `cosheaf/verification/sat_adapter.py`.
- Minimal optional SMT-LIB verifier adapter in `cosheaf/verification/smt_adapter.py`.
- Lean verifier skeleton in `cosheaf/verification/lean_adapter.py`.
- Optional verifier tests in `tests/test_optional_verifier_skeletons.py`.
- Focused SAT adapter tests in `tests/test_sat_adapter.py`.
- Focused SMT adapter tests in `tests/test_smt_adapter.py`.
- First graph-theory pilot issue in `issues/open/issue.graph-toy-search.0001.yaml`.
- Draft toy graph construction in `kb/draft/constructions/construction.graph-toy.0001.yaml`.
- Toy graph example in `examples/constructions/graph.toy.yaml`.
- Toy graph Python checker in `experiments/evaluators/check_graph_toy.py`.
- Toy graph checker tests in `tests/test_graph_toy_pilot.py`.
- Second SAT/CNF pilot issue in `issues/open/issue.sat-smt-gadget.0001.yaml`.
- Draft SAT/CNF construction in `kb/draft/constructions/construction.sat-smt-gadget.0001.yaml`.
- Tiny DIMACS CNF example in `examples/sat/tiny-sat.cnf`.
- Tiny SAT assignment input in `examples/sat/tiny-sat.assignment.json`.
- Tiny SAT Python fallback checker in `experiments/evaluators/check_sat_smt_gadget.py`.
- SAT/CNF pilot checker and optional SAT skipped tests in `tests/test_sat_smt_gadget_pilot.py`.
- GitHub Actions CI in `.github/workflows/ci.yml`.
- Feature task, bug task, and research issue forms under `.github/ISSUE_TEMPLATE/`.
- Pull request template in `.github/pull_request_template.md`.
- Branch protection and review policy in `docs/REVIEW_POLICY.md`.

## Not Implemented Yet

- External public KB repository integration beyond local workspace roots.
- Hosted LLM calls and model-provider worker integration.
- Task scheduling, retries, cancellation, and dependency management.
- Automatic merge of task outputs into accepted knowledge.
- Full SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Full SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Real Lean solver invocation and result parsing.
