# Project State

This file is ordered newest first. Older sections are historical snapshots and
must not override the current status recorded at the top of the file.

## V14 B.1 workflow core follow-up - 2026-06-18

Issue #426 implements the persistent reviewable-workflow core after the
published `v0.9.0` release. The current workflow surface now includes:

- `cosheaf workflow start --issue <issue-id> --query <query> --json`;
- `cosheaf workflow show <workflow-id> --json`;
- `cosheaf workflow step <workflow-id> --json`;
- `cosheaf workflow run <workflow-id> --max-steps <n>
  --execute-local-actions --json`;
- `cosheaf workflow readiness <workflow-id> --json`.

Workflow runtime records are written under
`.cosheaf/workflows/<workflow-id>/`:

- `workflow.json`;
- `events.jsonl`;
- `librarian.json`;
- `fsm.json`;
- `loop.json`;
- `readiness.json`.

The local execution path remains bounded by the existing whitelisted local
action registry. Accepted writes, network access, hosted providers, and
arbitrary shell execution remain disallowed through the workflow runner.
Unknown actions and accepted-write actions are blocked and recorded as review
context, not hidden or treated as pass.

This follow-up does not implement draft proposal generation, workflow handoff
build/show/scan/export, workflow scanner integration, reviewable-workflow eval
coverage, downstream workspace-template demo targets, or public-KB workflow
packet policy guards. Workflow output remains review context only. It is not
proof, source metadata, human review, verifier pass, gate pass, accepted
status, accepted refutation, or promotion authority.

## v0.9.0 documentation closeout, code audit, and CI repair - 2026-06-18

The `v0.9.0` tag and GitHub release are published:

- package metadata records `0.9.0`;
- `cosheaf.__version__` records `0.9.0`;
- `python -m cosheaf.cli version --json` reports `0.9.0`;
- GitHub release: https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0

This historical documentation closeout corrected stale current-state docs that still
described `v0.7.0` or `v0.7.0` release-candidate status as active. The current
release line is `v0.9.0 Reviewable Research Workflow MVP`, but the code audit
at PR #425 closeout found that the workflow implementation was still a thin
first surface:

- `cosheaf/workflow/engine.py` defines workflow DTOs, authority notices,
  `start_workflow`, `append_step`, and `assess_readiness`;
- `cosheaf/workflow/cli.py` registers `workflow start`, `workflow step`, and
  `workflow readiness`;
- `workflow start` emitted a workflow JSON record;
- `workflow step` and `workflow readiness` were ephemeral and did not yet load or
  persist `.cosheaf/workflows/<workflow-id>/` state.

At that closeout point, the following V14 items remained incomplete and were
not to be claimed as complete:

- persisted workflow runtime storage and replay;
- `workflow show` and bounded `workflow run`;
- draft proposal generation from workflow output;
- workflow handoff build/show/scan/export commands;
- workflow scanner integration;
- `cosheaf eval reviewable-workflow --json`;
- workspace-template `reviewable-workflow-demo`;
- public-KB workflow-output policy guard and framework pin closeout.

Initial verification during this documentation/code-audit closeout found
lint/typecheck failures in existing V13/V14 Python code. PR #425 now includes a
narrow code-quality repair for those issues, without adding new workflow
runtime capability or widening authority boundaries.

Local verification after the repair:

- `python -m cosheaf.cli version --json`: passed and reported `0.9.0`;
- `python -m cosheaf.cli workflow --help`: passed and showed only
  `start`, `step`, and `readiness`;
- `python -m cosheaf.cli workflow start --issue issue.audit.v090 --query
  "documentation closeout" --json`: passed and emitted a review-context
  authority notice;
- `make lint`: passed;
- `make typecheck`: passed for 201 source files;
- `make test`: passed with 753 tests;
- `make validate`: passed for 20 YAML records;
- `make gate`: passed;
- `git diff --check`: no whitespace errors, only LF/CRLF working-copy warnings.

The quality ladder was green locally on PR #425. Later V14 B.1 follow-up work
adds persisted workflow runtime storage, `workflow show`, persisted `workflow
step`, bounded `workflow run`, and persisted readiness reports. This still does
not make the V14 issue-to-handoff workflow engine complete; draft proposal,
workflow handoff, scanner, eval, and downstream policy work remain incomplete.

Downstream state observed during closeout:

- local workspace-template checkout was on `release-v090-pins`; README and
  Makefile referenced `v0.9.0`, but several scripts still defaulted to
  `v0.8.0` and some docs still mentioned `v0.7.0`;
- local public-KB `main` still installed `tcs-cosheaf` from `v0.7.0` in CI and
  README text.

No authority boundary changed. Workflow, loop, operator-session, provider,
MCP, eval, and handoff outputs remain review context only. They are not proof,
source metadata, human review, verifier pass, gate pass, accepted status,
accepted refutation, or promotion authority.

## Phase F completed: v0.7.0 published - 2026-06-17

v0.7.0 Bounded Research Loop + Attempt Memory is published:

- Annotated tag `v0.7.0` created and pushed
- GitHub release created: https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.7.0
- Post-tag install smoke from `@v0.7.0` passed
- Workspace-template PR #78: pins/docs/scripts updated to `@v0.7.0`
- Public KB PR #93: CI/docs updated to `@v0.7.0`
- Final ecosystem matrix: 22 pass, 0 fail, 3 skipped

All authority boundaries preserved. v0.7.0 does not add production autonomy,
automatic theorem proving, host-provider defaults, Lean semantic alignment, or
accepted-promotion authority.

## Task F.1: release-v070-readiness-and-rc - 2026-06-17

Branch `release-v070-readiness-and-rc` prepares the conservative `v0.7.0`
release candidate metadata. It bumps package version to `0.7.0`, adds
`docs/releases/v0.7.0.md`, and aligns README, roadmap, milestone, and project
state docs with the RC state.

Changes:
- `pyproject.toml`: version `0.7.0`
- `cosheaf/__init__.py`: `__version__ = "0.7.0"`
- `docs/releases/v0.7.0.md`: conservative RC release notes with explicit
  limitations and authority boundaries
- README, README.zh-CN.md, ROADMAP, CURRENT_MILESTONE, PROJECT_STATE updated

The RC does not claim `v0.7.0` is published. The public tag, GitHub release,
post-tag release smoke, and downstream pin alignment remain future Phase F.2
steps. No accepted writes, human-review creation, verifier/gate authority,
hosted-provider defaults, automatic theorem proving, or Lean semantic alignment
are added.

Local verification before PR:
- `make lint`: passed
- `make typecheck`: TBD
- `make test`: TBD
- `make validate`: TBD
- `make gate`: TBD
- `python scripts/ecosystem_smoke.py --matrix --framework-tag v0.7.0 ...`: TBD
- `git diff --check`: TBD

## Phase E completed: research-loop eval, downstream demo, and public-KB policy - 2026-06-17

The v0.7.0 Phase E ecosystem work has landed across the three repositories:

- `tcs-cosheaf` PR #407 added `cosheaf eval research-loop --json`,
  `evals/research_loop/cases.yaml`, research-loop workflow smoke coverage, and
  ecosystem matrix rows. It merged as commit
  `92d5360a58b1767f393a444cf766e772ee71b0c3`.
- `tcs-cosheaf-workspace-template` PR #77 added `make research-loop-demo` and
  `scripts/demo_research_loop.sh`. It merged as commit
  `7c30b3456c0123972fd3feb0fd7e0e147f3e27ed`.
- `tcs-kb-public` PR #92 added `docs/RESEARCH_LOOP_POLICY.md` and expanded
  the public-KB policy guard so research-loop output cannot be treated as
  source metadata, accepted proof, human review, verifier/gate pass, accepted
  status, accepted refutation, or promotion authority. It merged as commit
  `197eccd30a81842a23a36d1500261198d5579c22`.

The latest no-network three-repository matrix run used:

```bash
python scripts/ecosystem_smoke.py --matrix --framework-root . --workspace-template-root ../tcs-cosheaf-workspace-template --public-kb-root ../tcs-kb-public --cosheaf "python -m cosheaf.cli" --json
```

It passed with 25 rows: 22 pass, 0 fail, and 3 expected skipped rows for
optional verifier availability, the framework git-tag network release-smoke
row, and the workspace-template network install demo row.

Current handoff state:

- local squash-merged branches for the three Phase E PRs were cleaned after
  `git cherry` confirmed patch-equivalent content on `origin/main`;
- `tcs-cosheaf`, `tcs-cosheaf-workspace-template`, and `tcs-kb-public` main
  are synced to their merged Phase E commits;
- generated runtime outputs remain ignored under `.cosheaf/` or
  `context/TASKS/` and must not be committed.

Next task: start Phase F.1 `release-v070-readiness-and-rc` in
`tcs-cosheaf`. Do not claim `v0.7.0` has been published until package
metadata, release notes, tag/release, post-tag smoke, and downstream pin
closeout actually happen. The workspace-template published install pin remains
`v0.6.0`; the research-loop demo intentionally requires a local or otherwise
explicit v0.7-capable framework source.

Phase E did not add accepted writes, source-metadata authority, human-review
authority, verifier/gate pass authority, hosted-provider defaults, arbitrary
shell execution, automatic theorem proving, Lean semantic alignment, or
promotion-policy changes.

## Task E.1 completed: research-loop eval and ecosystem rows - 2026-06-17

Issue #406 / branch `research-loop-eval-and-ecosystem-demo` was the framework
Phase E.1 work item for the v0.7.0 bounded research-loop line. It merged in
PR #407.

Framework implementation state on this branch:

- `cosheaf.evals.research_loop` adds a deterministic eval harness with
  temporary fixtures containing an issue, public artifact marker, private draft
  artifact marker, prior failed loop memory, loop attempts, scanner checks, and
  budget-stop checks.
- `cosheaf eval research-loop --json` emits a deterministic
  `research_loop_eval` report with the Phase E metrics:
  `loop_validity_rate`, `attempt_schema_validity_rate`,
  `repeat_failure_detection_rate`, `unjustified_retry_block_rate`,
  `public_private_leak_count`, `scanner_blocker_accuracy`,
  `handoff_review_context_validity_rate`, `policy_overclaim_rejection_rate`,
  `budget_stop_accuracy`, `skipped_not_pass_count`, and
  `accepted_write_violation_count`.
- `scripts/ecosystem_smoke.py --matrix` now includes framework research-loop
  eval and workflow smoke rows, workspace-template `research-loop-demo`, and
  public-KB research-loop policy docs rows.
- `scripts/ecosystem_smoke.py --research-loop-workflow-smoke` runs a temporary
  local smoke for start, append-attempt, next, export-task, import-result with
  retry justification, scan, and finalize.
- The ecosystem matrix default framework tag is now `v0.6.0`, matching the
  current published release baseline.
- `README.md`, `README.zh-CN.md`, `docs/EVALUATION.md`,
  `docs/RESEARCH_LOOPS.md`, `docs/ROADMAP.md`,
  `context/CURRENT_MILESTONE.md`, and `context/INTERFACE_REGISTRY.md` describe
  the Phase E framework surfaces.

Local verification during framework E.1 closeout:

- `python -m pytest tests/evals/test_research_loop_eval.py -q`: passed with
  3 tests after type and CLI fixes.
- `python -m pytest tests/evals/test_research_loop_eval.py tests/test_ecosystem_smoke.py -q`:
  passed with 18 tests.
- `python -m cosheaf.cli eval research-loop --json`: passed with 10 cases,
  `skipped_not_pass_count: 1`, and `accepted_write_violation_count: 0`.
- `python scripts/ecosystem_smoke.py --research-loop-workflow-smoke`: passed
  with start, append-attempt, next, export-task, import-result, scan, and
  finalize against a temporary workspace.
- `make lint`: passed after line-length and import-order cleanup.
- `make typecheck`: passed for 189 source files.
- `make test`: passed with 753 tests.
- `make validate`: passed for 20 YAML records.
- `make gate`: passed and wrote ignored reports under `.cosheaf/reports/`.
- Documentation closeout also removed stale wording that said the Phase E eval
  command remained future work after the framework eval command was added.

The downstream workspace-template demo and public-KB policy/guard docs landed
after this framework PR; see the Phase E completed section above for the
cross-repository closeout.

No accepted KB writes, source-metadata semantics, human-review semantics,
verifier/gate authority, hosted provider calls, arbitrary shell execution, or
promotion-policy changes are added by the framework E.1 work.

## Task D.1 completed: attempt memory, failure avoidance, and loop scanner - 2026-06-17

Issue #404 / branch `attempt-memory-failure-avoidance-scanner` is the completed
Phase D.1 work item for the v0.7.0 bounded research-loop line.

Implementation state on this branch:

- `cosheaf/research/loop.py` adds `ResearchLoopMetrics`,
  `ResearchLoopAttemptMemoryEntry`, `ResearchLoopFailureCluster`,
  `ResearchLoopAttemptMemoryIndex`, `ResearchLoopScanFinding`, and
  `ResearchLoopScanResult`.
- `append_attempt` and `import_operator_result` rebuild the deterministic
  runtime index at `.cosheaf/research-loops/attempt-memory.json`.
- `next_loop_action`, `run_loop --dry-run`, and `export_operator_task` load
  attempt memory without writing source-of-truth files and surface cross-loop
  previous failures for the same issue.
- `import_operator_result` refuses repeated failed directions unless
  `retry_justification` is present, and records a non-blocking repeat-retry
  policy finding when the retry is justified.
- `scan_research_loop` and `cosheaf research-loop scan <loop-id> --json` scan
  loop runtime JSON, attempt JSON, and event logs for secrets, provider
  payloads, hidden reasoning, public-only private paths, accepted-write
  references, and authority claims.
- D.1 schema files cover metrics, memory entries, failure clusters,
  attempt-memory index, scan findings, and scan reports.

Documentation aligned for closeout:

- `README.md` and `README.zh-CN.md` distinguish the published `v0.6.0`
  release from the unreleased `v0.7.0` line and mention D.1 attempt memory,
  retry-justification checks, and loop scanning.
- `docs/RESEARCH_LOOPS.md` documents D.1 attempt memory, scanner CLI,
  `retry_justification`, runtime layout, and remaining Phase E/F work.
- `docs/CODEX_OPERATOR_RUNBOOK.md` includes the scanner command and D.1
  operator-loop boundary.
- `docs/AGENT_ACCESS.md` includes the scanner command, attempt-memory runtime
  writes, retry justification, and D.1 current status.
- `docs/SECURITY.md` records the loop scanner threat boundary and keeps scan
  reports review-context only.
- `docs/EVALUATION.md` records D.1 memory/scanner metrics. The earlier D.1
  closeout left Phase E eval as future work; the active E.1 framework section
  above supersedes that for `cosheaf eval research-loop --json`.
- `context/INTERFACE_REGISTRY.md` records the new Python, CLI, and schema
  surfaces.
- `context/CURRENT_MILESTONE.md` marks Phase D.1 complete and points next work
  at Phase E.

Verification during D.1 implementation:

- `python -m pytest tests/test_research_loop.py -q`: passed with 29 tests.
- `python -m pytest tests/test_research_loop.py tests/test_schema_files_exist.py -q`:
  passed with 38 tests.
- `make lint`: passed after formatting cleanup.
- `make typecheck`: passed for 187 source files after narrowing scanner JSON
  parsing.

Documentation closeout verification:

- `python -m pytest tests/test_research_loop.py tests/test_schema_files_exist.py -q`:
  passed with 38 tests.
- `make lint`: passed.
- `make typecheck`: passed for 187 source files.
- `make test`: passed with 748 tests.
- `make validate`: passed for 20 YAML records.
- `make gate`: passed and wrote reports under `.cosheaf/reports/`.
- `git diff --check`: no whitespace errors; Git reported expected LF-to-CRLF
  working-copy warnings.

Code-audit note:

- During closeout, a nested private-context scanner case was added so
  `unapproved_private_context` findings are handled by the research-loop
  scanner instead of relying on provider-log top-level JSON scanning.
- Scanner metrics now compute `repeat_failure_count` for scanned loop material,
  not only for the repository-level attempt-memory index.

Remaining Phase E/F work, not part of D.1:

- `cosheaf eval research-loop --json`;
- ecosystem smoke rows for loop start/next/import/finalize/scan/handoff dry-run;
- downstream workspace-template and public-KB demo/policy updates;
- v0.7.0 release-candidate metadata and publication closeout.

No accepted KB writes, human review creation, verifier-result mutation,
gate-pass creation, hosted-provider call, arbitrary shell execution through
Cosheaf, or promotion-policy change was added by D.1.

## Task C.1 completed: research-loop runner and operator protocol - 2026-06-17

Issue #402 / branch `research-loop-runner-and-operator-protocol` is the
completed Phase C.1 work item for the v0.7.0 bounded research-loop line.

Implementation state on this branch:

- `cosheaf/research/loop.py` adds DTOs for previous-failure summaries,
  deterministic next/step/run results, external operator task packets,
  operator result failures, operator results, and import results.
- `cosheaf/research/loop.py` adds service functions for `next_loop_action`,
  `step_loop`, `run_loop`, `build_operator_task`, `export_operator_task`, and
  `import_operator_result`.
- `cosheaf/cli.py` adds `cosheaf research-loop
  next/step/run/export-task/import-result`.
- `run_loop` currently supports dry-run planning only and explicitly refuses
  non-dry-run execution.
- C.1 JSON schemas are present for previous-failure summaries, next/step/run
  results, external-operator task packets, operator result failures, operator
  results, and import results.
- Focused regression coverage covers deterministic `next`, dry-run
  source-of-truth boundaries, `step` event writes, task-packet export,
  previous-failure surfacing, operator-result import, accepted-write
  rejection, authority-overclaim rejection, required result/failure evidence,
  budget exhaustion, and CLI JSON smoke.

Documentation aligned for closeout:

- `README.md` and `README.zh-CN.md` distinguish the published `v0.6.0` release
  from the active unreleased `v0.7.0` research-loop line.
- `docs/RESEARCH_LOOPS.md`, `docs/CODEX_OPERATOR_RUNBOOK.md`,
  `docs/AGENT_ACCESS.md`, `docs/OPERATOR_SESSIONS.md`, `docs/ROADMAP.md`, and
  `docs/SECURITY.md` describe the C.1 runner/operator-protocol boundary without
  granting accepted-write, review, verifier, gate, hosted-provider, shell, or
  promotion authority.
- `context/INTERFACE_REGISTRY.md` records the new Python, CLI, and schema
  surfaces.
- `context/CURRENT_MILESTONE.md` marks Phase C.1 complete and points next work
  at Phase D.
- `docs/CODEX_DEVELOPMENT_PLAN.md` now points readers to the current V11 plan
  instead of the historical V4 plan.
- `docs/LONGPLAN_COMPLETION_AUDIT.md` is explicitly historical and no longer
  claims the old V4/provider-hardening plan is current.

Verification during C.1 closeout:

- `python -m pytest tests/test_research_loop.py tests/test_schema_files_exist.py -q`:
  passed with 33 tests.
- `make lint`: passed after import-order and line-length cleanup.
- `make typecheck`: passed after narrowing optional event-path typing.
- Full closeout verification also passed:
  - `make lint`: all ruff checks passed.
  - `make typecheck`: mypy passed for 187 source files.
  - `make test`: 743 passed.
  - `make validate`: validation passed for 20 YAML records.
  - `make gate`: gate verdict passed.
  - `git diff --check`: no whitespace errors; Git reported expected LF-to-CRLF
    working-copy warnings on modified files.
