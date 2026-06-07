# Current Milestone

## Milestone

Phase 4 Task 4.4: local worker runner integration.

## Goal

Integrate deterministic orchestrator plans with the existing local command
runner while keeping execution local-only, dry-run oriented, and outside the
accepted-knowledge path.

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

- `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only` is
  available as the required local-only CLI surface.
- The local runner creates issue-scoped task records for planned nodes and runs
  explicit argv commands through the existing `LocalWorkerRunner`.
- Worker command execution keeps `shell=False`, repository-local cwd, and a
  required timeout through the existing local runner boundary.
- stdout, stderr, command metadata, exit code, bundle path, reducer results,
  and stop conditions are persisted in inspectable run records.
- Worker bundle v2 validation and reduction are required before a dry-run is
  considered completed.
- Timeout and unsafe proposed accepted-output paths are covered by tests.
- No hosted LLM, network, gate execution, human review request, accepted write,
  promotion, schema change, verifier semantic change, or public/private KB
  policy change is introduced.

## Next Focus

After Phase 4 Task 4.4 lands, the next fixed-plan item is Phase 4 Task 4.5:
agent dry-run workflow. Do not jump ahead into hosted LLM execution, external
Lean checking, web UI work, or accepted-promotion policy changes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
