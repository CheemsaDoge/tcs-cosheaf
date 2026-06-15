# TCS-Cosheaf longplan_v8 accelerated: v0.4.0 Strategy Planner + Research Task Graph

## Target

```text
v0.4.0 Strategy Planner + Research Task Graph
```

## One-line goal

Turn the v0.3.0 checked-evidence and research-run loop into a planned research process: decompose a problem into subgoals, rank next steps, avoid known failed directions, and give Codex-style external operators a bounded task graph to execute through the CLI.

## Current baseline

The previous line, `v0.3.0 Checked Evidence + Research Run Loop`, is treated as complete before this plan starts.

Baseline capabilities now available:

- Candidate counterexamples and checked counterexample evidence are separated.
- Checked counterexample evidence can be validated, shown, and staged under review evidence paths.
- Checked evidence is surfaced in context packs, retrieval audit, promotion readiness, and evals.
- Research-run records can start, append commands/artifacts/outputs, finalize, show, produce evidence reports, export review records, and emit replay plans.
- External operator docs instruct Codex-style agents to operate through CLI/Git/PR, not by becoming a default embedded model runtime inside Cosheaf.
- Workspace-template and public KB downstream pins are aligned to `v0.3.0` after release publication.

## Why v0.4.0

`v0.2.x` finished the agent/evidence/failure-memory foundation.
`v0.3.0` finished the auditable run loop.
`v0.4.0` should now add the missing planning layer.

The system should no longer only record what happened. It should help decide what to try next.

## Acceleration rule

Do not split this line into many small audit/doc PRs.

Use large but bounded implementation PRs:

1. Kickoff + plan + ADR.
2. Strategy/task-graph model + schema + CLI + docs + tests in one PR.
3. Planner/run-loop integration + context/readiness surfacing + eval/security in one PR.
4. Workspace/public-KB downstream demo/policy + ecosystem smoke in one PR.
5. Release candidate.
6. Publication closeout.

Avoid separate PRs for docs-only cleanup unless the cleanup is blocking release correctness.

## Non-goals

This line must not:

- embed GPT, Claude, or another hosted model as the default Cosheaf runtime;
- make provider calls default-on;
- require MCP;
- add controlled-write MCP;
- write accepted knowledge directly;
- promote artifacts automatically;
- mark AI review as human review;
- treat planner output as proof, checked evidence, verifier pass, gate pass, human review, accepted status, or promotion authority;
- claim automatic theorem proving, Lean semantic alignment, or autonomous mathematical discovery.

## Core concepts to add

### Research problem

A research problem is the root object for a strategy plan. It should point to an issue, domain, target artifacts, known baselines, constraints, and desired evidence.

### Research task graph

A task graph is a directed graph of research steps. Nodes should include:

- understand/problem-reading step;
- retrieval/context step;
- proof-attempt step;
- construction search step;
- counterexample search step;
- verification/checking step;
- formalization attempt step;
- literature/source lookup step;
- review/decision step;
- blocked/deferred step.

Edges record prerequisites, evidence dependencies, and blocked-by relationships.

### Strategy plan

A strategy plan ranks candidate routes through the task graph. It should explain why a step is next, what evidence is expected, what failure memory should be avoided, and which commands or controlled writes an operator should run.

### Planner output authority

A strategy plan is guidance only. It is not proof, not evidence, not review, not accepted knowledge, and not promotion authority.

## New public surfaces

Preferred CLI surfaces:

```bash
cosheaf strategy plan --issue <issue-id> --json
cosheaf strategy plan --issue <issue-id> --from-context <context-dir> --json
cosheaf strategy show <plan-id> --json
cosheaf strategy graph <plan-id> --json
cosheaf strategy next <plan-id> --json
cosheaf strategy update-from-run --plan <plan-id> --run <run-id> --json
cosheaf strategy export-review --plan <plan-id> --dry-run --json
cosheaf strategy export-review --plan <plan-id> --json
cosheaf eval strategy-planner --json
```

The exact command names may be adjusted during implementation, but the CLI must remain the primary interface.

