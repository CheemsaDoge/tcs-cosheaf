# Current Milestone

## Milestone

Phase 3 Task 3.1: memory policy docs and ADR.

## Goal

Add durable memory-policy documentation before librarian implementation starts.
This task is documentation-only and must not change application code, schemas,
gate behavior, accepted-promotion semantics, verifier behavior, or KB
artifacts.

## Current Baseline

- Phase 0 Task 0.1 is complete in `docs/CODEX_STATE_AUDIT.md`.
- Phase 0 Task 0.2 is complete in `docs/CODEX_DEVELOPMENT_PLAN.md` and
  `docs/ADR/0008-agent-memory-runtime-roadmap.md`.
- Phase 1 workspace-template reconciliation and Phase 2 public-KB policy
  groundwork have landed in their respective repositories.
- Framework package version is `0.1.1`.
- `tcs-cosheaf` has workspace-aware validation, gatekeeper G1-G10, deterministic
  index rebuilds, a Python query API, context-pack generation, local task-runner
  scaffolding, and minimal optional SAT, SMT, and plain Lean verifier adapters.
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

- `docs/MEMORY_POLICY.md` records hot/warm/cold memory, artifact cards,
  retrieval request/result schemas, graph nodes and edges, ranking formula,
  sidecar files, public/private filtering, the no-whole-repo-dump rule, and
  librarian authority boundaries.
- `docs/ADR/0009-librarian-memory-policy.md` records why the librarian starts
  deterministic-first.
- `docs/ARCHITECTURE.md` includes the planned Memory/Retrieval Layer without
  claiming that librarian code already exists.
- No code, schema, gate, promotion-policy, workflow-behavior, verifier, or KB
  artifact changes are included.
- Required validation commands are run when available, and unavailable commands
  are reported honestly.

## Next Focus

After this documentation-only task lands, continue Phase 3 with Task 3.2:
ArtifactCard and related retrieval request/result models. Do not implement
librarian retrieval, graph ranking, context-pack v2 integration, orchestrator
runtime, hosted LLM workers, or external Lean-library checking in Task 3.1.

Maintain the current maintainer override for this run: do not add `codex`
prefixes to issue names, branch names, or PR titles, even when older examples
show that prefix.
