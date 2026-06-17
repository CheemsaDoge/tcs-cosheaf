# ADR 0028: Bounded Research Loop + Attempt Memory

Date: 2026-06-17  
Status: Accepted  
Supersedes: N/A  
Superseded by: N/A

## Context

After v0.6.0 Operator Session + Review Handoff, the TCS-Cosheaf framework can record, audit, and hand off an external operator's work. The operator (e.g., Codex, Claude Code) can:

- Start a session
- Execute bounded commands
- Append check statuses and file references
- Scan for leaks
- Generate a handoff bundle
- Export review context

However, the current model treats each session as a one-shot effort. There is no structure for:

- **Multiple attempts** on the same research issue
- **Failure memory**: recording what was tried and why it failed
- **Repeat-failure detection**: preventing the same failed direction from being tried again without justification
- **Bounded research budget**: max attempts, wallclock time, or other stop conditions
- **Attempt-to-attempt context**: feeding previous failures into the next attempt's planning
- **Research-loop audit**: understanding how many directions were explored before success or abandonment

The project's stated target is not just a better static knowledge base. The target is an **AI research harness** where an external operator can:

1. Receive a research issue
2. Plan a direction
3. Execute one attempt
4. Record results, failures, and evidence
5. Learn from failures
6. Plan the next attempt with failure-avoidance context
7. Repeat within budget
8. Hand off all attempts, failures, and evidence for review

This is the bridge from "Codex can operate Cosheaf" to "Cosheaf can support 100-shot/1000-shot bounded research exploration."

## Decision

We will implement **v0.7.0 Bounded Research Loop + Attempt Memory** as the next accelerated line after v0.6.0.

### Core components

1. **Research loop model**
   - `ResearchLoop`: top-level container for one issue's exploration
   - `ResearchLoopAttempt`: one bounded attempt with plan/execution/result/failure
   - `AttemptFailureRecord`: structured failure with evidence, tags, and avoidance guidance
   - Loop status: `created | running | blocked | finalized | abandoned | failed`
   - Attempt status: `planned | running | succeeded | failed | blocked | inconclusive | abandoned`

2. **Loop storage**
   - `.cosheaf/research-loops/<loop-id>/loop.json`
   - `.cosheaf/research-loops/<loop-id>/attempts/<attempt-id>.json`
   - `.cosheaf/research-loops/<loop-id>/events.jsonl`
   - All runtime, Git-ignored

3. **Loop CLI**
   - `cosheaf research-loop start --issue <issue-id>`
   - `cosheaf research-loop show <loop-id>`
   - `cosheaf research-loop append-attempt <loop-id> --input-json <path>`
   - `cosheaf research-loop finalize <loop-id>`
   - `cosheaf research-loop next <loop-id>`: deterministic next-action planner
   - `cosheaf research-loop step <loop-id>`: execute one bounded step
   - `cosheaf research-loop run <loop-id> --max-attempts <n> --dry-run`
   - `cosheaf research-loop export-task <loop-id> --out <path>`: external operator task packet
   - `cosheaf research-loop import-result <loop-id> --input-json <path>`: structured result import
   - `cosheaf research-loop scan <loop-id>`: leak/privacy/overclaim scanner

4. **Attempt memory and failure avoidance**
   - `.cosheaf/research-loops/attempt-memory.json`: clustered failure index
   - Repeat-failure detection via lexical/signature similarity
   - Next-attempt context includes `previous_failures_to_avoid`
   - Unjustified retry blocked or strongly warned

5. **External operator protocol**
   - **Task packet**: loop exports a bounded task with objective, context, allowed actions, previous failures, budget, and stop conditions
   - **Result import**: operator returns structured result with attempted direction, actions taken, failures, evidence, and next recommendation
   - No hidden model state dependency
   - No accepted-write/promotion/human-review/verifier authority