- Stale-status scan found no remaining current-doc matches for C.1
  in-progress/pending schema/test wording after closeout updates.

At C.1 closeout, the remaining Phase D work was:

- attempt-memory indexing and repeat-failure detection;
- loop scanner CLI;
- loop handoff export beyond explicit operator task JSON packets;
- ecosystem demo/eval rows for completed loop workflows;
- conservative v0.7.0 release candidate closeout.

The first two items were completed by the later D.1 section above. Loop handoff
export, ecosystem demo/eval rows, and release closeout remain future work.

No accepted KB writes, human review creation, verifier-result mutation,
gate-pass creation, hosted-provider call, arbitrary shell execution through
Cosheaf, or promotion-policy change was added by C.1.

## Task B.1: bounded-research-loop-core completed - 2026-06-17

Landed the core research-loop data model, storage, CLI, schemas, tests, and docs
in one functional slice (`bounded-research-loop-core` branch).

Implementation:
- cosheaf/research/loop.py: ResearchLoop, ResearchLoopAttempt,
  ResearchLoopBudget, ResearchLoopStopCondition, ResearchLoopDecision,
  AttemptFailureRecord, AttemptEvidenceSummary, AttemptPolicyFinding,
  AttemptNextAction, and LoopReviewSummary models with validation, lifecycle
  states, JSON runtime storage, and event-log helpers
- schemas/research_loop.schema.json, research_loop_attempt.schema.json,
  attempt_failure_record.schema.json, and related research-loop DTO schemas
- CLI: cosheaf research-loop start/show/list/append-attempt/finalize
- tests/test_research_loop.py: 14 tests covering model serialization, validation,
  terminal attempt requirements, accepted path rejection, public-mode private
  reference rejection, status transitions, deterministic storage, and CLI JSON
  smoke
- docs/RESEARCH_LOOPS.md: full user-facing documentation

Verification:
- make lint: all checks passed
- make typecheck: no issues found in 187 source files
- make test: 733 passed
- make validate: passed
- make gate: pass

No accepted/promotion/human-review/verifier authority was added.

## v0.7.0 Development Kickoff - 2026-06-17

Started the v0.7.0 Bounded Research Loop + Attempt Memory development line
after completing the published v0.6.0 Operator Session + Review Handoff
release.

Task A.1 (post-v060-v070-kickoff) landed the post-v0.6.0 state audit, V11
development plan, ADR 0028, updated roadmap, and milestone/project-state
records. This is a docs-only kickoff task; no runtime behavior, schemas,
dependencies, CLI commands, or KB artifacts changed.

The v0.6.0 completion audit verified:
- Package version 0.6.0 ?
- Published v0.6.0 tag and GitHub release ?
- Downstream workspace-template pins @v0.6.0 ?
- Downstream public KB CI installs @v0.6.0 ?
- No open PRs/issues across three repos ?
- Operator session and handoff CLI present ?
- No accepted-write/promotion/human-review authority added ?
- Leak scanner blocks unsafe exports ?
- Public/private boundaries enforced ?
- MCP remains optional adapter ?
- No default hosted provider or CI network dependency ?
- Ecosystem smoke coverage present ?
- Limitations explicitly documented ?

The v0.7.0 line will add bounded multi-attempt research loops with:
- Research loop model, storage, CLI
- Loop runner with deterministic next-action planning
- External operator task export/result import protocol
- Attempt-memory index and repeat-failure detection
- Failure-avoidance context for next attempts
- Loop scanner extending session scanner
- Ecosystem demos and eval matrix
- Conservative v0.7.0 RC and publication

This line will NOT add production autonomy, automatic theorem proving, accepted
promotion through loops, AI as human review, default hosted provider, or
unrestricted shell execution. Loop success will never mean accepted status.

Reference plan: docs/CODEX_DEVELOPMENT_PLAN_V11.md
Reference ADR: docs/ADR/0028-bounded-research-loop-attempt-memory.md
Reference audit: docs/POST_V060_STATE_AUDIT.md


## v0.6.0 Publication Closeout - 2026-06-17

Issue 396 closes out the published `v0.6.0` Operator Session + Review Handoff
release after the release-candidate PR merged.

The annotated `v0.6.0` tag is published as tag object
`74fa02076607ab035011f10b7cae1b11246d0c5f`, peeled to main commit
`acc8d715f830672f516e41921eb6416978232374`. The GitHub release is published at
`https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.6.0`.

Post-tag release smoke from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.6.0` passed, installed
`tcs-cosheaf==0.6.0`, and ran help, version, validate, gate, index rebuild,
and context build in a temporary release-smoke workspace.

Workspace-template PR #75 moved active Makefile, demo scripts, and docs to
`@v0.6.0`; local verification ran `make install`, `make workspace-info`,
`make validate`, `make gate`, `make index`, `make pr-checklist`,
`make context`, `make demo`, and `git diff --check`, and GitHub Actions
`validate` passed. Public KB PR #90 moved CI/docs to `@v0.6.0`; local
verification ran installation from `@v0.6.0`, `cosheaf version`,
`cosheaf workspace info`, `cosheaf validate`, public KB policy guard
self-test and guard, both gate commands, and `git diff --check`, and GitHub
Actions `validate` passed.

The post-publication no-network ecosystem matrix with
`--framework-tag v0.6.0` reports 21 rows: 18 pass, 0 fail, and 3 skipped.
Optional verifier availability, framework git-tag release smoke, and
workspace-template install demo remain skipped by default because network rows
are opt-in. These skipped rows are not pass results; the separate release smoke
above covers the tag install path.

Publication closeout did not change runtime behavior, add dependencies, change
schemas, write KB artifacts, create human review, promote artifacts, change
accepted-promotion semantics, or widen MCP/provider authority. Operator
sessions and handoff bundles remain review context only, not proof, verifier
pass, gate pass, human review, source metadata, accepted status, accepted
refutation, or promotion authority.

## v0.6.0 Release Candidate - 2026-06-16

Issue 394 prepares the conservative `v0.6.0` Operator Session + Review Handoff
release candidate after the operator-session model/CLI, optional MCP session
recording, leak scanner, handoff bundle, handoff export, downstream
workspace-template demo, public KB handoff policy, and ecosystem smoke rows
landed.

The release-candidate task updates package metadata and `cosheaf.__version__`
to `0.6.0`, adds `docs/releases/v0.6.0.md`, and aligns README, roadmap,
release checklist, evaluation notes, current milestone, and project state with
the true RC boundary.

At that release-candidate stage, publication was deliberately deferred: no
public tag, GitHub release, post-tag release smoke, or downstream
workspace-template/public KB pin update was created by the RC task. The
publication closeout section above supersedes that historical snapshot.

The RC preserves the v0.6.0 authority boundary: operator sessions, MCP
recordings, leak scans, handoff bundles, and handoff exports are review context
only. They do not create proof, source metadata, verifier pass, gate pass,
human review, accepted status, accepted refutation, or promotion authority.
Skipped verifier/provider/network rows remain skipped and are not counted as
passes.

## Ecosystem Operator Session Smoke - 2026-06-16

Issue 392 adds ecosystem smoke matrix rows for the `v0.6.0` Operator Session
+ Review Handoff workflow across the framework, workspace template, and public
KB.

The framework matrix now includes:

- `framework.operator-session-cli-smoke`
- `framework.operator-handoff-dry-run-smoke`

The downstream matrix now includes:

- `workspace-template.operator-session-demo`
- `public-kb.operator-handoff-policy-docs`

The framework-local smoke rows create temporary workspaces, start and finalize
operator sessions, preserve skipped test/eval rows as skipped-not-pass, scan
sessions before handoff, build/show handoff bundles, and preview handoff
export with `--dry-run`. The workspace-template row runs the downstream
operator-session demo with the local framework checkout. The public KB row
checks the operator handoff policy and guard documentation surface.

The ecosystem matrix default release tag is updated to `v0.5.0`, matching the
published baseline that started the v0.6.0 line. Network rows remain opt-in,
optional verifier availability remains skipped when tools are unavailable, and
skips are not counted as passes.

This task does not add hosted providers, require API keys, require MCP, write
accepted knowledge, create human review, promote artifacts, mutate verifier
results, change accepted-promotion semantics, change public KB artifacts, or
claim theorem proving. Operator sessions and handoff bundles remain review
context only.

## Operator Handoff Export - 2026-06-16

Issue 390 adds explicit review-context export for operator handoff bundles in
the `v0.6.0` Operator Session + Review Handoff line.

The new commands are:

- `cosheaf operator handoff export --handoff <handoff-id> --dry-run --json`
- `cosheaf operator handoff export --handoff <handoff-id> --json`

The deterministic export target is `reviews/operator/<handoff-id>.yaml`.
Dry-run reports the target path without writing. Non-dry-run writes only
review-context YAML under `reviews/operator/`.

Export reads an existing runtime handoff bundle from
`.cosheaf/operator-sessions/<session-id>/handoff.json`, includes the handoff's
scanner result and authority disclaimer, fails closed when scanner blockers are
present, and rejects accepted KB export targets.

This task does not create human review, promote artifacts, mutate verifier
results, mark accepted/refuted/proved status, change gate behavior, change
accepted-promotion semantics, call hosted providers, or write KB artifacts.
Exported operator handoffs are review context only; they are not proof,
verifier pass, gate pass, source metadata, human review, accepted status,
accepted refutation, or promotion authority.

## Operator Handoff Bundle - 2026-06-16

Issue 388 adds compact runtime handoff bundles for finalized operator sessions
in the `v0.6.0` Operator Session + Review Handoff line.

The new commands are:

- `cosheaf operator handoff build --session <session-id> --json`
- `cosheaf operator handoff show <handoff-id> --json`

The deterministic handoff ID is `handoff.<session-id>`, and the runtime bundle
is written to `.cosheaf/operator-sessions/<session-id>/handoff.json`.

The builder requires the source session to be finalized, runs the session leak
scanner first, and fails closed when scanner blockers exist. A bundle includes
session and issue metadata, policy mode, KB root scope, referenced
repository-local files, draft/source-note/review-context references,
validation/gate/test/eval check statuses, skipped and missing check accounting,
bounded tool summary counts, scanner status, a human-review checklist, known
limitations, follow-up recommendations, and the operator-session authority
notice.

This task does not implement handoff export under `reviews/operator/`, accepted
writes, human-review creation, verifier-result mutation, promotion, provider
defaults, accepted-promotion semantics, or any proof/checking authority.
Handoff bundles are runtime review context only; they are not proof, verifier
pass, gate pass, source metadata, human review, accepted status, accepted
refutation, or promotion authority.

## Operator Session Leak Scanner - 2026-06-16

Issue 386 adds a deterministic scanner for operator-session runtime records
and future handoff candidates.

The new command is:

- `cosheaf operator session scan <session-id> --json`

The scanner reads `.cosheaf/operator-sessions/<session-id>/session.json` and
`.cosheaf/operator-sessions/<session-id>/events.jsonl`, then writes a runtime
report to `.cosheaf/operator-sessions/<session-id>/scan.json`. The report
includes `handoff_blocked`, finding counts, and stable finding records.
Blocking findings make the CLI exit nonzero after emitting JSON.

The scanner detects API-key-shaped values, bearer tokens, environment dumps,
secret-looking environment values, hidden-reasoning markers, raw provider
payloads, absolute private paths, accepted-write attempts, authority claims,
and private artifact IDs or private path references in `public_only` sessions.
It scans raw text plus parsed JSON so corrupted or unsafe runtime files can
still produce findings instead of being silently treated as clean.

This task does not implement handoff bundle/export behavior, accepted writes,
human-review creation, verifier-result mutation, promotion, provider defaults,
or accepted-promotion semantics. The scan report is runtime review metadata
only and is not proof, verifier pass, gate pass, human review, accepted status,
accepted refutation, source metadata, or promotion authority.

## MCP Session Recording - 2026-06-16

Issue 384 adds optional MCP tool-call recording for the `v0.6.0` Operator
Session + Review Handoff line.

MCP `tools/call` requests may now include `session_id` inside the tool
arguments. The MCP adapter strips that metadata before invoking the existing
tool handler, so existing tool semantics remain unchanged and MCP still works
without session tracking. When `session_id` is present, the adapter appends a
bounded `OperatorToolCallRecord` event under
`.cosheaf/operator-sessions/<session-id>/events.jsonl`.

The recorded event includes tool name, session mode, argument names/counts,
normalized status (`completed`, `failed`, `denied`, or `error`), a bounded
result summary, timestamp, and warning codes. It does not store full context
packs, full artifact YAML, provider request/response payloads, raw
stdout/stderr, environment dumps, API keys, hidden reasoning, or private query
text in public-only sessions.

Unknown or denied tools, validation-style MCP errors, and unexpected handler
errors are recorded when a valid session ID is supplied. Public-mode tool
results remain public-scoped before recording. This task does not add new MCP
tools, arbitrary shell access, accepted writes, human-review creation,
verifier-result mutation, promotion, provider defaults, leak scanning, handoff
bundle generation, or handoff export behavior.

## Operator Session CLI Core - 2026-06-16

Issue 382 adds the first CLI surface for `v0.6.0` Operator Session + Review
Handoff records.

The new commands are:

- `cosheaf operator session start --issue <issue-id> --json`
- `cosheaf operator session show <session-id> --json`
- `cosheaf operator session append-check <session-id> --kind validate|gate|test|eval --status pass|fail|error|skipped --json`
- `cosheaf operator session append-ref <session-id> --path <repo-local-path> --kind draft|review_context|runtime|report --json`
- `cosheaf operator session finalize <session-id> --json`

The CLI records bounded metadata only. It does not run validation, gates,
tests, evals, shell commands, MCP tools, providers, Lean, SAT, or SMT. Check
records preserve skipped as skipped; when no skipped summary is supplied, the
CLI records `Skipped operator-session checks are not pass evidence.`

`append-ref` rejects accepted KB paths and rejects private paths or
`--scope private` in `public_only` sessions. Finalized sessions reject later
`append-check` and `append-ref` operations.

This task did not add MCP session recording, leak scanning, handoff bundle or
export behavior, accepted writes, human-review creation, verifier-result
mutation, promotion, provider defaults, or accepted-promotion semantics. MCP
session recording was added later by Issue 384 as optional bounded metadata.

## Operator Session Model And Runtime Storage - 2026-06-16

Issue 380 adds the first functional `v0.6.0` Operator Session + Review Handoff
surface: strict operator-session DTOs and runtime storage.

The new `cosheaf.operator_session` package defines `OperatorSession`,
`OperatorToolCallRecord`, `OperatorArtifactRef`, `OperatorCheckResult`,
`OperatorSessionSummary`, and `OperatorPolicyFinding`. Runtime session records
are written under ignored `.cosheaf/operator-sessions/<session-id>/` paths as
`session.json` plus bounded `events.jsonl` event metadata. The matching schema
is `schemas/operator_session.schema.json`, and the user-facing boundary is
documented in `docs/OPERATOR_SESSIONS.md`.

Session records are review metadata only. The model rejects direct
`kb/accepted/` references, absolute paths, parent traversal, secret-looking
values, hidden-reasoning fields, environment dumps, raw stdout/stderr fields,
and full private/artifact text fields. Skipped check results must state that
skipped is not pass evidence.

This task does not add CLI commands, MCP session recording, leak scanning,
handoff bundle/export behavior, dependencies, accepted writes, human-review
creation, verifier-result mutation, promotion, provider defaults, or accepted
promotion semantics.

## Post-v0.5.0 To v0.6.0 Kickoff - 2026-06-16

Issue 378 starts the `v0.6.0` Operator Session + Review Handoff line after the
published `v0.5.0` Operator MCP + Codex Application Layer closeout.

The kickoff audit is recorded in `docs/POST_V050_STATE_AUDIT.md`. It verified
that package metadata, `cosheaf.__version__`, and
`python -m cosheaf.cli version --json` report `0.5.0`; the annotated
`v0.5.0` tag and GitHub release are published; release smoke from `@v0.5.0`
passed during publication closeout; workspace-template active demos/scripts
pin or install `@v0.5.0`; public KB CI installs `@v0.5.0`; and the three
repositories had no open PRs or issue blockers before this kickoff issue was
created.

The then-active plan was `docs/CODEX_DEVELOPMENT_PLAN_V10.md`; ADR 0027
records the Operator Session + Review Handoff direction. At kickoff, the optional MCP
surface already includes read-only/operator runtime tools and controlled
draft/review/runtime write tools, while forbidden authority-expanding tools
such as accepted writes, promotion, mark-human-reviewed, hosted-provider
default, and arbitrary shell remain absent.

The v0.6.0 line adds a deterministic audit and handoff layer over existing
CLI/MCP/service behavior. It is planned to record bounded operator-session
metadata under ignored `.cosheaf/operator-sessions/` runtime paths and to
export explicit review context under `reviews/operator/`.

This kickoff does not implement operator sessions, add dependencies, add
schemas, change runtime behavior, bump package version, write KB artifacts,
create human review, promote artifacts, mutate verifier results, change
accepted-promotion semantics, or claim automatic theorem proving. Operator
sessions, MCP recordings, leak scans, handoff bundles, and handoff exports
must remain review context only.

## v0.5.0 Publication Closeout - 2026-06-16

Issue 376 closes out the conservative `v0.5.0` Operator MCP + Codex
Application Layer publication after the release-candidate PR merged cleanly.

The annotated `v0.5.0` tag is published as tag object
`49ea4c9de153ccc9c41b39ec2fc705b3735c8795`, pointing through main commit
`25913148da5e512aa888ec76198146825509e071`. The GitHub release is published at
`https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.5.0`.

Release smoke from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.5.0` passed, installed
`tcs-cosheaf==0.5.0`, and covered help, version, validation, gate, index
rebuild, and context-build checks.

Downstream pin alignment is complete after release smoke. Workspace-template
PR #71 updated active demo, Makefile, provider-preview, fake-provider smoke,
verifier-evidence, failure-memory, checked-evidence, research-run, strategy,
and operator docs/scripts to `@v0.5.0`. Public KB PR #86 updated public KB CI
and release-facing docs to `@v0.5.0` without changing KB artifacts, review
records, formalization metadata, schemas, or promotion policy.

The post-publication ecosystem matrix with `--include-network` and
`--framework-tag v0.5.0` reports 17 rows: 16 pass, 0 fail, and 1 skipped. The
skipped row is optional verifier availability and is not counted as pass.

Publication closeout preserves the v0.5.0 authority boundary: CLI remains the
human and CI oracle, MCP remains optional and local, controlled MCP writes are
limited to draft/proposal/review-context/runtime records, and MCP/operator
output is not proof, checked evidence, verifier evidence, verifier pass, gate
pass, human review, accepted status, accepted refutation, or promotion
authority. This task does not add runtime behavior, dependencies, schemas,
default hosted provider calls, accepted writes, human-review creation,
verifier-result mutation, promotion semantics changes, public KB content,
workspace-template content, or automatic theorem-proving claims.

## v0.5.0 Release Candidate - 2026-06-16

Issue 374 prepares the conservative `v0.5.0` Operator MCP + Codex Application
Layer release candidate after the read-only MCP tools, controlled draft-write
MCP tools, operator runbook/workspace demo docs, public KB operator policy
smoke, and optional operator Skill package have merged.

