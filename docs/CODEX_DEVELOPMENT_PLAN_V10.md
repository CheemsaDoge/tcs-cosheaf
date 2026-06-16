# TCS-Cosheaf Development Plan V10: v0.6.0 Operator Session + Review Handoff

Status: proposed next accelerated line after published `v0.5.0` Operator MCP + Codex Application Layer closeout.

Target:

```text
v0.6.0 Operator Session + Review Handoff
```

One-line goal:

```text
Turn the v0.5.0 operator/MCP tool surface into a replayable, reviewable, privacy-audited operator session workflow that can hand a human maintainer a compact PR-ready evidence packet without granting accepted-write, human-review, verifier-pass, or promotion authority.
```

Maintainer execution note:

```text
Task-local "stop" language in this plan means stop the current PR scope after
verification and merge readiness. When a maintainer has explicitly instructed
continuous execution of the V10 queue, continue with the next task from clean
main after each merged PR.
```

## 0. Why this is the next line

`v0.5.0` finished the operator-facing tool layer:

```text
CLI-first runbook
+ optional MCP tools
+ controlled draft/review/runtime writes
+ workspace operator demo
+ public KB policy smoke
+ optional operator Skill package
```

The remaining bottleneck is not exposing more raw tools. The bottleneck is making an external operator's work auditable as a single session:

```text
What issue was worked on?
Which tools were called?
What context was used?
Which draft/review/runtime files were written?
Which validation/gate/eval checks ran?
Were private/public boundaries preserved?
What should the maintainer review next?
```

So v0.6.0 should add a thin, deterministic handoff layer over existing CLI/MCP/service semantics. It should not become a new planner, new proof system, or autonomous reviewer.

## 1. Non-negotiable rules

```text
1. One task = one issue = one branch = one PR.
2. Branch/PR/issue names must not use codex/, codex-, or any agent-specific prefix.
3. No direct main pushes.
4. No accepted KB writes through operator sessions, MCP, handoff bundles, or review exports.
5. No promotion through operator sessions.
6. No mark-human-reviewed operation.
7. No verifier-result mutation through operator sessions.
8. No hosted provider default and no API-key requirement.
9. No real network/API/provider calls in default tests or CI.
10. Session logs must be redacted and bounded; secrets, env dumps, hidden reasoning markers, and private content in public mode must be rejected or redacted.
11. Public/private and readonly/writable boundaries must have negative tests.
12. Runtime outputs stay under ignored `.cosheaf/` paths unless a task explicitly writes review-context exports under approved paths.
13. Validation/gate/eval pass does not equal human review or accepted status.
14. Skipped remains skipped and is never counted as pass.
```

## 2. Current baseline to verify at start

The first PR must verify actual repository state, not only documentation:

```text
- tcs-cosheaf package metadata and cosheaf.__version__ are 0.5.0.
- v0.5.0 annotated tag, GitHub release, release smoke, workspace-template pin update, and public KB CI pin update are complete.
- Open PRs/issues are empty or intentionally deferred.
- MCP read-only and controlled draft/review/runtime write tools are present and still optional.
- CLI remains the human and CI oracle.
- MCP remains an adapter and does not replace validation/gate/review/promotion.
- Controlled writes still cannot write kb/accepted/ or create human review.
- Workspace-template active demos pin/install @v0.5.0.
- tcs-kb-public CI installs @v0.5.0.
- No public KB artifacts, review records, formalization metadata, schemas, or promotion policy changed during pin alignment.
```

## 3. Scope

### In scope

```text
- Operator session DTOs and runtime storage under `.cosheaf/operator-sessions/`.
- Session-aware CLI wrappers for existing safe commands.
- Session-aware MCP tool-call recording for whitelisted tools.
- Redacted, bounded tool transcript records.
- Review handoff bundle generated from one session.
- Handoff export under `reviews/operator/` as review context only.
- Session leak scanner and negative security fixtures.
- Workspace-template operator-session demo.
- Public KB policy docs/checks for operator handoff imports.
- Ecosystem smoke rows for operator-session and handoff workflows.
- Conservative v0.6.0 RC and publication closeout.
```

