# Operator Handoff Bundles

Operator handoff bundles are the `v0.6.0` review-context summary layer for
finalized operator sessions. They let a maintainer inspect one compact runtime
bundle instead of reading raw session and MCP event transcripts.

## Authority Boundary

Handoff bundles are review context only. They are not:

- proof;
- verifier evidence;
- verifier pass;
- gate pass;
- source metadata;
- human review;
- accepted status;
- accepted refutation; or
- promotion authority.

The handoff model carries explicit false authority fields:

- `accepted_write_performed: false`
- `human_review_created: false`
- `promotion_performed: false`
- `verifier_result_mutated: false`

Validation, gate, test, eval, scanner, MCP, provider, Lean, SAT, SMT, and
network results must still be inspected from the command or tool that actually
ran them. Skipped checks remain skipped and are not passes.

## Runtime Storage

Build writes a runtime bundle under ignored `.cosheaf/` storage:

```text
.cosheaf/operator-sessions/<session-id>/handoff.json
```

The deterministic handoff ID is:

```text
handoff.<session-id>
```

This runtime bundle should not be committed by default. Explicit
review-context export writes to:

```text
reviews/operator/<handoff-id>.yaml
```

That export is persisted review context only. It is not human review.

## CLI Surface

Build a handoff from one finalized session:

```bash
cosheaf operator handoff build --session <session-id> --json
```

Show a previously built handoff:

```bash
cosheaf operator handoff show <handoff-id> --json
```

Preview the review-context export target without writing:

```bash
cosheaf operator handoff export --handoff <handoff-id> --dry-run --json
```

Persist explicit review-context YAML:

```bash
cosheaf operator handoff export --handoff <handoff-id> --json
```

The build command first runs the operator-session leak scanner. Blocking
scanner findings fail closed with a structured error and prevent handoff
creation.

The export command also fails closed if the handoff bundle contains blocking
scanner status. Non-dry-run export writes only under `reviews/operator/` and
rejects accepted KB targets.

## Bundle Contents

The bundle includes:

- session ID and issue ID;
- policy mode and session status;
- configured KB root names, paths, readonly flags, and priorities;
- referenced repository-local files;
- referenced draft artifact IDs;
- referenced source-note paths;
- referenced review-context records;
- validation, gate, test, and eval check statuses;
- missing check accounting;
- skipped check accounting, explicitly not pass;
- bounded MCP/CLI tool summary counts;
- scanner finding counts and report path;
- human-review checklist;
- known limitations;
- follow-up recommendations; and
- the operator-session authority notice.

The bundle does not copy full private artifact text, raw provider payloads,
hidden reasoning, environment dumps, API keys, or arbitrary stdout/stderr.

## Current Limitations

Handoff export does not create human review. It writes review-context YAML
only. Human review, accepted promotion, verifier evidence, gate behavior,
provider defaults, formal-link semantics, public KB policy, and workspace root
semantics remain unchanged.

The ecosystem smoke matrix now includes framework operator-session CLI and
handoff dry-run rows, plus downstream workspace-template and public-KB policy
rows. These rows are release-readiness checks only. They do not turn handoff
records into source metadata, human review, verifier evidence, accepted
status, accepted refutation, or promotion authority.
