# Current Milestone

## Milestone

Phase 2 Task 2.3: source ingestion policy for MarkItDown.

## Goal

Define a safe source-ingestion boundary before any MarkItDown adapter,
dependency, CLI command, script, CI path, schema, gate, verifier, promotion, or
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
- Phase 0 Task 0.3 recorded external-tool boundaries in
  `docs/EXTERNAL_TOOLS.md` and
  `docs/ADR/0011-external-tooling-boundaries.md`.

## Completion Criteria

- `docs/SOURCE_INGESTION.md` records source ingestion as staging only, not
  validation, gatekeeping, verification, human review, accepted knowledge, or
  promotion evidence.
- `docs/ADR/0012-source-ingestion-boundary.md` records the architectural
  decision before implementation begins.
- MarkItDown is documented as a future optional local-file converter that must
  preserve provenance: original path, input hash, converter version, timestamp,
  options, warnings, output path, and execution metadata where applicable.
- Converted Markdown may feed source notes, explorer tasks, or draft proposals
  only.
- URL, OCR, plugins, LLM vision, and Azure Document Intelligence remain
  disabled by default.
- Untrusted input must run through a bounded subprocess or documented sandbox
  boundary.
- No adapter code, package dependency, CLI command, script, schema, gate,
  verifier, promotion, public/private KB behavior, or runtime behavior changes
  in this task.

## Next Focus

After Phase 2 Task 2.3 lands, the next fixed-plan item is Phase 2 Task 2.4:
implement the optional local-file MarkItDown source-ingestion adapter. That
implementation must follow `docs/SOURCE_INGESTION.md` and keep MarkItDown
optional.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