### Out of scope

```text
- Production hosted multi-agent SaaS.
- Web UI.
- Multi-user permission system.
- Default real provider calls.
- Accepted promotion through MCP or session handoff.
- Human-review creation through MCP or session handoff.
- Automatic theorem proving.
- Automatic Lean/mathlib/CSLib semantic alignment.
- Automatic accepted refutation.
- Replacing GitHub PR review.
- Treating session transcripts as proof or source metadata.
```

## 4. Accelerated phase plan

```text
Phase A: v0.5.0 completion audit + V10 ADR
Phase B: operator session model and CLI core
Phase C: MCP session recording + leak scanner
Phase D: review handoff bundle and export
Phase E: downstream workspace/public-KB integration smoke
Phase F: v0.6.0 release candidate + publication closeout
```

This line is deliberately short. Do not add another large planning subsystem. Add only the missing audit/handoff layer needed to make operator work maintainable.

---

# Phase A: v0.5.0 completion audit and V10 landing

## Task A.1: post-v050-v060-kickoff

```text
Repository:
  tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.

Branch:
  post-v050-v060-kickoff

Goal:
  Verify the completed v0.5.0 state and land the v0.6.0 Operator Session + Review Handoff plan.

Create/update only:
  docs/POST_V050_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V10.md
  docs/ADR/0027-operator-session-review-handoff.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required audit answers:
  1. Is package metadata 0.5.0?
  2. Are v0.5.0 tag/release/release-smoke complete?
  3. Are workspace-template and public KB pinned to @v0.5.0?
  4. Are open PRs/issues empty or intentionally deferred?
  5. Which MCP tools exist now?
  6. Which controlled-write MCP tools exist now?
  7. Which operator runbook/demo/skill docs exist now?
  8. Which security and public/private negative tests exist now?
  9. Which outputs are runtime-only and which can be review-context exports?
  10. What must not become operator-session authority?

Do not:
  implement operator sessions
  add dependencies
  add schemas
  change runtime behavior
  bump version
  write KB artifacts

Before finishing:
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
- v0.5.0 completion state is verified from code/tests/docs/CLI surfaces, not docs alone.
- V10 plan and ADR are durable repo memory.
- No runtime or schema behavior changed.
```

---

# Phase B: operator session model and CLI core

## Task B.1: operator-session-model

```text
Repository:
  tcs-cosheaf

Branch:
  operator-session-model

Goal:
  Add strict, deterministic operator session DTOs and runtime storage without changing MCP behavior yet.

Allowed changes:
  cosheaf/operator_session/ or cosheaf/operator/
  schemas/operator_session.schema.json
  schemas/operator_handoff.schema.json only if needed for forward-compatible validation
  tests/test_operator_session_models.py
  tests/test_operator_session_storage.py
  docs/OPERATOR_SESSIONS.md
  context/INTERFACE_REGISTRY.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required models:
  OperatorSession
  OperatorToolCallRecord
  OperatorArtifactRef
  OperatorCheckResult
  OperatorSessionSummary
  OperatorPolicyFinding

Required storage:
  .cosheaf/operator-sessions/<session-id>/session.json
  .cosheaf/operator-sessions/<session-id>/events.jsonl

Rules:
  1. Session files are runtime records, not source-of-truth artifacts.
  2. Session records must include authority disclaimers.
  3. Session records must not store full private artifact text by default.
  4. Session records must not store environment dumps, API keys, hidden reasoning, or arbitrary stdout by default.
  5. Session IDs must be deterministic enough for tests but collision-safe in runtime.
  6. All paths must be repository-local normalized paths.
  7. Direct `kb/accepted/` write targets must be rejected.

Before finishing:
  - serialization tests
  - path-boundary tests
  - accepted-write rejection tests
  - redaction field tests
  - run standard commands
  - stop
```

Acceptance:

```text
- Operator session model exists and is strict.
- Runtime storage is deterministic and ignored.
- No MCP or CLI workflow behavior changes yet except model/storage tests.
```

