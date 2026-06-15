# Strategy Planner

The strategy planner is the first `v0.4.0` planning surface. It turns one
issue record plus visible repository memory into a deterministic research task
graph and ranked next-step list.

It is an operator aid only. A strategy plan is not proof, evidence, verifier
pass, gate pass, human review, accepted status, accepted refutation, or
promotion authority.

## Commands

Generate and persist a runtime plan:

```bash
cosheaf strategy plan --issue <issue-id> --json
cosheaf strategy plan --issue <issue-id> --from-context context/TASKS/<issue-id> --json
```

The plan is written under:

```text
.cosheaf/strategy/<plan-id>/strategy.json
```

Inspect a generated plan:

```bash
cosheaf strategy show <plan-id> --json
cosheaf strategy graph <plan-id> --json
cosheaf strategy next <plan-id> --json
cosheaf strategy update-from-run --plan <plan-id> --run <run-id> --json
cosheaf strategy export-review --plan <plan-id> --dry-run --json
cosheaf strategy export-review --plan <plan-id> --json
```

The strategy commands do not call hosted providers, do not execute tasks, do
not write accepted knowledge, do not create human review, and do not run
promotion.

## Inputs

The Phase 1 planner reads local repository state only:

- issue metadata and `related_artifacts`;
- direct issue-related artifacts;
- one-hop artifact dependencies;
- artifact `failure_log` entries;
- candidate counterexample IDs linked from failure logs;
- staged checked counterexample evidence under
  `reviews/evidence/checked-counterexamples/`;
- research-run records under `.cosheaf/runs/`.

Missing or invalid sidecar records are ignored rather than treated as passes.
Skipped tool results remain skipped, not pass.

## Task Graph

Plans include first-class tasks for:

- building issue context;
- running repository validation;
- running gatekeeper;
- reading direct and one-hop artifact context;
- reviewing known failed directions;
- reviewing counterexample candidates and checked evidence;
- reviewing related research-run provenance;
- choosing a bounded proof attempt only after known failures are considered.

Task nodes preserve public/private/workspace scope labels where the repository
layout exposes them. Candidate counterexamples remain candidate-only labels.
Checked counterexample evidence remains checked evidence for review only.
Research-run records remain provenance only.

## Run-Loop Integration

`update-from-run` reads an existing `.cosheaf/runs/<run-id>/run.json` record and
attaches non-authoritative references to matching strategy task nodes. Completed
commands remain completed, failed commands remain failed, and skipped commands
remain skipped. Skipped results are not passes.

The updater can attach references for context packs, validation reports, gate
reports, checked counterexample evidence, artifacts read or touched, and
research-run provenance. These references are planning context only.

`export-review` stages a copy of the strategy plan under:

```text
reviews/strategy/<plan-id>.yaml
```

That file is review context only. It does not satisfy human review, verifier
evidence, gate success, source metadata, accepted status, or promotion
authority.

## Context And Readiness

`context build` surfaces compact strategy-plan summaries when a runtime plan is
associated with the requested issue. `RETRIEVAL_AUDIT.json` records
`strategy_plan_count` and `strategy_plans` entries when such plans exist.

Public-only context excludes private-scope strategy nodes and records that
private strategy content was excluded. Private task text must not leak into
public-only context packs.

Promotion readiness can mention open strategy blockers as advisory warnings
only. Strategy blockers do not become automatic promotion blockers.

## Eval

The local deterministic eval surface is:

```bash
cosheaf eval strategy-planner --json
```

It checks planning boundaries such as problem decomposition, failed-direction
handling, candidate-vs-checked evidence labels, skipped-not-pass handling,
private leakage prevention, and authority escalation prevention.

## Schemas

Public schema files:

```text
schemas/research_strategy.schema.json
schemas/research_task_graph.schema.json
```

The schema and DTOs include an authority notice and
`accepted_write_performed: false`. Any future review export remains review
context only and must not replace source metadata, validation, gates, verifier
evidence, human review, or explicit promotion.

## Downstream Integration

The downstream v0.4.0 integration path now includes:

- `tcs-cosheaf-workspace-template` strategy-planner demo coverage through
  `make strategy-demo`;
- `tcs-kb-public` strategy-plan policy docs that keep strategy plans as
  review context only; and
- framework ecosystem-smoke matrix rows for strategy-planner eval,
  workspace-template strategy demo, and public KB strategy-plan policy docs.

The remaining v0.4.0 work is release-candidate and publication closeout:
version metadata, release notes, release smoke, and downstream pin alignment
after the public tag exists.
