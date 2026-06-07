# Current Milestone

## Milestone

Phase 4 Task 4.3: reducer and worker bundle v2.

## Goal

Standardize a strict worker bundle v2 contract and deterministic reducer
behavior without executing workers or changing accepted knowledge.

## Current Baseline

- Phase 0 Task 0.1 is complete in `docs/CODEX_STATE_AUDIT.md`.
- Phase 0 Task 0.2 is complete in `docs/CODEX_DEVELOPMENT_PLAN.md` and
  `docs/ADR/0008-agent-memory-runtime-roadmap.md`.
- Phase 2 Task 2.4 MarkItDown local source-ingestion adapter is complete.
- Phase 2 Task 2.5 added exactly one draft public foundation artifact in
  `tcs-kb-public`.
- Phase 3 Task 3.7 context-pack v2 integration is complete.
- Phase 4 Task 4.1 orchestrator state model is complete in
  `cosheaf.agent.orchestrator_state`,
  `schemas/orchestrator_run.schema.json`, and
  `docs/ADR/0010-orchestrator-state-machine.md`.
- Phase 4 Task 4.2 deterministic task-DAG planner stub is complete in
  `cosheaf.agent.orchestrator_planner` and
  `cosheaf orchestrator plan --issue <issue-id> --json`.
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

- `WorkerBundleV2` is strict and records bundle ID, task ID, worker role,
  creation time, summary, used artifacts and sources, claims, proposed
  artifacts, verification requests, failures or counterexamples, risk flags,
  next steps, and confidence.
- `schemas/worker_bundle_v2.schema.json` records the same required fields.
- Worker bundle v2 validation rejects repository-unsafe paths.
- Worker bundle v2 validation rejects proposed writes to accepted KB paths.
- Worker bundle v2 validation rejects worker-created `human_reviewed` or
  `accepted` review states on proposed artifacts.
- The reducer produces a deterministic `ReducerResult` and preserves failures,
  risk flags, and confidence as warnings.
- The v2 reducer does not execute workers, call hosted LLMs, run gates, request
  review, write files, merge outputs, or promote artifacts.
- No schema, gate, verifier, promotion, public/private KB, workspace root, or
  default dependency changes outside the new worker bundle v2 schema in this
  task.

## Next Focus

After Phase 4 Task 4.3 lands, the next fixed-plan item is Phase 4 Task 4.4:
local worker runner integration. Do not jump ahead into hosted LLM execution,
external Lean checking, web UI work, or accepted-promotion policy changes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
