# Current Milestone

## Milestone

Phase 0 Task 0.3: external tool decisions.

## Goal

Record durable boundaries for MarkItDown, Headroom, CodeGraph, and
Understand-Anything before any tool adapter, dependency, script, CI path, or
runtime behavior is added.

## Current Baseline

- Phase 0 Task 0.1 is complete in `docs/CODEX_STATE_AUDIT.md`.
- Phase 0 Task 0.2 is complete in `docs/CODEX_DEVELOPMENT_PLAN.md` and
  `docs/ADR/0008-agent-memory-runtime-roadmap.md`.
- Phase 3 Task 3.7 context-pack v2 integration is complete.
- Phase 4 Task 4.1 orchestrator state model is complete in
  `cosheaf.agent.orchestrator_state`,
  `schemas/orchestrator_run.schema.json`, and
  `docs/ADR/0010-orchestrator-state-machine.md`.
- Framework package version is `0.1.1`.
- `tcs-cosheaf` has workspace-aware validation, gatekeeper G1-G10,
  deterministic index rebuilds, read-only query surfaces, artifact-card
  retrieval, memory graph/PageRank surfaces, context-pack v2, local task-runner
  scaffolding, an orchestrator state-machine contract, and minimal optional
  SAT, SMT, and plain Lean verifier adapters.
- Formal-link metadata is implemented as artifact metadata, G10 static gate
  checks, context-pack display, and index/query output.
- External Lean-library `#check` for CSLib/mathlib references is not
  implemented.
- Hosted LLM worker execution is not implemented.
- MarkItDown, Headroom, CodeGraph, and Understand-Anything are not installed,
  not default dependencies, and not part of runtime behavior.

## Completion Criteria

- `docs/EXTERNAL_TOOLS.md` records per-tool license, install surface, data
  boundary, default state, allowed outputs, gitignore/cache expectations,
  fallback behavior, and rollback triggers.
- `docs/ADR/0011-external-tooling-boundaries.md` records the architectural
  decision before implementation begins.
- MarkItDown is documented as opt-in source ingestion only, not gate, review,
  verifier, promotion, or accepted-knowledge truth.
- Headroom is documented as Phase 5+ default-off compression experiment only,
  never canonical retrieval, gate, YAML, audit, accepted-KB, or project-memory
  input.
- CodeGraph is documented as optional dev-only code navigation and impact
  analysis, not runtime or CI truth.
- Understand-Anything is documented as isolated manual onboarding only, not
  runtime, default CI, package dependency, retrieval, memory, or KB truth.
- No adapter code, package dependency, schema, gate, verifier, promotion,
  public/private KB behavior, or runtime behavior changes in this task.

## Next Focus

After Phase 0 Task 0.3 lands, self-audit earlier fixed-plan tasks before
continuing. The next known gap is Phase 2 source-ingestion policy for
MarkItDown before any MarkItDown adapter code is added.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
