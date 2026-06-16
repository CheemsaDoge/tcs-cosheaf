# Current Milestone

## Milestone

`v0.5.0` Operator MCP + Codex Application Layer.

## Goal

Turn the published `v0.4.0` Strategy Planner + Research Task Graph release
into a safe operator-facing tool layer that Codex-style agents can use through
MCP or CLI without gaining accepted-write, human-review, or promotion
authority.

MCP is an adapter layer for operator access. It is not a new truth,
accepted-knowledge, review, proof, verifier, gate, provider, or promotion
authority.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.5.0` in the
  release-candidate branch.
- The public `v0.5.0` tag, GitHub release, post-tag release smoke, and
  downstream workspace/public-KB pin updates remain publication-closeout work.
- Remote tag `v0.4.0` exists as an annotated tag and the GitHub release is
  published.
- Release smoke from
  `git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.4.0` passed during
  the V9 kickoff audit.
- `tcs-cosheaf-workspace-template` active demo, Makefile, CLI-agent,
  provider-preview, fake-provider smoke, verifier-evidence, failure-memory,
  checked-evidence, research-run, and strategy paths pin or install `@v0.4.0`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.4.0`.
- `tcs-kb-public` public KB operator policy smoke is merged and records that
  operator, MCP, provider, LLM, checked-evidence, research-run, and strategy
  outputs are review context only.
- Downstream workspace-template/public-KB pin alignment to `@v0.4.0` is
  complete.
- `docs/CODEX_DEVELOPMENT_PLAN_V8.md` is the completed accelerated `v0.4.0`
  plan.
- ADR 0025 records the Strategy Planner + Research Task Graph direction.
- `docs/CODE_AUDIT_V040.md` records the v0.4.0 code audit closeout.
- `docs/POST_V040_STATE_AUDIT.md` records the V9 kickoff audit.
- `docs/CODEX_DEVELOPMENT_PLAN_V9.md` is the active accelerated `v0.5.0`
  plan.
- ADR 0026 records the Operator MCP + Codex Application Layer direction.

## Active Scope

The active line is:

```text
v0.5.0 Operator MCP + Codex Application Layer
```

Compressed milestones:

1. Post-v0.4.0 kickoff audit, V9 plan, and ADR.
2. Read-only operator MCP server core.
3. Controlled draft-write MCP tools.
4. Codex operator runbook and workspace demo.
5. Public KB operator policy smoke and optional operator skill docs.
6. v0.5.0 release candidate, publication closeout, and downstream pin
   alignment.

## Current And Next Functional Tasks

Current task:

```text
release-v050-readiness-and-rc
```

This task prepares the conservative `v0.5.0` release-candidate metadata and
status documentation after the read-only MCP tools, controlled draft-write MCP
tools, operator runbook/workspace demo docs, public KB operator policy smoke,
and optional operator Skill package have merged. It bumps package metadata to
`0.5.0` and records the release-candidate audit without creating a public tag,
publishing a GitHub release, updating downstream pins, changing runtime
behavior, adding dependencies, widening MCP/provider authority, writing
accepted knowledge, creating human review, promoting artifacts, changing
schemas, or claiming automatic theorem proving.

Next implementation task after this release-candidate work merges:

```text
release-v050-publication-closeout
```

## Explicit Boundaries

- CLI remains the human and CI oracle.
- Codex-style agents are external operators that call CLI/MCP tools, edit
  files, run tests, and open PRs.
- MCP remains optional; CLI fallback must stay documented and usable.
- Do not embed GPT, Claude, or any hosted model as the default Cosheaf runtime.
- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- No real provider calls run in CI or default tests.
- No accepted KB writes through MCP.
- No promotion through MCP.
- No human-review creation through MCP.
- No arbitrary shell through MCP.
- Operator/MCP output is not proof, checked evidence, verifier evidence,
  verifier pass, gate pass, human review, accepted status, accepted refutation,
  or promotion authority.
- Controlled writes may create only draft, proposal, review-context, or
  runtime records already allowed by Cosheaf policy.
- Research-run records remain provenance.
- Strategy plans remain guidance.
- Checked counterexample evidence remains review evidence.
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

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show
that prefix.
