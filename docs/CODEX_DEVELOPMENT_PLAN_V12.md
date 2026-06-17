# TCS-Cosheaf Development Plan V12

Target: `v0.8.0 Deterministic Worker Loop + Local Action Registry`

Status: proposed next accelerated line after published `v0.7.0`.

## One-sentence goal

Turn the `v0.7.0` bounded research loop from a dry-run planning and import/export harness into a deterministic local execution loop that can run whitelisted Cosheaf actions, record every action as evidence, and still never gain accepted-knowledge authority.

## Why this is next

`v0.7.0` completed the bounded research-loop substrate:

```text
issue -> plan -> attempt -> check -> failure/evidence memory -> next attempt -> stop/handoff
```

But the loop still refuses non-dry-run execution. That is correct for safety, but it means the system is still mostly a planning, packet, and audit harness. The next useful acceleration is not hosted LLM, not web UI, and not production autonomy. The next useful line is a local deterministic worker/action registry that lets the loop actually execute safe repository operations:

```text
memory search
context build
strategy next
validate
gate
eval
scan
handoff preview
failure-memory update
checked-evidence summary
research-run/session summary
```

This creates the first real closed local execution loop while preserving the core Cosheaf boundary: outputs are review context only, not accepted knowledge.

## Baseline to verify before starting

Expected state at the start of V12:

```text
tcs-cosheaf version: 0.7.0
published tag: v0.7.0
release closeout: complete
workspace-template pin: @v0.7.0
public KB CI pin: @v0.7.0
research-loop run: dry-run only; non-dry-run still refused
open blocker PRs: none expected
open stale issues: must be audited before implementation
```

Note: if issue #408 is still open and already superseded by Phase E documentation closeout and v0.7.0 publication closeout, close or mark it superseded during kickoff before starting feature work.

## Acceleration rules

Use fewer, larger implementation PRs. Do not split every DTO, CLI command, doc, eval, and security test into separate PRs.

```text
1. One task = one branch = one PR.
2. Do not use `codex/` or `codex-` in branch, PR, or issue names.
3. Every implementation PR must include model/service code, CLI, schemas if needed, tests, docs, interface registry updates, and security/eval coverage for that same functional slice.
4. Do not create pure docs PRs unless they are kickoff, release, or required cleanup.
5. Every task must inspect actual code, tests, CLI, schemas, runtime storage, and CI/docs before editing.
6. If repository state diverges from this plan, audit and stop.
7. Tests may use fake/mocked local fixtures only; no hosted provider calls or API keys in CI.
8. Skipped rows are not pass.
9. Runtime outputs stay under ignored `.cosheaf/` paths unless an explicit review-context export is requested.
10. No loop/action/worker output may write accepted KB, create human review, mutate verifier result, mark gate pass as review, or authorize promotion.
```

## Non-goals

Do not implement in V12:

```text
- production autonomous AI mathematician
- default hosted model/provider calls
- real provider calls in CI/default tests
- arbitrary shell execution
- unrestricted plugin execution
- automatic theorem proving
- automatic Lean/mathlib/CSLib semantic alignment
- accepted promotion from loop result
- AI as human review
- web UI / SaaS / multi-user permissions
- public KB content expansion unless separately scoped
```

## Key invariants

### Knowledge authority

```text
- Local action success is not proof.
- Validate/gate/eval success is not human review.
- Loop success is not accepted status.
- Checked evidence remains evidence, not accepted truth.
- Handoff export remains review context only.
- Failure memory remains research memory, not refutation authority.
- Public KB accepted artifacts still require source metadata and human review.
```

### Execution authority

```text
- All executable loop actions must come from a typed allowlist.
- No arbitrary shell.
- No external network by default.
- No provider call by default.
- No dynamic import of untrusted code.
- Every action records input refs, output refs, command/service name, status, timestamps, error code, scanner status, and authority notice.
- Non-dry-run loop execution must still be bounded by max attempts and stop conditions.
```

### Public/private policy

