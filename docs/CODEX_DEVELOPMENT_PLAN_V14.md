# TCS-Cosheaf Development Plan V14

Target: `v0.9.0 Reviewable Research Workflow MVP + Benchmark Harness`

This is the accelerated post-`v0.8.0` plan.

Current closeout note, 2026-06-18: the public `v0.9.0` tag and GitHub release
are published. Later V14 B.1, C.1, D.1, and E.1 follow-ups add persistent
workflow storage, `workflow show`, persisted `workflow step`, bounded
`workflow run`, persisted readiness reports, draft proposal generation,
workflow handoff build/show/scan/export with scanner integration, and
`cosheaf eval reviewable-workflow --json`. Downstream workspace-template PR
#83 added `make reviewable-workflow-demo`; public KB PR #97 added workflow
packet policy guard coverage. This V14 plan is closed. Current development
continues in `docs/CODEX_DEVELOPMENT_PLAN_V15.md`.

`v0.8.0` delivered the deterministic execution kernel: librarian v0, orchestrator FSM v1, whitelisted local action registry, non-dry-run local loop execution, worker profiles, and deterministic memory feedback. The next line should not add a new low-level subsystem. It should turn those capabilities into a single reviewable research workflow:

```text
issue -> librarian context -> FSM plan -> bounded local loop -> evidence/failures -> draft artifact proposal -> review handoff -> benchmark/eval report
```

One-sentence goal:

```text
Make Cosheaf produce a human-review-ready research packet from an issue, while keeping every generated claim in draft/review-context state and preserving all authority boundaries.
```

## 0. Acceptance precondition from v0.8.0

The v0.8.0 code/release surface appears functionally complete, but the repository state documents must be checked before further implementation.

Known evidence:

```text
- pyproject.toml records package version 0.8.0.
- PR #420 merged librarian v0 + orchestrator FSM v1.
- PR #421 updated v0.8.0 release notes to the full Deterministic Execution Kernel + Librarian + FSM scope.
- docs/releases/v0.8.0.md says status: published.
```

Known state drift to resolve before any new feature work:

```text
context/CURRENT_MILESTONE.md still contains stale v0.7/v0.8 kickoff text and old version fields.
```

Therefore the first task is a closeout/audit task, not implementation.

## 1. Acceleration rules

```text
1. One task = one branch = one PR = stop.
2. No direct pushes to main.
3. Branch/PR/issue titles must not use `codex/`, `codex-`, or agent-specific prefixes.
4. Do not split model, CLI, docs, tests, and eval for the same functional slice into many tiny PRs.
5. Every implementation PR must include tests, CLI smoke, docs, interface registry updates, and negative authority tests when applicable.
6. Do not rely on docs-only state. Inspect code, tests, CLI, schemas, release notes, and runtime paths before changing behavior.
7. Skipped is not pass.
8. Generated runtime outputs remain under ignored `.cosheaf/` paths unless an explicit review-context export is requested.
9. YAML artifacts remain source of truth. Sidecars, logs, runs, loops, librarian traces, and action records are rebuildable/review context only.
10. No result from this line creates accepted knowledge, human review, verifier pass, gate pass, source metadata, accepted refutation, or promotion authority.
```

## 2. Non-goals

Do not implement:

```text
- production autonomous AI mathematician
- automatic theorem proving
- automatic accepted promotion
- AI as human review
- default hosted provider calls
- network/API-key-dependent tests
- unrestricted shell execution
- web UI / SaaS / multi-user auth
- direct public KB content expansion
- claim that loop success means mathematical truth
```

This line creates **reviewable research workflow**, not **automatic knowledge acceptance**.

## 3. Phase plan

Accelerated structure: six phases.

```text
Phase A: post-v0.8.0 audit + V14 landing
Phase B: issue-to-workflow service and CLI
Phase C: draft proposal generation from workflow output
Phase D: review handoff and authority scanner
Phase E: benchmark/eval suite + workspace/public-KB smoke
Phase F: v0.9.0 RC + publication closeout
```

---

# Phase A: post-v0.8.0 audit + V14 landing

