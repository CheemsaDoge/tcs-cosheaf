# Current Milestone

## Milestone

Phase 4 Task 4.5: agent dry-run workflow.

## Goal

Demonstrate an end-to-end local agent dry-run workflow where fake reasoner and
verifier workers produce worker bundle proposals only, while review, gates, and
promotion remain separate.

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

- `examples/issues/issue.agent-dry-run.demo.yaml` and
  `examples/claims/claim.agent-dry-run.demo.yaml` provide a draft-only demo
  issue and claim.
- The default local orchestrator dry-run worker writes role-aware worker bundle
  v2 manifests for fake reasoner, verifier, and orchestrator steps.
- Generated bundle proposal paths stay under
  `.cosheaf/orchestrator/.../proposals/`; the dry-run does not write proposal
  artifacts or `kb/accepted/` records.
- The verifier dry-run records that no gate, Lean, SAT, SMT, or promotion
  result was produced and must not be treated as a verifier pass.
- Tests cover the end-to-end dry-run workflow and CLI smoke path.
- No hosted LLM, network, human review request, gate execution, accepted write,
  promotion, schema change, verifier semantic change, or public/private KB
  policy change is introduced.

## Next Focus

After Phase 4 Task 4.5 lands, the next fixed-plan item is Phase 4 Task 4.6:
CodeGraph dev-only impact-analysis integration. Do not jump ahead into hosted
LLM execution, external Lean checking, web UI work, or accepted-promotion policy
changes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