This release-candidate branch updates package metadata and `cosheaf.__version__`
to `0.5.0`, adds `docs/releases/v0.5.0.md`, and aligns README, roadmap,
release checklist, current milestone, and project state with the true RC
status.

Observed release-candidate verification reports `0.5.0` from
`python -m cosheaf.cli version --json`; `make lint`, `make typecheck`,
`make test`, `make validate`, and `make gate` pass; `make test` reports 679
passed tests; and the no-network ecosystem matrix targeting `v0.5.0` reports
17 rows: 14 pass, 0 fail, and 3 skipped. The skipped rows are
optional verifier availability, future tag release smoke, and
workspace-template install demo; they are not counted as pass.

At the time of the release-candidate task, the public `v0.5.0` tag was not
published by that task. GitHub release publication, post-tag release smoke,
and downstream workspace-template/public KB pin updates were intentionally
left for the later publication closeout recorded above.

The RC preserves the v0.5.0 authority boundary: MCP remains optional and local,
CLI remains the human and CI oracle, controlled MCP writes are limited to
draft/proposal/review-context/runtime records, and MCP/operator output is not
proof, checked evidence, verifier evidence, verifier pass, gate pass, human
review, accepted status, accepted refutation, or promotion authority. This
task does not add runtime behavior, dependencies, schemas, default hosted
provider calls, accepted writes, human-review creation, verifier-result
mutation, promotion semantics changes, public KB content, workspace-template
content, or automatic theorem-proving claims.

## Optional Operator Skill Package - 2026-06-16

Issue 372 adds a documentation-only Cosheaf operator Skill package for
ChatGPT/Skill-like environments. The package lives at
`docs/skills/cosheaf-operator/SKILL.md`, with stable entrypoints in
`docs/OPERATOR_SKILL.md`, `docs/CODEX_OPERATOR_RUNBOOK.md`, and
`docs/OPERATOR_MCP.md`.

The package keeps CLI as the preferred operator path and MCP as an optional
adapter over whitelisted service-layer operations. It documents required repo
memory reads, workspace inspection, validate/gate baselines, bounded context
and strategy use, research-run provenance, controlled draft/review/runtime
writes, final verification, and PR summary expectations.

This documentation work does not add runtime dependencies, schemas, provider
defaults, hosted network calls, accepted writes, promotion authority,
human-review creation, verifier-result mutation, arbitrary shell, public KB
content, workspace-template behavior, or automatic theorem-proving claims.

## Operator Runbook And Workspace Demo Docs - 2026-06-16

Issue 370 documents the v0.5.0 operator workflow after the read-only and
controlled-write MCP surfaces landed.

The framework docs now include `docs/OPERATOR_WORKSPACE_DEMO.md`, a CLI-first
demo flow that covers workspace inspection, validation, gatekeeper, memory
search, context build, strategy planning, research-run provenance,
draft/review-context staging, check reruns, run finalization, and review-export
dry-runs. The demo keeps MCP optional and does not require hosted providers,
API keys, network access, public KB write access, Lean, SAT, SMT, or an
external MCP client.

This documentation work does not add runtime behavior, dependencies, schemas,
accepted writes, promotion, human-review creation, verifier-result mutation,
arbitrary shell, hosted-provider behavior, workspace-template content, or
public KB content.

## Controlled Draft-Write MCP Tools - 2026-06-16

Issue 368 extends the optional stdio MCP adapter for the `v0.5.0` Operator MCP
+ Codex Application Layer line with the C.1 controlled draft/review/runtime
write tool set.

The MCP tool whitelist now includes controlled tools for draft artifact writes,
draft source notes, WorkerBundle validation/staging, draft informational review
requests generated from WorkerBundles, checked counterexample evidence
validation/staging, failure-log appends on writable non-accepted artifacts,
research-run provenance start/append/finalize/review-export operations, and
strategy plan update/review-export operations.

These tools call typed Python service-layer logic rather than arbitrary shell.
They may write only draft/pre-accepted artifact records, staged source notes,
draft informational review requests, checked-evidence review records,
failure-log entries on writable non-accepted artifacts, research-run runtime
records, or review-context exports. They do not write accepted KB content,
promote artifacts, create human review, mutate verifier results, call hosted
providers, expose environment data, or bypass validation, gate, review, or
promotion policy. Checked counterexample evidence remains review evidence only,
research-run records remain provenance only, and strategy plans remain guidance
only.

## Read-Only Operator MCP Core - 2026-06-16

Issue 366 extends the optional stdio MCP adapter for the `v0.5.0` Operator MCP
+ Codex Application Layer line with the B.1 read-only operator tool set.

The read-only whitelist now covers workspace info, validation, gate and
PR-checklist gate reports, public memory cards/search, public-only context
build/show, public-scoped strategy plan/show/graph/next, research-run
show/evidence reports, and deterministic strategy/research-run eval smoke.
Legacy `gate_run` and `orchestrator_plan` remain available for compatibility.

The MCP implementation continues to call typed Python service-layer logic
rather than arbitrary shell. It may write deterministic runtime sidecars such
as gate reports, context packs, and runtime strategy plans. That read-only-core
task did not write accepted KB content, promote artifacts, create human review,
mutate verifier results, call hosted providers, or add controlled-write MCP
tools. Later v0.5.0 work added only narrow controlled draft/review/runtime MCP
tools under the same no-accepted-write boundary. Public operator mode filters
strategy output so private artifact IDs and private issue tags are not
returned.

## Post-v0.4.0 to v0.5.0 Kickoff - 2026-06-16

Issue 364 starts the `v0.5.0` Operator MCP + Codex Application Layer line
after the published `v0.4.0` Strategy Planner + Research Task Graph closeout.

The kickoff audit is recorded in `docs/POST_V040_STATE_AUDIT.md`. It verified
package metadata `0.4.0`, the annotated `v0.4.0` tag, the published GitHub
release, a fresh release smoke from `@v0.4.0`, workspace-template/public-KB
pin alignment to `@v0.4.0`, and the absence of open PR/issue blockers across
the three repositories.

The then-active plan was `docs/CODEX_DEVELOPMENT_PLAN_V9.md`; ADR 0026
records the Operator MCP + Codex Application Layer direction. At kickoff, the
MCP surface was a minimal read-only stdio layer. V9 expands it only as an optional operator
adapter over existing service-layer or CLI-equivalent policy boundaries.

This kickoff does not change runtime behavior, dependencies, schemas, package
version, provider behavior, MCP behavior, accepted writes, human-review state,
artifact status, promotion semantics, workspace-template content, public KB
content, or downstream pins.

## v0.4.0 Documentation And Code Audit Closeout - 2026-06-16

Issue 362 closes out stale active-line wording after the published `v0.4.0`
release and records a focused strategy-planner code audit in
`docs/CODE_AUDIT_V040.md`.

The audit confirms that strategy plans remain guidance only: runtime plans stay
under `.cosheaf/strategy/`, explicit review exports stay under
`reviews/strategy/`, skipped research-run results remain skipped, direct
`kb/accepted/` strategy write targets are rejected, and strategy outputs do not
claim proof, verifier pass, gate pass, human review, accepted status, accepted
refutation, or promotion authority.

This closeout does not change runtime behavior, schemas, provider behavior,
MCP behavior, accepted writes, human-review state, artifact status, promotion
semantics, workspace-template content, or public KB content.

## v0.4.0 Publication Closeout - 2026-06-15

Issue 358 closes out the `v0.4.0` Strategy Planner + Research Task Graph
publication after the release-candidate PR merged cleanly. The annotated
`v0.4.0` tag object is `4c58cf94499d6b18ffec1c98157b608b90a9ad63`, pointing
through the reviewed `Prepare v0.4.0 release candidate` main commit
`9f2e51eddeca6bc09d1915e706493ca4b4d5f99a`.

The GitHub release `v0.4.0 Strategy Planner + Research Task Graph` is
published. Release smoke installed `tcs-cosheaf==0.4.0` from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0` and passed help,
version, validation, gate, index rebuild, and context-build checks.

The planned release-smoke command in the external longplan used
`--framework-ref`, but the current `scripts/release_smoke.py` interface accepts
`--source`; the successful smoke used the equivalent explicit git source.

Downstream workspace-template and public KB active pins were aligned to
`@v0.4.0` after release smoke: workspace-template PR #69 updated active demo
and script pins, and tcs-kb-public PR #80 updated CI and README baseline text.
This closeout does not add runtime behavior, does not call hosted providers by
default, does not require MCP, does not write accepted knowledge, does not
create human review, does not promote artifacts, and does not change
accepted-promotion semantics.

## v0.4.0 Release Candidate - 2026-06-15

Issue 356 prepares the conservative `v0.4.0` Strategy Planner + Research Task
Graph release candidate after the strategy/task-graph core, planner/run-loop
integration, downstream workspace/public-KB policy work, and ecosystem smoke
rows landed.

This release-candidate branch updates package metadata and `cosheaf.__version__`
to `0.4.0`, adds `docs/releases/v0.4.0.md`, and aligns README, roadmap,
release checklist, current milestone, and project state with the true RC
status.

At the time of the release-candidate task, the public `v0.4.0` tag was not
published by that task. GitHub release publication, post-tag release smoke,
and downstream workspace-template/public KB pin updates were intentionally
left for the later v0.4.0 publication closeout.

The RC continues to preserve the v0.4.0 authority boundary: strategy plans are
guidance only, not proof, checked evidence, verifier evidence, verifier pass,
gate pass, human review, accepted status, accepted refutation, or promotion
authority. This task does not add hosted provider calls, does not require MCP,
does not write accepted knowledge, does not create human review, does not
promote artifacts, and does not change accepted-promotion semantics.

## v0.4.0 Downstream Strategy Smoke - 2026-06-15

Issue 354 extends the three-repository ecosystem smoke matrix for the active
`v0.4.0` Strategy Planner + Research Task Graph line after the downstream
workspace-template strategy demo and public KB strategy-plan policy landed.

The matrix now includes:

- `framework.strategy-planner-eval` through
  `cosheaf eval strategy-planner --json`;
- `workspace-template.strategy-demo` through the workspace-template
  `make strategy-demo` target with local framework checkout environment; and
- `public-kb.strategy-plan-policy-docs`, a docs smoke that confirms public KB
  strategy-plan policy keeps strategy plans non-authoritative.

The default network-release row now points at the active `v0.4.0` target and
remains skipped unless `--include-network` is explicitly supplied. This work
does not publish the `v0.4.0` tag, does not call hosted providers, does not
require MCP, does not execute strategy tasks, does not create human review,
does not write accepted knowledge, and does not change promotion semantics.

## v0.4.0 Strategy Run-Loop Integration - 2026-06-15

Issue 352 connects the strategy planner to the completed `v0.3.0`
research-run loop while keeping `v0.4.0` as the active development line and
`0.3.0` as the current package/release baseline until release-candidate work.

The Phase 2 CLI adds:

- `cosheaf strategy plan --issue <issue-id> --from-context <context-dir> --json`
- `cosheaf strategy update-from-run --plan <plan-id> --run <run-id> --json`
- `cosheaf strategy export-review --plan <plan-id> --dry-run --json`
- `cosheaf strategy export-review --plan <plan-id> --json`
- `cosheaf eval strategy-planner --json`

Strategy task nodes can now carry non-authoritative references to commands,
context packs, research runs, artifacts, checked counterexample evidence,
validation reports, gate reports, and review exports. Failed and skipped
research-run steps remain failed/skipped, not pass. Strategy review export
writes only under `reviews/strategy/` and remains review context only.

Context packs surface compact strategy-plan summaries when a plan is associated
with the issue, and `RETRIEVAL_AUDIT.json` records strategy-plan counts and
summary entries. Public-only context excludes private-scope strategy node text.
Promotion readiness may report open strategy blockers as advisory warnings,
not automatic promotion blockers.

This work does not add hosted provider calls, does not require MCP, does not
execute strategy tasks, does not create human review, does not write accepted
knowledge, and does not change accepted-promotion semantics.

## v0.4.0 Strategy Task Graph Core - 2026-06-15

Issue 350 implements the first functional `v0.4.0` strategy-planner surface.
The new `cosheaf.strategy` package defines strict Pydantic DTOs for
`StrategyPlan`, `StrategyProblem`, `StrategyTaskGraph`, `StrategyTaskNode`,
and ranked `StrategyNextStep` records. Runtime plans are written as
deterministic JSON under `.cosheaf/strategy/<plan-id>/strategy.json`.

The Phase 1 CLI exposes:

- `cosheaf strategy plan --issue <issue-id> --json`
- `cosheaf strategy show <plan-id> --json`
- `cosheaf strategy graph <plan-id> --json`
- `cosheaf strategy next <plan-id> --json`

The deterministic planner reads issue metadata, direct related artifacts,
one-hop dependencies, artifact failure memory, candidate counterexample
references, staged checked counterexample evidence, and research-run records.
It ranks bounded next actions and treats `cosheaf context build`,
`cosheaf validate`, and `cosheaf gate run` as first-class recommended tasks.

The new public schema files are `schemas/research_strategy.schema.json` and
`schemas/research_task_graph.schema.json`. The docs surface is
`docs/STRATEGY_PLANNER.md`, with matching agent-access, Codex-workflow, and
interface-registry updates.

Strategy plans remain guidance only. They do not execute tasks, call hosted
providers, require MCP, create verifier results, create human review, write
accepted knowledge, mark accepted status, mark accepted refutation, or
authorize promotion. Candidate counterexamples remain candidate-only labels,
checked counterexample evidence remains review evidence only, research-run
records remain provenance only, and skipped results remain non-pass.

## Post-v0.3.0 to v0.4.0 Kickoff - 2026-06-15

Issue 348 starts the `v0.4.0` Strategy Planner + Research Task Graph line after
the published `v0.3.0` Checked Evidence + Research Run Loop release.

The active target is now `v0.4.0`. The `v0.2.x` series is treated as the
completed agent/access/evidence/failure-memory foundation, and `v0.3.0` is the
completed auditable checked-evidence and research-run loop. The new line adds
the missing planning layer: deterministic research problem decomposition,
task-graph modeling, ranked next steps, failed-direction avoidance, and
bounded command-oriented guidance for Codex-style external operators.

This kickoff lands `docs/CODEX_DEVELOPMENT_PLAN_V8.md`, ADR 0025, roadmap,
current milestone, and project-state updates only. It does not add runtime
behavior, schemas, provider or MCP behavior, accepted KB writes, version
bumps, release tags, or downstream pin changes.

Strategy plans are guidance only. They are not proof, checked evidence,
verifier evidence, verifier pass, gate pass, human review, accepted status,
accepted refutation, or promotion authority. The planned runtime implementation
must preserve the v0.3.0 boundaries for checked evidence and research-run
records, keep provider calls default-off, keep MCP optional, and keep skipped
rows visibly non-pass.

## v0.3.0 Published Release Closeout - 2026-06-15

Issue 344 closes out the `v0.3.0` Checked Evidence + Research Run Loop
publication after the release-candidate PR merged cleanly. The annotated
`v0.3.0` tag points through the reviewed `Prepare v0.3.0 release candidate`
main commit, and the GitHub release `v0.3.0 Checked Evidence + Research Run
Loop` is published.

Release smoke installed `tcs-cosheaf==0.3.0` from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.3.0` and ran help,
version, validation, gate, index rebuild, and context-build checks. The
workspace-template active demo/Makefile/CLI-agent/provider/verifier/failure
memory/checked-evidence/research-run paths now pin `v0.3.0`, and
`tcs-kb-public` CI installs `tcs-cosheaf` from `v0.3.0`.

This closeout is documentation/status only. It does not add runtime behavior,
change schemas, alter verifier semantics, expand provider or MCP authority,
write accepted knowledge, mark human review, promote artifacts, or claim
production readiness. Checked counterexample evidence remains review evidence
only, and research-run records remain provenance only.

## v0.3.0 Release Candidate Readiness - 2026-06-15

Issue 342 prepares the `v0.3.0` Checked Evidence + Research Run Loop release
candidate after the checked counterexample evidence core, research-run record
CLI core, external-operator workflow docs, downstream workspace/public-KB
surfaces, and integration/eval/ecosystem smoke matrix have landed.

The release-candidate branch updates package metadata and `cosheaf.__version__`
to `0.3.0`, adds `docs/releases/v0.3.0.md`, and refreshes release/status docs
so they distinguish:

- the published `v0.2.4` baseline, whose tag/release/smoke/downstream pins are
  complete;
- the `v0.3.0` release-candidate metadata, which is prepared in this PR; and
- the later publication closeout, which must create the public `v0.3.0` tag,
  publish the GitHub release, run release smoke from `@v0.3.0`, and update
  downstream workspace-template/public-KB pins only after smoke passes.

The readiness audit records no release blocker for entering the release
candidate. Checked counterexample evidence remains review evidence only, not
human review, accepted refutation, accepted status, verifier pass, gate pass,
or promotion authority. Research-run records remain provenance only, not proof,
human review, verifier pass, gate pass, accepted status, or promotion
authorization. Skipped verifier, provider, optional-tool, network, or operator
rows remain skipped, not pass.

This release-candidate task does not create the public `v0.3.0` tag, publish a
GitHub release, run post-tag release smoke, update downstream pins, add runtime
behavior, expand provider or MCP authority, run real provider calls, write
accepted knowledge, mark human review, promote artifacts, or change schema,
gate, verifier, public/private policy, or accepted-promotion semantics.

## v0.3.0 Integration Eval And Ecosystem Smoke - 2026-06-15

Issue 340 extends the framework ecosystem smoke matrix for the active
`v0.3.0` Checked Evidence + Research Run Loop line. The matrix now includes
direct framework rows for:

- `cosheaf eval checked-evidence-run-loop --json`
- `cosheaf eval research-run-loop --json`

It also includes the downstream workspace-template `make research-run-demo`
row and a public KB checked-evidence policy documentation smoke row. The
existing network rows remain opt-in and skipped by default; optional external
SAT/SMT/Lean/lake availability remains a skipped row when unavailable, not a
pass. The default release-smoke tag in `scripts/ecosystem_smoke.py` is aligned
with the published baseline `v0.2.4`. At the time this integration task
landed, package metadata and `cosheaf.__version__` still recorded `0.2.4`;
the release-candidate entry above supersedes that state by preparing the
`0.3.0` metadata bump.

This task does not add provider or MCP behavior, call hosted providers, require
network in default tests, write accepted knowledge, create human review, alter
promotion policy, claim automatic theorem proving, or claim informal/formal
semantic alignment. Checked evidence remains review evidence only, and
research-run records remain provenance only.

## External Operator Workflow Docs - 2026-06-15

Issue 338 updates the operator-facing v0.3.0 run-loop documentation after the
research-run record CLI core landed. The new
`docs/EXTERNAL_OPERATOR_RUN_LOOP.md` runbook records the expected CLI/Git
sequence for Codex-style external operators: read policy and issue context,
start a research run, inspect workspace state, establish validation/gate
baseline, search memory, build context, read known failures and evidence,
make issue-scoped edits, record commands/outputs, stage only controlled
review or draft records, re-run checks, finalize/export the run, and open a PR
with run and authority-boundary details.