## Task A.1: post-v080-v090-kickoff

```text
Repository:
  tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.

Branch:
  post-v080-v090-kickoff

Goal:
  Verify v0.8.0 completion, fix stale project-state/milestone drift, and land the v0.9.0 Reviewable Research Workflow MVP plan.
```

Create/update only:

```text
docs/POST_V080_STATE_AUDIT.md
docs/CODEX_DEVELOPMENT_PLAN_V14.md
docs/ADR/0030-reviewable-research-workflow-mvp.md
docs/ROADMAP.md
context/CURRENT_MILESTONE.md
context/PROJECT_STATE.md
```

Must verify:

```text
- pyproject.toml version is 0.8.0
- cosheaf.__version__ is 0.8.0
- docs/releases/v0.8.0.md says published and describes full V13 scope
- PR #420 is merged
- PR #421 is merged
- open PR/issue state across tcs-cosheaf, workspace-template, tcs-kb-public
- librarian CLI is registered
- orchestrator-fsm CLI is registered
- action registry has whitelisted safe local actions
- research-loop non-dry-run execution only executes whitelisted local actions
- no arbitrary shell, network, hosted-provider default, accepted write, human review, verifier mutation, gate mutation, or promotion authority
- identify and fix stale CURRENT_MILESTONE / PROJECT_STATE text
```

Do not:

```text
- implement workflow runtime
- add schemas
- add dependencies
- change CLI behavior
- bump version
- write KB artifacts
- create tags/releases
```

Run:

```text
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

Acceptance:

```text
- v0.8.0 state is factual and no stale v0.6/v0.7 status remains in current milestone fields.
- V14 plan and ADR are durable repo memory.
- No runtime behavior changed.
```

---

# Phase B: issue-to-workflow service and CLI

## Task B.1: reviewable-research-workflow-core

```text
Repository:
  tcs-cosheaf

Branch:
  reviewable-research-workflow-core

Goal:
  Add a single deterministic service/CLI that wires the existing librarian, FSM, action registry, research-loop, and handoff primitives into one workflow record.
```

New concepts:

```text
ReviewableResearchWorkflow
WorkflowStep
WorkflowInput
WorkflowOutput
WorkflowEvidenceRef
WorkflowFailureSummary
WorkflowAuthorityNotice
WorkflowReadinessSummary
```

Runtime storage:

```text
.cosheaf/workflows/<workflow-id>/workflow.json
.cosheaf/workflows/<workflow-id>/events.jsonl
.cosheaf/workflows/<workflow-id>/librarian.json
.cosheaf/workflows/<workflow-id>/fsm.json
.cosheaf/workflows/<workflow-id>/loop.json
.cosheaf/workflows/<workflow-id>/readiness.json
```

CLI:

```text
cosheaf workflow start --issue <issue-id> --query <query> --json
cosheaf workflow show <workflow-id> --json
cosheaf workflow step <workflow-id> --json
cosheaf workflow run <workflow-id> --max-steps <n> --execute-local-actions --json
cosheaf workflow readiness <workflow-id> --json
```

Required behavior:

```text
- `start` creates one workflow record and links issue/query.
- `step` performs one deterministic local orchestration step using existing services.
- `run` may call only whitelisted local actions already exposed by the action registry.
- Every step records inputs, outputs, exit status, warnings, and authority notice.
- Workflow records are review context only.
- No accepted writes.
- No human review creation.
- No verifier/gate/pass mutation.
- No provider/network/arbitrary-shell execution.
```

Readiness output must classify:

```text
ready_for_draft_proposal
blocked_by_gate
blocked_by_scanner
blocked_by_missing_evidence
blocked_by_private_leak_risk
blocked_by_unchecked_counterexample
inconclusive
```

Tests:

```text
- workflow start/show JSON
- deterministic step with empty/minimal repo
- run bounded by max steps
- rejected non-whitelisted action
- accepted-write rejection
- authority overclaim rejection
- private leakage warning
- readiness classification
```

Docs/update:

```text
docs/REVIEWABLE_RESEARCH_WORKFLOWS.md
docs/CODEX_OPERATOR_RUNBOOK.md
docs/RESEARCH_LOOPS.md
context/INTERFACE_REGISTRY.md
context/CURRENT_MILESTONE.md
context/PROJECT_STATE.md
```

Acceptance:

```text
- A maintainer can run one command sequence from issue to readiness report.
- Output remains runtime review context only.
```

---

# Phase C: draft proposal generation from workflow output

## Task C.1: draft-proposal-from-workflow

```text
Repository:
  tcs-cosheaf

