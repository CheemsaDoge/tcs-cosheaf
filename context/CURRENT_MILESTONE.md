# Current Milestone

Milestone: **v0.8.0 Deterministic Worker Loop + Local Action Registry**

Status: **kickoff (Phase A.1 in progress)**

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
- Attempt-memory index and repeat-failure detection (Phase D.1 complete)
- Failure-avoidance context injection into next attempts (Phase D.1 complete)
- Loop scanner extending session scanner coverage (Phase D.1 complete)
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
4. Ecosystem demos and eval (Phase E complete)
5. v0.7.0 release candidate and publication (Phase F)

## Current phase

**Phase F: v0.7.0 release candidate and publication closeout**

Task B.1: bounded-research-loop-core (completed)
Task C.1: research-loop-runner-and-operator-protocol (completed on branch
`research-loop-runner-and-operator-protocol`, issue #402)
Task D.1: attempt-memory-failure-avoidance-scanner (completed on branch
`attempt-memory-failure-avoidance-scanner`, issue #404)
Task E.1: research-loop-eval-and-ecosystem-demo (completed through framework
PR #407, workspace-template PR #77, and public-KB PR #92)

Current v0.7.0 status:

- service and CLI implementation is present for `next`, `step`, `run
  --dry-run`, `export-task`, and `import-result`;
- C.1 DTO schemas are present under `schemas/`;
- focused C.1 regression coverage is present for deterministic planning,
  dry-run write boundaries, operator task export, operator result import,
  authority rejection, missing result/failure rejection, previous-failure
  surfacing, and budget exhaustion;
- D.1 adds `.cosheaf/research-loops/attempt-memory.json`, deterministic
  failure clustering, cross-loop repeat-failure surfacing, required
  `retry_justification` for repeated directions, `cosheaf research-loop scan`,
  and runtime scanner metrics;
- focused D.1 regression coverage is present for memory-index persistence,
  repeat clustering, cross-loop failure surfacing, unjustified retry refusal,
  justified retry recording, scanner blocking, scanner clean path, and schema
  file presence;
- framework E.1 work adds `cosheaf eval research-loop --json`, default cases
  under `evals/research_loop/cases.yaml`, a research-loop workflow smoke row,
  a workspace-template `research-loop-demo` matrix row, and a public-KB
  research-loop policy-docs matrix row;
- workspace-template PR #77 adds `make research-loop-demo` and
  `scripts/demo_research_loop.sh`, using a local or otherwise explicit
  v0.7-capable framework source while preserving the published `v0.6.0`
  install pin;
- public-KB PR #92 adds `docs/RESEARCH_LOOP_POLICY.md` and policy guard
  coverage rejecting research-loop output as source metadata, accepted proof,
  human review, verifier/gate pass, accepted status, or promotion authority;
- a no-network three-repository matrix run passed with 25 rows: 22 pass, 0
  fail, and 3 expected skipped rows for optional verifier availability,
  framework git-tag network release smoke, and workspace-template network
  install demo;
- non-dry-run loop execution remains refused until a later explicit
  deterministic implementation.

Next milestone: v0.8.0 Deterministic Worker Loop + Local Action Registry.
Phases: A (kickoff), B (action registry), C (loop execution),
D (worker profiles), E (ecosystem), F (release).

Plan: docs/CODEX_DEVELOPMENT_PLAN_V12.md
ADR: docs/ADR/0029-deterministic-worker-loop-action-registry.md
Audit: docs/POST_V070_STATE_AUDIT.md

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
