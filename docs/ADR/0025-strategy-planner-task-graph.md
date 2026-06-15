# ADR 0025: Strategy Planner And Research Task Graph

Status: Accepted for the `v0.4.0` implementation line.

Date: 2026-06-15

## Context

The published `v0.3.0` Checked Evidence + Research Run Loop release gives
Cosheaf a durable way to record checked counterexample evidence and
repository-local external-operator research runs. That line records what
happened, which commands were run, which evidence was referenced, and which
outputs were produced.

The missing layer is planning. A Codex-style external operator still needs a
bounded way to decide what to try next from issue context, dependency
structure, failure memory, checked evidence, candidate counterexamples, and
research-run provenance.

## Decision

Cosheaf will add a Strategy Planner and Research Task Graph line for `v0.4.0`.

The framework will store a strategy plan as a deterministic, typed,
repository-local planning artifact. The plan will contain a research problem,
a directed research task graph, ranked next steps, evidence expectations,
known constraints, failed-direction warnings, and references to related
artifacts, failure logs, candidate counterexamples, checked counterexample
evidence, and research runs.

The primary interface remains the CLI. Planned surfaces include:

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

Runtime strategy plans will default to:

```text
.cosheaf/strategy/<plan-id>/strategy.json
```

Explicit review exports will be controlled and non-authoritative:

```text
reviews/strategy/<plan-id>.yaml
```

## Authority Boundary

A strategy plan is guidance only. It is not:

- proof;
- checked counterexample evidence;
- verifier evidence;
- verifier pass;
- gate pass;
- human review;
- accepted status;
- accepted refutation;
- promotion authority;
- a source of public KB truth.

Planner output must not write accepted knowledge, promote artifacts, mark
human review, or change accepted-promotion semantics. Candidate
counterexamples remain candidate evidence only. Checked counterexample
evidence remains checked evidence only. Skipped, failed, unavailable,
inconclusive, provider, SAT, SMT, Lean, lake, network, or operator rows remain
non-pass unless a separate checker records an actual pass.

## Consequences

The `v0.4.0` line will add models, schemas, CLI commands, deterministic evals,
security tests, context/readiness surfacing, workspace demos, and public KB
policy around strategy plans.

The planner must remain deterministic and local by default. It may rank next
steps using repository data, but it must not embed GPT, Claude, or another
hosted model as the default runtime. Hosted provider calls remain explicit,
default-off, policy-scoped, consented, and excluded from CI/default tests.
MCP remains optional and non-blocking.

The first implementation should prefer conservative deterministic heuristics:
issue-related artifacts, one-hop dependencies, known failed directions,
candidate-vs-checked evidence separation, validation/gate/context commands as
first-class tasks, and low-risk high-information next actions.

## Non-Goals

This ADR does not approve:

- default real provider calls;
- embedded hosted-model planning as the normal runtime;
- required MCP or controlled-write MCP;
- direct writes to `kb/accepted/`;
- automatic accepted promotion;
- automatic theorem proving;
- Lean/mathlib/CSLib semantic-alignment claims;
- copying private strategy content into public KB paths.

## Follow-Ups

- Land `docs/CODEX_DEVELOPMENT_PLAN_V8.md` as the active plan.
- Implement the strategy/task-graph core model, schemas, CLI, docs, and tests.
- Integrate strategy plans with research-run records, context packs,
  promotion-readiness reports, evals, and security tests.
- Add workspace-template strategy demo and public KB strategy-plan policy.
- Prepare and publish a conservative `v0.4.0` release only after downstream
  alignment and release smoke pass.