6. **Scanner integration**
   - Loop scanner extends session scanner
   - Blocks: secrets, provider dumps, hidden reasoning, private content in public mode, accepted-write attempts, promotion/review overclaims
   - Blocker findings prevent handoff export

7. **Evaluation and ecosystem demo**
   - `cosheaf eval research-loop`: deterministic eval fixture
   - Ecosystem smoke rows for loop start/next/import/finalize/scan/handoff
   - Workspace-template `make research-loop-demo`
   - Public KB policy docs for loop exports (review context only, not source/proof)

### What this is NOT

- Production autonomous AI mathematician
- Automatic theorem proving
- Accepted promotion through loop results
- AI as human review
- Default hosted provider
- Unrestricted shell execution
- Automatic Lean/mathlib/CSLib semantic alignment
- Replacement for validation/gate/review/promotion

Loop success never means accepted status. Loop outputs are draft artifacts, checked-evidence candidates, failure logs, and review context only.

### Boundary enforcement

All v0.6.0 invariants remain:

- Loop attempts cannot write `kb/accepted/`
- Loop attempts cannot create human review
- Loop attempts cannot mutate verifier results into pass
- Skipped remains skipped
- Public mode cannot leak private content
- Scanner blocks unsafe exports
- CLI remains the oracle
- MCP remains optional adapter
- No real provider/network/API-key dependency in CI/default tests

## Consequences

### Positive

- External operators can explore multiple directions within budget
- Failures become useful memory, not lost context
- Repeat failures are detected and surfaced before retry
- Loop audit trail is replayable and reviewable
- Bounded budgets prevent runaway exploration
- Deterministic next-action planning (no hidden model state)
- Conservative: no accepted-write/promotion/review authority widening

### Negative

- Adds complexity: loop model, attempt records, failure clustering, task protocol
- Operator must structure results according to import contract
- Loop evaluation requires careful fixture design to avoid test brittleness
- Failure clustering heuristics may have false positives/negatives

### Mitigations

- Keep loop model strict and schema-validated
- Require explicit failure records in every attempt
- Make repeat-failure warnings strong but not absolute blockers (allow justified retries)
- Scanner remains fail-closed: uncertain findings are warnings or blockers, never silently ignored
- Tests use fake/deterministic operations
- Documentation explicitly states what loop success does NOT mean

## Alternatives considered

### A. Continue expanding operator session capabilities

Could add more session tools, more MCP endpoints, more review-handoff features.

**Rejected:** This widens the tool surface without addressing the core bottleneck: making many attempts and learning from failures.

### B. Build a web UI or SaaS deployment first

Could prioritize multi-user permissions, hosted service, or browser interface.

**Rejected:** Premature. The research-loop substrate must work locally and deterministically before becoming a service.

### C. Integrate a production LLM planner

Could add default hosted provider, auto-planning, auto-promotion.

**Rejected:** Violates conservative boundary principles. Loop planning must be deterministic and auditable; model calls remain optional and external.

### D. Add automatic theorem proving or Lean integration as next step

Could focus on formal verification, autoformalization, or proof search.

**Rejected:** Useful later, but research loops are the prerequisite. You cannot explore 100 proof strategies without a loop harness.

## Implementation plan

Accelerated 6-phase structure:

- **Phase A**: post-v0.6.0 audit + V11 ADR (this document)
- **Phase B**: bounded research-loop core (models, storage, CLI)
- **Phase C**: loop runner + external operator task protocol
- **Phase D**: attempt memory / failure avoidance / scanner integration
- **Phase E**: ecosystem demos + eval matrix
- **Phase F**: v0.7.0 RC + publication closeout

Target: conservative v0.7.0 release with explicit limitations, no production-autonomy claims, and strict authority boundaries.

## References

- v0.6.0 release notes
- docs/OPERATOR_SESSIONS.md
- docs/OPERATOR_HANDOFF.md
- docs/POST_V060_STATE_AUDIT.md
- docs/CODEX_DEVELOPMENT_PLAN_V11.md
