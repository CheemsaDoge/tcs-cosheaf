# Operator Sessions

Operator sessions are the `v0.6.0` audit layer for external-operator work.
They record bounded metadata about one issue-focused session so a maintainer
can review what happened without reading raw terminal or MCP transcripts.

This document describes the model and storage layer landed in the
`operator-session-model` task. CLI commands, MCP session recording, leak
scanning, handoff bundle generation, and review-context export are follow-up
tasks in `docs/CODEX_DEVELOPMENT_PLAN_V10.md`.

## Authority Boundary

Operator session records are review metadata only. They are not:

- proof;
- verifier evidence;
- verifier pass;
- gate pass;
- human review;
- accepted status;
- accepted refutation;
- public KB source metadata; or
- promotion authority.

The model carries explicit false authority fields:

- `accepted_write_performed: false`
- `human_review_created: false`
- `promotion_performed: false`
- `verifier_result_mutated: false`

Validation, gate, eval, MCP, provider, Lean, SAT, SMT, and network results must
still be reported by the command or tool that actually ran them. Skipped
results remain skipped and are not passes.

## Runtime Storage

Session records are runtime files under ignored `.cosheaf/` paths:

```text
.cosheaf/operator-sessions/<session-id>/session.json
.cosheaf/operator-sessions/<session-id>/events.jsonl
```

They are not source-of-truth artifacts. They should not be committed unless a
future task explicitly asks for a review-context export.

Future handoff export is planned for:

```text
reviews/operator/<handoff-id>.yaml
```

That export will also be review context only, not human review or accepted
knowledge.

## Model Surface

The model layer currently defines:

- `OperatorSession`
- `OperatorToolCallRecord`
- `OperatorArtifactRef`
- `OperatorCheckResult`
- `OperatorSessionSummary`
- `OperatorPolicyFinding`

The schema file is:

```text
schemas/operator_session.schema.json
```

Session records include:

- session and issue IDs;
- policy mode, currently `public_only` or `private_research`;
- lifecycle status;
- started/finalized timestamps;
- safe artifact or file references;
- check results;
- policy findings;
- authority disclaimers; and
- non-authority false fields.

## Privacy And Redaction Rules

The model rejects direct `kb/accepted/` paths, absolute paths, parent traversal,
secret-looking values, environment dumps, hidden-reasoning fields, raw stdout
or stderr fields, and full artifact/private text fields.

Tool-call records store bounded metadata and summaries only. They do not store
full context packs, full artifact YAML, provider request/response payloads,
arbitrary stdout/stderr, API keys, environment dumps, hidden reasoning, or full
private artifact text by default.

## Current Limitations

This task does not add CLI commands yet. There is no `cosheaf operator session`
CLI surface until the next task.

This task does not record MCP calls yet. MCP session recording is a separate
follow-up task.

This task does not build handoff bundles or export `reviews/operator/` files.
Those are later `v0.6.0` tasks.

This task does not change accepted promotion, human review, verifier results,
gate behavior, provider defaults, formal-link semantics, or public KB policy.
