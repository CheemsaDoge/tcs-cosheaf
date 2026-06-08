# TCS-Cosheaf

TCS-Cosheaf is a Git-backed typed research knowledge base and agent harness for
AI-assisted theoretical computer science. It keeps definitions, claims, proofs,
constructions, algorithms, reductions, counterexamples, experiments, reviews,
issues, and verifier evidence in reviewable repository files.

Current status: **post-v0.1.1 release-hardening / pre-MVP scaffold**. The
`v0.1.1` tag is the downstream Formal Link Layer support baseline. The current
`main` branch has additional hardening work while the Python package metadata
still records version `0.1.1` until the next release tag is cut. The repository
has working Python scaffolding, typed artifact models, filesystem loading,
validation, dependency graph indexing,
workspace-aware KB root loading, artifact lifecycle CLI commands, gatekeeper
reports including the G10 Formal Link Gate, ranked context-pack generation with
compact formal-link display, local task harness stubs, verifier adapters
including a Python checker, a minimal optional SAT DIMACS path, a minimal
optional SMT-LIB path, a minimal optional plain Lean file path, and an optional
external Lean library reference `#check` path, GitHub Actions CI, and
collaboration templates. It is not production software and does not yet provide
a web UI, automatic theorem proving, full Lean autoformalization, or multi-user
permissions.

## Problem

Research projects in theoretical computer science accumulate claims, proof
attempts, constructions, counterexamples, experiments, and review notes across
papers, chats, scripts, and local files. That makes it hard to answer basic
questions:

- Which claims are accepted, draft, refuted, or obsolete?
- Which artifacts depend on which assumptions?
- Which evidence was checked, by what command, and from what repository state?
- What context should a human or agent read before working on an issue?

TCS-Cosheaf treats the repository as the durable project memory so research
state can be reviewed, validated, indexed, and handed to agents without relying
on conversation history.

## Approach

- Store typed research artifacts as Git-backed YAML files.
- Validate artifact shape, IDs, status/path invariants, dependencies, and local
  evidence paths.
- Build deterministic dependency graphs and repository indexes.
- Run gatekeeper checks before accepting behavior or artifact changes.
- Normalize verifier outputs through optional adapters.
- Generate ranked bounded context packs for issue-scoped Codex or agent tasks.
- Run explicit local worker commands against issue-scoped tasks and validate
  structured output bundles without merging accepted knowledge automatically.
- Record metadata-only references to external formal declarations through the
  Formal Link Layer without copying Lean proofs.

Optional formal tools stay optional. Missing SAT, SMT, Lean, or similar tools
must produce skipped verifier results rather than crashing the core system.
Cosheaf does not replace CSLib, mathlib, or Lean: formal links are metadata
plus gate, context-pack, index, query, and optional verifier surfaces. The
external Lean library reference checker can run `import <module>` and
`#check <symbol>` when Lean or lake is available, but a successful `#check`
only means the import and symbol resolved. It does not prove informal/formal
semantic alignment.

## Current Status

Implemented:

- Python 3.11+ package scaffold with Typer CLI.
- Pydantic v2 artifact models and status helpers.
- Initial JSON Schemas and example YAML records.
- Filesystem-backed artifact/issue/review loading and deterministic YAML
  writing.
- Optional `cosheaf.toml` workspace configuration with multiple KB roots,
  readonly roots, public/private dependency policy, and legacy fallback.
- `cosheaf validate`, `cosheaf artifact validate <path>`,
  `cosheaf artifact create`, `cosheaf artifact move-status`,
  `cosheaf artifact promote`, and `cosheaf workspace info`.
- Dependency graph inspection and deterministic SQLite/manifest index rebuilds.
- Read-only SQLite query API over rebuilt index output through
  `ArtifactIndexQuery`, including artifact, status, type, domain, dependency,
  reverse-dependency, formalization, and formal-policy queries.
- `cosheaf gate` and `cosheaf gate run` report generation.
- Ranked issue-scoped context pack generation with
  `cosheaf context build <issue-id>`.
- Formal Link Layer artifact metadata fields `formalizations`, `alignment`,
  and `verification_policy`.
- G10 Formal Link Gate metadata and verifier-result consistency checks.
- SQLite `formalizations` and `artifact_formal_policy` index tables plus
  compact manifest metadata.
- Context-pack display of formal-link metadata without claiming Lean
  verification or informal/formal alignment.
- Local task harness stubs with `cosheaf task create`, `cosheaf task list`, and
  `cosheaf task complete`.
- Verifier adapter protocol, Python checker adapter, minimal optional SAT
  DIMACS adapter, minimal optional SMT-LIB adapter, minimal optional Lean
  plain-file adapter, and optional external Lean library reference checker.
- Reproducibility metadata gate for executable evidence verifier results.
- Local PR checklist gate support through `cosheaf gate run --pr-checklist
  <path>`.
- First graph-theory pilot workflow with draft artifact evidence and a local
  Python checker.
- Second SAT/CNF pilot workflow with optional SAT evidence, a known satisfying
  assignment, and a Python fallback checker.
- Lean core formal-link pilot with draft metadata for `import Init` / `#check
  Nat`; missing Lean remains `skipped`, and the pilot does not claim alignment
  or accepted knowledge.
- GitHub Actions CI with separate `lint`, `typecheck`, `test`, `validate`, and
  `gate` checks.

Planned or incomplete:

- Full SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Full SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Full Lean proof-assistant integration beyond optional plain-file and external
  library reference checks.
- Hosted PR checklist source discovery beyond explicit local markdown files.
- Hosted LLM/model-provider worker execution.
- External public KB repository integration beyond local workspace roots.
- Automatic informal/formal semantic alignment checking.

