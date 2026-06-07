# Current Milestone

## Milestone

Phase 6 Task 6.3: Formal Link Gate hardening.

## Goal

Harden G10 Formal Link Gate so checked formal-link metadata cannot be treated
as a Lean pass without matching verifier evidence, while preserving the
boundary that G10 does not execute Lean or prove informal/formal alignment.

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
- Framework package version is `0.1.1`.
- `tcs-cosheaf` has workspace-aware validation, gatekeeper G1-G10,
  deterministic index rebuilds, read-only query surfaces, artifact-card
  retrieval, memory graph/PageRank surfaces, context-pack v2, local task-runner
  scaffolding, an orchestrator state-machine contract, and minimal optional
  SAT, SMT, plain Lean, and external Lean library reference verifier adapters.
- Formal-link metadata is implemented as artifact metadata, G10 gate checks,
  context-pack display, and index/query output.
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

- G10 resolves artifact `library_ref` values against a local formal library
  manifest and blocks missing or unknown manifest references when
  formalization links are present.
- G10 requires `import_path` and `symbol` metadata for `linked` and `checked`
  formalization references.
- G10 requires a matching Lean verifier `pass` when
  `verification_policy.require_lean_check` is true; skipped, failed, or errored
  verifier results are not passes.
- Planned formalizations remain metadata and are not treated as checked.
- Alignment review remains separate from Lean checking.
- No Lean execution is added to G10, no external library fetch is added, and no
  accepted-promotion policy path is changed beyond ordinary gatekeeper
  blocking behavior.

## Next Focus

After Phase 6 Task 6.3 lands, the next fixed-plan item is Phase 6 Task 6.4:
formal link pilot. Do not expand this task into hosted LLM execution, agent
runtime work, public KB artifact batches, web UI work, or accepted-promotion
policy changes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
