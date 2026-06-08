# Current Milestone

## Milestone

Phase 8 Task 8.1: three-repository release checklist and stale-docs cleanup.

## Goal

Close the current framework documentation gap before showcase work by making
the release checklist, roadmap, project state, and milestone docs match the
actual three-repository implementation. This task is documentation-only and
must not change framework behavior, artifact schema, gate semantics, verifier
adapters, accepted-promotion policy, public KB content, or workspace-template
behavior.

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
  Makefile shortcuts, public KB bootstrap guidance, onboarding docs, and CI
  smoke coverage have landed.
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
- Headroom and CodeGraph are documented as optional developer or experiment
  surfaces only; they do not alter artifact truth, retrieval truth, gate input,
  verifier input, review, or promotion.
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

## Completion Criteria

- `RELEASE_CHECKLIST.md` is actionable for the three-repository release/demo
  workflow.
- Stale claims that external Lean-library reference checking is only future
  work are removed from current-state docs.
- `context/CURRENT_MILESTONE.md` no longer points to Phase 6 Task 6.4 as the
  active milestone.
- `docs/ROADMAP.md` describes the current Phase 8 release-hardening/showcase
  focus and keeps non-goals explicit.
- `context/PROJECT_STATE.md` records that Phase 8 Task 8.1 corrected stale
  release/milestone docs.
- Required local commands are run and reported honestly.

## Next Focus

After Phase 8 Task 8.1 lands, the next fixed-plan item is Phase 8 Task 8.2:
showcase demo docs. Start in `tcs-cosheaf-workspace-template` first, then make
framework documentation updates only if needed.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