Branch:
  draft-proposal-from-workflow

Goal:
  Convert a completed/inconclusive workflow into a private draft proposal packet without entering accepted knowledge.
```

CLI:

```text
cosheaf workflow draft-proposal <workflow-id> --out <path> --json
cosheaf workflow draft-proposal <workflow-id> --private-root <path> --artifact-id <id> --json
cosheaf workflow draft-proposal <workflow-id> --dry-run --json
```

Proposal output:

```text
DraftResearchArtifactProposal
DraftClaimCandidate
DraftProofSketchCandidate
DraftCounterexampleCandidate
DraftEvidenceSummary
DraftKnownFailureSummary
DraftDependencySummary
DraftReviewChecklist
```

Rules:

```text
- default output must be review-context JSON/YAML, not accepted artifact YAML.
- writing artifact YAML is allowed only under a writable private/draft root.
- proposal must include provenance back to workflow, loop, librarian result, FSM record, and actions.
- proposal must mark all claims as candidate/draft.
- proposal must include unresolved failures and unchecked evidence.
- no source metadata fabrication.
- no accepted status.
- no human review.
```

Negative tests:

```text
- reject `kb/accepted/` output path
- reject public KB output by default
- reject missing provenance
- reject candidate marked as theorem/accepted
- reject AI review as human review
- reject gate pass as acceptance
```

Docs/update:

```text
docs/DRAFT_PROPOSALS.md
docs/ARTIFACT_LIFECYCLE.md
docs/REVIEWABLE_RESEARCH_WORKFLOWS.md
context/INTERFACE_REGISTRY.md
```

Acceptance:

```text
- Workflow output can become a reviewable private draft proposal.
- The proposal is explicitly not accepted knowledge.
```

---

# Phase D: review handoff and authority scanner

## Task D.1: workflow-review-handoff-scanner

```text
Repository:
  tcs-cosheaf

Branch:
  workflow-review-handoff-scanner

Goal:
  Build a human-review handoff packet from workflow/draft proposal output and scan it for authority, privacy, and provenance risks.
```

CLI:

```text
cosheaf workflow handoff build <workflow-id> --json
cosheaf workflow handoff show <handoff-id> --json
cosheaf workflow handoff scan <handoff-id> --json
cosheaf workflow handoff export <handoff-id> --dry-run --json
```

Handoff packet sections:

```text
- issue summary
- query/objective
- librarian context summary
- FSM trace
- actions executed
- failures and avoided directions
- candidate claims
- evidence and limitations
- scanner findings
- human-review checklist
- explicit non-authority notice
```

Scanner must block:

```text
- accepted-write attempts
- public/private leakage
- hidden reasoning markers
- provider payload dumps
- API keys/secrets/env dumps
- human-review overclaims
- verifier/gate/pass overclaims
- source metadata fabrication
- accepted theorem/refutation language without promotion
```

Tests:

```text
- clean handoff dry-run
- private leakage blocked
- accepted-write blocked
- human-review overclaim blocked
- source metadata fabrication blocked
- skipped-not-pass warning preserved
```

Docs/update:

```text
docs/REVIEW_HANDOFFS.md
docs/SECURITY.md
docs/PUBLIC_PRIVATE_KB.md
context/INTERFACE_REGISTRY.md
```

Acceptance:

```text
- A workflow can produce a safe human-review handoff.
- Handoff is review context only.
```

---

# Phase E: benchmark/eval suite + workspace/public-KB smoke

## Task E.1: reviewable-workflow-benchmark-and-ecosystem-smoke

```text
Repository:
  tcs-cosheaf first; then downstream workspace-template and tcs-kb-public if needed.