```text
- Public mode cannot include private paths, private artifact IDs, private issue IDs, or private failure summaries.
- Private mode must be explicit.
- Review handoff to public KB must pass policy guards.
- Scanner blockers prevent export.
```

---

# Phase A: post-v0.7.0 audit and V12 landing

## Task A.1: post-v070-v080-kickoff

```text
Repository:
  tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.

Branch:
  post-v070-v080-kickoff

Goal:
  Verify the completed v0.7.0 state, resolve stale post-v0.7.0 issue state, and land the accelerated v0.8.0 deterministic worker-loop plan.

Create/update only:
  docs/POST_V070_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V12.md
  docs/ADR/0029-deterministic-worker-loop-action-registry.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required audit checks:
  - package version is 0.7.0
  - tag/release v0.7.0 exists and is documented
  - workspace-template active pins are @v0.7.0
  - public KB CI pin is @v0.7.0
  - open PRs/issues across all three repos
  - explicitly resolve whether issue #408 is stale/superseded or still blocking
  - research-loop non-dry-run execution remains refused
  - existing local services available for safe worker actions
  - no accepted write, human-review, verifier-pass, gate-pass, hosted-provider, arbitrary-shell, or promotion authority exists

Do not:
  implement action registry
  add schemas
  add runtime behavior
  add dependencies
  bump version
  write KB artifacts
  create release tags

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
- Audit records exact v0.7.0 state.
- Stale issue state is addressed or explicitly carried as a blocker.
- V12 plan and ADR are durable repo memory.
- No runtime behavior changed.
```

---

# Phase B: local action registry core

## Task B.1: deterministic-local-action-registry-core

```text
Repository:
  tcs-cosheaf

Branch:
  deterministic-local-action-registry-core

Goal:
  Implement a typed local action registry and action result model that research loops can call without arbitrary shell or hosted providers.
```

Required models/services:

```text
LocalActionSpec
LocalActionInput
LocalActionResult
LocalActionError
LocalActionRegistry
LocalActionPolicy
LocalActionEvidenceRef
LocalActionScannerSummary
```

Required initial whitelisted actions:

```text
workspace.info
validate.run
gate.run
index.rebuild
memory.search
context.build
strategy.next
research_loop.scan
operator_session.scan
operator_handoff.preview
research_run.summary
checked_evidence.summary
failure_memory.summary
eval.research_loop
```

Rules:

```text
- Registry is static and deterministic.
- No arbitrary command strings.
- No shell=True.
- No network by default.
- No provider calls.
- No accepted writes.
- Actions may write only ignored runtime outputs or explicit review-context dry-run outputs.
- Every action has an authority notice.
- Every action declares allowed input refs and output refs.
```

Required CLI:

```text
cosheaf action list --json
cosheaf action describe <action-id> --json
cosheaf action run <action-id> --input-json <path> --json
cosheaf action run <action-id> --input-json <path> --dry-run --json
```

Tests:

```text
- registry lists expected actions
- unknown action rejected
- unsafe shell/action rejected
- accepted-write output rejected
- public/private policy enforced
- deterministic JSON output
- scanner blockers represented
- no API key/network dependency
```

Docs/update:

```text
docs/LOCAL_ACTIONS.md
docs/RESEARCH_LOOPS.md
docs/SECURITY.md
docs/AGENT_ACCESS.md
context/INTERFACE_REGISTRY.md
context/CURRENT_MILESTONE.md
context/PROJECT_STATE.md
```

Acceptance:

```text
- Safe local actions are callable through a typed registry.
- Registry cannot run arbitrary shell.
- Output remains non-authoritative review context.
```

---

# Phase C: research-loop execution engine

## Task C.1: research-loop-nondryrun-local-execution

```text
Repository:
  tcs-cosheaf

Branch:
  research-loop-nondryrun-local-execution

Goal:
  Enable bounded non-dry-run research-loop execution for whitelisted local actions only.
```

Required behavior:

