# Current Milestone

Milestone: **v0.7.0 Bounded Research Loop + Attempt Memory**

Status: **in progress**

Started: 2026-06-17

Previous milestone: v0.6.0 Operator Session + Review Handoff (completed 2026-06-16)

## Objective

Turn the v0.6.0 operator session and review handoff layer into a bounded multi-attempt research loop harness. Enable external operators to explore multiple directions within budget, record failures as useful memory, detect repeat failures, and hand off complete loop audit trails for review.

## Scope

### In scope

- Research loop data model, storage, CLI, schemas, tests, and docs (Phase B
  complete)

- Loop runner with deterministic next-action planning (Phase C.1 complete)
- External operator task packet export and result import protocol (Phase C.1
  complete)
- Attempt-memory index and repeat-failure detection
- Failure-avoidance context injection into next attempts
- Loop scanner extending session scanner coverage
- Ecosystem demos and eval matrix for research-loop workflows
- Conservative v0.7.0 RC and publication closeout

### Out of scope

- Production autonomous AI mathematician
- Automatic theorem proving
- Accepted promotion through loop results
- AI as human review
- Default hosted provider calls
- Unrestricted shell execution
- Automatic Lean/mathlib/CSLib semantic alignment
- Replacing validation/gate/review/promotion

## Key deliverables

1. Research loop model and storage (Phase B)
2. Loop runner and operator protocol (Phase C)
3. Attempt memory and scanner (Phase D)
4. Ecosystem demos and eval (Phase E)
5. v0.7.0 release candidate and publication (Phase F)

## Current phase

**Phase D: attempt memory, repeat-failure detection, and loop scanner**

Task B.1: bounded-research-loop-core (completed)
Task C.1: research-loop-runner-and-operator-protocol (completed on branch
`research-loop-runner-and-operator-protocol`, issue #402)

Current C.1 status:

- service and CLI implementation is present for `next`, `step`, `run
  --dry-run`, `export-task`, and `import-result`;
- C.1 DTO schemas are present under `schemas/`;
- focused C.1 regression coverage is present for deterministic planning,
  dry-run write boundaries, operator task export, operator result import,
  authority rejection, missing result/failure rejection, previous-failure
  surfacing, and budget exhaustion;
- non-dry-run loop execution remains refused until a later explicit
  deterministic implementation.

Next milestone work should start from Phase D. C.1 does not include
attempt-memory clustering, scanner CLI, loop handoff export, hosted provider
calls, automatic theorem proving, or Lean semantic alignment.

## Non-negotiable invariants

- Loop attempts cannot write `kb/accepted/`
- Loop attempts cannot create human review
- Loop attempts cannot mutate verifier results
- Skipped remains skipped
- Public mode cannot leak private content
- Scanner blocks unsafe exports
- CLI remains oracle
- MCP remains optional adapter
- No real provider/network/API-key in CI/default tests
- Loop success never means accepted status

## Framework package version

Current: `0.6.0`
Target: `0.7.0`

## References

- Plan: [`docs/CODEX_DEVELOPMENT_PLAN_V11.md`](../docs/CODEX_DEVELOPMENT_PLAN_V11.md)
- ADR: [`docs/ADR/0028-bounded-research-loop-attempt-memory.md`](../docs/ADR/0028-bounded-research-loop-attempt-memory.md)
- Audit: [`docs/POST_V060_STATE_AUDIT.md`](../docs/POST_V060_STATE_AUDIT.md)
- Roadmap: [`docs/ROADMAP.md`](../docs/ROADMAP.md)
