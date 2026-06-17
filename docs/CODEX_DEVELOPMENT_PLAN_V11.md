# TCS-Cosheaf Development Plan V11

Target: `v0.7.0 Bounded Research Loop + Attempt Memory`

This is the accelerated post-`v0.6.0` plan.

The previous line, `v0.6.0 Operator Session + Review Handoff`, made external-operator work replayable and reviewable. The next line should turn that replayable session layer into a bounded multi-attempt research loop: issue-scoped, budgeted, resumable, auditable, failure-aware, and still unable to write accepted knowledge.

One-sentence goal:

```text
Turn operator sessions and strategy plans into a bounded 100-shot/1000-shot research-loop harness that records every attempt, avoids repeated failed directions, produces review handoffs, and remains safely outside accepted-knowledge authority.
```

## 0. Acceleration rules

Use larger PRs than before. Do not split every DTO, CLI command, eval, and doc update into separate tasks unless the repository state forces it.

```text
1. One task = one branch = one PR.
2. No direct main pushes.
3. No branch/PR/issue title may use `codex/`, `codex-`, or any agent-specific prefix.
4. Each task may include code + tests + docs + interface registry updates when they are part of the same functional slice.
5. Do not create tiny docs-only followups unless the implementation is already too large or risky.
6. Every task must inspect actual code, CLI, tests, schemas, runtime paths, and current docs before editing.
7. If tests or commands cannot run, report the exact reason. Do not claim success.
8. Skipped is not pass.
9. Any runtime output must stay under ignored `.cosheaf/` paths unless an explicit review-context export is requested.
10. Never let loop/session/operator output become accepted knowledge, human review, verifier pass, gate pass, source metadata, accepted refutation, or promotion authority.
```

## 1. Current verified baseline

```text
Framework version: 0.6.0
Published release: v0.6.0
Completed line: Operator Session + Review Handoff
Downstream workspace-template pin: @v0.6.0
Downstream public KB CI pin: @v0.6.0
Open blocking issues/PRs at planning time: none observed
```

Relevant completed capabilities:

```text
- operator session DTOs and storage under `.cosheaf/operator-sessions/`
- session CLI start/show/append-check/append-ref/finalize/scan
- optional MCP session recording for whitelisted calls
- deterministic leak scanner
- operator handoff build/show
- explicit review-context handoff export under `reviews/operator/`
- workspace-template operator-session demo
- public KB operator-handoff policy and guard checks
- ecosystem smoke rows for session/handoff workflows
```

## 2. Why this line comes next

The project target is not just a better static knowledge base. The target is an AI research harness where an external operator can make many attempts, remember failures, reuse reviewed knowledge, and hand off outputs for review.

After `v0.6.0`, the system can record and hand off a session. The missing capability is the actual loop structure:

```text
issue -> plan -> attempt -> check -> failure/evidence memory -> next attempt -> stop/handoff
```

This is the bridge from 鈥淐odex can operate Cosheaf鈥?to 鈥淐osheaf can support 100-shot/1000-shot research exploration.鈥?
## 3. Non-goals for v0.7.0

Do not implement:

```text
- production autonomous AI mathematician
- automatic theorem proving
- automatic accepted promotion
- AI as human review
- default hosted provider calls
- real provider calls in CI/default tests
- web UI / SaaS / multi-user permissions
- unrestricted shell execution
- automatic Lean/mathlib/CSLib semantic alignment
- public KB content expansion unless explicitly scoped
```

`v0.7.0` is a bounded research-loop substrate, not a claim of solved autonomy.

## 4. Invariants

### 4.1 Knowledge authority

```text
- accepted artifacts still require validation/gate/review/promotion.
- loop attempts may create draft artifacts, worker bundles, checked-evidence candidates, failure-log entries, research-run records, operator sessions, and review-context handoffs only.
- loop attempts may not write `kb/accepted/`.
- loop attempts may not mark human review.
- loop attempts may not mutate verifier results into pass.
- loop success never means accepted status.
```

### 4.2 Failure memory

Every loop attempt must preserve failures explicitly.

```text
Required failure fields:
- attempted_direction
- why_it_failed
- evidence_for_failure
- related_artifacts
- related_previous_attempts
- counterexample_candidate_ids
- checked_counterexample_ids
- verifier_or_gate_errors
- should_retry
- retry_conditions
- avoid_in_future
```

Failure records are useful memory, not shameful noise. The loop must make it harder to repeat the same failed direction without justification.

### 4.3 Privacy and public/private policy

```text
- public mode cannot include private artifact IDs, private paths, private issue tags, secrets, provider dumps, hidden reasoning, or raw environment data.
- private research mode must be explicit.
- handoff export to public KB must remain review context only and pass public KB policy guards.
- scanner status must block export when blocking findings exist.
```

