# Current Milestone

## Milestone

Phase 2 Task 2.4: MarkItDown local source-ingestion adapter.

## Goal

Add an optional local-file MarkItDown adapter for converting repository-local
source files into staged Markdown with provenance metadata, while preserving
the source-ingestion boundary.

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
- MarkItDown, Headroom, CodeGraph, and Understand-Anything are not default
  dependencies.
- Phase 0 Task 0.3 recorded external-tool boundaries in
  `docs/EXTERNAL_TOOLS.md` and
  `docs/ADR/0011-external-tooling-boundaries.md`.
- Phase 2 Task 2.3 recorded the source-ingestion boundary in
  `docs/SOURCE_INGESTION.md` and
  `docs/ADR/0012-source-ingestion-boundary.md`.

## Completion Criteria

- `cosheaf ingest convert <path>` converts a repository-local source file into
  staged Markdown and provenance metadata when optional MarkItDown support is
  installed.
- `cosheaf ingest convert <path> --metadata-json` emits deterministic
  provenance JSON.
- Missing MarkItDown reports unavailable with install guidance and does not
  affect validation, gates, index rebuilds, context packs, promotion, or
  default installation.
- Provenance records the original path, input SHA-256, converter name/version,
  timestamp, options, warnings, output path, and metadata path.
- URL, OCR, plugins, LLM vision, and Azure Document Intelligence remain
  disabled by default.
- Source and output paths must stay inside the repository, and accepted KB
  output paths are rejected.
- Converted Markdown may feed source notes, explorer tasks, or draft proposals
  only.
- The adapter does not write artifact YAML, review records, verifier results,
  accepted knowledge, or promotion evidence.
- No schema, gate, verifier, promotion, public/private KB, workspace root, or
  default dependency changes in this task.

## Next Focus

After Phase 2 Task 2.4 lands, the next fixed-plan item is Phase 2 Task 2.5:
add exactly one small public foundation artifact in `tcs-kb-public`, only if
reliable source metadata and required review evidence are available. Prefer
draft status unless accepted-policy evidence is complete.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
