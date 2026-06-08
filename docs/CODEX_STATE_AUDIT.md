# Codex State Audit

Date: 2026-06-06

Scope:

- Framework repository: `tcs-cosheaf`
- Public KB repository: `tcs-kb-public`
- Workspace template repository: `tcs-cosheaf-workspace-template`

This audit records the actual current implementation state before later
longplan phases add new behavior. It is descriptive only. It does not change
application code, schemas, gate behavior, accepted-promotion policy, or KB
artifacts.

## Sources Inspected

Framework checkout:

- `AGENTS.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/GATES.md`
- `docs/ARTIFACT_SCHEMA.md`
- `docs/OPERATOR_NOTES.md`
- `docs/releases/v0.1.1.md`
- `context/PROJECT_STATE.md`
- `context/INTERFACE_REGISTRY.md`
- `context/CURRENT_MILESTONE.md`
- `pyproject.toml`
- `Makefile`
- `.github/workflows/ci.yml`
- `cosheaf/`
- `tests/`
- `scripts/`

Public KB checkout:

- `AGENTS.md`
- `README.md`
- `cosheaf.toml`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/`
- `sources/`
- `reviews/`
- `kb/public/accepted/`

Workspace template checkout:

- `AGENTS.md`
- `README.md`
- `cosheaf.toml`
- `Makefile`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/`
- `scripts/demo_workspace.sh`
- `scripts/bootstrap_public_kb.sh`
- `scripts/bootstrap_public_kb.ps1`

## Audit Answers

### 1. Current Framework Version

Current framework package version is `0.1.1`.

Evidence:

- `pyproject.toml` has `version = "0.1.1"`.
- `python -m cosheaf.cli version` prints `tcs-cosheaf 0.1.1`.
- `docs/releases/v0.1.1.md` describes the Formal Link Layer support release.

### 2. CLI Commands That Exist

The implemented top-level CLI groups are:

- `cosheaf version`
- `cosheaf validate`
- `cosheaf artifact ...`
- `cosheaf index ...`
- `cosheaf graph ...`
- `cosheaf gate ...`
- `cosheaf context ...`
- `cosheaf task ...`
- `cosheaf workspace ...`

Implemented subcommands:

- `cosheaf artifact validate <path>`
- `cosheaf artifact create ...`
- `cosheaf artifact move-status <artifact-id> <new-status>`
- `cosheaf artifact promote <artifact-id>`
- `cosheaf index rebuild`
- `cosheaf graph show`
- `cosheaf gate`
- `cosheaf gate run`
- `cosheaf context build <issue-id>`
- `cosheaf context show <issue-id>`
- `cosheaf task create --issue <issue-id> --worker <worker-type>`
- `cosheaf task list`
- `cosheaf task complete <task-id> --bundle <path>`
- `cosheaf task run <task-id> -- <command> [args...]`
- `cosheaf workspace info`

No `cosheaf query` CLI group currently exists. Formalization query capability is
available through the Python `ArtifactIndexQuery` API over the rebuilt SQLite
index, not through a user-facing CLI command.

### 3. Gates That Exist And Placeholder Status

`cosheaf gate run` currently assembles these gates:

| Gate | Name | Current status |
| --- | --- | --- |
| G1 | Schema gate | Implemented through schema/model loading. |
| G2 | ID uniqueness gate | Implemented. |
| G3 | Status/path gate | Implemented, including workspace-relative KB root path semantics. |
| G4 | Dependency gate | Implemented, including accepted-to-draft and public-to-private dependency checks. |
| G5 | Evidence path gate | Implemented for repository-local evidence paths with external references exempted. |
| G6 | Verifier gate | Implemented over registered adapters; reports `skipped` when no adapter applies or optional backend is unavailable. |
| G7 | Reproducibility metadata gate | Implemented for executable verifier results; reports `not_applicable` when no executable evidence applies. |
| G8 | PR checklist gate | Implemented for local markdown checklist sources; reports `skipped` when no source is provided. |
| G9 | Source metadata gate | Implemented for accepted public artifacts in configured public KB roots with `accepted_requires_source = true`; otherwise `not_applicable`. |
| G10 | Formal link gate | Implemented as static formal-link metadata policy validation. |