### 4.4 Provider and MCP

```text
- CLI remains the oracle.
- MCP remains optional local adapter.
- hosted provider remains default-off.
- no real provider/network/API-key dependency in CI/default tests.
- all model-like behavior in tests must be fake/mocked/deterministic.
```

## 5. Phase plan

Accelerated structure: 6 functional phases, with 5 implementation PRs plus release closeout.

```text
Phase A: post-v0.6.0 audit + V11 ADR
Phase B: bounded research-loop core
Phase C: loop runner + external operator task protocol
Phase D: attempt-memory / failure-avoidance / scanner integration
Phase E: ecosystem demos + eval matrix
Phase F: v0.7.0 RC + publication closeout
```

---

# Phase A: post-v0.6.0 audit + V11 ADR

## Task A.1: post-v060-v070-kickoff

```text
Repository:
  tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.

Branch:
  post-v060-v070-kickoff

Goal:
  Verify the completed v0.6.0 state and land the accelerated v0.7.0 bounded research-loop plan.

Create/update only:
  docs/POST_V060_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V11.md
  docs/ADR/0028-bounded-research-loop-attempt-memory.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required audit checks:
  - package version is 0.6.0
  - v0.6.0 tag and release are published
  - workspace-template active pins are @v0.6.0
  - public KB CI pin is @v0.6.0
  - open PRs/issues across the three repos
  - operator session storage exists
  - session scan CLI exists
  - handoff build/show/export CLI exists
  - review-context export remains non-authoritative
  - no accepted writes/promotion/human-review authority added
  - no default hosted provider or real provider CI dependency

Do not:
  implement research-loop runtime
  add schemas
  add dependencies
  change CLI behavior
  bump version
  write KB artifacts

Run:
  make lint
  make typecheck
  make test
  make validate
  make gate
  git diff --check

Stop after this task.
```

Acceptance:

```text
- v0.6.0 completion audit is factual.
- V11 plan is durable repo memory.
- ADR explains why the next step is bounded loop + attempt memory, not web UI or production autonomy.
- No runtime behavior changed.
```

---

# Phase B: bounded research-loop core

## Task B.1: bounded-research-loop-core

```text
Repository:
  tcs-cosheaf

Branch:
  bounded-research-loop-core

Goal:
  Implement the core research-loop data model, storage, CLI, schemas, tests, and docs in one functional slice.
```

Required models:

```text
ResearchLoop
ResearchLoopAttempt
ResearchLoopBudget
ResearchLoopStopCondition
ResearchLoopDecision
AttemptFailureRecord
AttemptEvidenceSummary
AttemptPolicyFinding
AttemptNextAction
LoopReviewSummary
```

Required storage:

```text
.cosheaf/research-loops/<loop-id>/loop.json
.cosheaf/research-loops/<loop-id>/attempts/<attempt-id>.json
.cosheaf/research-loops/<loop-id>/events.jsonl
```

Required CLI:

```text
cosheaf research-loop start --issue <issue-id> --json
cosheaf research-loop show <loop-id> --json
cosheaf research-loop append-attempt <loop-id> --input-json <path> --json
cosheaf research-loop finalize <loop-id> --json
```

Required behavior:

```text
- start creates deterministic runtime state under `.cosheaf/research-loops/`.
- append-attempt validates attempt records before storing them.
- every attempt requires either result, failure, or blocked status.
- failure records are first-class, not optional notes.
- attempts can reference operator sessions, research runs, strategy plans, checked-evidence records, draft artifacts, and handoff bundles by safe reference.
- accepted KB paths are forbidden.
- session/loop runtime outputs are ignored by Git.
```

Required statuses:

```text
loop: created | running | blocked | finalized | abandoned | failed
attempt: planned | running | succeeded | failed | blocked | inconclusive | abandoned
```

Tests:

```text
- model serialization
- schema validation
- invalid status transition
- accepted-write/path rejection
- missing failure/result rejection
- deterministic storage path
- no private leakage in public mode
- CLI JSON smoke
```

Docs/update:

```text
- docs/RESEARCH_LOOPS.md
- docs/CODEX_OPERATOR_RUNBOOK.md
- docs/SECURITY.md
- context/INTERFACE_REGISTRY.md
- context/CURRENT_MILESTONE.md
- context/PROJECT_STATE.md
```

Acceptance:

```text
- A loop can be created, shown, appended, and finalized.
- A failed attempt is as structured and inspectable as a successful attempt.
- No accepted/promotion/human-review/verifier authority is added.
```

---

# Phase C: loop runner + external operator task protocol

## Task C.1: research-loop-runner-and-operator-protocol