The PR and issue templates now ask for research-run context and
candidate-vs-checked evidence distinctions where applicable. Review policy now
states that research-run records are provenance only and must not be treated as
proof, human review, verifier pass, gate pass, accepted status, or promotion
authority.

This task is documentation/template-only. It does not add provider or MCP
behavior, change runtime semantics, write accepted knowledge, create human
review, alter promotion policy, or bump the package version.

## Research Run Record CLI Core - 2026-06-15

Issue 336 implements the second functional `v0.3.0` research-run surface. The
new `ResearchRunRecord` model and `schemas/research_run.schema.json` define a
repository-local provenance ledger for external operator work. Runtime records
are written under `.cosheaf/runs/<run-id>/run.json`; explicit review exports
are written under `reviews/runs/<run-id>.yaml`.

The CLI now exposes:

- `cosheaf run start --issue <issue-id> --operator external --json`
- `cosheaf run append-command --run <run-id> --input-json <path> --json`
- `cosheaf run append-artifact --run <run-id> --artifact <artifact-id> --json`
- `cosheaf run append-output --run <run-id> --input-json <path> --json`
- `cosheaf run finalize --run <run-id> --status <status> --stop-reason <text> --json`
- `cosheaf run show <run-id> --json`
- `cosheaf run evidence-report --run <run-id> --json`
- `cosheaf run export-review --run <run-id> --dry-run --json`
- `cosheaf run export-review --run <run-id> --json`
- `cosheaf run replay-plan --run <run-id> --json`

Command records are sanitized before persistence, and output references must be
repository-local and outside accepted KB paths. Research-run payloads reject
authority-spoofing fields, hidden-reasoning fields, and secret-looking text in
free-form summaries. `replay-plan` is read-only and performs no execution.

The new deterministic eval harness `cosheaf.evals.research_run_loop` and CLI
command `cosheaf eval research-run-loop --json` cover command coverage,
skipped-not-pass, evidence separation, private-leak prevention, and authority
escalation. The harness uses local fixtures and does not call hosted providers,
MCP, SAT, SMT, Lean, lake, network, or API-key-backed services.

This task does not bump package version, run providers, require MCP, write
accepted knowledge, create human review, mark verifier or gate pass, change
promotion semantics, or claim proof/semantic alignment. Research-run records
are provenance for review only.

## Checked Counterexample Evidence Core - 2026-06-15

Issue 334 implements the first functional `v0.3.0` checked-evidence surface.
The new `CheckedCounterexampleEvidenceRecord` model and
`schemas/counterexample_evidence.schema.json` define durable checked
counterexample evidence separately from WorkerBundle counterexample candidates,
failure memory, verifier requests, verifier evidence, human review, accepted
refutation, accepted status, and promotion authority.

The CLI now exposes:

- `cosheaf counterexample evidence validate --input-json <path> --json`
- `cosheaf counterexample evidence stage --input-json <path> --json`
- `cosheaf counterexample evidence stage --input-json <path> --dry-run --json`
- `cosheaf counterexample evidence show --evidence <path-or-id> --json`

Staging writes only under
`reviews/evidence/checked-counterexamples/<evidence-id>.yaml`. The write path
refuses accepted KB paths, absolute paths, path traversal, duplicate staged
records, and authority-spoofing fields such as `human_reviewed`,
`review_state`, `accepted`, `artifact_status`, and `promote`.

Context packs now render visible checked counterexample evidence in
`CONTEXT.md`, `KNOWN_FAILURES.md`, and `RETRIEVAL_AUDIT.json`. Public-only
context excludes private checked evidence text and private target artifact IDs.
Promotion readiness reports checked evidence as advisory
`checked_counterexample_evidence` warning reasons only; those warnings do not
block promotion by themselves and do not replace validation, gates, verifier
policy, human review, or explicit promotion.

The new deterministic eval harness
`cosheaf.evals.checked_evidence_run_loop` and CLI command
`cosheaf eval checked-evidence-run-loop --json` cover candidate-vs-checked
separation, `checked_refutes` support evidence, skipped-not-pass behavior,
non-refuting `inconclusive`/`error` results, and accepted-write non-authority.
The harness uses local in-memory fixtures and does not call hosted providers,
MCP, SAT, SMT, Lean, lake, network, or API-key-backed services.

This task does not bump package version, change accepted promotion semantics,
mark human review, write accepted knowledge, refute artifacts automatically,
expand provider/MCP authority, run automatic theorem proving, or claim Lean or
informal/formal semantic alignment.

## Post-v0.2.4 to v0.3.0 Kickoff Audit And Plan - 2026-06-15

Issue 332 starts the `v0.3.0` Checked Evidence + Research Run Loop line after
the published `v0.2.4` Artifact Failure Memory + Attempt Traceability release.
The kickoff adds a minimum state audit, the active accelerated V7 development
plan, and ADR 0024.

The audit records that candidate counterexamples currently live in
WorkerBundle v2, reducer warnings, failure/counterexample evals, review
requests, and artifact failure-memory links as review-only metadata. These
surfaces do not create checked counterexample evidence, verifier evidence,
human review, accepted refutation, accepted status, or promotion authority.

The audit also records that run logging exists across task runs, orchestrator
runs, provider logs, and structured run logs, but that this is not yet a
complete external-operator research-run provenance ledger with start, append,
finalize, show, evidence-report, export-review, and replay-plan lifecycle
commands.

The active target is now `v0.3.0`. The `v0.2.x` series is treated as the
completed CLI-agent, provider, evidence, and failure-memory foundation. The
next functional task is `checked-counterexample-evidence-core`, followed by
`research-run-record-cli-core`.

This kickoff is documentation/status only. It does not add runtime behavior,
change schemas, alter verifier semantics, expand provider or MCP authority,
write accepted knowledge, mark human review, promote artifacts, change KB
content, or bump the package version. Skipped verifier, provider, SAT, SMT,
Lean, lake, optional-tool, network, or operator results remain skipped, not
pass.

## Post-v0.2.4 V6 Completion Audit And Docs Closeout - 2026-06-15

Issue 330 adds a V6 completion/code-surface audit after the published
`v0.2.4` release closeout and cleans up stale current-state wording that still
described V6 as an active implementation queue.

The audit records that all V6 tasks from the source longplan are complete:
post-v0.2.3 state audit, plan/ADR landing, failure-log schema design,
model/schema implementation, read-only and controlled draft-write CLI
surfaces, WorkerBundle bridge, memory/context surfacing, promotion-readiness
warnings, workspace demo, public KB policy, security regression coverage,
deterministic eval coverage, release readiness, release candidate, and
publication closeout.

This closeout is documentation/status only. It does not add runtime behavior,
change schemas, alter verifier semantics, expand provider or MCP authority,
write accepted knowledge, mark human review, promote artifacts, change KB
content, or claim production readiness. Failure memory remains
non-authoritative research memory, not proof, verifier success, checked
counterexample evidence, human review, gate success, accepted status, or
promotion evidence.

## v0.2.4 Artifact Failure Memory Published Release Closeout - 2026-06-15

Issue 328 closes out `v0.2.4` after tag/release publication, release smoke, and
downstream pin alignment. The annotated `v0.2.4` tag points through the
reviewed `Prepare v0.2.4 release candidate` main commit, and the GitHub
release `v0.2.4 Artifact Failure Memory` is published.

Release smoke installed `tcs-cosheaf==0.2.4` from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.4` and ran help,
version, validation, gate, index rebuild, and context-build checks. The
workspace-template active demo/Makefile/CLI-agent/provider/verifier paths now
pin `v0.2.4`, and `tcs-kb-public` CI installs `tcs-cosheaf` from `v0.2.4`.

This closeout is documentation/status only. It does not add runtime behavior,
change schemas, alter verifier semantics, expand provider or MCP authority,
write accepted knowledge, mark human review, promote artifacts, or claim
production readiness. Failure memory remains non-authoritative research memory,
not proof, verifier success, checked counterexample evidence, human review,
gate success, accepted status, or promotion evidence.

## v0.2.4 Artifact Failure Memory Release Candidate - 2026-06-15

Issue 326 prepares `v0.2.4` as the Artifact Failure Memory + Attempt
Traceability release candidate after the readiness audit. The release-candidate
branch updates package metadata and `cosheaf.__version__` to `0.2.4` and
converts `docs/releases/v0.2.4.md` from readiness-audit draft into conservative
release-candidate notes.

The candidate packages already-merged artifact failure-memory work:
optional artifact-level `failure_log` model/schema support, read-only
inspection, controlled draft/pre-accepted failure-log writes,
WorkerBundle-to-failure-log bridges, memory/search/context/promotion-readiness
surfacing, workspace-template demonstration, public KB policy, security
regression coverage, and deterministic eval coverage.

This release-candidate task does not create the public `v0.2.4` tag, publish a
GitHub release, run release smoke, update downstream pins, add runtime
behavior, expand provider or MCP authority, run real provider calls in CI,
write accepted knowledge, mark human review, promote artifacts, or change
schema, gate, verifier, public/private policy, or accepted-promotion
semantics. The public `v0.2.4` tag is expected only after the
release-candidate PR and required checks pass, main is re-synced, and the
maintainer release action verifies the tag target and release smoke.

## v0.2.4 Release Readiness Audit - 2026-06-15

Issue 324 adds `docs/releases/v0.2.4.md` as a conservative readiness-audit
draft for Artifact Failure Memory + Attempt Traceability. The audit records
that package metadata and `cosheaf.__version__` remain `0.2.3`, no local or
remote `v0.2.4` tag exists, and all three repositories had no open issues or
pull requests before the audit issue was created.

The audit finds no release blocker for entering a release-candidate PR after
the audit PR and CI pass. Deferred non-blockers remain explicit: checked
counterexample review artifacts beyond WorkerBundle candidate records are
future evidence-taxonomy work, downstream pins stay on `@v0.2.3` until a
reviewed `v0.2.4` tag and release smoke exist, and optional external tools or
network rows must remain skipped rather than pass when unavailable.

This is documentation/status only. It does not change runtime behavior,
version metadata, tags, downstream pins, schemas, verifier semantics, provider
or MCP authority, accepted-promotion policy, public/private policy, KB
artifacts, accepted knowledge, human-review status, or artifact promotion.

## Artifact Failure-Memory Eval Suite - 2026-06-15

Issue 322 adds deterministic artifact failure-memory retrieval/governance eval
coverage. The new Python-level harness in
`cosheaf.evals.artifact_failure_memory` loads
`evals/artifact_failure_memory/cases.yaml`, creates local temporary workspace
fixtures under `.cosheaf/evals/artifact_failure_memory/`, and exercises the
existing artifact-card search surface.

The default cases cover failure-memory retrieval recall, repeated failed
direction detection, public-only private failure-log leakage, authority
boundary preservation, and candidate-counterexample mislabel prevention. The
report exposes retrieval recall, repeated-direction slip rate, scope leak
count, authority violation count, and candidate-counterexample mislabel count.

This is evaluation coverage only. It does not add a CLI command, does not
change artifact schema, does not write accepted knowledge in the source
repository, does not create verifier results, does not mark human review, does
not run promotion, does not change gates or accepted-promotion semantics, does
not expand provider/MCP authority, and does not make failure memory proof,
verifier success, checked counterexample evidence, gate success, accepted
status, or promotion evidence.

## Artifact Failure Log Security Regression - 2026-06-15

Issue 320 adds executable security regression coverage for artifact-level
failure memory misuse. The new tests reject failure-log inputs that try to
claim human review, verifier pass, checked counterexample status, accepted
artifact status, or accepted evidence paths, including provider-origin inputs
that attempt to claim accepted authority.

The suite also verifies that public-only context builds exclude private
failure-log text and private artifact IDs. This is regression coverage only:
it does not change promotion semantics, verifier semantics, provider/MCP
authority, accepted-write policy, artifact schema, or public/private root
semantics.

## Promotion Readiness Failure Memory Reporting - 2026-06-15

Issue 318 adds read-only promotion-readiness surfacing for unresolved artifact
failure memory. `cosheaf promotion readiness --artifact ... --json` and
`--issue ... --json` now include `unresolved_failure_memory` warning reasons
for `failure_log` entries with `status: open`. The warnings include the failed
direction, failed reason, origin, attempt kind, and next possible directions.

These warnings are advisory review context only. They are distinct from
verifier failures, do not create verifier evidence, do not satisfy or replace
human review, do not write accepted knowledge, do not change artifact status,
do not run promotion, and are not automatic promotion blockers by themselves.
Resolved failure-memory entries do not clutter readiness reports.

## Context Pack Failure Sections - 2026-06-15

Issue 316 adds explicit failure-memory sections to context packs. When visible
artifact cards have artifact-level `failure_log` entries, `CONTEXT.md` and
`KNOWN_FAILURES.md` render a `Known Failed Directions` section with artifact
ID, direction, failed reason, status, next possible directions, origin, attempt
kind, path, root scope, and source/origin label. Empty failure logs do not add
that markdown section.

`RETRIEVAL_AUDIT.json` now includes a structured `failure_memory` array and
`context_payload.failure_entry_count` for the same visible entries. Public-only
context continues to exclude private artifacts, private artifact IDs, and
private failure-log text. The section is explicitly failed/unresolved attempt
memory only and does not create proof, refutation, verifier pass, checked
counterexample evidence, human review, gate success, accepted status, or
promotion evidence. It does not change promotion semantics, provider/MCP
authority, artifact schema, or accepted-write policy.

## Failure Log Memory Index - 2026-06-15

Issue 314 surfaces artifact-level `failure_log` metadata in memory and context
handoff surfaces. `ArtifactCard` now includes `failure_count` and
`recent_failure_directions`, and cards with failure-log entries receive
`failure-log:<status>` risk flags. `cosheaf memory search` indexes recent
failure directions so failed approaches can be found by keyword, with explicit
failure-memory relevance reasons and audit warnings that failure memory is not
proof, verifier success, human review, checked counterexample evidence, or
accepted-status evidence.

Context-pack card lines and `RETRIEVAL_AUDIT.json` include compact failure
summary metadata for visible cards. Public-only context still excludes private
artifacts, private artifact IDs, and private failure-log text. The change does
not alter artifact trust scores, review state, verifier state, gates,
promotion readiness, accepted status, provider/MCP authority, or accepted
promotion semantics.

## Failure Log From WorkerBundle - 2026-06-15

Issue 312 adds WorkerBundle-to-artifact-failure-log bridge commands.
`cosheaf artifact failure plan-from-bundle --bundle <path> --target-artifact
<artifact-id> --json` validates a WorkerBundle v2 and returns proposed
`FailureLogEntry` values derived from `failed_attempts` without writing files.
`cosheaf artifact failure add-from-bundle` applies the same conversion through
the controlled artifact failure-log write path, including dry-run support.

The bridge preserves WorkerBundle provenance with `origin: imported_bundle`.
Typed `counterexample_candidates` are linked only by candidate ID in
`related_counterexample_candidates`; they are not duplicated as checked
refutations or verifier results. Unsafe WorkerBundle authority claims, accepted
paths/status, readonly KB roots, and accepted artifact mutation remain refused.
The bridge does not create verifier results, does not mark human review, does
not run gates, does not promote artifacts, does not write accepted knowledge,
and does not change promotion semantics.

## Artifact Failure Log Draft Write CLI - 2026-06-15

Issue 310 adds `cosheaf artifact failure add --artifact <artifact-id>
--input-json <path>` with deterministic JSON output and dry-run support. The
command validates one artifact `FailureLogEntry`, appends it to a writable
non-accepted artifact, refreshes `updated_at` only on actual writes, reports
the exact target path, and keeps `accepted_write_performed=false`.

The write path refuses direct `kb/accepted/` mutation, accepted artifact status,
readonly KB roots, missing artifacts, duplicate artifact IDs, invalid
failure-log entries, and authority-spoofing fields that claim human review,
accepted status, verifier pass, or checked counterexample status. It does not
create verifier results, does not mark human review, does not run gates, does
not promote artifacts, does not write accepted knowledge, and does not change
promotion semantics. Failure-log entries remain research memory only: not
proof, not verifier success, not checked counterexample evidence, not human
review, not gate success, not accepted status, and not promotion evidence.

## Artifact Failure Log Read CLI - 2026-06-14

Issue 308 adds the read-only `cosheaf artifact failures <artifact-id>` command.
The command can emit deterministic JSON with artifact ID/path, KB root
name/scope/readonly metadata, `failure_count`, `failure_log` entries, and an
explicit authority notice. Missing artifacts return the stable
`artifact_not_found` `ErrorResult` code.

This task is read-only. It does not add a failure-log write command, does not
write files, does not create verifier results, does not mark human review,
does not run gates, does not promote artifacts, does not change accepted
promotion semantics, and does not expand provider/MCP authority. Failure-log
entries remain research memory only: not proof, not verifier success, not
checked counterexample evidence, not human review, not gate success, not
accepted status, and not promotion evidence.

## Artifact Failure Log Model And Schema - 2026-06-14

Issue 306 implements optional artifact-level `failure_log` support in the
framework model and artifact JSON Schema. `BaseArtifact.failure_log` defaults
to an empty list, preserving compatibility for existing artifacts. Each entry
is represented by `cosheaf.core.artifact.FailureLogEntry` with strict origin,
attempt-kind, status, timezone-aware timestamp, failure ID, required text, and
repository-local non-accepted evidence-path validation.

The artifact schema now accepts optional `failure_log` entries and records the
same required fields, origin/attempt/status enums, and repository-local
non-accepted evidence-path boundary. Tests cover default compatibility, valid
entry parsing and normalization, external targets, timezone-naive timestamp
rejection, empty required text rejection, invalid ID and target rejection,
unsafe evidence-path rejection, authority-spoofing rejection, and JSON Schema
structure.

This implementation changes artifact model/schema acceptance only. It does not
add read/write CLI commands, does not change validation/gate/promotion
semantics, does not create verifier results, does not mark human review, does
not write accepted knowledge, does not expand provider/MCP authority, and does
not treat failure memory as proof, verifier success, checked counterexample
evidence, gate success, accepted status, or promotion evidence.

## Artifact Failure Memory Plan Landing - 2026-06-14

Issue 302 lands the active V6 plan for `v0.2.4` Artifact Failure Memory +
Attempt Traceability and records ADR 0023. The plan follows the published
`v0.2.3` release and the post-v0.2.3 state audit. It defines the next line of
work: design and implement optional artifact-level `failure_log`, add read-only
and controlled draft write surfaces, bridge WorkerBundle failures into
artifact failure-log proposals, surface failure memory in retrieval/context and
promotion-readiness reports, update workspace/public KB policy surfaces, and
add security/eval regression coverage before v0.2.4 readiness.

This plan-landing task is documentation only. It does not change artifact
schema, Pydantic models, CLI behavior, retrieval, context-pack rendering,
promotion-readiness logic, verifier behavior, accepted-promotion semantics,
provider/MCP authority, workspace-template behavior, or public KB content.
Failure memory remains non-authoritative: not proof, not verifier success, not
human review, not a checked counterexample, and not promotion evidence by
itself.

## Post-v0.2.3 Artifact Failure Memory State Audit - 2026-06-14

Issue 300 audits the current three-repository state after the published
`v0.2.3` Verification Evidence Hardening release and confirms the next
implementation gap for artifact-level failure memory. `tcs-cosheaf` still
reports package version `0.2.3`; `tcs-cosheaf-workspace-template` active
workflow pins/defaults use `tcs-cosheaf@v0.2.3`; and `tcs-kb-public` CI
installs `tcs-cosheaf@v0.2.3`. Before issue 300 was opened, all three
repositories had no open pull requests or issues.

The audit confirms that `cosheaf/core/artifact.py` `BaseArtifact` and
`schemas/artifact.schema.json` do not yet define `failure_log`. Existing
failure/counterexample memory is preserved in WorkerBundle v2
`failed_attempts`, legacy and typed counterexample fields, draft review
requests from `cosheaf review request-from-bundle`, deterministic
failure/counterexample evals, verifier evidence evals, and read-only
promotion-readiness reporting, but not on durable artifact records.

This audit is documentation/status only. It does not implement `failure_log`,
change schemas, change runtime behavior, alter verifier or promotion
semantics, expand provider/MCP authority, modify workspace-template behavior,
or touch public KB content. Failure memory remains non-authoritative: not
proof, not verifier success, not human review, not checked refutation, and not
promotion evidence by itself.

## Post-v0.2.3 Documentation Audit Closeout - 2026-06-14

Issue 298 closes the remaining post-v0.2.3 documentation-audit drift after the
published `v0.2.3` tag/release, release smoke, downstream workspace/public KB
pin updates, and branch hygiene. The update marks
`docs/CODEX_DEVELOPMENT_PLAN_V5.md` as the completed durable record of the
v0.2.3 verification-evidence hardening plan rather than an active task queue,
and it updates `context/CURRENT_MILESTONE.md` so the current operating state no
longer describes release-closeout documentation as an active task.

The change is documentation/status only. It does not change runtime behavior,
schemas, verifier semantics, provider/MCP authority, accepted-promotion
semantics, public/private KB policy, workspace-template behavior, or public KB
content. The post-v0.2.3 baseline remains conservative: no production-readiness
claim, no automatic theorem proving, no Lean semantic-alignment claim, no
automatic autoformalization, no AI-as-human-review, no default real provider
calls, no accepted-write bypass, and skipped verifier/provider/tool results are
still not passes.

## v0.2.3 Verification Evidence Hardening Published Release Closeout - 2026-06-14

Issue 296 closes out `v0.2.3` after tag/release publication, release smoke, and
downstream pin alignment. The annotated `v0.2.3` tag points to the reviewed
`Prepare v0.2.3 release candidate` main commit, and the GitHub release
`v0.2.3 Verification Evidence Hardening` is published. Release smoke installed
`tcs-cosheaf==0.2.3` from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.3` and ran the clean
workspace help, version, validate, gate, index rebuild, and context-pack
checks.

