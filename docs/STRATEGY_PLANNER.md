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
```

The `plan`, `show`, `graph`, and `next` commands do not call hosted providers,
do not execute tasks, do not write accepted knowledge, do not create human
review, and do not run promotion.

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

## Current Limits

Phase 1 does not implement:

- `--from-context`;
- `update-from-run`;
- `export-review`;
- strategy context-pack surfacing;
- promotion-readiness strategy warnings;
- strategy planner evals or security tests;
- downstream workspace-template strategy demos;
- public KB strategy policy docs.

Those are the next `v0.4.0` tasks.
