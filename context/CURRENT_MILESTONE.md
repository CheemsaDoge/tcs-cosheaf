# Current Milestone

## Milestone

Phase 8 Task 8.4: v0.2.0 milestone proposal.

## Goal

Close Phase 8 hardening by proposing the next bounded milestone after the
current pre-MVP scaffold. This task is documentation-only and must not change
framework behavior, artifact schema, gate semantics, verifier adapters,
accepted-promotion policy, public KB content, workspace-template behavior, or
runtime dependencies.

## Current Baseline

- Framework package metadata currently records version `0.1.1`.
- Remote tag `v0.1.1` exists and remains the downstream formal-link metadata
  baseline. Current `main` also contains later hardening work that is not part
  of that tag.
- `tcs-cosheaf` is the framework package for CLI, schema, validation, gates,
  index/query, context packs, local task/orchestrator dry-runs, verifier
  adapters, evaluation, and observability scaffolding.
- `tcs-kb-public` is the reusable public KB and must stay public, citable,
  source-reviewed, and human-reviewed before accepted knowledge is added.
- `tcs-cosheaf-workspace-template` is the user-facing entry point with readonly
  public KB plus writable private KB overlay.
- Workspace-template productization is complete for the current scope: demo,
  Makefile shortcuts, public KB bootstrap guidance, onboarding docs, showcase
  docs, and CI smoke coverage have landed.
- Public KB policy-first work is in place: contribution/review guidance,
  graph-foundation backlog, source-note convention, and policy CI guard exist.
- MarkItDown local source ingestion exists only as an optional staging adapter.
  It cannot write accepted artifacts, gate evidence, verifier evidence, human
  review, or promotion evidence.
- Deterministic librarian work is implemented through artifact cards, lexical
  and SQLite FTS/BM25 search, memory graph/PageRank, Personalized PageRank, and
  context-pack v2 integration.
- Local orchestrator work is implemented as explicit state-machine contracts,
  deterministic planner stubs, reducer and worker-bundle v2 validation, local
  worker-runner integration, and local-only dry-run workflow. It is not hosted
  LLM execution.
- The provider-neutral model interface exists with deterministic fake-provider
  tests. Hosted provider integration is not enabled as a default runtime path.
- Headroom, CodeGraph, and Understand-Anything are documented as optional
  developer or experiment surfaces only; they do not alter artifact truth,
  retrieval truth, gate input, verifier input, review, or promotion.
- Formal-link metadata, formal library manifest schema, G10 hardening, and a
  draft formal-link pilot are in place.
- Optional external Lean-library `#check` support is implemented on current
  `main` by `LeanLibraryRefAdapter` for linked or checked Lean 4
  formalization metadata when Lean or lake is available. It requires a later
  release tag before downstream pinned work can rely on it.
- Missing Lean/lake remains `skipped`, not `pass`.
- A successful external Lean `#check` means only that the import and symbol
  resolved; it does not prove informal/formal semantic alignment.
- Retrieval/context evals, structured run logs, and optional OpenTelemetry run
  log export scaffolding are implemented. Telemetry is optional and disabled
  unless configured.

## Proposed v0.2.0 Scope

`v0.2.0` should be a bounded local-MVP milestone. It should package and polish
the existing deterministic workflow rather than introduce a production agent
platform.

Included scope:

- Librarian v1 usability and evaluation.
- Context pack v2 as the default card-first context handoff.
- Local orchestrator state machine and local-only dry-run ergonomics.
- Fake provider model interface for deterministic provider-neutral tests.
- Retrieval evaluation harness and regression metrics.
- Optional external Lean `#check` ergonomics only if the current checker remains
  stable, optional, and honest about its narrow meaning.

Explicit non-goals:

- Production hosted multi-agent system.
- Automatic theorem proving.
- Automatic accepted promotion.
- Web UI.
- Multi-user authentication or permissions.
- Full CSLib/mathlib ingestion, vendoring, or semantic-alignment automation.

## Completion Criteria

- `docs/ROADMAP.md` records the concrete `v0.2.0` proposal.
- `docs/ADR/0014-v020-scope.md` records the milestone-scope decision.
- This milestone file no longer points at completed Phase 8 Task 8.1 work.
- The proposal remains conservative about hosted LLMs, Lean, CSLib, mathlib,
  review, gates, and promotion.
- Required local commands are run and reported honestly.

## Next Focus

After Phase 8 Task 8.4 lands, continue from the next unfinished item in
`longplan_fixed.md` or run a requirement-by-requirement audit before declaring
the documentation update and code audit objective complete.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
