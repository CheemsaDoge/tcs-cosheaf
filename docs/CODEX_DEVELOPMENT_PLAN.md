# Codex Development Plan

This document is durable repository memory for the next TCS-Cosheaf development
phases. It summarizes the current longplan in repository-facing terms and must
be reconciled with `docs/CODEX_STATE_AUDIT.md` before each new phase task.

Codex conversations are not project memory. If a decision, workflow constraint,
known limitation, or operator pitfall matters after context compaction, record
it in repository files.

## Operating Rule

Use issue-driven, reviewable increments:

```text
one task = one issue = one branch = one pull request
```

Do not push directly to `main`. Do not combine unrelated roadmap items in one
branch. If a task, issue, maintainer instruction, or release workflow specifies
a human-readable branch name, preserve it exactly. Current maintainer override:
do not add `codex` prefixes to issue titles, branch names, or pull request
titles, even when older examples show that prefix.

Each task must end with a PR summary and verification results. Do not proceed
to the next longplan task in the same PR.

## Three-Repository Responsibilities

### `tcs-cosheaf`

Framework repository. It owns:

- CLI commands.
- Artifact schema and typed models.
- Workspace configuration and KB-root loading.
- Validation and gatekeeper behavior.
- Artifact lifecycle and promotion commands.
- Dependency graph, deterministic index, and query surfaces.
- Context-pack generation.
- Verifier adapter interfaces and optional local tool adapters.
- Local task harness, future deterministic librarian, and future orchestrator
  state/runtime scaffolding.
- Architecture decisions, interface registry, project state, and operator
  workflow rules.

The framework repository may contain tiny fixtures and examples needed for
tests and documentation. It must not vendor the full public KB.

### `tcs-kb-public`

Public reusable TCS knowledge base. It owns public, citable, source-reviewed
knowledge artifacts and supporting source/review records.

Rules:

- No private conjectures or unpublished research ideas.
- No LLM-generated accepted artifacts without human review.
- Accepted public artifacts require source metadata and human review.
- Validation and gate success are required checks, not substitutes for human
  review.
- Formal links remain metadata unless a checker actually verifies them.
- Do not mass-import foundation packs or theorem packs without focused review.

### `tcs-cosheaf-workspace-template`

User-facing workspace entry point. It combines:

- the `tcs-cosheaf` framework package,
- a readonly reusable public KB root,
- a writable private KB overlay.

The template should support local demo, validation, gates, indexing, and
context-pack generation without requiring hosted LLM services. Users should not
manually merge the framework, public KB, and private workspace repositories.

### Private User KB

Private KB roots are writable overlays for conjectures, proof attempts,
failures, experiments, private notes, and work-in-progress claims. Private
artifacts may depend on public accepted artifacts. Private knowledge must not
enter public accepted knowledge without explicit review, gates, and promotion.

## Global Invariants

### Knowledge Lifecycle

- YAML artifacts are the source of truth.
- Accepted artifacts must pass validation, gates, review, and promotion.
- Worker output must not write directly to accepted knowledge.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier results are not passes.
- Failed or errored verifier results must not be hidden.
- Accepted artifacts must not depend on draft or private artifacts.
- Public KB artifacts must not depend on private KB artifacts.
- Private KB artifacts may depend on public accepted artifacts.
- Public KB must not contain private conjectures, unpublished ideas, or
  unreviewed LLM output.

### Storage And Indexing

- Generated indexes, manifests, retrieval caches, graph snapshots, and run
  logs are sidecars.
- Sidecars must be rebuildable and must not become manually edited facts.
- Runtime output should live under `.cosheaf/` or another ignored runtime
  directory unless a task explicitly asks to persist a review record.
- Generated outputs must be deterministic unless explicitly documented as
  experimental cache output.

### Agent Authority

- The orchestrator may plan, route, summarize, and coordinate checks; it must
  not accept knowledge.
- The librarian may retrieve, rank, and summarize artifact cards; it must not
  create new claims.