## Task B.2: operator-session-cli-core

```text
Repository:
  tcs-cosheaf

Branch:
  operator-session-cli-core

Goal:
  Add CLI commands to start, inspect, append safe references to, and finalize an operator session.

Allowed changes:
  cosheaf/operator_session/
  cosheaf/cli.py
  tests/test_operator_session_cli.py
  docs/OPERATOR_SESSIONS.md
  docs/CODEX_OPERATOR_RUNBOOK.md
  context/INTERFACE_REGISTRY.md

Required CLI:
  cosheaf operator session start --issue <issue-id> --json
  cosheaf operator session show <session-id> --json
  cosheaf operator session append-check <session-id> --kind validate|gate|test|eval --status pass|fail|error|skipped --json
  cosheaf operator session append-ref <session-id> --path <repo-local-path> --kind draft|review_context|runtime|report --json
  cosheaf operator session finalize <session-id> --json

Rules:
  1. CLI only records session metadata and references; it does not execute arbitrary commands.
  2. `append-ref` rejects accepted KB paths.
  3. `append-ref` rejects private paths when session policy is public-only.
  4. `append-check` preserves skipped as skipped.
  5. Finalized sessions remain immutable except for explicit follow-up event records, if documented.
  6. No human-review or promotion authority is created.

Before finishing:
  - CLI smoke tests
  - public/private negative tests
  - skipped-not-pass tests
  - run standard commands
  - stop
```

Acceptance:

```text
- A user can create and finalize a session around existing Cosheaf commands.
- Session records do not grant any new authority.
- Tests prove accepted paths and private public-mode leakage are blocked.
```

---

# Phase C: MCP session recording and leak scanner

## Task C.1: mcp-session-recording

```text
Repository:
  tcs-cosheaf

Branch:
  mcp-session-recording

Goal:
  Allow optional MCP tool calls to be associated with an operator session and recorded as bounded event metadata.

Allowed changes:
  cosheaf/mcp/
  cosheaf/operator_session/
  cosheaf/cli.py if MCP serve/list help changes
  tests/test_mcp_server.py
  tests/test_operator_session_mcp.py
  docs/OPERATOR_MCP.md
  docs/OPERATOR_SESSIONS.md
  context/INTERFACE_REGISTRY.md

Required behavior:
  1. MCP requests may include an optional `session_id` argument or server option.
  2. For each whitelisted tool call, record tool name, public/private mode, normalized input metadata, status, redacted result summary, timestamps, and warning codes.
  3. Do not record full context packs, full artifact YAML, provider payloads, or raw stdout/stderr by default.
  4. Public-mode results must remain public-scoped before session recording.
  5. Failed and denied tool calls must be recorded as failed/denied, not omitted.
  6. Session recording can be disabled; MCP still works without session tracking.

Do not:
  add new MCP authority
  add arbitrary shell tools
  add accepted-write tools
  add promotion tools
  add human-review tools

Before finishing:
  - MCP tool-call recording tests
  - denied-call recording tests
  - public-mode privacy tests
  - backward compatibility tests without session_id
  - run standard commands
  - stop
```

Acceptance:

```text
- MCP calls can produce a replayable bounded session transcript.
- Recording cannot leak private content in public mode.
- No new tool authority is added.
```

## Task C.2: operator-session-leak-scanner

```text
Repository:
  tcs-cosheaf

Branch:
  operator-session-leak-scanner

Goal:
  Add a deterministic leak scanner for operator sessions and handoff candidates.

Allowed changes:
  cosheaf/operator_session/security.py or equivalent
  cosheaf/cli.py
  tests/security/test_operator_session_leak_scanner.py
  docs/OPERATOR_SESSIONS.md
  docs/SECURITY.md if present
  context/INTERFACE_REGISTRY.md

Required CLI:
  cosheaf operator session scan <session-id> --json

Scanner must detect or flag:
  - API keys and bearer-token-like strings
  - `.env` dumps and environment-variable dumps
  - private artifact IDs in public-only sessions
  - private path references in public-only sessions
  - hidden reasoning markers or chain-of-thought looking blocks
  - raw provider request/response payloads
  - absolute private filesystem paths where avoidable
  - direct accepted-write attempts
  - human-review/promotion authority claims in session notes

Rules:
  1. Scanner findings are deterministic.
  2. Blocking findings prevent handoff export by default.
  3. Scanner does not mutate source-of-truth files.
  4. Scanner may write runtime reports under `.cosheaf/operator-sessions/<session-id>/scan.json`.

Before finishing:
  - positive/negative fixture tests
  - handoff-blocking integration test if handoff scaffold exists
  - run standard commands
  - stop
```