```text
Repository:
  tcs-cosheaf

Branch:
  research-loop-runner-and-operator-protocol

Goal:
  Add a bounded deterministic loop runner and an external-operator task protocol that lets Codex-style operators drive many attempts without granting Cosheaf hidden autonomy.
```

Required CLI:

```text
cosheaf research-loop next <loop-id> --json
cosheaf research-loop step <loop-id> --json
cosheaf research-loop run <loop-id> --max-attempts <n> --dry-run --json
cosheaf research-loop export-task <loop-id> --out <path> --json
cosheaf research-loop import-result <loop-id> --input-json <path> --json
```

Runner semantics:

```text
- deterministic by default
- no hosted model calls
- no arbitrary shell
- may call existing service-layer functions for memory cards/search, context build, strategy next, research-run summary, session show, scan, and handoff preview
- `run --dry-run` produces planned next actions only
- non-dry-run is allowed only for deterministic local actions already exposed by Cosheaf services
- max attempts and wallclock budget required
- stop conditions explicit
```

External operator task packet:

```text
operator_task.json contains:
- loop_id
- attempt_id
- issue_id
- objective
- allowed_actions
- forbidden_actions
- context_refs
- relevant_artifact_cards
- previous_failures_to_avoid
- required_outputs
- budget
- stop_conditions
- review_handoff_instructions
```

Import result contract:

```text
operator_result.json contains:
- attempted_direction
- actions_taken
- artifacts_referenced
- drafts_created
- checks_run
- failures
- candidate_counterexamples
- checked_counterexamples
- evidence_refs
- next_recommendation
- claimed_authority_flags, all false unless explicitly allowed
```

Tests:

```text
- next action deterministic
- dry-run writes no source-of-truth files
- import rejects accepted-write references
- import rejects human-review/promotion overclaims
- repeated failure is surfaced to next task packet
- budget exhaustion stops loop
```

Docs/update:

```text
- docs/RESEARCH_LOOPS.md
- docs/CODEX_OPERATOR_RUNBOOK.md
- docs/AGENT_ACCESS.md
- docs/OPERATOR_SESSIONS.md
- context/INTERFACE_REGISTRY.md
```

Acceptance:

```text
- Codex can receive a bounded task packet, work externally, and import a structured result.
- The loop can plan the next attempt without relying on hidden model state.
- Repeat-failure warnings are visible before the next attempt.
```

---

# Phase D: attempt memory / failure avoidance / scanner integration

## Task D.1: attempt-memory-failure-avoidance-scanner

```text
Repository:
  tcs-cosheaf

Branch:
  attempt-memory-failure-avoidance-scanner

Goal:
  Make attempts useful as memory: detect repeated failed directions, update retrieval/task context with failure summaries, and extend scanner coverage to loop artifacts.
```

Required features:

```text
1. Attempt-memory index:
   .cosheaf/research-loops/attempt-memory.json

2. Failure clustering:
   deterministic lexical/signature grouping over attempted_direction, issue_id, artifact refs, and failure tags.

3. Repeat-failure warning:
   `cosheaf research-loop next` must report similar previous failures and require justification to retry.

4. Failure context injection:
   operator task packets include a bounded `previous_failures_to_avoid` section.

5. Loop scanner:
   `cosheaf research-loop scan <loop-id> --json`

6. Blocking findings:
   secrets, provider dumps, hidden reasoning markers, private content in public mode, accepted-write attempts, promotion/human-review/verifier-pass overclaims, raw environment dumps, absolute private paths.
```

Required metrics:

```text
attempt_count
unique_direction_count
repeat_failure_count
blocked_repeat_retry_count
candidate_counterexample_count
checked_counterexample_count
draft_artifact_ref_count
handoff_ref_count
scanner_blocker_count
```

Tests:

```text
- repeat-failure detection
- justified retry allowed with explicit reason
- unjustified retry blocked or strongly warned according to policy
- secret/private/provider marker scanner failures
- public mode denial
- metrics deterministic
```

Docs/update:

```text
- docs/RESEARCH_LOOPS.md
- docs/SECURITY.md
- docs/EVALUATION.md
- context/INTERFACE_REGISTRY.md
```

Acceptance:

```text
- The system remembers failed directions in a machine-readable way.
- The next attempt sees failures to avoid.
- The scanner blocks unsafe loop/handoff material before review export.
```

---

# Phase E: ecosystem demos + eval matrix

## Task E.1: research-loop-eval-and-ecosystem-demo

```text
Repository:
  tcs-cosheaf first; then workspace-template and tcs-kb-public updates in separate downstream PRs if needed.

Branch:
  research-loop-eval-and-ecosystem-demo

Goal:
  Add deterministic evaluation and downstream demonstrations for the bounded research-loop workflow.
```

