# TCS-Cosheaf

中文文档：[中文简介](README.zh-CN.md) | [中文文档导航](docs/README.zh-CN.md)

TCS-Cosheaf is a Git-backed typed research knowledge base and agent harness for
AI-assisted theoretical computer science. It keeps definitions, claims, proofs,
constructions, algorithms, reductions, counterexamples, experiments, reviews,
issues, and verifier evidence in reviewable repository files.

Current status: **v0.2.4 Artifact Failure Memory + Attempt Traceability
published release**. The package metadata records `0.2.4`, the public
`v0.2.4` tag and GitHub release are published, release smoke from `@v0.2.4`
passed, and downstream workspace-template and public-KB pins have been updated
to `v0.2.4`. The active development line is now **v0.3.0 Checked Evidence +
Research Run Loop**; checked counterexample evidence and research-run
provenance surfaces are implemented on `main`, but package metadata remains
`0.2.4` until the later release-candidate PR. The `v0.1.1` tag remains the
downstream Formal Link Layer support
baseline; the `v0.2.0` tag packages the deterministic local-MVP workflow; the
`v0.2.1` tag packages the CLI-first agent and hosted-provider gateway surfaces
as a pin-able framework prerelease; `v0.2.2` packages the explicit default-off
provider transport and agent workflow hardening surfaces; `v0.2.3` packages
verifier evidence records, promotion-readiness reporting, optional
SAT/SMT/Lean result-depth fixtures, failure/counterexample evidence workflow
hardening, verifier-evidence evals, and the expanded three-repository
readiness matrix; and `v0.2.4` packages optional artifact-level
failure memory, failure-log CLI inspection and controlled draft writes,
WorkerBundle failure-log bridges, retrieval/context/promotion-readiness
surfacing, workspace/public-KB policy updates, and security/eval regression
coverage. The repository has working Python
scaffolding, typed artifact models, filesystem loading, validation, dependency
graph indexing, workspace-aware KB root loading, artifact lifecycle CLI
commands, gatekeeper reports including the G10 Formal Link Gate, ranked
context-pack generation with compact formal-link display, local task harness
and orchestrator dry-run surfaces, controlled draft-write CLI commands,
provider gateway and fake/mocked hosted-worker dispatch paths, verifier
adapters including a Python checker, a minimal optional SAT DIMACS path, a
minimal optional SMT-LIB path, a minimal optional plain Lean file path, and an
optional external Lean library reference `#check` path, an optional stdlib
OpenAI-compatible HTTP transport object plus a deliberately hard-to-trigger
provider `real-run` CLI path that is not used by default, GitHub Actions CI,
checked counterexample evidence CLI/eval surfaces, research-run provenance
CLI/eval surfaces, and collaboration templates. It is not production-ready
software and does not
yet provide a web UI, a default real hosted provider path, hosted worker CLI
commands, automatic theorem proving, full Lean autoformalization, automatic
accepted promotion, or multi-user permissions.

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
  `cosheaf artifact promote`, `cosheaf promotion readiness`, and
  `cosheaf workspace info`.
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
- Local task harness and local orchestrator dry-run surfaces with
  `cosheaf task ...`, `cosheaf orchestrator plan`, and
  `cosheaf orchestrator run --dry-run --local-only`.
- CLI-first agent-access surfaces with deterministic `--json` output for core
  read/check commands.
- Controlled draft, source-note, bundle, and review-request write commands
  that refuse accepted writes and readonly KB roots.
- Provider gateway commands for configuration inspection, context-send
  preview, and deterministic fake provider runs.
- Role-specific hosted worker services and explicit orchestrator dispatch
  through fake or OpenAI-compatible provider boundaries, with fake/mocked tests
  only.
- Optional stdlib OpenAI-compatible HTTP transport object for explicitly
  configured and injected provider calls; no default CLI path instantiates it.
- Explicit `cosheaf provider real-run --input-json <path> --provider
  openai-compatible --confirm-send --allow-network --json` path that requires
  inline context preview, operator send consent, explicit network permission,
  endpoint/API-key environment configuration, and redacted run logging.
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
- Hosted worker CLI commands.
- External public KB repository integration beyond local workspace roots.
- Automatic informal/formal semantic alignment checking.

## Worker, Provider, And Orchestrator Boundary

TCS-Cosheaf includes a lightweight task-execution and provider-worker layer.
Tasks are issue-scoped records, context packs provide bounded repository
context, and local worker runs execute explicit command argv lists with
repository-local working directories, timeout metadata, stdout, stderr, and
return-code records. Workers and hosted-worker services can return structured
output bundles that the existing contract validates for review.

The orchestrator surface has two controlled paths. The local dry-run path is
deterministic and uses fake local workers. The hosted-worker path is explicit:
`cosheaf orchestrator run --issue <issue-id> --provider fake --json` uses the
deterministic fake provider, while the OpenAI-compatible boundary requires
explicit `--confirm-send` and configured or injected transport. Default tests
and CI use fake or mocked providers only. These paths do not write accepted
knowledge, do not mark human review, do not run real provider network calls in
CI, do not bypass reducers, validation, gates, verifier results, review, or
promotion. Accepted knowledge still enters through review, gates, and
`cosheaf artifact promote`.

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

Inspect promotion readiness without promoting:

```bash
cosheaf promotion readiness --artifact claim.example.new --json
```

Readiness reports are advisory. They do not write accepted artifacts, do not
create human review, and do not convert skipped verifier output into a pass.

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
Downstream repositories that only need Formal Link Layer metadata can stay
pinned to `v0.1.1`. Downstream repositories that need the deterministic
local-MVP workflow can pin to `v0.2.0`. Downstream repositories that need the
CLI-agent and hosted-provider gateway surfaces can pin to `v0.2.1`.
Downstream repositories that need the provider transport hardening,
context-send policy matrix, provider log scanner, and failure/counterexample
workflow evals can pin to `v0.2.2`. Downstream repositories that need
verification-evidence hardening can pin to `v0.2.3`. Downstream repositories
that need artifact failure memory and attempt traceability can pin to
`v0.2.4`; the workspace-template and public KB active pins now use `v0.2.4`.

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
- [Agent access](docs/AGENT_ACCESS.md)
- [Agent providers](docs/AGENT_PROVIDERS.md)
- [Evaluation](docs/EVALUATION.md)
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