Acceptance:

```text
- Session leaks are detected before review handoff.
- False pass is avoided; uncertain findings are warnings or blockers, never silently ignored.
```

---

# Phase D: review handoff bundle and export

## Task D.1: operator-handoff-bundle

```text
Repository:
  tcs-cosheaf

Branch:
  operator-handoff-bundle

Goal:
  Generate a compact review handoff bundle from one finalized operator session.

Allowed changes:
  cosheaf/operator_session/
  schemas/operator_handoff.schema.json
  cosheaf/cli.py
  tests/test_operator_handoff.py
  docs/OPERATOR_HANDOFF.md
  docs/CODEX_OPERATOR_RUNBOOK.md
  context/INTERFACE_REGISTRY.md

Required CLI:
  cosheaf operator handoff build --session <session-id> --json
  cosheaf operator handoff show <handoff-id> --json

Bundle must include:
  - session ID and issue ID
  - policy mode and KB root scope
  - files referenced/changed, repo-local only
  - draft artifacts/source notes/review-context records referenced
  - validation/gate/eval/test check statuses
  - MCP/CLI tool summary, bounded and redacted
  - scanner findings and blocker status
  - skipped checks, explicitly not pass
  - human-review checklist
  - known limitations
  - follow-up recommendations
  - authority disclaimer

Rules:
  1. Handoff bundle is review context only.
  2. It does not create human review.
  3. It does not promote artifacts.
  4. It does not mark accepted/refuted/proved.
  5. It must fail closed when blocking leak scanner findings exist.

Before finishing:
  - bundle schema tests
  - missing-check tests
  - leak-blocking tests
  - skipped-not-pass tests
  - run standard commands
  - stop
```

Acceptance:

```text
- Maintainer can inspect one compact bundle instead of a raw tool transcript.
- Bundle cannot hide skipped/failed/blocked checks.
- Bundle has no authority beyond review context.
```

## Task D.2: operator-handoff-export

```text
Repository:
  tcs-cosheaf

Branch:
  operator-handoff-export

Goal:
  Add explicit review-context export for a handoff bundle.

Allowed changes:
  cosheaf/operator_session/
  cosheaf/cli.py
  tests/test_operator_handoff_cli.py
  docs/OPERATOR_HANDOFF.md
  docs/CODEX_WORKFLOW.md
  context/INTERFACE_REGISTRY.md

Required CLI:
  cosheaf operator handoff export --handoff <handoff-id> --dry-run --json
  cosheaf operator handoff export --handoff <handoff-id> --json

Export target:
  reviews/operator/<handoff-id>.yaml

Rules:
  1. Dry-run must show target path without writing.
  2. Non-dry-run writes only review-context YAML under `reviews/operator/`.
  3. Export cannot write `kb/accepted/`.
  4. Export cannot create human review or promotion.
  5. Export must include scanner result and authority disclaimer.
  6. Export should be deterministic enough for tests.

Before finishing:
  - dry-run test
  - export test
  - accepted-write rejection test
  - scanner-blocked export test
  - run standard commands
  - stop
```

Acceptance:

```text
- Review handoff can be persisted intentionally.
- Persisted handoff is clearly review context, not review approval.
```

---

# Phase E: downstream workspace/public-KB integration smoke

## Task E.1: workspace-operator-session-demo