Downstream alignment is complete for the active repositories:
`tcs-cosheaf-workspace-template` pins active demo, Makefile, CLI-agent,
provider-preview, fake-provider smoke, and verifier-evidence demo paths to
`v0.2.3`, and `tcs-kb-public` CI installs `tcs-cosheaf` from `v0.2.3`.

Release closeout verification reran the full framework command ladder and the
network-enabled ecosystem matrix. `make lint`, `make typecheck`, `make test`
(535 passed), `make validate`, and `make gate` passed. The
`--include-network` ecosystem matrix reported 10 rows with 9 pass, 0 fail, and
1 skipped; the skipped row was optional verifier availability because
SAT/SMT/Lean/lake tools were unavailable and was not counted as pass.

This closeout is documentation/status only. It does not add runtime behavior,
does not expand provider or MCP authority, does not run real provider calls in
CI or default tests, does not write accepted knowledge, does not mark human
review, does not promote artifacts, and does not change schema, gate,
verifier, public/private policy, or accepted-promotion semantics. `v0.2.3` is
not a production-readiness claim and does not provide automatic theorem
proving, Lean/mathlib/CSLib semantic alignment, automatic autoformalization,
or automatic accepted promotion.

## v0.2.3 Verification Evidence Hardening RC - 2026-06-14

Issue 294 prepares `v0.2.3` as the Verification Evidence Hardening release
candidate after the readiness audit. The release-candidate branch updates
`pyproject.toml` and `cosheaf.__version__` to `0.2.3` and converts
`docs/releases/v0.2.3.md` from readiness-audit draft into conservative
release-candidate notes.

The candidate packages already-merged verification/evidence hardening work:
verifier evidence record v1, read-only promotion-readiness reporting, SAT and
SMT result-depth fake-backend fixtures, Lean external reference ergonomics,
typed counterexample candidate records, failure-preserving review-request
generation, verifier-evidence evals, and the v0.2.3 three-repository readiness
matrix.

This release-candidate task does not create the public `v0.2.3` tag, publish a
GitHub release, update downstream repository pins, add runtime behavior, expand
provider or MCP authority, run real provider calls in CI, require API keys,
write accepted knowledge, mark human review, promote artifacts, or change
schema, gate, verifier, public/private policy, or accepted-promotion
semantics. The public `v0.2.3` tag is expected only after the
release-candidate PR and required checks pass, main is re-synced, and the
maintainer release action verifies the tag target and release smoke.

Local release-candidate verification passed: `python -m cosheaf.cli version
--json` reported `0.2.3`; `make lint`, `make typecheck`, `make test`,
`make validate`, and `make gate` passed; the no-network ecosystem matrix
reported 10 rows with 7 pass, 0 fail, and 3 skipped; and `git diff --check`
exited 0 with CRLF warnings only. The skipped matrix rows were optional
verifier availability, framework git-tag network install, and workspace demo
network install; they were not counted as pass.

## v0.2.3 Release Readiness Audit - 2026-06-14

Issue 292 audits whether the current framework main line can enter the
`v0.2.3` release-candidate task. The audit is documentation/status only. It
adds `docs/releases/v0.2.3.md` as a readiness-audit draft and updates the
roadmap, release checklist, and current milestone to record the release
readiness boundary.

The audit records that package metadata and `cosheaf.__version__` still report
`0.2.2`; the `v0.2.3` version bump, tag, GitHub release, and downstream pin
updates belong to a later release-candidate task. It answers the required
readiness questions: verifier evidence records are stable for the current
scope, SAT/SMT/Lean optional paths are tested without mandatory tools,
skipped-not-pass remains enforced, counterexample candidates remain
review-only until checked and reviewed, promotion-readiness reports remain
read-only, local three-repository compatibility paths are clean, and the only
open issue at audit start was the audit issue itself.

This task does not change runtime behavior, schema, verifier adapters, gates,
provider or MCP authority, promotion semantics, public/private policy, KB
artifacts, accepted knowledge, human-review status, or package version. It
does not claim production readiness, automatic theorem proving, automatic
accepted promotion, or informal/formal semantic alignment.

## v0.2.3 Three-Repository Readiness Matrix - 2026-06-14

Issue 290 extends `scripts/ecosystem_smoke.py --matrix` for the v0.2.3
verification-evidence readiness line. The structured matrix now includes the
framework local ecosystem smoke, framework verifier-evidence eval smoke,
optional verifier availability probe, framework git-tag release smoke,
workspace-template install demo, workspace-template CLI-agent demo,
workspace-template fake-provider smoke, workspace-template verifier-evidence
demo, public KB policy guard, and public KB verifier-policy self-test.

The matrix still reports pass, fail, and skipped rows separately. Network
install rows remain opt-in through `--include-network`. The optional verifier
availability row returns a skipped matrix result when SAT/SMT/Lean/lake tools
are unavailable; that skipped row is counted as skipped, not pass. Failure
messages still include the repository and command that failed. The public KB
row does not modify public KB content, and no matrix row performs accepted
writes, promotion, human review, hosted provider calls, provider authority
expansion, or MCP authority expansion.

## v0.2.3 Verifier Evidence Eval Suite - 2026-06-14

Issue 288 adds a deterministic Python-level verifier evidence eval harness
under `cosheaf.evals.verifier_evidence` plus the default case suite in
`evals/verifier_evidence/cases.yaml`. The suite covers passing verifier
evidence supporting readiness only when policy allows, failed evidence blocking
readiness, skipped checker-required evidence remaining not-a-pass, typed
candidate counterexamples staying review-only, and external Lean `#check`
evidence staying limited to symbol/import resolution rather than semantic
alignment.

The report exposes readiness boundary accuracy, failed-evidence blocker count,
skipped-not-pass count, candidate-counterexample review-only count, Lean
alignment-claim count, and accepted-write violation count. The harness uses
deterministic fake `VerifierEvidenceRecord` fixtures and typed
`CounterexampleCandidate` records only. It does not run SAT, SMT, Lean, lake,
or hosted providers; does not add MCP behavior; does not write accepted
knowledge; does not create human review; and does not change promotion,
gatekeeper, verifier, public/private, or formal-link semantics.

## v0.2.3 Failure-Preserving Review Request Generation - 2026-06-14

Issue 286 adds `cosheaf review request-from-bundle --bundle <path>` for
turning WorkerBundle v2 failure and counterexample evidence into draft
informational review-request records. The command validates the bundle through
the existing WorkerBundle v2 boundary and writes or previews a
`reviews/requests/*.yaml` record through the same controlled review-request
write path used by `cosheaf review request`.

Generated requests preserve assumptions, uncertainty, failed attempts,
verifier requests, legacy string counterexamples, typed
`counterexample_candidates`, dependency questions, risk flags, next steps,
confidence, and candidate limitations as findings. They remain draft review
context only. They do not mark `human_reviewed`, approve or reject claims,
create verifier results, write accepted knowledge, or promote artifacts.

Unsafe bundles that target accepted paths or stage human-reviewed proposed
artifacts are rejected before any review request is written. This task does
not change accepted-promotion semantics, provider/MCP authority, verifier
execution, or gate behavior.

## v0.2.3 Typed Counterexample Candidate Records - 2026-06-14

Issue 284 adds optional typed WorkerBundle v2 `counterexample_candidates` for
reviewable counterexample evidence. Each candidate records a candidate ID,
optional target claim, construction summary, evidence paths,
verifier-request IDs, status, and limitations. Candidate statuses are
`proposed`, `needs_check`, `checked_false`, `checked_true`, `rejected`, and
`superseded`.

The legacy string `counterexamples` field remains backward-compatible.
Reducers preserve both legacy and typed candidates as labeled review warnings.
Typed candidate records do not write accepted knowledge, do not create
verifier results, do not mark human review, do not promote artifacts, and do
not refute accepted claims by themselves. `checked_false` and `checked_true`
candidate statuses require at least one evidence path in the bundle schema,
but that evidence still remains review context until ordinary verifier and
human-review workflows handle it.

This task does not change accepted-promotion semantics, does not add provider
or MCP authority, does not write KB artifacts, and does not treat candidate
counterexamples as accepted refutations.

## v0.2.3 Lean External Reference Ergonomics - 2026-06-14

Issue 282 improves optional external Lean library reference `#check`
ergonomics without adding Lean, lake, CSLib, mathlib, or any external library
as a required dependency. The Lean external reference adapter remains a narrow
symbol/import resolution path: it generates a temporary Lean file with
`import <import_path>` and `#check <symbol>` for linked or checked external
formalization metadata, then records normalized verifier evidence when a fake
or real optional backend runs.

The task adds fake-backend coverage for missing import and missing symbol
stderr preservation, keeps fake pass/fail/skipped/error paths covered, and
improves formal library manifest diagnostics so unknown `library_ref` failures
list available manifest IDs. G10 surfaces that diagnostic in blocking issues,
but its policy semantics are unchanged.

This task does not fetch CSLib/mathlib, does not vendor Lean code, does not
autoformalize natural language, does not prove informal/formal semantic
alignment, does not update formalization status automatically, does not write
accepted knowledge, and does not change accepted-promotion semantics. Missing
Lean or lake remains `skipped`, not `pass`.

## v0.2.3 SMT Adapter Result-Depth Fixtures - 2026-06-14

Issue 280 expands SMT adapter result-depth coverage with fake-backend fixtures
for `sat`, `unsat`, `unknown`, malformed SMT-LIB, timeout, and unavailable
solver paths. The coverage asserts normalized `pass`, `fail`, `error`, and
`skipped` behavior, plus command metadata, repository-root cwd, timeout
metadata, stdout/stderr log paths, and skipped-not-pass boundaries.

This task does not add a mandatory SMT solver dependency, does not require
`z3` in CI, does not claim theorem proving, does not write accepted knowledge,
and does not change accepted-promotion semantics. Malformed SMT-LIB coverage
is represented as backend parse-error/`unknown` output normalized to `error`,
preserving the existing result taxonomy.

## v0.2.3 SAT Adapter Result-Depth Fixtures - 2026-06-14

Issue 278 expands SAT adapter result-depth coverage with fake-backend fixtures
for satisfiable, unsatisfiable, malformed DIMACS, timeout, and unavailable
solver paths. The coverage asserts normalized `pass`, `fail`, `error`, and
`skipped` behavior, plus command metadata, repository-root cwd, timeout
metadata, stdout/stderr log paths, and skipped-not-pass boundaries.

This task does not add a mandatory SAT solver dependency, does not require
`kissat` in CI, does not claim theorem proving, does not write accepted
knowledge, and does not change accepted-promotion semantics. Malformed DIMACS
coverage is represented as backend `unknown`/parse-error output normalized to
`error`, preserving the existing result taxonomy.

## v0.2.3 Promotion Readiness Report - 2026-06-14

Issue 274 adds read-only promotion-readiness reporting through
`cosheaf promotion readiness --artifact <artifact-id> --json` and
`cosheaf promotion readiness --issue <issue-id> --json`. The report evaluates
target artifacts from validation, gatekeeper output, review metadata,
dependency status, public/private KB roots, source metadata, readonly-root
status, draft status, target verifier results, and repository-wide gatekeeper
blockers.

The report is advisory and records `accepted_write_performed: false`. It does
not call accepted promotion, does not move artifacts, does not change artifact
status, does not create human review, does not satisfy human-review policy,
and does not convert skipped verifier output into a pass. Accepted promotion
continues to use `cosheaf artifact promote <artifact-id>` with a fresh
validation and gatekeeper run.

## v0.2.3 Verifier Evidence Record v1 - 2026-06-14

Issue 272 adds a typed, serializable verifier evidence record v1 after the
C.1 audit. The new `VerifierEvidenceRecord` model and
`schemas/verifier_evidence.schema.json` record verifier outputs with stable
evidence IDs, verifier kind, tool metadata, command/cwd metadata, normalized
`pass`/`fail`/`error`/`skipped` result state, reason code, log paths, optional
checker hashes, and explicit limitations.

The record is serialization support for verifier output. It does not change
verifier execution, gatekeeper behavior, accepted promotion semantics,
provider/MCP authority, KB artifacts, human-review policy, or the
skipped-not-pass invariant. Promotion continues to use a fresh validation and
gatekeeper run.

## v0.2.3 Verification Evidence Plan Landing - 2026-06-14

Issue 265 lands the post-`v0.2.2` durable plan for `v0.2.3` Verification
Evidence Hardening. `docs/CODEX_DEVELOPMENT_PLAN_V5.md` is now the current
plan, ADR 0022 records the architecture decision, and
`docs/CODEX_DEVELOPMENT_PLAN_V4.md` is historical/completed after the published
`v0.2.2` release and downstream pin alignment.

The first implementation task after plan landing was the verifier evidence
status audit in `docs/VERIFIER_EVIDENCE_AUDIT.md`. That audit inspected
existing verifier adapters, result states, log capture, gate integration,
promotion evidence, skipped-not-pass tests, and Lean `#check`
symbol-resolution boundaries before C.2 schema work started.

This planning task is documentation-only. It does not change schema, verifier
behavior, gates, promotion semantics, provider/MCP authority, public/private
policy, KB artifacts, accepted knowledge, human-review status, or runtime code.

## v0.2.2 Release Closeout - 2026-06-14

Issue 263 closes out `v0.2.2` after tag/release publication and downstream pin
alignment. The annotated `v0.2.2` tag points to the reviewed post-audit main
commit, and the GitHub release `v0.2.2 Provider Transport + Agent Workflow
Hardening` is published. Release smoke installed `tcs-cosheaf==0.2.2` from
`git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.2.2` and ran the clean
workspace help, version, validate, gate, index rebuild, and context-pack
checks.

Downstream alignment is complete for the active repositories:
`tcs-cosheaf-workspace-template` pins active demo, Makefile, CLI-agent,
provider-preview, and fake-provider smoke paths to `v0.2.2`, and
`tcs-kb-public` CI installs `tcs-cosheaf` from `v0.2.2`.

This closeout is documentation/status only. It does not add runtime behavior,
does not start `v0.2.3` code, does not add provider or MCP authority, does not
write accepted knowledge, does not mark human review, does not promote
artifacts, and does not change schema, gate, verifier, public/private policy,
or accepted-promotion semantics. The next focus is `v0.2.3` Verification
Evidence Hardening through small issue/branch/PR increments.

## v0.2.2 Pre-Tag Release Audit - 2026-06-14

Issue 261 audits whether framework main is ready for `v0.2.2` tag and release
publication. The audit is documentation-only: it does not create a tag, update
downstream repositories, add provider/MCP/runtime behavior, change schema or
gate semantics, write accepted knowledge, mark human review, or promote
artifacts.

The audit verified that `pyproject.toml`, `cosheaf.__version__`, and
`python -m cosheaf.cli version --json` all report `0.2.2`; README, release
notes, roadmap, and current milestone keep `v0.2.2` framed as a conservative
release candidate; provider transport remains default-off; and CI/default
tests remain fake, mocked, or local non-live-network fixtures rather than real
provider calls.

Before issue 261 was created, the repository had no open PRs or open issues.
Local tags included `v0.2.0` and `v0.2.1`; `v0.2.2` was absent locally and on
`origin`. The default ecosystem matrix reported 4 pass, 0 fail, and 2 skipped
rows. The skipped rows were the framework git-tag release smoke and
workspace-template install demo because default matrix runs do not perform
network installs; they were not counted as passes.

The v5 runbook references `docs/FORMAL_LINKS.md`, but the current repository
document is `docs/FORMALIZATION_LINKS.md`. This naming difference is recorded
as informational audit evidence and is not a release blocker. Tag publication
may proceed after this audit PR merges, main is re-synced, and the maintainer
release action re-verifies that no unexpected `v0.2.2` tag exists.

## v0.2.2 Provider Transport And Workflow Hardening RC - 2026-06-14

Issue 259 prepares `v0.2.2` as the Provider Transport + Agent Workflow
Hardening release candidate after the readiness audit. The release-candidate
branch updates package metadata and `cosheaf.__version__` to `0.2.2` and
converts `docs/releases/v0.2.2.md` from readiness-audit evidence into
conservative release-candidate notes.

The candidate packages already-merged provider/workflow hardening work:
optional default-off OpenAI-compatible HTTP transport, explicit provider
`real-run` CLI with inline preview, consent, network, endpoint/key, and
private-context checks, provider context-send policy matrix, provider log leak
scanner, WorkerBundle failure/counterexample preservation, role-contract
hardening, malformed-output recovery, deterministic provider-workflow and
failure/counterexample evals, three-repository ecosystem smoke matrix,
workspace provider setup/preview docs, public KB source-note/backlog refresh,
one draft-only foundation tightening, and optional read-only MCP review.