```text
- `cosheaf research-loop run <loop-id> --max-attempts <n> --json` executes only LocalActionRegistry actions.
- Dry-run remains available and default-safe in docs/demos.
- Non-dry-run requires explicit `--execute-local-actions`.
- The loop records each action result as an attempt event.
- Budget exhaustion stops the loop.
- Scanner blockers stop the loop.
- Repeat-failure retry still requires justification.
- No arbitrary shell, network, hosted provider, accepted write, human review, verifier mutation, gate promotion, or source metadata authority.
```

Required CLI updates:

```text
cosheaf research-loop run <loop-id> --max-attempts <n> --execute-local-actions --json
cosheaf research-loop step <loop-id> --execute-local-actions --json
cosheaf research-loop actions <loop-id> --json
```

Execution policy:

```text
Allowed actions for first non-dry-run implementation:
  - memory.search
  - context.build
  - strategy.next
  - validate.run
  - gate.run
  - research_loop.scan
  - eval.research_loop
  - operator_handoff.preview

Explicitly forbidden:
  - arbitrary shell
  - provider real-run
  - write accepted
  - promote artifact
  - mark human reviewed
  - mutate verifier result
  - git commit/push
```

Tests:

```text
- non-dry-run refused without --execute-local-actions
- allowed actions execute and record events
- forbidden action rejected
- scanner blocker stops loop
- budget exhaustion stops loop
- repeat failure requires justification
- output path remains under .cosheaf/
- no accepted writes
```

Docs/update:

```text
docs/RESEARCH_LOOPS.md
docs/CODEX_OPERATOR_RUNBOOK.md
docs/LOCAL_ACTIONS.md
docs/EVALUATION.md
context/INTERFACE_REGISTRY.md
```

Acceptance:

```text
- Bounded loop can actually run safe local actions.
- It is still not autonomous theorem proving.
- It remains review context only.
```

---

# Phase D: worker profile layer

## Task D.1: deterministic-worker-profiles

```text
Repository:
  tcs-cosheaf

Branch:
  deterministic-worker-profiles

Goal:
  Add deterministic worker profiles that bundle allowed local actions into reusable research roles without adding hosted models.
```

Required worker profiles:

```text
librarian_local:
  allowed: memory.search, context.build, index.rebuild

planner_local:
  allowed: strategy.next, context.build, failure_memory.summary

checker_local:
  allowed: validate.run, gate.run, checked_evidence.summary, eval.research_loop

handoff_local:
  allowed: research_loop.scan, operator_session.scan, operator_handoff.preview
```

Required CLI:

```text
cosheaf worker list --json
cosheaf worker describe <worker-id> --json
cosheaf worker run <worker-id> --input-json <path> --dry-run --json
cosheaf worker run <worker-id> --input-json <path> --execute-local-actions --json
```

Rules:

```text
- Workers are deterministic wrappers over the LocalActionRegistry.
- Workers cannot call hosted providers.
- Workers cannot write accepted KB.
- Workers cannot call arbitrary shell.
- Workers cannot mark human review.
- Worker result is review context only.
```

Tests:

```text
- profile action allowlist enforced
- forbidden action rejected per profile
- dry-run and execute modes deterministic
- public/private policy preserved
- authority overclaims rejected
```

Docs/update:

```text
docs/WORKERS.md
docs/LOCAL_ACTIONS.md
docs/RESEARCH_LOOPS.md
docs/AGENT_ACCESS.md
context/INTERFACE_REGISTRY.md
```

Acceptance:

```text
- Cosheaf has deterministic local worker profiles.
- These are not LLM workers and not accepted-knowledge authority.
```

---

# Phase E: loop-worker integration, eval, and ecosystem smoke

## Task E.1: local-worker-loop-eval-ecosystem

```text
Repository:
  tcs-cosheaf first; downstream workspace-template and public KB PRs only if needed.

Branch:
  local-worker-loop-eval-ecosystem

Goal:
  Add deterministic evaluation and ecosystem smoke for local worker execution inside research loops.
```

Framework requirements:

```text
- `cosheaf eval local-worker-loop --json`
- eval fixture with issue, public artifact, private draft, prior failure, local action registry, worker profiles, scanner block, and safe handoff preview
- ecosystem smoke row for non-dry-run local action execution
- matrix must report skipped as skipped
```