```text
Repository:
  tcs-cosheaf-workspace-template

Branch:
  workspace-operator-session-demo

Goal:
  Add a workspace demo that exercises operator sessions and handoff preview without modifying public KB or accepted artifacts.

Allowed changes:
  Makefile
  README.md
  docs/OPERATOR_SESSION_DEMO.md
  scripts/demo_operator_session.sh or .py
  RELEASE_CHECKLIST.md
  .gitignore if needed

Required Make target:
  make operator-session-demo

Demo flow:
  1. install or locate framework
  2. run workspace info
  3. validate and gate
  4. build context for demo issue
  5. create strategy plan or use existing strategy demo path
  6. start operator session
  7. append check/reference records
  8. scan session
  9. build handoff bundle
  10. preview export with dry-run

Rules:
  1. No accepted writes.
  2. No public KB modification.
  3. No hosted provider/API key.
  4. Runtime outputs stay ignored.
  5. Demo must work with published tag after v0.6.0; during development it may support local framework checkout.

Before finishing:
  - make validate
  - make gate
  - make operator-session-demo if available
  - git diff --check
  - stop
```

Acceptance:

```text
- Workspace users can see the whole operator-session and handoff shape.
- Demo remains local and review-only.
```

## Task E.2: public-kb-operator-handoff-policy

```text
Repository:
  tcs-kb-public

Branch:
  public-kb-operator-handoff-policy

Goal:
  Document and guard how operator handoff bundles may be referenced in public KB work without becoming source metadata, human review, or accepted evidence.

Allowed changes:
  README.md
  RELEASE_CHECKLIST.md
  docs/OPERATOR_HANDOFF_POLICY.md
  .github/pull_request_template.md
  scripts/check_public_kb_policy.py only if a small deterministic guard is needed
  tests/ if present

Required policy:
  1. Operator handoff is review context only.
  2. Operator handoff cannot replace source metadata.
  3. Operator handoff cannot replace human review.
  4. Operator handoff cannot authorize accepted status or accepted refutation.
  5. Public KB must not import private workspace session logs.
  6. Handoff records must not contain secrets, provider dumps, hidden reasoning, or private paths.
  7. Any public contribution still needs normal validation, gate, source metadata, human review, and promotion policy.

Do not:
  add public KB artifacts
  change accepted artifacts
  change review records
  change formalization metadata
  change promotion semantics

Before finishing:
  - python scripts/check_public_kb_policy.py if available
  - cosheaf validate
  - cosheaf gate run
  - cosheaf gate run --pr-checklist .github/pull_request_template.md
  - git diff --check
  - stop
```

Acceptance:

```text
- Public KB policy clearly handles operator handoff records.
- No KB content or artifact authority changed.
```

## Task E.3: ecosystem-operator-session-smoke

```text
Repository:
  tcs-cosheaf

Branch:
  ecosystem-operator-session-smoke

Goal:
  Add ecosystem smoke rows for operator-session and handoff workflows across framework/workspace/public-KB.

Allowed changes:
  scripts/ecosystem_smoke.py
  tests/test_ecosystem_smoke.py
  docs/EVALUATION.md
  docs/OPERATOR_HANDOFF.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required smoke rows:
  - framework operator session model/CLI smoke
  - framework handoff build/export dry-run smoke
  - workspace-template operator-session demo smoke
  - public KB operator handoff policy smoke

Rules:
  1. Network rows remain opt-in.
  2. Missing optional verifier/provider/network rows are skipped, not pass.
  3. Generated runtime outputs stay under ignored `.cosheaf/` paths.
  4. Smoke must not require API keys.

Before finishing:
  - targeted ecosystem-smoke tests
  - full standard framework commands
  - git diff --check
  - stop
```

Acceptance:

```text
- Three-repo operator-session workflow is covered by deterministic smoke.
- Skips remain truthful.
```

---

# Phase F: v0.6.0 release candidate and publication closeout

## Task F.1: release-v060-readiness-and-rc