This v0.2.2 release-candidate task did not implement new runtime provider
behavior, did not add MCP tools, did not add controlled-write MCP, did not run
real provider calls in CI, did not require API keys, did not write accepted
knowledge, did not mark human review, did not promote artifacts, and did not
change schema, gate, verifier, public/private policy, or accepted promotion
semantics. The public `v0.2.2` tag was expected only after the
release-candidate PR and required checks passed.

## Three-Repo Compatibility Smoke Matrix - 2026-06-14

Issue 253 extends `scripts/ecosystem_smoke.py` with a structured
three-repository compatibility matrix. The matrix rows cover framework local
checkout, framework git tag release smoke, workspace-template demo,
workspace-template CLI-agent demo, workspace-template fake-provider smoke, and
public KB policy guard.

The default no-network matrix run executes the local framework smoke, the
workspace-template CLI-agent demo, the workspace-template fake-provider smoke,
and the public KB policy guard against local checkouts. It reports the
framework tag release-smoke row and the workspace-template install-demo row as
`skipped`, not `pass`, unless the operator explicitly supplies
`--include-network`.

The structured report includes per-row repository names, commands, statuses,
return codes, and failure messages. Failure messages identify both the
repository and the failing command. The public KB row runs the policy guard,
policy guard self-test, workspace info, validation, gatekeeper, and PR
checklist gate. The workspace provider row uses `provider=fake` only and does
not perform a hosted API call.

This task does not change artifact schema, accepted-promotion semantics, gate
semantics, public/private policy, formal-link semantics, provider
default-off behavior, MCP behavior, or KB artifact content. It does not add
real provider calls or require API keys. Runtime outputs remain under ignored
`.cosheaf/` and context-pack paths in the downstream checkouts.

## Failure/Counterexample Workflow Eval - 2026-06-14

Issue 251 adds a deterministic Python-level failure/counterexample workflow
eval harness under `cosheaf.evals.failure_counterexample` plus the default case
suite in `evals/failure_counterexample/cases.yaml`. The suite covers reasoner
uncertainty, counterexampleer candidate evidence, verifier rejection of an
invalid proof attempt, reducer preservation of failure records, and the
accepted-write boundary.

The report exposes regression metrics for failure preservation, uncertainty
field presence, counterexample candidate flag accuracy, verifier request
presence, and accepted-write violation count. Metrics are computed from each
case's configured expectations, not inferred only from case kind, so custom
negative cases can verify that missed preservation is scored as a failure.

The harness writes deterministic WorkerBundle v2 fixtures under
`.cosheaf/evals/failure_counterexample/` and invokes the existing reducer
boundary. It does not add a failure/counterexample CLI command, does not call
real provider networks, does not require API keys, does not add MCP behavior,
does not write accepted knowledge, and does not change review, gate,
promotion, public/private, formal-link, or schema semantics. Candidate
counterexamples remain review-only evidence until checked and reviewed through
ordinary verifier and human-review workflows.

## Provider Workflow Eval Suite - 2026-06-14

Issue 249 adds a deterministic Python-level provider workflow eval harness
under `cosheaf.evals.provider_workflow` plus the default case suite in
`evals/provider_workflow/cases.yaml`. The suite covers fake-provider success,
mocked OpenAI-compatible success, missing provider configuration, missing
send consent, private-context denial, malformed provider output,
policy-violating verifier output, and injected rate-limit, timeout, and
cancellation transport failures.

The report exposes provider-workflow regression metrics for policy-denial
accuracy, validation-rejection accuracy, secret-leak count,
malformed-output rejection count, bundle-validity rate, and context-scope
violation count. Expected failures are successful eval outcomes only when the
structured error code matches the case expectation. The harness scans
structured output and generated `.cosheaf/providers/` logs for provider-log
leak findings.

This task does not add a provider-workflow CLI command, does not call real
provider networks, does not require API keys, does not add provider MCP tools,
does not change provider default-off behavior, does not write accepted
knowledge, and does not change review, gate, promotion, public/private,
formal-link, or schema semantics.

## Full Artifact Pull Audit - 2026-06-14

Issue 247 makes context payload shape visible across the context-pack and
provider-preview surfaces. `ContextBuildResult` now reports card count,
full-artifact count, and content mode. `RETRIEVAL_AUDIT.json` now records a
`context_payload` object with `card_count`, `full_artifact_count`, and
`content_mode`, and full-artifact pull reasons include the retrieval role,
policy scope, and explicit full-artifact budget.

Provider context-send previews now report the same card/full-artifact count
and content-mode metadata while remaining metadata-only and cards-only under
the implemented provider-send boundary. Orchestrator hosted-worker defaults
continue to use provider previews with zero full-artifact pulls.

This task does not add real provider/network tests, does not change provider
default-off behavior, does not alter MCP behavior, does not change G10 or
formal-link semantics, does not change artifact schemas or accepted-promotion
policy, and does not touch public KB or workspace-template content.

## Provider Log Leak Scanner - 2026-06-14

Issue 245 adds `cosheaf.security.provider_logs`, a deterministic scanner for
generated provider logs and run records. The scanner returns stable,
explainable findings for API-key-shaped values, bearer tokens,
environment-like dumps, secret-looking key/value pairs, hidden reasoning
markers, unapproved private context markers, and avoidable absolute
user/workspace filesystem paths.

Security tests now cover synthetic leaked fixtures, a representative redacted
provider log shape, and an actual generated redacted provider log from the
gateway. Existing redaction remains the first boundary; the scanner is a
regression guard and does not make provider calls, contact live networks,
redact logs by itself, write accepted knowledge, change promotion policy,
change schema, or alter MCP behavior.

## Context Send Policy Matrix - 2026-06-14

Issue 243 defines the provider context-send preview matrix for the current
stable service boundary. The serialized public research mode remains
`policy_mode=public` for backward compatibility with the agent-access DTOs;
the v4 plan name `public_research` refers to that public mode. Public-mode
previews include public KB scope only. Private KB context is previewable only
with `policy_mode=private_research`, `public_only=false`, and explicit
private-context consent.

Provider previews remain metadata-only: artifact IDs, root scopes, token
estimates, and risk flags. They do not include full artifact statements, full
issue text, provider credentials, secrets, or raw private content. Workspace
and framework scope cards are excluded from provider-send previews under the
current matrix unless a later explicit design changes that boundary.

Table-driven tests cover allowed and denied combinations, stable denial error
codes, fake and OpenAI provider preview metadata, public-only filtering before
private ranking can surface results, and full-text exclusion from previews.
This task does not add real provider/network tests, accepted writes, promotion
changes, MCP changes, schema changes, or KB content changes.

## Provider Malformed-Output Recovery - 2026-06-14

Issue 241 adds deterministic output-validation retry behavior for
OpenAI-compatible provider calls that request `worker_bundle` output. Malformed
JSON or schema-invalid WorkerBundle v2 payloads still become
`provider_output_validation_failed`. When the configured retry budget permits,
the gateway performs at most one output-validation retry with a stricter
WorkerBundle schema reminder in the retry prompt.

Provider logs record `attempt_count`, `output_validation_retry_count`,
`output_validation_retry_code`, `output_validation_retry_status`, and
`output_validation_retry_final_status` when this path runs. A successful retry
must validate as WorkerBundle v2 before it can become `ModelCallResult`
content. Failed retries remain `ProviderError`; malformed output is not
silently coerced into draft artifacts, accepted artifacts, verifier results,
human review, gate output, or promotion.

## Role Contract V2 Failure Fields - 2026-06-13

Issue 239 updates built-in role contracts for `reasoner`, `verifier`,
`counterexampleer`, `explorer`, `formalizer`, and `librarian_summarizer`.
Role-specific validation now requires structured output fields for uncertainty,
failures, verifier requests, dependency questions, candidate-vs-verified
counterexamples, and formal symbol resolution vs semantic alignment.

`HostedWorkerService` now includes each role contract's required output fields,
optional output fields, and forbidden authority list in the provider prompt.
The service still validates provider output locally as WorkerBundle v2 or typed
review-only sub-results, rejects unsafe authority claims, and does not write
accepted knowledge, create human review, create verifier results, run gates, or
promote artifacts.

## WorkerBundle Failure And Counterexample Preservation - 2026-06-13

Issue 237 hardens WorkerBundle v2 with backward-compatible review-only fields
for `assumptions`, `uncertainty`, `failed_attempts`, `counterexamples`, and
`dependency_questions`. Existing bundles that only use the older
`verification_requests`, `failures_or_counterexamples`, `risk_flags`, and
`next_steps` fields remain valid.

Bundle reducers and bundle submission now preserve assumptions, uncertainty,
verification requests, failed attempts, candidate counterexamples, dependency
questions, legacy failure/counterexample notes, risk flags, and confidence as
labeled review warnings. Verification requests are not verifier results, and
candidate counterexamples are not accepted refutations. WorkerBundle v2 still
does not authorize accepted writes, accepted refutation of public knowledge,
human review creation, verifier result creation, gate bypass, or promotion.

## Explicit Provider Real-Run CLI Path - 2026-06-13

Issue 235 adds `cosheaf provider real-run --input-json <path> --provider
openai-compatible --confirm-send --allow-network --json` as a deliberately
hard-to-trigger operator path for one OpenAI-compatible provider call. The
input JSON must include inline `context_preview` metadata and
`provider_config` with endpoint and API-key environment variable name. The
command fails closed without send confirmation, explicit network permission,
inline preview, valid provider configuration, an environment-provided key, or
required private-context consent.

Successful real-run calls still go through the provider gateway, the optional
stdlib HTTP transport, redaction, and run-record logging under
`.cosheaf/providers/`. The command emits structured JSON when requested and
does not write draft artifacts, accepted artifacts, human review records, gate
results, verifier results, or promotion output from raw provider responses.

Tests use mocked transport injection and do not contact live provider networks
or require real API keys. This task does not add hosted worker CLI commands,
provider MCP tools, SDK dependencies, default real provider calls, accepted
writes, promotion changes, schema changes, or public/private KB changes.

## Optional OpenAI-Compatible HTTP Transport - 2026-06-13

Issue 233 implements `OpenAICompatibleHttpTransport`, an optional stdlib HTTP
transport object for OpenAI-compatible chat-completions calls. It is not
instantiated by default and must be explicitly injected through
`OpenAICompatibleProvider` with `ProviderConfig.enabled=true`,
`mode=openai_compatible`, explicit `base_url`, `api_key_env`,
`NetworkPolicy.EXPLICIT_ALLOW`, and an environment-provided API key.

The transport maps expected failures to `ProviderTransportResult` values
instead of uncaught tracebacks: missing configuration, missing key, missing
network permission, timeout, rate limit, HTTP error, network error, invalid
JSON, and malformed provider output. Gateway integration still redacts secret
values from result content and provider logs under `.cosheaf/providers/`.

Tests use injected local fixtures and do not call live provider networks or
require real API keys. This task does not add a provider `real-run` CLI, hosted
worker CLI commands, provider MCP tools, SDK dependencies, accepted writes,
promotion changes, schema changes, or public/private KB changes.

## Real Provider Transport Boundary ADR - 2026-06-13

Issue 231 adds ADR 0021 for the first real provider transport boundary before
runtime implementation. The chosen first transport is OpenAI-compatible HTTP,
but it must be optional, default-off, explicitly configured, blocked without
context preview, operator send consent, explicit network permission, and
environment or secret-manager key source.

The ADR and docs require private context to fail closed unless
`policy_mode=private_research`, `public_only=false`, and explicit
private-context consent are all present. They also require unsupported
parameters, timeout, cancellation, rate limit, HTTP error, invalid JSON,
malformed model output, schema rejection, redaction failure, and log-write
failure to become structured provider errors or rejected output, not passes.

This is documentation-only design work. It does not add a real HTTP transport,
real-run CLI, dependencies, provider MCP tools, schema changes, accepted writes,
promotion changes, or public/private KB changes.

## v4 Provider/Workflow Hardening Plan Landing - 2026-06-13

Issue 229 lands `docs/CODEX_DEVELOPMENT_PLAN_V4.md` as the current
post-`v0.2.1` durable plan and adds ADR 0020 for the `v0.2.2 Provider
Transport + Agent Workflow Hardening` direction. The plan uses
`docs/POST_V021_STATE_AUDIT.md` as its baseline.

The next concrete work is a real-provider transport ADR and threat model
before runtime implementation. CLI remains the first agent interface, real
provider transport remains explicit/default-off, CI/default tests must stay
fake or mocked, and MCP remains optional. At this v0.2.2 planning point,
controlled-write MCP was not planned unless a separate maintainer-approved
issue reopened that scope; ADR 0026 later reopened only a narrow
draft/review/runtime MCP write scope for the v0.5.0 line. Provider, worker,
MCP, and agent outputs still may not write accepted knowledge, mark human
review, or bypass validation, gates, reducers, verifier results, review, or
promotion.

This is documentation-only plan/state alignment. It does not implement real
provider HTTP transport, provider real-run CLI, provider MCP tools,
controlled-write MCP, schema changes, promotion policy changes, or KB artifact
changes.

## v0.2.1 CLI Agent Access Prerelease Closeout - 2026-06-13

Issue 221 prepared `v0.2.1` as the CLI Agent Access + Hosted Provider Gateway
release candidate. PR #222 merged it to `main`, the package metadata and
`cosheaf.__version__` now record `0.2.1`, the `v0.2.1` tag is published as a
GitHub prerelease, and `docs/releases/v0.2.1.md` documents conservative
release boundaries.

The candidate packages the already-merged CLI-first agent-access surface,
controlled draft/staging write CLI, provider gateway, fake and mocked
OpenAI-compatible provider paths, role-specific hosted worker service,
explicit orchestrator hosted-worker dispatch, optional operator Skill, security
regression suite, and Python-level agent workflow evaluation suite. It does not
add accepted writes, does not create human review, does not enable default real
hosted HTTP transport, does not run real provider calls in CI, and does not let
provider, MCP, Skill, retrieval, context, SAT, SMT, Lean, validation, or gate
output bypass reducer, review, verifier, promotion, or accepted-knowledge
policy.

`v0.2.0` remains the local-MVP baseline. The workspace template now pins
CLI-agent/provider demo workflows to `@v0.2.1`, and `tcs-kb-public` CI now
installs `tcs-cosheaf` from `@v0.2.1` for validation, gate, PR-checklist, and
repository-local policy guard checks. MCP remains optional and is not required
for `v0.2.1`.

## Agent Workflow Evaluation Suite - 2026-06-10

Issue 219 adds a deterministic Python-level agent workflow eval harness under
`cosheaf.evals.agent_workflow` plus the default case suite in
`evals/agent_workflow/cases.yaml`. The suite exercises existing CLI-agent and
provider-worker paths through `CliRunner` and records metrics for command exit
expectations, JSON parsing, required artifact hits, private leakage, expected
accepted-write rejection, expected malformed-bundle rejection, fake-provider
redaction, and surface counts.

The default suite distinguishes `cli`, `provider`, and `optional_mcp` surfaces.
At this eval task point, the optional MCP case only listed the then-existing
read-only MCP tool whitelist; this did not make MCP mandatory and did not add
MCP write behavior. Later v0.5.0 work added narrow controlled
draft/review/runtime MCP tools. The harness does not add a
`cosheaf eval agent-workflow` CLI command,
does not run real hosted provider calls, does not require API keys, does not
use network access, does not write accepted knowledge, and does not bypass
validation, gates, verifier results, human review, reducers, or promotion.

Running the suite may refresh runtime context-pack files under
`context/TASKS/` and redacted fake-provider logs under `.cosheaf/providers/`.
Those are generated runtime outputs and should not be committed.

## Internal Orchestrator Hosted-Worker Dispatch - 2026-06-10

Issue 215 adds explicit internal orchestrator dispatch to role-specific hosted
workers. `cosheaf orchestrator run --issue <issue-id> --provider fake --json`
now runs the deterministic fake-provider hosted-worker path end to end:
planning, provider-send context preview, role-specific hosted worker calls,
WorkerBundle v2 validation, typed sub-result persistence, reducer execution
for validated bundles, run-record persistence, and run-local provider-record
copies under `.cosheaf/orchestrator/<issue-id>/runs/<run-id>/providers/`.

`cosheaf orchestrator run --issue <issue-id> --provider openai-compatible
--confirm-send --json` enters the OpenAI-compatible hosted-worker boundary only
after explicit consent. The default CLI path does not instantiate the optional
stdlib HTTP transport and reports missing transport unless a provider
transport is configured or injected. CI and unit tests use the fake provider,
mocked transport, or local transport fixtures only.

The hosted-worker orchestrator path does not write accepted knowledge, does
not write proposed artifacts into KB paths, does not create human review
records, does not promote artifacts, does not run real hosted network calls in
CI, and does not let provider output bypass reducers, validation, gates,
verifier results, review, or promotion policy. Private context remains
public-only by default and requires private-research policy plus explicit
private-context consent.

## Role-Specific Hosted API Workers - 2026-06-10

Issue 213 connects the provider gateway to role-specific hosted worker
contracts through `HostedWorkerService`. The required hosted worker roles are
`reasoner`, `verifier`, `counterexampleer`, `explorer`, `formalizer`, and
`librarian_summarizer`.

The service uses the existing provider gateway and model-call service. It
supports deterministic fake-provider runs and OpenAI-compatible mocked
transport runs through injected transport only. Worker output is validated as
WorkerBundle v2 for `reasoner`, `verifier`, `counterexampleer`, and
`formalizer`; `explorer` and `librarian_summarizer` return typed review-only
sub-results. Invalid provider output returns
`provider_output_validation_failed`, invalid request policy returns
`provider_request_validation_failed`, and unsafe authority claims return
`hosted_worker_policy_violation`.

This is a service-layer bridge, not production hosted multi-agent execution.
It does not add a hosted worker CLI command, does not add built-in real HTTP
transport, does not run real hosted network calls in CI, does not write
proposed artifacts, does not write accepted knowledge, does not create human
review records, does not promote artifacts, and does not bypass validation,
gates, verifier results, reducers, review, or promotion.

## Provider CLI Commands - 2026-06-10

Issue 211 exposes the provider gateway through conservative CLI commands for
agent-facing inspection, preview, and deterministic fake runs:
`cosheaf provider list --json`, `cosheaf provider config-check --json`,
`cosheaf provider preview-send --issue <issue-id> --provider <provider>
--json`, and `cosheaf provider fake-run --input-json <path> --json`.

These commands do not add a real-run command, do not import hosted provider
SDKs, do not perform real hosted network calls, do not write accepted
knowledge, and do not bypass review, gate, verifier, reducer, or promotion
policy. `config-check` reports secret presence only and redacts secret values.
`preview-send` shows root scopes and estimated payload shape without sending
artifact text. `fake-run` forces the deterministic fake provider and writes
redacted provider logs under `.cosheaf/providers/`.

The current provider CLI supports only `fake` and `openai` mode names.
Future provider identifiers such as `anthropic`, `google`, and `local` remain
model enums only until later tasks implement and test their behavior; the CLI
returns `provider_unsupported` for those names.

## CLI-First Direction Alignment - 2026-06-09