## Worker And Orchestrator Boundary

TCS-Cosheaf includes a lightweight local task-execution layer. Tasks are
issue-scoped records, context packs provide bounded repository context, and
local worker runs execute explicit command argv lists with repository-local
working directories, timeout metadata, stdout, stderr, and return-code records.
Workers can return structured output bundles that the existing contract
validates for review.

The current orchestrator is a local filesystem stub. It does not call hosted
LLMs or model providers, does not run network services, does not merge worker
outputs, and does not promote accepted knowledge. Accepted knowledge still
enters through review, gates, and `cosheaf artifact promote`.

## Core Concepts

- **Artifact**: A typed research record such as a definition, claim, proof,
  construction, algorithm, reduction, counterexample, experiment, review,
  verifier, or issue.
- **Status lattice**: Artifact status values such as `draft`, `accepted`,
  `refuted`, `obsolete`, and `superseded` describe lifecycle state.
- **Accepted knowledge**: `kb/accepted/` contains only accepted artifacts.
  Accepted artifacts must not depend on draft artifacts.
- **Draft knowledge**: `kb/draft/` contains draft or pre-accepted artifacts.
- **Gatekeeper**: Repository checks that turn schema, dependency, evidence,
  verifier, and review invariants into machine-readable and human-readable
  reports.
- **Workspace**: A `cosheaf.toml` configuration that layers one or more KB roots
  such as readonly public KB and writable private KB overlay.
- **Context pack**: A deterministic issue-scoped bundle of ranked repository
  context for Codex or other agents.
- **Verifier adapter**: A pluggable checker interface that records normalized
  `pass`, `fail`, `error`, or `skipped` results.

## Quickstart

This repository is the framework package. For a user-facing research
workspace, start from
[`tcs-cosheaf-workspace-template`](https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template)
instead of manually merging framework and KB repositories. The intended model
is:

- `tcs-cosheaf`: framework, CLI, schema, gates, and agent harness.
- [`tcs-kb-public`](https://github.com/CheemsaDoge/tcs-kb-public): reusable
  public TCS KB, mounted readonly in downstream workspaces.
- `tcs-cosheaf-workspace-template`: user entry point with a readonly public KB
  root plus writable `kb/private` overlay.

Private artifacts may depend on public artifacts. Public artifacts must not
depend on private artifacts.

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf.git
cd tcs-cosheaf
python -m pip install -e ".[dev]"
```

Inspect the CLI:

```bash
cosheaf --help
cosheaf version
cosheaf workspace info
```

Run repository validation and gatekeeper checks:

```bash
cosheaf validate
cosheaf gate
```

Create and move draft lifecycle artifacts:

```bash
cosheaf artifact create --id claim.example.new --type claim --title "New claim" --domain graph-theory --status draft --statement "Statement under review."
cosheaf artifact move-status claim.example.new locally_tested
```

Promote eligible reviewed artifacts into accepted knowledge:

```bash
cosheaf artifact promote claim.example.new
```

Direct accepted creation and direct `move-status ... accepted` remain refused.
Promotion requires repository validation, gatekeeper, target verifier,
dependency, and review checks.

Build an index and inspect the artifact dependency graph:

```bash
cosheaf index rebuild
cosheaf graph show
```

Generate task context for an issue:

```bash
cosheaf context build <issue-id>
cosheaf context show <issue-id>
```

See [Workspace quickstart](docs/WORKSPACE_QUICKSTART.md),
[Workspace model](docs/WORKSPACE.md), and
[Public/private KB policy](docs/PUBLIC_PRIVATE_KB.md) for layered KB roots.
Downstream repositories should pin to `v0.1.1` before using formalization
fields in artifact YAML. Post-tag `main` features, such as the optional
external Lean library reference checker, require a later validated release tag
before downstream pinned work can rely on them.

## Development Commands

```bash
make lint
make typecheck
make test
make validate
make gate
```

`make validate` runs the current repository validation CLI. `make gate` runs the
gatekeeper and writes reports under `.cosheaf/reports/`. G8 is skipped when no
PR checklist source is provided; use `cosheaf gate run --pr-checklist <path>` to
validate a local PR body markdown file.

## Roadmap

The roadmap is tracked in [docs/ROADMAP.md](docs/ROADMAP.md). Live issue state
is tracked in GitHub issues rather than hard-coded in this README.

## Non-Goals

For the MVP, TCS-Cosheaf does not aim to provide:

- A web UI.
- Model training.
- An automatic theorem-proving agent.
- Full Lean autoformalization.
- A multi-user permission system.
- A replacement for peer review, formal proof assistants, or domain expert
  judgment.
- A replacement for CSLib, mathlib, Lean, or human semantic alignment review.

## Key Documentation

- [Project rules](AGENTS.md)
- [Product spec](docs/PRODUCT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Workspace quickstart](docs/WORKSPACE_QUICKSTART.md)
- [Workspace model](docs/WORKSPACE.md)
- [Public/private KB policy](docs/PUBLIC_PRIVATE_KB.md)
- [Gatekeeper and validation gates](docs/GATES.md)
- [Artifact lifecycle](docs/ARTIFACT_LIFECYCLE.md)
- [Artifact schema](docs/ARTIFACT_SCHEMA.md)
- [Codex workflow](docs/CODEX_WORKFLOW.md)
- [Review policy](docs/REVIEW_POLICY.md)
- [Release checklist](RELEASE_CHECKLIST.md)
- [Current milestone](context/CURRENT_MILESTONE.md)
- [Project state](context/PROJECT_STATE.md)
- [Public interface registry](context/INTERFACE_REGISTRY.md)

## License

This project is licensed under the [Apache License 2.0](LICENSE).