```text
Repository:
  tcs-cosheaf

Branch:
  release-v060-readiness-and-rc

Goal:
  Prepare conservative v0.6.0 release candidate metadata after operator-session and handoff workflows are implemented and downstream smoke is complete.

Allowed changes:
  pyproject.toml
  cosheaf/__init__.py
  docs/releases/v0.6.0.md
  README.md
  README.zh-CN.md
  RELEASE_CHECKLIST.md
  docs/ROADMAP.md
  docs/EVALUATION.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required verification:
  - operator session CLI works
  - MCP session recording works and is optional
  - leak scanner blocks handoff export on blockers
  - handoff bundle/export works as review context only
  - workspace operator-session demo merged or ready
  - public KB operator-handoff policy merged or ready
  - ecosystem matrix rows pass/skip truthfully

Do not:
  publish tag
  update downstream pins yet
  claim production readiness
  change accepted-promotion semantics

Before finishing:
  - python -m cosheaf.cli version --json
  - make lint
  - make typecheck
  - make test
  - make validate
  - make gate
  - python scripts/ecosystem_smoke.py --matrix ...
  - git diff --check
  - stop
```

Acceptance:

```text
- Package metadata records 0.6.0 RC.
- Release note is conservative and lists limitations.
- No tag/release publication is claimed by this task.
```

## Task F.2: release-v060-publication-closeout

```text
Repository:
  tcs-cosheaf, after maintainer creates tag/release and downstream pin PRs merge.

Branch:
  release-v060-publication-closeout

Goal:
  Record the published v0.6.0 release state after tag, release, release smoke, workspace pin update, and public KB CI pin update complete.

Allowed changes:
  README.md
  README.zh-CN.md
  RELEASE_CHECKLIST.md
  docs/ROADMAP.md
  docs/releases/v0.6.0.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Required evidence:
  - annotated tag object and peeled commit
  - GitHub release URL
  - release smoke from @v0.6.0
  - workspace-template pin PR number and tests
  - public KB pin PR number and tests
  - ecosystem matrix result with pass/fail/skipped counts

Do not:
  change runtime behavior
  add dependencies
  change schemas
  write KB artifacts
  create human review
  promote artifacts

Before finishing:
  - make validate
  - make gate
  - git diff --check
  - stop
```

Acceptance:

```text
- Published v0.6.0 state is recorded truthfully.
- Downstream pins are complete only after release smoke passes.
- Future next-line planning starts from a new audit.
```

---

## First task to give Codex now

```text
Task: post-v050-v060-kickoff
Repository: tcs-cosheaf first; inspect workspace-template and tcs-kb-public as needed.
Branch: post-v050-v060-kickoff

Goal:
  Verify the completed v0.5.0 state and land the v0.6.0 Operator Session + Review Handoff plan.

Create/update only:
  docs/POST_V050_STATE_AUDIT.md
  docs/CODEX_DEVELOPMENT_PLAN_V10.md
  docs/ADR/0027-operator-session-review-handoff.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md

Do not:
  implement operator sessions
  add dependencies
  add schemas
  change runtime behavior
  bump version
  write KB artifacts

Required checks:
  - package metadata and cosheaf.__version__ are 0.5.0
  - v0.5.0 tag/release/release-smoke complete
  - workspace-template active pins use @v0.5.0
  - public KB CI installs @v0.5.0
  - open PRs/issues are empty or intentionally deferred
  - MCP controlled-write tools exist but remain bounded
  - no accepted-write, promotion, human-review, verifier-pass, provider-default, or production-ready claims are introduced

Run:
  make lint
  make typecheck
  make test
  make validate
  make gate
  git diff --check

Stop after this task.
```

## Completion checklist for V10

```text
- [x] v0.5 completion audit landed.
- [x] ADR 0027 landed.
- [x] Operator session DTO/storage landed.
- [ ] Operator session CLI landed.
- [ ] MCP session recording landed.
- [ ] Leak scanner landed.
- [ ] Handoff bundle landed.
- [ ] Handoff export landed.
- [ ] Workspace demo landed.
- [ ] Public KB handoff policy landed.
- [ ] Ecosystem smoke rows landed.
- [ ] v0.6.0 RC prepared.
- [ ] v0.6.0 tag/release/downstream pins closed out.
```