Branch:
  reviewable-workflow-benchmark-and-ecosystem-smoke

Goal:
  Add deterministic benchmarks and ecosystem smoke rows for issue-to-reviewable-packet workflow.
```

Framework eval:

```text
cosheaf eval reviewable-workflow --json
```

Implementation status: the framework eval and ecosystem smoke matrix row are
implemented by issue #432. The downstream workspace-template demo landed in
workspace-template PR #83, and the public-KB workflow packet policy guard
landed in public-KB PR #97.

Default cases:

```text
- issue with accepted dependency and draft target
- issue with repeated failure memory
- issue with unchecked counterexample
- issue with private leakage risk
- issue with gate/scanner blocker
- issue that reaches draft-proposal-ready state
```

Metrics:

```text
workflow_validity_rate
librarian_trace_completeness_rate
fsm_replay_validity_rate
local_action_whitelist_rate
draft_proposal_validity_rate
handoff_scanner_block_rate
authority_overclaim_rejection_rate
private_leak_rejection_rate
review_readiness_classification_rate
skipped_not_pass_count
```

Workspace-template downstream:

```text
- add `make reviewable-workflow-demo`
- demo uses published framework tag or local checkout
- demo writes only ignored runtime outputs and private draft/review context
- no public KB writes
- no accepted artifacts
```

Public KB downstream:

```text
- add/extend policy docs: workflow outputs are review context only
- guard fixture rejects workflow packet as source metadata / accepted proof / human review
- no KB content expansion
```

Acceptance:

```text
- End-to-end demo works locally.
- Matrix reports pass/fail/skipped honestly.
- Public KB keeps workflow packets out of source-of-truth accepted knowledge.
```

---

# Phase F: v0.9.0 RC + publication closeout

## Task F.1: release-v090-readiness-and-rc

```text
Repository:
  tcs-cosheaf

Branch:
  release-v090-readiness-and-rc

Goal:
  Prepare conservative v0.9.0 release-candidate metadata after workflow, proposal, handoff, eval, and ecosystem smoke land.
```

Required:

```text
- version bump to 0.9.0 only here
- docs/releases/v0.9.0.md
- README / ROADMAP / CURRENT_MILESTONE / PROJECT_STATE update
- truthful limitations
```

Release notes must not claim:

```text
- production autonomous AI mathematician
- automatic theorem proving
- default hosted provider
- accepted promotion
- human review creation
- formal semantic alignment
```

Run:

```text
python -m cosheaf.cli version --json
make lint
make typecheck
make test
make validate
make gate
python scripts/ecosystem_smoke.py --matrix --framework-tag v0.9.0 --json
git diff --check
```

## Task F.2: release-v090-publication-closeout

```text
Repository:
  tcs-cosheaf, then downstream workspace-template and public KB as needed.

Branch:
  release-v090-publication-closeout

Goal:
  Publish v0.9.0 and align downstream pins after post-tag smoke passes.
```

Required:

```text
- annotated tag v0.9.0 as maintainer action
- GitHub release URL recorded
- post-tag install smoke from @v0.9.0
- workspace-template pin/demo update PR
- public KB CI/policy update PR
- final ecosystem matrix recorded
- no authority boundary widened
```

---

# 4. First task to run now

```text
Task: post-v080-v090-kickoff
Branch: post-v080-v090-kickoff
Repository: tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.

Goal:
  Verify completed v0.8.0 state, fix stale milestone/project-state drift,
  and land V14 plan for v0.9.0 Reviewable Research Workflow MVP.

Create/update only:
  docs/POST_V080_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V14.md
  docs/ADR/0030-reviewable-research-workflow-mvp.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Do not:
  implement workflow runtime
  add schemas
  add dependencies
  change CLI behavior
  bump version
  write KB artifacts
  create tags/releases

Run:
  make lint
  make typecheck
  make test
  make validate
  make gate
  git diff --check

Stop after this task.
```