Issue 201 adds the first controlled CLI write surface for external coding
agents. `cosheaf draft write-artifact --input-json <path> --json`,
`cosheaf draft write-source-note --input-json <path> --json`,
`cosheaf bundle submit --input-json <path> --json`, and
`cosheaf review request --input-json <path> --json` now route through the
service layer, support dry-run previews, report exact target/written paths,
and use structured `ErrorResult` payloads for expected failures. These
commands are deliberately narrow: they reject accepted writes, readonly KB
roots, accepted artifact status, and `human_reviewed` review spoofing. They do
not promote artifacts, do not create human review, do not complete tasks, do
not call hosted providers, and at that issue-201 point did not implement MCP
writes. Later v0.5.0 work added only narrow controlled draft/review/runtime MCP
tools under the same no-accepted-write boundary.

Issue 199 stabilized deterministic JSON output for the core read-only
agent-facing CLI commands: version, workspace info, validation, gate runs,
memory cards/search, context build/show, and orchestrator planning. JSON mode
keeps Rich markup out of stdout and preserves structured error responses for
expected failures.

Issue 193 aligns the durable post-`v0.2.0` direction with
`longplan_v3_fixed_cli_first.md`. The current roadmap now treats CLI as the
first agent interface, the service layer as the shared implementation boundary,
hosted provider support as planned but default-off and fake/mocked in tests,
MCP as optional adapter work rather than a `v0.2.1` blocker, and Skill as an
operator runbook rather than a source of truth.

This is documentation-only direction cleanup after the rollback audit in
`docs/POST_V020_ROLLBACK_AUDIT.md`. It does not change code, schemas, tests,
gates, verifier adapters, accepted-promotion policy, public KB artifacts,
workspace-template behavior, runtime dependencies, or release tags. Existing
read-only MCP code remains factual optional adapter surface; it is not the
primary agent path.

## v0.2.0 Local-MVP Release - 2026-06-08

Issue 153 prepared `v0.2.0` as a pin-able local-MVP framework release. The
package version is `0.2.0`, `cosheaf.__version__` reports `0.2.0`, the
annotated `v0.2.0` tag points to the reviewed default-branch merge commit, and
the GitHub release is published as a prerelease to avoid production-readiness
overclaiming. `docs/releases/v0.2.0.md` records release boundaries for the
already-merged deterministic librarian, context-pack v2, local orchestrator
dry-run, fake provider, retrieval/context evals, optional OpenTelemetry
scaffold, optional MarkItDown staging, and optional Lean external-library
`#check` path.

This release did not add new capability beyond packaging the already-merged
local-MVP surfaces. It does not enable hosted LLM execution, automatic theorem
proving, automatic accepted promotion, web UI, multi-user permissions, or
automatic informal/formal semantic alignment. Hosted provider work is planned
after `v0.2.0`, but remains default-off, explicit, and fake/mocked in tests.

## v0.2.0 Closeout Hygiene - 2026-06-08

Issue 151 aligned repository-facing status language after the fixed longplan
completion audit. The durable state now distinguishes three separate concepts:
the existing `v0.1.1` release tag, the current default branch, and the
published `v0.2.0` local-MVP tag. The `v0.2.0` release does not imply
production readiness.

This is documentation-only cleanup. It does not change code, schemas, gates,
verifier adapters, accepted-promotion policy, public KB artifacts,
workspace-template behavior, or runtime dependencies. The longplan completion
audit remains conservative: it is documentation and code-surface evidence, not
a production-ready claim.

## Longplan Completion Audit - 2026-06-08

Issue 145 adds `docs/LONGPLAN_COMPLETION_AUDIT.md`, a requirement-by-requirement
audit of `longplan_fixed.md` against merged PR evidence across `tcs-cosheaf`,
`tcs-kb-public`, and `tcs-cosheaf-workspace-template`. The audit records that
all fixed-plan tasks through Phase 8 have merged evidence except Phase 5 Task
5.3. That was a historical audit of the older `longplan_fixed.md` baseline; the
current `longplan_v3_fixed_cli_first.md` direction supersedes it for future
task ordering and schedules hosted provider work as explicit, default-off,
fake/mocked-in-tests capability rather than a blocked local-only track.

This is an audit/documentation update only. It does not add hosted provider
SDKs, does not enable hosted LLM execution, does not change code, schemas,
gates, verifier adapters, accepted-promotion policy, public KB artifacts, or
workspace-template behavior. The current provider boundary remains
`FakeModelProvider` plus provider-neutral contracts; hosted provider work must
stay explicit, default-off, and fake/mocked in tests.

## Phase 8 Release-Hardening Docs - 2026-06-08

Issue 133 updates the durable release-hardening documentation after the current
Phase 8 baseline. `RELEASE_CHECKLIST.md` is now an actionable
three-repository checklist for the framework package, public KB, and workspace
template rather than a stale checklist for creating the already-existing
`v0.1.1` tag. `context/CURRENT_MILESTONE.md` now points to Phase 8 Task 8.1
instead of the completed Phase 6 formal-link pilot. `docs/ROADMAP.md` now
describes release hardening and showcase preparation after the `v0.1.1`
baseline.

This update is documentation-only. It does not change code, CLI behavior,
schemas, gate semantics, verifier adapters, accepted-promotion policy, public
KB artifacts, or workspace-template behavior. The `v0.1.1` tag remains the
downstream metadata baseline; later `main` hardening includes the optional
external Lean library reference adapter. The current formal-link boundary
remains: the adapter can check `import`/`#check` symbol resolution when Lean or
lake is available, missing Lean/lake is `skipped`, and a successful `#check`
does not prove informal/formal semantic alignment.

## Phase 0 State Audit - 2026-06-06

`docs/CODEX_STATE_AUDIT.md` records the current three-repository state before
later longplan phases proceed. The audit confirms that the framework package is
`0.1.1`, the workspace template has demo, Makefile, bootstrap, and CI smoke
coverage, and the public KB currently has 19 accepted public artifacts. All
accepted public KB formalization references are still `planned` metadata with
`check_mode: external_library_ref`; the framework now has an optional
external-library `#check` adapter, but planned links remain metadata unless a
checker actually runs.

The audit also confirms that `context/CURRENT_MILESTONE.md` was stale relative
to the current `v0.1.1` and three-repo MVP productization state and has been
updated as part of the same documentation-only task.

## Historical Snapshot: v0.1.1 Formal Link Layer Support

TCS-Cosheaf is in v0.1.1 Formal Link Layer support / pre-MVP scaffold state. The repository contains project governance documentation, a short README, a Python-oriented `.gitignore`, the durable documentation skeleton, the minimal Python project scaffold, the initial repository directory layout, initial JSON Schema files, example YAML artifacts, initial Pydantic v2 core artifact models including structured source metadata and formalization-link metadata, filesystem-backed storage loading utilities, optional workspace configuration, workspace-aware validation gates including accepted public source metadata enforcement, artifact lifecycle CLI commands including controlled accepted-artifact promotion, an artifact dependency graph, deterministic repository index rebuilds including formal-link metadata, a read-only SQLite query API over rebuilt index output including formalization queries, gatekeeper report generation including G10 Formal Link Gate output, ranked issue-scoped context pack generation with compact formal-link display, local agent task records, a worker output bundle contract, an orchestrator stub, a local worker command runner, the initial verifier adapter interface, a Python checker verifier adapter, minimal optional SAT DIMACS, SMT-LIB, plain Lean, and external Lean library reference verifier adapters, graph/SAT/formal-link pilot workflows, GitHub Actions CI, and GitHub collaboration templates.

Issue 61 prepares the `v0.1.1` release after Formal Link Layer metadata, G10
static metadata validation, context-pack display, deterministic
SQLite/manifest indexing, and read-only query API support have landed. The
Python package version is `0.1.1`. That release boundary was metadata-only:
Cosheaf did not replace CSLib or mathlib, did not copy Lean proof bodies, did
not run external Lean library checks, did not add Lean, lake, mathlib, or CSLib
dependencies, did not fetch external libraries, and did not change
accepted-promotion semantics beyond ordinary gatekeeper blocking behavior.
Downstream repositories should pin to `v0.1.1` before using formalization
fields.

Issue 46 clears the release-accounting contradictions before tagging the
framework as `v0.1.0`. The Python package version is already `0.1.0`; the
release tag must wait until the release-cleanup PR passes CI and human review.
`LICENSE`, README license text, and `pyproject.toml` project metadata now use
Apache-2.0 consistently. `RELEASE_CHECKLIST.md` records CI, license, docs,
demo, tag, and known-limitation checks for the framework release.

Issue 49 starts P1 testing hardening with a deterministic release smoke helper.
`scripts/release_smoke.py` creates a clean virtual environment, installs a
chosen framework source such as the `v0.1.0` tag, writes a tiny local fixture,
and runs `cosheaf --help`, `cosheaf version`, `cosheaf validate`, `cosheaf gate
run`, `cosheaf index rebuild`, and `cosheaf context build
issue.release-smoke`. Fast unit tests verify the smoke plan and fixture without
requiring network access.

Issue 65 adds a local ecosystem smoke helper for the intended three-repository
model. `scripts/ecosystem_smoke.py` writes temporary workspace-like fixtures
with a readonly public KB root, writable private KB root, accepted public
artifact, private draft artifact depending on public accepted knowledge, and a
private issue for context-pack generation. The smoke plan runs `cosheaf
workspace info`, `cosheaf validate`, `cosheaf gate run`, `cosheaf index
rebuild`, and `cosheaf context build
issue.ecosystem-smoke.private-context`. It also verifies expected policy
failures: lifecycle writes to the readonly public root are refused, public
artifacts depending on private artifacts are rejected, and accepted artifacts
depending on draft artifacts are rejected. This smoke uses only local fixtures,
does not clone remote repositories, does not promote artifacts, and does not
add Lean, CSLib, mathlib, SAT, SMT, or theorem-proving claims.

Issue 51 adds cross-repository integration fixture coverage for the intended
three-repository model. The tests build local public/private KB roots without
cloning external repositories and cover private-to-public dependencies, public
to private dependency rejection, accepted-to-draft dependency rejection,
readonly public-root write refusal, and deterministic validation/gate behavior
across workspace roots.

Issue 53 extends P1 regression coverage around accepted-knowledge safety gates.
The added tests cover target verifier `error` results blocking promotion,
external evidence references bypassing local path checks while missing local
evidence fails cleanly, machine-readable gate report shape for reviewed draft
fixtures, and unavailable optional verifier tooling staying `skipped` rather
than being reported as `pass`.

Branch protection and review expectations are now documented in
`docs/REVIEW_POLICY.md`. The documented policy requires protected `main`,
disallows direct pushes to `main`, and routes all changes through issue,
branch, pull request, CI/gate checks, review, and merge.

Issue 20 updates the durable agent operating protocol for the planned
three-repository architecture. `AGENTS.md` and `docs/CODEX_WORKFLOW.md` now
record that `tcs-cosheaf` is the framework repository, `tcs-kb-public` is the
public reusable TCS knowledge base, and `tcs-cosheaf-workspace-template` is the
user-facing workspace template. The documented user model is framework package
plus readonly public KB plus writable private KB overlay; users should not
manually merge framework and KB repositories.

Issue 30 extends the framework user-facing documentation for that
three-repository model. `README.md`, `docs/WORKSPACE.md`, and
`docs/PUBLIC_PRIVATE_KB.md` now name `tcs-cosheaf-workspace-template` as the
recommended user entry point, link the public KB repository, explain that
downstream workspaces should mount public knowledge readonly with private
knowledge writable, and restate that private artifacts may depend on public
artifacts while public artifacts must not depend on private artifacts. This is
documentation-only framework work and does not change code, schemas, or gates.

Issue 33 adds a framework-level integration smoke test for the workspace
template model. The test builds a representative local workspace-template
layout in a temporary directory without cloning remote repositories or requiring
network access. It verifies `cosheaf.toml` public/private KB policy, readonly
public and writable private root metadata, private-to-public dependencies,
`cosheaf workspace info`, `cosheaf validate`, `cosheaf gate run`, explicit
`cosheaf gate run --pr-checklist .github/pull_request_template.md`, and the
negative rule that public artifacts must not depend on private artifacts. This
is test coverage for existing workspace behavior and does not add public
interfaces, schema fields, accepted artifacts, or SAT/SMT/Lean execution.

The durable workflow rules now require nontrivial Codex work to be issue-driven
where possible, with one issue, one focused branch, one PR, and one reviewable
increment. Branches should use short human-readable names and should not add
`codex/`, `codex-`, or other agent-specific prefixes to issue titles, branch
names, or PR titles unless the maintainer explicitly asks for that prefix. The
rules also record repository creation checks through `gh --version` and
`gh auth status`, local issue-draft fallback behavior when remote issue
creation is unavailable, and the rule that repository, branch, issue, PR,
remote push, and check success must never be faked.

`AGENTS.md` now also records the accepted-artifact promotion protocol: accepted
knowledge must enter lifecycle KB roots through
`cosheaf artifact promote <artifact-id>`, with repository validation,
gatekeeper, target verifier, review-state, dependency, readonly-root, and
deterministic-write checks preserved as durable Codex operating rules.

The documented workspace layering policy expects future `cosheaf.toml`
workspaces to support multiple KB roots with public readonly KB and private
writable overlay semantics. Private artifacts may depend on public artifacts,
public artifacts must not depend on private artifacts, accepted artifacts must
not depend on draft artifacts across KB roots, and readonly KB roots must not be
modified by write commands.

The Python scaffold defines a `cosheaf` package, a Typer-based `cosheaf` CLI entry point, development dependencies, Makefile targets, a Dockerfile for reproducible local development, and smoke tests for import and CLI help/version behavior.

The filesystem layout now includes accepted and draft knowledge-base directories, refuted and obsolete artifact areas, issue directories, experiment directories, and review directories. The initial schemas live under `schemas/`, and examples live under `examples/`.

The core model layer now defines artifact type and status enums, base artifact data models, artifact ID and dependency-reference validation, timestamp validation, risk/evidence/source/review value objects, pure status/path helper functions, artifact type directory mapping, and deterministic lifecycle artifact path derivation. Artifact `depends_on` values may reference local artifact IDs or explicit external references beginning with `external:`. Artifact `sources` entries record structured citation metadata with kind, title, authors, year, DOI, arXiv, URL, theorem number, page, and notes fields.

The Formal Link Layer now adds optional artifact fields for external formal
library references. `formalizations` records Lean 4 declaration references with
library, library reference, import path, symbol, declaration kind, status,
check mode, expected type, and notes. `alignment` records separate semantic
alignment review between the informal artifact statement and the formal
declaration. `verification_policy` records whether a formal link, Lean check,
or alignment review is expected. These fields are metadata only in this MVP:
they do not copy Lean proofs, do not add CSLib or mathlib dependencies, do not
require network access, and do not change accepted promotion semantics beyond
ordinary gatekeeper blocking behavior. Issue #57 added G10 Formal Link Gate as
static metadata validation over `verification_policy`, `formalizations`, and
`alignment` without running Lean. Issue #59 surfaced the same formal-link
metadata in context packs and deterministic SQLite/query outputs without
changing G10 behavior. External Lean `#check` support for CSLib/mathlib
declaration references is now available through an optional verifier adapter,
but only for linked or checked formalization metadata and only when Lean or lake
is available.

The configuration layer defines optional `cosheaf.toml` workspace loading. A
workspace has a name, public/private policy fields, and one or more KB roots,
each with `name`, path, `readonly`, and `priority`. If no `cosheaf.toml` exists,
TCS-Cosheaf preserves the previous single-repository behavior with one writable
default KB root at `kb/`.

The storage layer defines `RepoContext`, workspace-aware YAML discovery under
configured KB roots plus repository-local `issues/` and `examples/`, typed YAML
loading into `BaseArtifact`, `IssueRecord`, or `ReviewRecord`,
repository-relative source paths on loaded records, source KB root metadata,
deterministic ordering by path then ID, clear load errors, and deterministic
YAML writing helpers.

The validation CLI implements repository validation for YAML parse/model parse, ID uniqueness across all active roots, status/path consistency relative to each KB root, dependency existence, accepted-artifact-to-draft-artifact dependencies across roots, public-artifact-to-private-artifact dependency violations, external dependency references, and local evidence path existence. Expected validation failures produce concise Rich output and nonzero exit codes without stack traces unless `--debug` is used.

The artifact lifecycle CLI now implements `cosheaf artifact create`, `cosheaf artifact move-status`, and `cosheaf artifact promote`. Artifact creation writes deterministic BaseArtifact YAML records under canonical lifecycle paths, refuses duplicate IDs, refuses direct accepted creation, and validates the new file before reporting success. In configured workspaces, creation writes to the writable private root by default. Status movement loads artifacts by unique ID, requires the current file path to match the current status, refuses readonly KB roots, validates the repository before moving, updates YAML deterministically, moves terminal failure statuses to the active KB root's refuted or obsolete area, and refuses direct accepted promotion. Accepted promotion is handled only by `cosheaf artifact promote <artifact-id>`; it validates the repository, runs gatekeeper, refuses blocking gatekeeper issues and target verifier `fail`/`error` results, requires `review.state` to be `human_reviewed` or `accepted`, requires dependencies to be accepted local artifacts or explicit external references, refuses readonly KB roots, requires complete structured source metadata for public KB artifacts when `accepted_requires_source = true`, updates status to `accepted`, refreshes `updated_at`, and writes deterministic YAML under the accepted area of the artifact's KB root.

The workspace CLI now implements `cosheaf workspace info`, which reports the
active workspace name, whether the repository is in configured or legacy mode,
and the configured KB roots with paths, readonly flags, and priorities.

The graph layer builds directed dependency edges from artifact to dependency, detects missing dependencies, detects directed cycles, and reports accepted artifacts depending on draft or otherwise pre-accepted artifacts.

The index rebuild command writes `.cosheaf/index.sqlite` and `.cosheaf/artifact_manifest.json` from scratch. The SQLite index stores artifact ID, type, status, path, title, domain, source KB root, deterministic dependency rows, formalization rows, and artifact formal-policy rows. The manifest ordering is deterministic and stable across delete-and-rebuild cycles and now includes compact formalization, alignment-status, and verification-policy metadata per artifact. The SQLite query API reads that rebuilt index without modifying YAML or rebuilding implicitly, and provides deterministic artifact, status, type, domain, dependency, reverse-dependency, source-KB-root, formalization, and formal-policy queries.

The gatekeeper command runs G1-G5 implemented gates, the G6 verifier gate, the
G7 reproducibility metadata gate, the G8 PR checklist gate, the G9 source
metadata gate, and the G10 formal link gate. It writes JSON and Markdown
reports to `.cosheaf/reports/` by default, can persist copies under
`reviews/gatekeeper/` with `--persist-review`, and exits nonzero when blocking
issues exist. G7 reports `pass`, `fail`, or `not_applicable` depending on
executable evidence metadata. G8 is a local filesystem-only gate: it reports
`skipped` when no PR checklist source is provided, and
`cosheaf gate run --pr-checklist <path>` checks a local markdown PR body for
the required checklist sections without GitHub API or network access. G9
enforces complete structured source metadata for accepted artifacts in
configured public KB roots when `accepted_requires_source = true`; it is not
applicable for draft public artifacts, accepted private artifacts, or legacy
single-root repositories.

