# Current Milestone

## Milestone

Phase 0 Task 0.2: durable development plan.

## Goal

Make the current longplan durable repository memory before later implementation
phases proceed. This task is documentation-only and must not change application
code, schemas, gate behavior, accepted-promotion semantics, verifier behavior,
or KB artifacts.

## Current Baseline

- Phase 0 Task 0.1 is complete in `docs/CODEX_STATE_AUDIT.md`.
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
- `tcs-kb-public` currently has 19 accepted public artifacts. Their
  formalization references are planned metadata, not Lean-checked results.

## Completion Criteria

- `docs/CODEX_DEVELOPMENT_PLAN.md` records the three-repo responsibilities,
  global invariants, phased roadmap, concrete Phase 1 follow-up tasks,
  explicit non-goals, stop rules, and one task / one branch / one PR rule.
- `docs/ADR/0008-agent-memory-runtime-roadmap.md` records why deterministic
  librarian and orchestrator work belongs inside `tcs-cosheaf` rather than a
  fourth core repository.
- This milestone file points to the durable plan rather than the completed
  Task 0.1 audit as the active task.
- No code, schema, gate, promotion-policy, workflow-behavior, verifier, or KB
  artifact changes are included.
- Required validation commands are run when available, and unavailable commands
  are reported honestly.

## Next Focus

After this documentation-only task lands, continue the longplan from the next
task. Because the state audit confirms that much of Phase 1 workspace-template
productization already exists, begin any Phase 1 work with a focused
reconciliation against the exact longplan requirements instead of duplicating
already merged template features.

Maintain the current maintainer override for this run: do not add `codex`
prefixes to issue names, branch names, or PR titles, even when older examples
show that prefix.
