# Current Milestone

## Milestone

`v0.4.0` Strategy Planner + Research Task Graph.

## Goal

Turn the published `v0.3.0` checked-evidence and research-run loop into a
planned research process. The `v0.4.0` line should decompose an issue into
bounded research tasks, rank next steps, avoid known failed directions, and
give Codex-style external operators a deterministic task graph to execute
through the CLI/Git/PR workflow.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving,
automatic Lean autoformalization, automatic accepted promotion,
AI-as-human-review, provider/MCP authority expansion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.3.0`.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3`, `v0.2.4`,
  and `v0.3.0` exist.
- The GitHub release `v0.3.0 Checked Evidence + Research Run Loop` is
  published and is not a production-readiness claim.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.3.0` passed.
- `tcs-cosheaf-workspace-template` active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, verifier-evidence, failure-memory,
  checked-evidence, and research-run paths pin or install `@v0.3.0`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.3.0`.
- `docs/CODEX_DEVELOPMENT_PLAN_V7.md` is the completed accelerated `v0.3.0`
  plan.
- ADR 0024 records the checked-evidence and research-run-loop direction.
- `docs/releases/v0.3.0.md` records release-candidate verification,
  publication closeout, release smoke, and downstream pin alignment.
- `docs/CODEX_DEVELOPMENT_PLAN_V8.md` is the active accelerated `v0.4.0`
  plan.
- ADR 0025 records the Strategy Planner + Research Task Graph direction.

## Active Scope

The active line is:

```text
v0.4.0 Strategy Planner + Research Task Graph
```

Compressed milestones:

1. Kickoff + plan + ADR.
2. Strategy/task-graph model, schema, CLI, docs, and tests.
3. Planner/run-loop integration, context/readiness surfacing, eval, and
   security coverage.
4. Workspace-template strategy demo, public KB strategy policy, and ecosystem
   smoke rows.
5. v0.4.0 release candidate.
6. v0.4.0 publication closeout and downstream pin alignment.

## Current And Next Functional Tasks

Current task:

```text
strategy-run-loop-integration
```

This task implements the Phase 2 planner/run-loop integration: planning from
existing context packs, updating strategy plans from research-run provenance,
strategy review export, context-pack strategy summaries, promotion-readiness
advisory warnings, deterministic strategy-planner evals, and security
coverage. It must not add provider calls, MCP requirements, task execution,
accepted KB writes, human review creation, promotion behavior, version bumps,
or release tags.

After this task merges, proceed directly to:

```text
strategy-downstream-demo-policy-smoke
```

That follow-up should add the workspace-template strategy demo, public KB
strategy-plan policy, and framework ecosystem-smoke rows in separate repo PRs
where required.

## Explicit Boundaries

- CLI remains the first agent interface and the human/CI oracle.
- Codex-style agents are external operators that call CLI, edit files, run
  tests, and open PRs.
- Do not embed GPT, Claude, or any hosted model as the default Cosheaf runtime
  in this milestone.
- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- No real provider calls run in CI or default tests.
- MCP remains optional and non-blocking.
- No controlled-write MCP, provider MCP tools, direct accepted writes, or
  accepted-promotion bypass is part of this milestone.
- A strategy plan is guidance only. It is not proof, checked evidence,
  verifier evidence, verifier pass, gate pass, human review, accepted status,
  accepted refutation, or promotion authority.
- Strategy exports are review context only and must stay under controlled
  review paths.
- Worker/provider/Codex/verifier output may become draft/proposal/bundle/run
  evidence context only.
- A `candidate_counterexample` is not checked counterexample evidence.
- Checked counterexample evidence is evidence for review, not human review,
  accepted refutation, accepted status, or promotion authorization by itself.
- A research run record is provenance, not proof, verifier pass, gate pass,
  human review, accepted status, or promotion authorization.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, verifier evidence where applicable, and explicit
  promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, Lean, lake, optional-tool, network, or
  operator results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Current Operating State

The accelerated V7 implementation and publication for `v0.3.0` are complete.
Checked counterexample evidence is a durable review-evidence surface, but it
remains separate from human review, accepted refutation, accepted status, and
promotion authority. Research-run records are provenance, not proof or review
authority.

The current work adds the deterministic planning layer on top of those surfaces
without changing their authority. Continue to avoid treating failure memory,
counterexample candidates, verifier requests, verifier evidence, checked
evidence, research-run records, strategy plans, provider output, evals,
validation, gates, or context retrieval as human review, proof, accepted
status, verifier pass, gate pass, or promotion authority.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