- Reasoner-like workers may propose drafts and verification requests; they
  must not label conjectures as theorems.
- Verifier-like workers must emit `pass`, `fail`, `error`, or `skipped` based
  on real checker behavior, not natural-language confidence.
- Formalizer-like workers must not claim informal/formal semantic alignment
  without alignment review.
- Hosted LLM workers are disabled by default.
- Tests must not require real network access, API keys, or hosted models.

### External Tools

- SAT, SMT, Lean, Python, and future formal-library checkers are optional
  tools.
- Missing optional tools produce skipped results, not core crashes.
- Available tool failures produce `fail` or `error` according to verifier
  semantics.
- External command results must record command, working directory, timeout,
  exit code, stdout/stderr log paths, and tool metadata where available.
- A successful Lean `#check`, if implemented later, proves only that an import
  and symbol/type reference resolved. It does not prove informal/formal
  semantic alignment.

## Phased Roadmap

### Phase 0: State Audit And Plan Memory

Purpose: record the actual three-repository baseline, then put this durable
plan into the framework repository before implementation phases proceed.

Status:

- Task 0.1 state audit is complete in `docs/CODEX_STATE_AUDIT.md`.
- Task 0.2 adds this plan, an ADR for the agent-memory runtime roadmap, and a
  current milestone update.

### Phase 1: Workspace-Template Productization

Purpose: make the workspace template the user entry point, with a local demo,
safe public KB bootstrap guidance, CI smoke, and a private draft example.

Next concrete Phase 1 tasks from the longplan:

- Task 1.1: workspace Makefile and demo command surface.
- Task 1.2: safe public KB bootstrap script.
- Task 1.3: workspace CI smoke.
- Task 1.4: demo issue and private draft example.

Current audit note: prior workspace-template work already added demo,
Makefile, bootstrap guidance, onboarding docs, and CI smoke coverage. Before
opening any Phase 1 PR, audit the template against the exact Task 1.1-1.4
requirements and create only a focused reconciliation or bug-fix PR if a real
gap remains. Do not add new workspace-template features just to duplicate
already merged work.

### Phase 2: Public KB Trusted Foundation Growth

Purpose: grow `tcs-kb-public` slowly through policy-first, source-reviewed
foundation artifacts.

Tasks:

- Add contribution templates and source/review policy guidance.
- Create a graph/foundations backlog before more accepted artifacts.
- Add exactly one small foundation artifact per PR when reliable source
  metadata and required review evidence are available.
- Add policy CI guards for common public-KB violations.

Do not continue ad hoc theorem/proof-sketch expansion before backlog and
source-note policy are in place.

### Phase 3: Librarian / Memory Policy MVP

Purpose: implement deterministic retrieval and graph-weighted memory before
any free agent runtime.

Tasks:

- Add memory policy docs and ADR.
- Add typed artifact-card and retrieval request/result models.
- Add deterministic card-building CLI.
- Add SQLite FTS/BM25 retrieval before embeddings.
- Add memory graph and deterministic PageRank.
- Add issue-conditioned Personalized PageRank retrieval.
- Integrate librarian retrieval into context packs as context-pack v2.

Default output should be cards, not full artifacts. Public/private filtering
and no-whole-repo-dump rules are core behavior, not UI preferences.

### Phase 4: Orchestrator State Machine And Local Worker Runtime

Purpose: turn the task harness into a replayable local orchestration system
without default hosted LLM execution.

Tasks:

- Add explicit orchestrator state models.
- Add deterministic task-DAG planner stubs.
- Standardize worker bundle v2 and reducer behavior.
- Integrate local worker runner with orchestrator plans.
- Demonstrate an end-to-end dry run where outputs remain proposals/drafts.

No task in this phase may write accepted knowledge or bypass gates/review.

### Phase 5: Optional LLM Worker Interface

Purpose: reserve provider-neutral interfaces while keeping hosted execution
disabled by default.

Tasks:

- Add provider-neutral model interface with a fake provider only.
- Add role prompt/context contracts.
- Add hosted provider adapter only behind explicit maintainer approval and
  explicit opt-in flags.

Tests must use fake providers or fake transports. No test may require an API
key or network access.

### Phase 6: Formal Link And External Lean `#check`

Purpose: make formal-library references more useful without pretending Cosheaf
is a formal proof library.

Tasks:

- Add or audit a formal library manifest.
- Add optional external Lean library `#check` adapter.
- Harden G10 Formal Link Gate around checked-link claims.
- Run a one-artifact formal-link pilot only when the workflow is honest.

Formal links remain metadata unless a checker runs and records a result.
Alignment review remains separate from symbol availability.

### Phase 7: Evaluation / Observability

Purpose: make retrieval, context packs, and local dry runs measurable.

Tasks:

- Add retrieval evaluation harness.
- Add context-pack regression evaluation.
- Add structured run logging.
- Add optional OpenTelemetry only if local default behavior stays unaffected.

No observability output may store secrets or hidden reasoning.

### Phase 8: Release Hardening / Showcase

Purpose: close the work into a conservative, reproducible, demo-ready
milestone.

Tasks:

- Add a three-repo release checklist.
- Add showcase demo docs.
- Propose the next `v0.2.0` milestone.

Release/showcase docs must not overclaim production readiness, automatic
theorem proving, Lean/mathlib/CSLib integration, hosted agent runtime, or
semantic alignment.

## Explicit Non-Goals

These are out of scope unless a later task explicitly changes them with an ADR,
tests, and maintainer approval:

- Production web UI.
- Multi-user auth or permissions.
- Hosted multi-agent runtime by default.
- Automatic theorem proving.
- Natural-language autoformalization.
- Automatic informal/formal semantic alignment.
- Treating formal-link metadata as Lean verification.
- Treating Lean `#check` as a proof of informal statement alignment.
- Treating validation/gate success as human review.
- Allowing AI review to count as human review.
- Allowing agents or workers to write accepted artifacts directly.
- Mass public KB import.
- Replacing CSLib, mathlib, Lean, SAT solvers, or SMT solvers.
- Making sidecar indexes or caches the source of truth.
- Requiring real network access, hosted LLM providers, or API keys in tests.

## Stop Rules

Stop and request maintainer decision before proceeding if a task would require:

- Creating a fourth core repository.
- Changing public/private dependency policy.
- Allowing an agent or worker to write accepted artifacts.
- Treating AI review as human review.
- Adding a hosted LLM provider dependency.
- Requiring real API keys or network tests.
- Changing license terms.
- Large-scale module refactors outside the current task.
- Mass-importing public KB artifacts.
- Claiming automatic Lean/mathlib/CSLib semantic alignment.
- Removing existing gate, review, or promotion constraints.
- Treating a sidecar index/cache as artifact truth.
- Weakening tests, gates, or skipped/fail/error semantics to make a PR pass.

## Per-PR Definition Of Done

Before opening or updating a PR, verify:

- Scope did not expand.
- No accepted KB writes occurred unless the task explicitly requires them and
  review/promotion policy is satisfied.
- Public/private dependency direction remains valid.
- Skipped verifier results are not described as passes.
- AI output is not labeled as human review.
- Hosted LLM behavior is not enabled by default.
- Tests do not require real network access.
- New public interfaces update `context/INTERFACE_REGISTRY.md`.
- New architecture decisions have ADR coverage.
- New behavior has tests or explicit documentation of why this is docs-only.
- CLI changes have smoke coverage.
- Gate changes have pass/fail tests.
- Docs and `context/PROJECT_STATE.md` or `context/CURRENT_MILESTONE.md` are
  updated when relevant.
- Required commands are run when available.
- Unavailable commands or skipped checks are reported honestly.

Use PR summaries with at least:

```text
Goal:
Scope:
Files changed:
Tests run:
Commands unavailable:
Invariants checked:
Known limitations:
Follow-up tasks:
```
