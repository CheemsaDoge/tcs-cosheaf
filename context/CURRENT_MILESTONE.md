# Current Milestone

## Milestone

Phase 3 Task 3.7: context pack v2 integration.

## Goal

Integrate local librarian retrieval into context pack generation while
preserving bounded, auditable context. The default context handoff should use
compact `ArtifactCard` rows, keep orchestrator context cards-only by default,
and require an explicit full-artifact budget before writing full YAML into the
generated context pack.

## Current Baseline

- Phase 0 Task 0.1 is complete in `docs/CODEX_STATE_AUDIT.md`.
- Phase 0 Task 0.2 is complete in `docs/CODEX_DEVELOPMENT_PLAN.md` and
  `docs/ADR/0008-agent-memory-runtime-roadmap.md`.
- Phase 1 workspace-template reconciliation and Phase 2 public-KB policy
  groundwork have landed in their respective repositories.
- Framework package version is `0.1.1`.
- `tcs-cosheaf` has workspace-aware validation, gatekeeper G1-G10,
  deterministic index rebuilds, a Python query API, artifact-card retrieval,
  memory graph/PageRank surfaces, local task-runner scaffolding, and minimal
  optional SAT, SMT, and plain Lean verifier adapters.
- Formal-link metadata is implemented as artifact metadata, G10 static gate
  checks, context-pack display, and index/query output.
- External Lean-library `#check` for CSLib/mathlib references is not
  implemented.
- Hosted LLM worker execution is not implemented.
- `tcs-cosheaf-workspace-template` is the user-facing entry point and currently
  has demo, Makefile, public-KB bootstrap guidance, onboarding docs, and CI
  smoke coverage.
- `tcs-kb-public` currently has accepted public artifacts whose formalization
  references remain metadata unless a checker result is explicitly recorded.

## Completion Criteria

- `cosheaf context build` and `cosheaf context show` use `ArtifactCard` rows by
  default.
- The default `orchestrator` role has `max_full_artifacts = 0`.
- Full artifact YAML appears only in `FULL_ARTIFACTS.md` when a caller passes a
  positive `--max-full-artifacts` budget.
- Generated context packs include `RETRIEVAL_AUDIT.json` with request, score,
  exclusion, warning, and full-artifact-pull metadata.
- Public-only context excludes private cards and private artifact IDs from both
  rendered context and audit output.
- Tests cover bounded output, role-specific full-artifact budget behavior, CLI
  options, and private-leakage prevention.
- `docs/MEMORY_POLICY.md`, `docs/ARCHITECTURE.md`, and
  `context/INTERFACE_REGISTRY.md` describe the new context-pack v2 behavior.
- No hosted LLM runtime, agent autonomy, autoformalization, external
  Lean-library checking, artifact schema change, gate behavior change, or
  promotion-policy change is included.

## Next Focus

After Task 3.7 lands, continue with Phase 4 Task 4.1: orchestrator state model.
That task should define explicit serializable state models without changing
runtime behavior, without hosted LLM calls, without auto-promotion, and without
direct accepted writes.

Maintain the current maintainer override for this run: do not add `codex`
prefixes to issue names, branch names, or PR titles, even when older examples
show that prefix.