## Storage policy

Recommended locations:

```text
.cosheaf/strategy/<plan-id>/strategy.json       runtime/generated plan
reviews/strategy/<plan-id>.yaml                 explicit review export only
schemas/research_strategy.schema.json           public schema
schemas/research_task_graph.schema.json         public schema if separate
```

Runtime plans stay under ignored `.cosheaf/` by default. Review exports require an explicit export command and remain non-authoritative review context.

Do not write plans into `kb/accepted/`.
Do not write plans into readonly public KB roots.
Do not copy private task graph content into public KB docs.

## Phase 0: Kickoff + ADR + accelerated plan landing

### Task 0.1: post-v030-v040-kickoff

```text
Branch: post-v030-v040-kickoff
Repository: tcs-cosheaf
```

Goal:

- Confirm v0.3.0 is the current published baseline.
- Add the accelerated v0.4.0 plan as `docs/CODEX_DEVELOPMENT_PLAN_V8.md`.
- Add ADR for Strategy Planner + Research Task Graph.
- Update milestone/roadmap/project-state to say v0.4.0 is the active line.

Allowed files:

```text
docs/CODEX_DEVELOPMENT_PLAN_V8.md
docs/ADR/0025-strategy-planner-task-graph.md
docs/ROADMAP.md
context/CURRENT_MILESTONE.md
context/PROJECT_STATE.md
```

Required commands:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

Stop after merge. No runtime behavior in this task.

## Phase 1: Strategy/task-graph core

### Task 1.1: strategy-task-graph-core

```text
Branch: strategy-task-graph-core
Repository: tcs-cosheaf
```

Goal:

Implement the durable data model, schema, deterministic planner, CLI, docs, and unit tests in one PR.

Must add:

```text
cosheaf/strategy/
cosheaf/strategy/models.py
cosheaf/strategy/planner.py
cosheaf/strategy/storage.py
schemas/research_strategy.schema.json
schemas/research_task_graph.schema.json  # if separate
```

Must support:

- strict Pydantic DTOs;
- deterministic serialization;
- timezone-aware timestamps;
- repository-local path validation;
- explicit authority notice;
- public/private scope labels;
- issue ID, target artifacts, domains, tags, known constraints;
- subgoals and task nodes;
- task dependencies and blocked-by edges;
- expected evidence kinds;
- related artifacts;
- related failure-log entries;
- related candidate counterexamples;
- related checked counterexample evidence;
- related research-run IDs;
- next-step ranking with explanations.

Minimal deterministic planner heuristics:

- prefer direct issue-related artifacts;
- include one-hop dependencies;
- surface known failed directions from failure memory;
- mark candidate counterexamples as candidate only;
- mark checked evidence as checked evidence only;
- recommend validate/gate/context commands as first-class tasks;
- prefer low-risk, high-information next actions;
- avoid repeatedly recommending a direction already marked as failed unless explicitly marked retryable.

CLI:

```bash
cosheaf strategy plan --issue <issue-id> --json
cosheaf strategy show <plan-id> --json
cosheaf strategy graph <plan-id> --json
cosheaf strategy next <plan-id> --json
```

Tests:

- model/schema validation;
- duplicate node IDs rejected;
- non-repository paths rejected;
- accepted-path write authority rejected;
- candidate-vs-checked evidence labels preserved;
- failed directions influence next-step ranking;
- JSON output deterministic;
- old workspaces unaffected.

Docs:

```text
docs/STRATEGY_PLANNER.md
docs/AGENT_ACCESS.md
docs/CODEX_WORKFLOW.md
context/INTERFACE_REGISTRY.md
```

Do not:

- call provider APIs;
- execute tasks;
- write accepted knowledge;
- promote artifacts;
- create human review.

## Phase 2: Planner/run-loop integration

### Task 2.1: strategy-run-loop-integration

```text
Branch: strategy-run-loop-integration
Repository: tcs-cosheaf
```

Goal:

Connect strategy plans with v0.3.0 research-run records and evidence surfaces.

Must implement:

```bash
cosheaf strategy plan --issue <issue-id> --from-context <context-dir> --json
cosheaf strategy update-from-run --plan <plan-id> --run <run-id> --json
cosheaf strategy export-review --plan <plan-id> --dry-run --json
cosheaf strategy export-review --plan <plan-id> --json
cosheaf eval strategy-planner --json
```

Behavior:

- `update-from-run` reads research-run provenance and updates task statuses.
- Completed commands, touched artifacts, staged checked evidence, exported reviews, validation reports, and gate reports become references on strategy nodes.
- Failed or skipped commands are preserved as failed/skipped, not pass.
- Inconclusive checked evidence does not refute anything.
- Strategy review export writes only under `reviews/strategy/`.
- Exported strategy review remains review context only.

Context integration:

- `context build` should be able to surface compact strategy-plan summaries when the issue has an associated plan.
- `RETRIEVAL_AUDIT.json` should include strategy-plan references and counts.
- Public-only context must not include private strategy content.

Promotion readiness integration:

- Promotion readiness may mention open strategy blockers as advisory warnings.
- Strategy blockers must not become automatic promotion blockers unless a separate existing gate already blocks promotion.

Eval:

Add:

```text
cosheaf/evals/strategy_planner.py
evals/strategy_planner/cases.yaml
tests/evals/test_strategy_planner_eval.py
```

Eval cases should check:

- problem decomposition exists;
- failed directions are not blindly repeated;
- candidate counterexample remains candidate;
- checked evidence remains checked evidence;
- skipped tools are not pass;
- private strategy text does not leak into public-only context;
- next steps are bounded and command-oriented;
- no accepted-write authority is implied.

Security tests:

```text
tests/security/test_strategy_planner_security.py
```

Must reject:

- authority-spoofing fields;
- hidden-reasoning fields;
- absolute or parent-traversal paths;
- direct `kb/accepted/` targets;
- private content in public export mode;
- provider/API key looking text in strategy summaries.

## Phase 3: Downstream demos and policy in one pass

### Task 3.1: strategy-downstream-demo-policy-smoke

This is a coordinated two-repository plus framework-smoke task. Keep PRs separate by repo, but execute as one planned downstream phase.

#### 3.1a Workspace-template demo

```text
Repository: tcs-cosheaf-workspace-template
Branch: workspace-strategy-demo
```

Add:

```text
scripts/demo_strategy_planner.sh
make strategy-demo
docs/STRATEGY_PLANNER_WORKFLOW.md
README.md update
```

Demo must:

- use `tcs-cosheaf@v0.4.0` only after release; before release, support local checkout override;
- build or reuse a context pack;
- create a strategy plan;
- start a research run;
- record at least one command;
- show next step;
- export strategy review with dry-run by default;
- run validate/gate;
- write runtime outputs only under ignored `.cosheaf/` paths unless explicitly exporting review context.

Demo must not:

- call hosted provider APIs;
- require API keys;
- require MCP;
- write accepted knowledge;
- promote artifacts;
- mark human review.

#### 3.1b Public KB policy

```text
Repository: tcs-kb-public
Branch: public-kb-strategy-policy
```

Add:

```text
docs/STRATEGY_PLAN_POLICY.md
README.md policy mention
.github/pull_request_template.md reminder
```

Policy must say:

- public strategy plans are review context only;
- strategy plans cannot replace source metadata, validation, gates, human review, verifier evidence, or promotion;
- private strategy plans must not be copied into public KB;
- candidate counterexamples and checked counterexample evidence remain distinct;
- checked evidence can support review but does not by itself create accepted refutation.

#### 3.1c Framework ecosystem smoke

```text
Repository: tcs-cosheaf
Branch: strategy-ecosystem-smoke
```

Update:

```text
scripts/ecosystem_smoke.py
tests/test_ecosystem_smoke.py
docs/EVALUATION.md
```

Add matrix rows:

- framework strategy planner eval;
- workspace strategy demo;
- public KB strategy-policy docs smoke.

Default matrix remains network-free. Network rows remain skipped unless explicitly enabled.

