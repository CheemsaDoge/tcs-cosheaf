# Operator Sessions

Operator sessions are the `v0.6.0` audit layer for external-operator work.
They record bounded metadata about one issue-focused session so a maintainer
can review what happened without reading raw terminal or MCP transcripts.

This document describes the model, runtime storage, CLI metadata surface, and
optional MCP tool-call recording landed so far. Leak scanning, handoff bundle
generation, and review-context export are follow-up tasks in
`docs/CODEX_DEVELOPMENT_PLAN_V10.md`.

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

## CLI Surface

The operator-session CLI records bounded metadata and references only. It does
not run validation, gates, tests, evals, MCP tools, providers, Lean, SAT, SMT,
or shell commands.

Start a session:

```bash
cosheaf operator session start --issue <issue-id> --json
```

Optional start arguments:

```bash
cosheaf operator session start \
  --issue <issue-id> \
  --policy public_only \
  --operator-label "external operator" \
  --session-id <session-id> \
  --json
```

Supported policies are `public_only` and `private_research`. The default is
`public_only`. Public-only sessions reject private references.

Inspect a session:

```bash
cosheaf operator session show <session-id> --json
```

Append a check-status summary:

```bash
cosheaf operator session append-check <session-id> \
  --kind validate \
  --status pass \
  --summary "validation command completed outside this metadata recorder" \
  --report-path .cosheaf/reports/validate.json \
  --json
```

Allowed CLI check kinds are `validate`, `gate`, `test`, and `eval`. Allowed
statuses are `pass`, `fail`, `error`, and `skipped`. A skipped check remains
`skipped`; when no skipped summary is supplied the CLI records:

```text
Skipped operator-session checks are not pass evidence.
```

Append a safe repository-local reference:

```bash
cosheaf operator session append-ref <session-id> \
  --kind draft \
  --path kb/private/draft/claims/claim.example.yaml \
  --artifact claim.example \
  --scope private \
  --summary "private draft reference only" \
  --json
```

Allowed CLI reference kinds are `draft`, `review_context`, `runtime`, and
`report`. References to `kb/accepted/` are rejected. References to private
paths or `--scope private` are rejected in `public_only` sessions.

Finalize a session:

```bash
cosheaf operator session finalize <session-id> --json
```

Finalized sessions are immutable for `append-check` and `append-ref`.

## Optional MCP Tool-Call Recording

MCP `tools/call` requests may include an optional `session_id` field inside
the tool arguments:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "workspace_info",
    "arguments": {
      "session_id": "session.issue.example.0001"
    }
  }
}
```

When `session_id` is present, the MCP adapter strips it before invoking the
underlying whitelisted tool. The tool result is generated through the same
service-layer path as before. After the tool call, the adapter appends one
bounded `OperatorToolCallRecord` event to:

```text
.cosheaf/operator-sessions/<session-id>/events.jsonl
```

The event records only:

- tool name;
- session mode;
- argument names and count;
- normalized status: `completed`, `failed`, `denied`, or `error`;
- bounded result summary;
- timestamp; and
- warning codes.

Calls without `session_id` continue to work and do not create session events.
Unknown tools, denied tools, expected MCP errors, and unexpected handler errors
are recorded when a valid session ID is supplied. Public-mode MCP results are
still public-scoped before recording.

## Privacy And Redaction Rules

The model rejects direct `kb/accepted/` paths, absolute paths, parent traversal,
secret-looking values, environment dumps, hidden-reasoning fields, raw stdout
or stderr fields, and full artifact/private text fields.

Tool-call records store bounded metadata and summaries only. They do not store
full context packs, full artifact YAML, provider request/response payloads,
arbitrary stdout/stderr, API keys, environment dumps, hidden reasoning, or full
private artifact text by default. Public-only sessions record argument names
and counts but do not record private query text.

## Leak Scanner

Before building or exporting a handoff bundle, scan the session:

```bash
cosheaf operator session scan <session-id> --json
```

The scanner reads:

```text
.cosheaf/operator-sessions/<session-id>/session.json
.cosheaf/operator-sessions/<session-id>/events.jsonl
```

and writes a deterministic runtime report to:

```text
.cosheaf/operator-sessions/<session-id>/scan.json
```

The report includes `handoff_blocked`, `finding_count`,
`blocking_finding_count`, and stable finding records. Blocking findings cause
the CLI to exit nonzero after emitting JSON.

The scanner flags API-key-shaped values, bearer-token-like strings,
environment dumps, secret-looking environment values, hidden-reasoning
markers, raw provider payloads, absolute private paths, accepted-write
attempts, authority claims, and private artifact IDs or private path
references in `public_only` sessions.

The scanner does not mutate source-of-truth files, does not create human
review, does not promote artifacts, and does not prove or verify any claim. It
is a fail-closed review/handoff guard.

## Current Limitations

This task does not build handoff bundles or export `reviews/operator/` files.
Those are later `v0.6.0` tasks.

MCP session recording and leak scanning do not change accepted promotion,
human review, verifier results, gate behavior, provider defaults, formal-link
semantics, or public KB policy.
