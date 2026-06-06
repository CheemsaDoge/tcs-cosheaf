# Current Milestone

## Milestone

Phase 0 three-repository state audit for MVP productization.

## Goal

Record the actual current state of `tcs-cosheaf`, `tcs-kb-public`, and
`tcs-cosheaf-workspace-template` before later longplan phases add new
capabilities. The current task is documentation-only and must not change
application code, schemas, gate behavior, accepted-promotion semantics, or KB
artifacts.

## Current Baseline

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
  has demo, Makefile, public-KB bootstrap guidance, and CI smoke coverage.
- `tcs-kb-public` currently has 19 accepted public artifacts. Their
  formalization references are planned metadata, not Lean-checked results.

## Completion Criteria

- `docs/CODEX_STATE_AUDIT.md` exists and answers the Phase 0 Task 0.1 audit
  questions.
- `context/PROJECT_STATE.md` points to the audit and remains consistent with
  the current v0.1.1 framework baseline.
- This milestone file no longer describes the stale v0.1.0 release-candidate
  cleanup state.
- No code, schema, gate, promotion-policy, workflow-behavior, or KB artifact
  changes are included in this task.
- Required validation commands are run when available, and unavailable commands
  are reported honestly.

## Next Focus

After this audit lands, continue with the next `longplan.md` task. Do not jump
into implementation phases until the durable in-repository development plan is
reconciled with this audit and the already-merged workspace-template work.

Maintain the current maintainer override for this run: do not add `codex`
prefixes to issue names, branch names, or PR titles.
