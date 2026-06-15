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

- Framework package metadata and `cosheaf.__version__` record `0.4.0`.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3`, `v0.2.4`,
  `v0.3.0`, and `v0.4.0` exist.
- The GitHub release `v0.4.0 Strategy Planner + Research Task Graph` is
  published and is not a production-readiness claim.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0` passed.
- `tcs-cosheaf-workspace-template` active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, verifier-evidence, failure-memory,
  checked-evidence, research-run, and strategy paths pin or install `@v0.4.0`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.4.0`.
- Downstream workspace-template/public-KB pin alignment to `@v0.4.0` is
  complete.
- `docs/CODEX_DEVELOPMENT_PLAN_V7.md` is the completed accelerated `v0.3.0`
  plan.
- ADR 0024 records the checked-evidence and research-run-loop direction.
- `docs/releases/v0.3.0.md` records release-candidate verification,
  publication closeout, release smoke, and downstream pin alignment.
- `docs/CODEX_DEVELOPMENT_PLAN_V8.md` is the completed accelerated `v0.4.0`
  plan.
- ADR 0025 records the Strategy Planner + Research Task Graph direction.

## Completed Scope

The completed line is:

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

No in-repository v0.4.0 implementation tasks remain open after downstream pin
alignment. Future work should begin from a new issue and plan rather than
continuing to treat the V8 release line as active.

Most recent completed task:

```text
downstream-v040-pins
```

This task records that downstream pin alignment is complete after
workspace-template PR #69 and tcs-kb-public PR #80 moved active pins to
`@v0.4.0` and reran the documented demo, validation, gate, and policy guard
checks. It does not add provider calls, require MCP, write accepted knowledge,
create human review, change promotion behavior, or change framework runtime
behavior.

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

The accelerated V8 implementation, downstream integration, release candidate,
tag publication, GitHub release, post-tag release smoke, and downstream
workspace/public-KB pin alignment for `v0.4.0` are complete. Checked
counterexample evidence remains durable review evidence, research-run records
remain provenance, and strategy plans remain guidance only.

This closeout does not change authority boundaries. Continue to avoid treating
failure memory, counterexample candidates, verifier requests, verifier
evidence, checked evidence, research-run records, strategy plans, provider
output, evals, validation, gates, or context retrieval as human review, proof,
accepted status, verifier pass, gate pass, or promotion authority.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