No gate is currently represented as a fake pass placeholder. Some gates can be
`skipped` or `not_applicable`; those states remain distinct from `pass`.

### 4. Whether G10 Formal Link Gate Exists

Yes. G10 exists in `cosheaf/gates/formal_link_gate.py` and is wired into
`run_gatekeeper`.

G10 checks static consistency among:

- `formalizations`
- `alignment`
- `verification_policy`

G10 does not execute Lean, fetch CSLib or mathlib, inspect external symbols, or
prove informal/formal semantic alignment.

### 5. SAT, SMT, And Lean Adapter Status

The SAT, SMT, and Lean adapters are real optional command-invocation adapters,
but they are intentionally minimal.

- SAT: `SatAdapter` recognizes `sat`, `sat_solver`, and `sat_checker` evidence.
  It can run a repository-local DIMACS CNF file through an optional external
  backend, defaulting to `kissat`. If no backend is available, the result is
  `skipped`, not `pass`.
- SMT: `SmtAdapter` recognizes `smt`, `smt_solver`, and `smt_checker` evidence.
  It can run a repository-local SMT-LIB file through an optional external
  backend, defaulting to `z3 -smt2`. If no backend is available, the result is
  `skipped`, not `pass`.
- Lean: `LeanAdapter` recognizes `lean`, `lean4`, `lean_checker`, and
  `lean_proof` evidence. It can run a repository-local plain Lean file through
  an optional external `lean <file.lean>` backend. If Lean is unavailable, the
  result is `skipped`, not `pass`.

These are not full SAT, SMT, Lean, CSLib, or mathlib integrations. They do not
autoformalize natural language and do not check external formal-library
references stored under `formalizations`.

### 6. Whether External Lean Library `#check` Exists

No. External Lean library reference checking is not implemented.

There is no `LeanLibraryRefAdapter`, no generated temporary Lean file with
`import <module>` and `#check <symbol>`, and no `lake env lean` workflow for
CSLib/mathlib references. Existing references with
`check_mode: external_library_ref` are metadata for future checking workflows.

Post-audit note: Phase 6 Task 6.2 adds an optional
`LeanLibraryRefAdapter` after this 2026-06-06 snapshot. The adapter can check
linked external references by generating temporary `import`/`#check` Lean files
when Lean or lake is available. It still does not fetch CSLib/mathlib or prove
informal/formal semantic alignment.

### 7. Whether Query API Exists

Yes, a read-only Python query API exists:

- `cosheaf.storage.query.ArtifactIndexQuery`
- artifact, status, type, domain, dependency, reverse-dependency, source-root
  queries
- formalization queries
- formal-policy queries

The API reads `.cosheaf/index.sqlite` after `cosheaf index rebuild`. It does not
rebuild the index implicitly. There is no dedicated `cosheaf query` CLI surface
yet.

### 8. Whether Local Worker Runner Exists

Yes. A local explicit-command runner exists:

- `cosheaf task create`
- `cosheaf task list`
- `cosheaf task complete`
- `cosheaf task run`

`cosheaf task run` executes an explicit argv command with `shell=False`, keeps
working directories repository-local, captures stdout/stderr, enforces a
timeout, records run metadata under `.cosheaf/tasks/...`, and can validate a
local worker output bundle. It does not merge outputs into accepted knowledge
and does not promote artifacts.

### 9. Whether Hosted LLM Worker Exists

No. The current task harness and orchestrator are local filesystem stubs. They
do not call hosted LLM APIs, model providers, network services, or remote worker
runtimes.

### 10. Workspace Template State

The workspace template has the expected productized entry-point pieces:

- `Makefile` exists with thin wrapper targets:
  `install`, `workspace`, `validate`, `gate`, `pr-checklist`, `context`, and
  `demo`.
- `scripts/demo_workspace.sh` exists and runs the documented demo flow:
  install framework from `v0.1.1`, workspace info, validate, gate, PR checklist
  gate, and context build for `issue.example-private-claim`.
- `scripts/bootstrap_public_kb.sh` and `scripts/bootstrap_public_kb.ps1` exist.
  They clone or update a local `tcs-kb-public` checkout under `.cosheaf/`
  without modifying `kb/public` or copying private artifacts.
- `cosheaf.toml` configures a readonly `public` KB root at `kb/public` and a
  writable `private` KB root at `kb/private`.
- `.github/workflows/ci.yml` is a real smoke workflow that installs
  `tcs-cosheaf@v0.1.1`, runs `cosheaf workspace info`, `cosheaf validate`,
  `cosheaf gate run`,
  `cosheaf gate run --pr-checklist .github/pull_request_template.md`,
  `cosheaf context build issue.example-private-claim`, and
  `git diff --check`.

The template docs explicitly state that seed files are examples only, real
public KB content should come from `tcs-kb-public`, private work belongs under
`kb/private`, formal links are metadata only unless checked, and validation/gate
success is not a substitute for human review.

### 11. Accepted Public KB Artifact Count

Current `tcs-kb-public` has 19 accepted public KB artifacts under
`kb/public/accepted/`:

- 12 definitions
- 4 theorem statements
- 3 proof-sketch artifacts

All 19 accepted artifacts currently have `status: accepted` and inline
`review.state: human_reviewed`. Human review notes exist under
`reviews/human/`.

### 12. Public KB Formal Link Status

All 19 accepted public KB artifacts currently carry one formalization reference.
The current formalization status distribution is:

- `planned`: 19
- `linked`: 0
- `checked`: 0

All 19 use `check_mode: external_library_ref`. No public KB formal link is
currently Lean-checked by the framework, and no CSLib/mathlib symbol existence
check is recorded by an implemented checker.

### 13. Known Stale Docs Or Milestones

Known stale or follow-up documentation state:

- `context/CURRENT_MILESTONE.md` was still describing the old `v0.1.0` release
  candidate cleanup milestone even though the framework is now `v0.1.1` and
  ecosystem work has moved into three-repo MVP productization. This PR updates
  that file.
- The durable docs still record `codex/<task-id-or-short-name>` as the default
  branch convention. The maintainer has explicitly overridden the current run:
  do not add `codex` prefixes to issue names, branch names, or PR titles. This
  audit branch is therefore `phase0-state-audit`.
- `longplan.md` remains the authoritative execution runbook outside the repo,
  but some Phase 1 workspace-template items have already landed through prior
  PRs. Later planning should reconcile that history before opening duplicate
  workspace-template work.

## Current Three-Repo Summary

`tcs-cosheaf` is a v0.1.1 pre-MVP framework scaffold with validation, gates,
workspace-aware KB roots, deterministic indexing, a Python query API,
formal-link metadata surfaces, local task-runner scaffolding, and minimal
optional verifier adapters.

`tcs-kb-public` is a small public KB with accepted graph-theory foundation
artifacts, source-note policy, human review notes, and planned-only formal-link
metadata. Its accepted artifacts remain source-reviewed public knowledge, not
Lean/mathlib/CSLib checked facts.

`tcs-cosheaf-workspace-template` is currently the recommended user entry point.
It has demo, Makefile, public-KB bootstrap guidance, readonly public KB plus
writable private KB configuration, and CI smoke coverage for the demo flow.

## Non-Goals Confirmed By Audit

- No web UI.
- No hosted LLM worker runtime.
- No automatic theorem proving.
- No full SAT/SMT/Lean proof-assistant integration.
- No external Lean library `#check` workflow.
- No automatic informal/formal semantic alignment checking.
- No accepted public artifact should be treated as accepted solely because
  validation or gates pass.