Metrics:

```text
local_action_success_rate
forbidden_action_rejection_rate
scanner_blocker_stop_rate
accepted_write_violation_count
authority_overclaim_rejection_count
public_private_leak_count
budget_stop_accuracy
repeat_failure_guard_accuracy
worker_profile_policy_accuracy
skipped_not_pass_count
```

Workspace-template downstream:

```text
- add or update `make local-worker-loop-demo`
- demo runs deterministic local actions only
- no hosted provider/API key/MCP required
- runtime outputs ignored
- no accepted writes or promotion
```

Public KB downstream:

```text
- update policy docs/guard only if local-worker outputs need explicit rejection examples
- no artifact/content expansion
- local worker output is not source metadata, proof, human review, verifier pass, gate pass, accepted status, or promotion authority
```

Acceptance:

```text
- v0.8 local worker loop is covered by deterministic eval and ecosystem matrix.
- Downstream demos show the safe workflow.
- Public KB remains protected.
```

---

# Phase F: v0.8.0 RC and publication closeout

## Task F.1: release-v080-readiness-and-rc

```text
Repository:
  tcs-cosheaf

Branch:
  release-v080-readiness-and-rc

Goal:
  Prepare conservative v0.8.0 release-candidate metadata after local action registry, non-dry-run local loop execution, worker profiles, and ecosystem smoke land.
```

Required:

```text
- bump pyproject and cosheaf.__version__ to 0.8.0
- add docs/releases/v0.8.0.md
- update README, README.zh-CN, ROADMAP, CURRENT_MILESTONE, PROJECT_STATE
- state exact limitations
- do not claim public release until tag/release/post-tag smoke/downstream pins happen
```

Run:

```text
python -m cosheaf.cli version --json
make lint
make typecheck
make test
make validate
make gate
python scripts/ecosystem_smoke.py --matrix --framework-tag v0.8.0 --cosheaf "python -m cosheaf.cli" --framework-root . --workspace-template-root ../tcs-cosheaf-workspace-template --public-kb-root ../tcs-kb-public --json
git diff --check
```

Acceptance:

```text
- Framework reports 0.8.0.
- RC docs are conservative and accurate.
- No authority expansion is claimed.
```

## Task F.2: release-v080-publication-closeout

```text
Repository:
  tcs-cosheaf, then downstream workspace-template and tcs-kb-public as needed.

Branch:
  release-v080-publication-closeout

Goal:
  Publish v0.8.0 and align downstream pins after post-tag release smoke passes.
```

Required:

```text
- maintainer creates/pushes annotated tag v0.8.0
- GitHub release URL recorded
- post-tag install smoke from @v0.8.0 passes
- workspace-template pins/docs/scripts updated to @v0.8.0
- public KB CI/docs updated to @v0.8.0
- final ecosystem matrix recorded
- release notes and project state updated from RC to published
```

Acceptance:

```text
- v0.8.0 is published.
- downstream pins aligned.
- no KB artifacts/content changed.
- no runtime authority widened during closeout.
```

---

# First Codex task

```text
Task: post-v070-v080-kickoff
Repository: tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.
Branch: post-v070-v080-kickoff

Goal:
  Verify the completed v0.7.0 state, resolve stale issue state, and land the accelerated v0.8.0 Deterministic Worker Loop + Local Action Registry plan.

Create/update only:
  docs/POST_V070_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V12.md
  docs/ADR/0029-deterministic-worker-loop-action-registry.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Do not:
  implement local action registry
  add schemas
  change runtime behavior
  add dependencies
  bump version
  write KB artifacts
  create release tags

Required checks:
  - pyproject and cosheaf.__version__ are 0.7.0
  - v0.7.0 tag/release/publication closeout is recorded
  - workspace-template PR #78 pin alignment is complete
  - public KB PR #93 pin alignment is complete
  - open PR/issue state across all three repos
  - issue #408 status is resolved or explicitly explained
  - research-loop non-dry-run execution remains refused
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
