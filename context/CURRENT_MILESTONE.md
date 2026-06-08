# Current Milestone

## Milestone

Phase 6 Task 6.4: formal link pilot.

## Goal

Add one minimal formal-link pilot showing metadata and optional external Lean
library reference checking without claiming accepted knowledge, automatic
proof, or informal/formal alignment.

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
- Phase 4 Task 4.3 reducer and worker bundle v2 is complete in
  `cosheaf.agent.worker_bundle_v2` and
  `schemas/worker_bundle_v2.schema.json`.
- Phase 4 Task 4.4 local worker runner integration is complete in
  `cosheaf.agent.orchestrator_runner` and
  `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only`.
- Phase 4 Task 4.5 agent dry-run workflow is complete in
  `cosheaf.agent.dry_run_workers` and
  `examples/issues/issue.agent-dry-run.demo.yaml`.
- Phase 6 Task 6.3 Formal Link Gate hardening is complete. G10 consumes
  normalized verifier results when policy requires a Lean check, but still
  does not execute Lean.
- Framework package version is `0.1.1`.
- `tcs-cosheaf` has workspace-aware validation, gatekeeper G1-G10,
  deterministic index rebuilds, read-only query surfaces, artifact-card
  retrieval, memory graph/PageRank surfaces, context-pack v2, local task-runner
  scaffolding, an orchestrator state-machine contract, and minimal optional
  SAT, SMT, plain Lean, and external Lean library reference verifier adapters.
- Formal-link metadata is implemented as artifact metadata, G10 gate checks,
  context-pack display, index/query output, and one draft Lean core pilot.
- External Lean-library `#check` for linked Lean formalization references is
  available as an optional verifier adapter. Missing Lean/lake remains
  `skipped`, not `pass`.
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

- Exactly one minimal pilot artifact or example is added for formal-link
  metadata and optional `#check`.
- The pilot remains draft/example material and is not promoted to accepted
  knowledge.
- The formalization is not marked `checked` unless a checker result is actually
  recorded as pass.
- Alignment is not marked `human_reviewed` without real human review metadata.
- Missing Lean/lake remains `skipped`, not `pass`.
- No accepted-promotion policy path is changed.

## Next Focus

After Phase 6 Task 6.4 lands, the next fixed-plan item is Phase 7 Task 7.1:
retrieval eval harness. Do not expand this task into hosted LLM execution,
agent runtime work, public KB artifact batches, web UI work, or
accepted-promotion policy changes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