Framework requirements:

```text
- eval fixture with an issue, public artifact, private draft, prior failure, and loop attempts
- `cosheaf eval research-loop --json`
- ecosystem smoke rows for loop start/next/import/finalize/scan/handoff dry-run
- metrics summarized in docs/EVALUATION.md
```

Evaluation metrics:

```text
loop_validity_rate
attempt_schema_validity_rate
repeat_failure_detection_rate
unjustified_retry_block_rate
public_private_leak_count
scanner_blocker_accuracy
handoff_review_context_validity_rate
policy_overclaim_rejection_rate
budget_stop_accuracy
skipped_not_pass_count
```

Workspace-template downstream:

```text
- add `make research-loop-demo`
- demo must use local/fake/deterministic operations only
- demo must write ignored runtime outputs only
- handoff export stays dry-run by default
- pin remains published framework tag when release exists
```

Public KB downstream:

```text
- add/update policy docs for research-loop exports if needed
- public KB guard must reject operator loop material used as source metadata or accepted proof
- no KB artifact/content expansion in this task
```

Tests:

```text
- framework eval test
- ecosystem smoke matrix
- workspace demo smoke
- public KB policy guard negative fixture
```

Acceptance:

```text
- Research loop is demonstrable across the ecosystem.
- Public KB treats loop outputs as review context only.
- No accepted KB, source metadata, or human-review semantics changed.
```

---

# Phase F: v0.7.0 RC + publication closeout

## Task F.1: release-v070-readiness-and-rc

```text
Repository:
  tcs-cosheaf

Branch:
  release-v070-readiness-and-rc

Goal:
  Prepare conservative v0.7.0 release-candidate metadata after all bounded-loop implementation and ecosystem smoke tasks land.
```

Required checks:

```text
- package metadata bump to 0.7.0 only in this task
- release notes clearly state exact implemented features
- no production autonomy claims
- no automatic theorem-proving claims
- no default hosted provider claims
- no accepted promotion / human review / verifier authority claims
- skipped rows reported as skipped, not pass
```

Run:

```text
python -m cosheaf.cli version --json
make lint
make typecheck
make test
make validate
make gate
python scripts/ecosystem_smoke.py --matrix --framework-tag v0.7.0 --cosheaf "python -m cosheaf.cli" --framework-root . --workspace-template-root ../tcs-cosheaf-workspace-template --public-kb-root ../tcs-kb-public --json
git diff --check
```

Acceptance:

```text
- RC docs are truthful.
- framework reports 0.7.0.
- tests/gates/evals pass or failures are reported honestly.
- public tag/release/downstream pin update is not claimed until closeout.
```

## Task F.2: release-v070-publication-closeout

```text
Repository:
  tcs-cosheaf, then downstream workspace-template and public KB as needed.

Branch:
  release-v070-publication-closeout

Goal:
  Publish v0.7.0 and align downstream pins after post-tag release smoke passes.
```

Required:

```text
- create/publish annotated tag v0.7.0 outside this plan task flow as maintainer action
- GitHub release URL recorded
- post-tag install smoke from @v0.7.0 passes
- workspace-template pins/demos moved to @v0.7.0 in downstream PR
- public KB CI/docs moved to @v0.7.0 in downstream PR
- final ecosystem matrix recorded
- release note and project state updated from RC to published
```

Acceptance:

```text
- v0.7.0 is published.
- downstream pins are aligned.
- no runtime authority widened during closeout.
- no KB artifacts/content changed.
```

---

# 6. First Codex task to run now

```text
Task: post-v060-v070-kickoff
Repository: tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.
Branch: post-v060-v070-kickoff

Goal:
  Verify the completed v0.6.0 state and land the accelerated v0.7.0 Bounded Research Loop + Attempt Memory plan.

Create/update only:
  docs/POST_V060_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V11.md
  docs/ADR/0028-bounded-research-loop-attempt-memory.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Do not:
  implement research-loop runtime
  add schemas
  add dependencies
  change CLI behavior
  bump version
  write KB artifacts
  create release tags

Required checks:
  - pyproject and cosheaf.__version__ are 0.6.0
  - v0.6.0 tag/release/publication closeout is recorded
  - workspace-template PR #75 pin alignment is complete
  - public KB PR #90 pin alignment is complete
  - open PR/issue state across all three repos
  - current operator session/handoff CLI capabilities
  - no accepted-write/promotion/human-review/verifier authority change
  - no default hosted provider or real provider CI dependency

Run:
  make lint
  make typecheck
  make test
  make validate
  make gate
  git diff --check

Stop after this task.
```