G10 checks consistency between `verification_policy`, `formalizations`,
`alignment`, local formal library manifests, and G6 Lean verifier results. It
blocks artifacts whose policy requires a formal link, Lean check, or alignment
review when the corresponding metadata is missing, not human-reviewed, or not
backed by a matching verifier `pass`. It also blocks unknown formal
`library_ref` manifest references, missing local formal manifests for artifacts
with formalization links, rejected alignment on accepted artifacts, and
required formal-link policies whose only formalizations are `broken` or
`deprecated`. Warning-only states, such as planned links on accepted artifacts
or checked external-library references without verifier evidence linkage,
remain nonblocking and are not proof failures. G10 does not run external
library checks for CSLib or mathlib references, does not execute Lean, and does
not treat a Lean pass as proof of informal/formal statement alignment. Missing
optional Lean tooling remains a skipped verifier result, not a pass. External
`#check` output for linked formalization metadata is produced by the G6
`lean_library_ref` verifier adapter; G10 only consumes the normalized result
when policy requires it.

Issue 85 integrates context-pack v2 with the local librarian retrieval surface.
The agent harness layer now builds bounded deterministic context packs for
issue IDs from compact `ArtifactCard` rows by default. Context packs are
written under `context/TASKS/<issue-id>/` and include `CONTEXT.md`,
`ACCEPTANCE.md`, `RELEVANT_ARTIFACTS.md`, `KNOWN_FAILURES.md`,
`FULL_ARTIFACTS.md`, `RETRIEVAL_AUDIT.json`, and `COMMANDS.md`. The default
orchestrator role has `max_full_artifacts = 0`, so full artifact YAML is not
included unless the caller explicitly sets a positive full-artifact budget.
Retrieved cards are filtered through the existing issue-local relevance rules:
direct issue references, one-hop dependency neighbors, domain matches against
issue text/tags, and artifact tag matches against issue tags. Public-only
context excludes private cards and private artifact IDs from the rendered
context and retrieval audit. Retrieval scores remain metadata only; they do not
authorize review, promotion, proof, or public/private policy bypasses. When
relevant artifacts carry formal-link metadata or policy-relevant formal
settings, context packs show compact formalization, alignment,
verification-policy, and G10-relevant hint lines without loading gate reports
or claiming Lean verification.

The agent task harness now defines protocol worker types for `reasoner`, `verifier`, `counterexampleer`, `construction_searcher`, `formalizer`, `literature_scout`, and `orchestrator`. Task records use deterministic default IDs of the form `task.<issue-id>.<worker-type-slug>`, support lifecycle statuses `open`, `in_progress`, `blocked`, `completed`, `failed`, and `cancelled`, and are written under `.cosheaf/tasks/`. The `cosheaf task create`, `cosheaf task list`, and `cosheaf task complete` CLI commands are local filesystem stubs only: they do not call LLMs, do not make network calls, and do not execute model-provider worker runtimes.

The local worker runner executes explicit repository-local command argv lists for existing task records. `cosheaf task run <task-id> -- <command> [args...]` uses `shell=False`, defaults to the repository root, rejects `--cwd` outside the repository, enforces a timeout, captures stdout/stderr, records return code, and writes run records under `.cosheaf/tasks/<task-id>/runs/<run-id>/` with stdout and stderr stored as separate files. `--bundle <path>` validates an optional worker output bundle without completing the task. `--complete-with-bundle <path>` delegates task completion to the existing orchestrator stub after a successful run and valid bundle. The local runner is not an LLM runtime, does not call hosted APIs or network services, does not merge worker outputs, does not promote artifacts, and does not implement SAT, SMT, or Lean execution.

The local orchestrator dry-run workflow now runs the deterministic planner through local fake workers for reasoner, verifier, and orchestrator nodes. `cosheaf orchestrator run --issue <issue-id> --dry-run --local-only` writes role-aware worker bundle v2 manifests under `.cosheaf/orchestrator/<issue-id>/runs/<run-id>/`, validates and reduces them, and records stdout/stderr paths in the run record. The generated bundles may reference proposal paths under `.cosheaf/orchestrator/.../proposals/`, but the dry-run does not write proposal artifacts, does not create human review or gate records, does not write accepted knowledge, and does not promote artifacts. The verifier dry-run is not a verifier pass and does not run Lean, SAT, SMT, or gate checks.

CodeGraph is now documented as optional developer-only, local-only tooling in `docs/DEV_TOOLING.md`, with a safe availability probe at `scripts/dev/codegraph_probe.py`. The probe reports `fallback: run_full_verification` when CodeGraph is unavailable, and generated CodeGraph outputs are gitignored under `.codegraph/`, `.cosheaf/dev/codegraph/`, and `codegraph*.db`. CodeGraph output remains sidecar/cache only and must not feed artifact truth, retrieval ranking, context generation, gates, verifier results, review records, or promotion.

Worker output bundles are local YAML manifests. `cosheaf task complete` validates the bundle shape, checks that it matches the task, verifies referenced output paths are repository-local, and runs artifact/review YAML outputs through the existing schema gate. Outputs under `kb/accepted/` are rejected, and completion does not merge anything into accepted knowledge.

The verification layer now defines the `VerifierAdapter` protocol, normalized `VerificationResult` model, `VerificationStatus` enum, instance-local `VerifierRegistry`, and `PythonCheckerAdapter`. Verification results distinguish `pass`, `fail`, `error`, and `skipped`; command-backed results record command and working directory metadata.

The Python checker adapter runs `kind: python_checker` evidence from the repository root, enforces a timeout, writes stdout/stderr logs under `.cosheaf/logs/`, and records command metadata, input/output paths, timeout, tool metadata, and environment notes in `VerificationResult`. The gatekeeper G6 verifier gate now runs the default verifier registry and reports Python checker results. G6 is skipped only when no verifier adapters are applicable.

The SAT adapter now supports a minimal optional DIMACS CNF invocation path. It checks repository-local SAT evidence paths, skips clearly when no supported backend is available, and when a backend is available records command, cwd, timeout, input path, stdout/stderr logs, output paths, backend metadata, exit code, and a normalized `sat`/`unsat`/`unknown` result. The default backend is an optional external command backend for `kissat`; tests can inject a fake backend and CI does not require a SAT solver. SAT skipped results are not pass results.

The SMT adapter now supports a minimal optional SMT-LIB invocation path. It checks repository-local SMT evidence paths, skips clearly when no supported backend is available, and when a backend is available records command, cwd, timeout, input path, stdout/stderr logs, output paths, backend metadata, exit code, and a normalized `sat`/`unsat`/`unknown` result. The default backend is an optional external command backend for `z3`; tests can inject a fake backend and CI does not require an SMT solver. SMT skipped results are not pass results.

The Lean adapter now supports a minimal optional plain Lean file invocation
path. It checks repository-local Lean evidence paths, reports missing files as
`error`, skips clearly when no supported Lean backend is available, and when a
backend is available records command, cwd, timeout, input path, stdout/stderr
logs, output paths, backend metadata, and exit code. The default backend is an
optional external command backend for `lean`; tests can inject a fake backend
and CI does not require Lean, mathlib, or lake. Lean skipped results are not
pass results. The adapter does not autoformalize natural language and does not
implement SAT or SMT behavior. SAT and SMT support are still intentionally
minimal: they execute DIMACS CNF or SMT-LIB evidence only when optional
backends are available and are not a full SAT/SMT theorem-proving integration.

The external Lean library reference adapter now supports optional
formalization-metadata checks. `LeanLibraryRefAdapter` recognizes Lean 4
formalizations with `check_mode: external_library_ref` and `status: linked` or
`checked`, generates a temporary Lean file containing `import <import_path>` and
`#check <symbol>`, and runs either `lean <tempfile>` or configured
`lake env lean <tempfile>`. Missing Lean/lake returns `skipped`, nonzero Lean
exit returns `fail`, and timeout/startup failures return `error`. The adapter
writes stdout/stderr logs under `.cosheaf/logs/`, records command metadata, and
does not fetch CSLib/mathlib, update formalization status automatically, or
prove informal/formal semantic alignment.

The reproducibility metadata gate is now implemented. It checks executable
evidence verifier results for command, working directory, timeout, input paths,
stdout/stderr and output paths, tool metadata, and exit code for pass/fail
results. Randomized evidence requires seed metadata. Non-executable evidence is
reported as not applicable.

The source metadata gate is now implemented for accepted public artifacts in
configured workspaces. Accepted public artifacts must have at least one
`sources` entry; each source must include kind, non-empty title, at least one
author, year, and at least one locator from DOI, arXiv, URL, theorem number, or
page. External dependency references are not accepted as source metadata.
Draft public artifacts and accepted private artifacts may omit formal source
metadata under the current policy, and legacy single-root mode remains
unchanged.

The first graph-theory pilot workflow now exists for
`issue.graph-toy-search.0001`. It adds a finite-combinatorics issue, a
`locally_tested` draft construction artifact for a toy five-cycle graph, a
matching example artifact, and executable Python-checker evidence. The checker
verifies vertex count, edge count, sorted degree sequence, connectedness, and
triangle-freeness. The artifact is not accepted and does not claim a new
theorem or novelty.

The second SAT/CNF pilot workflow now exists for
`issue.sat-smt-gadget.0001`. It adds a satisfiability issue, a `locally_tested`
draft construction artifact for a tiny 3-variable CNF formula, a DIMACS CNF
example, a known satisfying assignment JSON file, optional `sat` evidence, and
executable Python-checker fallback evidence. The SAT adapter reports `skipped`
when no solver backend is available and can execute the tiny DIMACS CNF when a
backend is available; the Python fallback checker verifies the CNF and
assignment locally. The artifact is not accepted and does not claim a new
theorem, novelty, or full SAT/SMT solver integration.

GitHub Actions CI is configured to run on pull requests and pushes to `main`
with Python 3.11. It installs the package with development dependencies and
runs `make lint`, `make typecheck`, `make test`, `make validate`, and
`make gate` as separate status checks. The CI workflow does not install
optional external formal tools.

The formal-link example
`examples/claims/claim.formal-link.example.yaml` demonstrates source metadata,
a fake CSLib `lean4` symbol reference, requested alignment review, and
`source_reviewed_with_formal_link` verification policy without requiring Lean,
CSLib, mathlib, lake, or network access.

The Lean core formal-link pilot
`examples/claims/claim.lean-core-formal-link-pilot.yaml` records a draft
`linked` formalization reference for `import Init` and `#check Nat`. The pilot
is not accepted knowledge, keeps `require_lean_check: false`, and keeps
alignment in `requested` state. If local Lean is unavailable, the optional
`lean_library_ref` verifier remains `skipped`, not `pass`; if Lean is
available, a pass means only that the import and symbol resolved.

GitHub issue templates now cover feature tasks, bug tasks, and research issues.
The pull request template requires summary, changed files, tests run, risks,
interface changes, documentation changes, artifact/schema changes, and the
gatekeeper result.

## Implemented

- Project-wide engineering rules in `AGENTS.md`.
- Multi-repository workspace and public/private KB operating rules in
  `AGENTS.md` and `docs/CODEX_WORKFLOW.md`.
- Pre-MVP overview in `README.md`.
- Documentation skeleton under `docs/`.
- Initial ADRs under `docs/ADR/`.
- Context skeleton under `context/`.
- Python project metadata in `pyproject.toml`.
- Minimal `cosheaf` package and CLI.
- Makefile targets for `lint`, `typecheck`, `test`, `validate`, and `gate`.
- Implemented `cosheaf validate` repository validation CLI.
- Implemented `cosheaf artifact validate <path>` single-file validation CLI.
- Implemented `cosheaf artifact create` deterministic artifact lifecycle creation CLI.
- Implemented `cosheaf artifact move-status <artifact-id> <new-status>` safe lifecycle status movement CLI for non-accepted transitions.
- Implemented `cosheaf artifact promote <artifact-id>` controlled accepted-artifact promotion CLI.
- Implemented `cosheaf index rebuild` deterministic repository index rebuild CLI.
- Implemented `cosheaf graph show` dependency graph inspection CLI.
- Implemented `cosheaf gate run` gatekeeper report CLI.
- Implemented `cosheaf gate run --pr-checklist <path>` local G8 PR checklist
  gate input.
- Implemented `cosheaf gate` default gatekeeper run for the existing `make gate` target.
- Implemented G9 source metadata gate for accepted public artifacts in
  configured workspaces.
- Implemented optional `cosheaf.toml` workspace configuration with
  `WorkspaceConfig`, `WorkspacePolicy`, and `KbRootConfig` Pydantic models.
- Implemented workspace-aware storage discovery across multiple configured KB
  roots with source-root metadata on loaded records.
- Implemented public/private dependency validation and accepted-to-draft
  validation across KB roots.
- Implemented readonly KB write refusal and writable private-root default for
  lifecycle artifact creation.
- Implemented `cosheaf workspace info` to inspect the active workspace and KB
  roots.
- Added workspace-template integration smoke tests that exercise a representative
  readonly public KB plus writable private KB fixture without network access.
- Dockerfile for local development.
- Smoke tests under `tests/`.
- Repository layout under `kb/`, `issues/`, `experiments/`, and `reviews/`.
- JSON Schema files under `schemas/`.
- Example YAML artifacts under `examples/`.
- Schema/example filesystem smoke tests in `tests/test_schema_files_exist.py`.
- Pydantic v2 core models under `cosheaf/core/`.
- Structured artifact source metadata model and schema field `sources`.
- Formal Link Layer artifact metadata with `formalizations`, `alignment`, and
  `verification_policy`.
- Formalization-link documentation in `docs/FORMALIZATION_LINKS.md`.
- Formal Link Layer ADR in `docs/ADR/0005-formal-link-layer.md`.
- G10 Formal Link Gate ADR in `docs/ADR/0006-g10-formal-link-gate.md`.
- Formal-link context and query ADR in
  `docs/ADR/0007-formal-link-surface-query.md`.
- Formal-link example artifact in
  `examples/claims/claim.formal-link.example.yaml`.
- Lean core formal-link pilot example in
  `examples/claims/claim.lean-core-formal-link-pilot.yaml`.
- Artifact status/path helper functions that do not scan the repository.
- Model tests in `tests/test_artifact_models.py`.
- Repository path helpers in `cosheaf/core/paths.py`.
- Artifact type directory and lifecycle path helpers in `cosheaf/core/paths.py`.
- Filesystem-backed storage context, loader, and writer under `cosheaf/storage/`.
- Storage loader tests and fixtures in `tests/test_loader.py` and `tests/fixtures/`.
- Initial validation gates under `cosheaf/gates/`.
- Validation CLI tests in `tests/test_validate_cli.py` and `tests/test_status_path_validation.py`.
- Dependency graph utilities under `cosheaf/graph/`.
- Deterministic SQLite and manifest index rebuild in `cosheaf/storage/index.py`.
- Formalization and artifact formal-policy indexing in
  `.cosheaf/index.sqlite`.
- Read-only SQLite query API in `cosheaf/storage/query.py`, including
  formalization and formal-policy queries.
- Graph and index tests in `tests/test_claim_graph.py` and `tests/test_index_rebuild.py`.
- Query API tests in `tests/test_index_query.py`.
- Gatekeeper reports in `cosheaf/gates/gatekeeper.py`.
- Gatekeeper tests in `tests/test_gatekeeper.py`.
- Context-pack v2 generation in `cosheaf/agent/context_pack.py`, using
  `ArtifactCard` retrieval by default with explicit full-artifact budgets and
  retrieval audit output.
- Formal-link metadata display in context packs without Lean verification
  claims.
- Context pack CLI commands `cosheaf context build <issue-id>` and `cosheaf
  context show <issue-id>`, including `--role`, `--max-cards`,
  `--max-full-artifacts`, and `--public-only`.
- Context pack tests in `tests/test_context_pack.py`.
- Agent task model in `cosheaf/agent/task.py`.
- Worker output bundle contract in `cosheaf/agent/worker_contract.py`.
- Local orchestrator stub in `cosheaf/agent/orchestrator_stub.py`.
- Local worker command runner in `cosheaf/agent/local_runner.py`.
- Task CLI commands `cosheaf task create --issue <issue-id> --worker <worker-type>`, `cosheaf task list`, `cosheaf task complete <task-id> --bundle <path>`, and `cosheaf task run <task-id> -- <command> [args...]`.
- Task JSON Schema in `schemas/task.schema.json`.
- Task example YAML in `examples/tasks/task.example.yaml`.
- Task model, local runner, and CLI tests in `tests/test_task_model.py`, `tests/test_local_worker_runner.py`, and `tests/test_task_cli.py`.
- Verifier adapter protocol in `cosheaf/verification/base.py`.
- Normalized verification result model in `cosheaf/verification/result.py`.
- Instance-local verifier registry in `cosheaf/verification/registry.py`.
- Verification result and registry tests in `tests/test_verification_result.py`.
- Python checker verifier adapter in `cosheaf/verification/python_checker.py`.
- Python checker evaluator example in `experiments/evaluators/check_graph_example.py`.
- Python checker tests in `tests/test_python_checker.py`.
- Gatekeeper G6 verifier gate execution for the default Python checker registry.
- Gatekeeper G7 reproducibility metadata gate execution.
- Gatekeeper G9 accepted public source metadata gate execution.
- Gatekeeper G10 formal link metadata and verifier-result consistency gate execution.
- Minimal optional SAT DIMACS verifier adapter in `cosheaf/verification/sat_adapter.py`.
- Minimal optional SMT-LIB verifier adapter in `cosheaf/verification/smt_adapter.py`.
- Minimal optional Lean verifier adapter in `cosheaf/verification/lean_adapter.py`.
- Optional external Lean library reference verifier adapter in
  `cosheaf/verification/lean_external.py`.
- Optional verifier tests in `tests/test_optional_verifier_skeletons.py`.
- External Lean library reference adapter tests in
  `tests/test_lean_external_adapter.py`.
- Focused SAT adapter tests in `tests/test_sat_adapter.py`.
- Focused SMT adapter tests in `tests/test_smt_adapter.py`.
- First graph-theory pilot issue in `issues/open/issue.graph-toy-search.0001.yaml`.
- Draft toy graph construction in `kb/draft/constructions/construction.graph-toy.0001.yaml`.
- Toy graph example in `examples/constructions/graph.toy.yaml`.
- Toy graph Python checker in `experiments/evaluators/check_graph_toy.py`.
- Toy graph checker tests in `tests/test_graph_toy_pilot.py`.
- Second SAT/CNF pilot issue in `issues/open/issue.sat-smt-gadget.0001.yaml`.
- Draft SAT/CNF construction in `kb/draft/constructions/construction.sat-smt-gadget.0001.yaml`.
- Tiny DIMACS CNF example in `examples/sat/tiny-sat.cnf`.
- Tiny SAT assignment input in `examples/sat/tiny-sat.assignment.json`.
- Tiny SAT Python fallback checker in `experiments/evaluators/check_sat_smt_gadget.py`.
- SAT/CNF pilot checker and optional SAT skipped tests in `tests/test_sat_smt_gadget_pilot.py`.
- GitHub Actions CI in `.github/workflows/ci.yml`.
- Feature task, bug task, and research issue forms under `.github/ISSUE_TEMPLATE/`.
- Pull request template in `.github/pull_request_template.md`.
- Branch protection and review policy in `docs/REVIEW_POLICY.md`.

## Not Implemented Yet

- External public KB repository integration beyond local workspace roots.
- Hosted LLM calls and model-provider worker integration.
- Task scheduling, retries, cancellation, and dependency management.
- Automatic merge of task outputs into accepted knowledge.
- Full SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Full SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Full Lean proof-assistant integration beyond the minimal optional plain-file
  invocation path.
- Automatic informal/formal semantic alignment checking.