## Phase 4: Release candidate

### Task 4.1: release-v040-readiness-and-rc

```text
Branch: release-v040-readiness-and-rc
Repository: tcs-cosheaf
```

Goal:

Prepare conservative v0.4.0 release candidate after all implementation and downstream integration PRs have merged.

Allowed changes:

```text
pyproject.toml
cosheaf/__init__.py
docs/releases/v0.4.0.md
README.md
README.zh-CN.md
RELEASE_CHECKLIST.md
docs/ROADMAP.md
context/CURRENT_MILESTONE.md
context/PROJECT_STATE.md
```

Required checks:

```bash
python -m cosheaf.cli version --json
make lint
make typecheck
make test
make validate
make gate
python scripts/ecosystem_smoke.py --matrix --cosheaf "python -m cosheaf.cli" --framework-root . --workspace-template-root ../tcs-cosheaf-workspace-template --public-kb-root ../tcs-kb-public --json
git diff --check
```

Expected:

- package version reports `0.4.0`;
- no public `v0.4.0` tag yet;
- release note says not production-ready;
- no default provider calls;
- no MCP requirement;
- no accepted writes;
- skipped rows not counted as pass.

## Phase 5: Publication closeout

### Task 5.1: release-v040-publication-closeout

```text
Branch: release-v040-publication-closeout
Repository: tcs-cosheaf
```

Maintainer release action before PR:

```bash
git fetch --tags
python -m cosheaf.cli version --json
git tag -a v0.4.0 -m "v0.4.0 Strategy Planner + Research Task Graph"
git push origin v0.4.0
# publish GitHub release
python scripts/release_smoke.py --framework-ref v0.4.0
```

Then update docs to published-release state.

### Task 5.2: downstream-v040-pins

After release smoke passes:

- update workspace-template active pins to `@v0.4.0`;
- update public KB CI pin to `@v0.4.0`;
- run workspace validate/gate/context/strategy demo;
- run public KB validate/gate/pr-checklist/policy guard;
- update release checklists.

If downstream pins are already done before framework closeout, the framework closeout should record that instead of duplicating work.

## Definition of done for v0.4.0

v0.4.0 is done when:

- Strategy/task-graph model and schema exist.
- Strategy CLI exists and emits deterministic JSON.
- Strategy plans can be generated from issues/context.
- Strategy next-step ranking exists and explains reasons.
- Strategy update-from-run exists.
- Strategy review export exists and is non-authoritative.
- Context/retrieval surfaces show compact strategy references without private leakage.
- Promotion readiness can mention strategy blockers as advisory context only.
- Security tests cover authority spoofing and path/private leakage.
- Deterministic eval suite covers strategy planning boundaries.
- Workspace-template has a strategy demo.
- Public KB has strategy-plan policy.
- Ecosystem smoke includes strategy rows.
- `v0.4.0` tag and GitHub release are published.
- Workspace-template and public KB pins are aligned to `v0.4.0`.

## Stop rules

Stop and ask for maintainer decision if a task would require:

- default real provider calls;
- embedding GPT/Claude as default runtime;
- MCP as required interface;
- direct accepted writes;
- changing promotion semantics;
- treating strategy plans as proof/evidence/review;
- private-to-public content copying;
- broad public KB content growth unrelated to strategy policy;
- weakening validation, gate, security, or skipped-not-pass tests.

## First Codex task

```text
Task: post-v030-v040-kickoff
Branch: post-v030-v040-kickoff
Repository: tcs-cosheaf

Goal:
  Start the accelerated v0.4.0 Strategy Planner + Research Task Graph line.
  Land the plan, ADR, and current milestone/roadmap state only.

Do not:
  implement runtime behavior;
  add schemas;
  alter provider/MCP behavior;
  write accepted KB;
  bump version;
  create release tags.
```

## Summary

This line should move quickly. The next real implementation work is not another long audit. It is the strategy/task-graph core: a planner that turns issue context, failure memory, checked evidence, and research-run provenance into bounded next actions for Codex-style external operators.
