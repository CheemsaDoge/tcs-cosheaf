# Operator MCP

This is the operator-facing entrypoint for MCP documentation.

The implemented adapter and threat model are documented in
`docs/MCP_SERVER.md`. MCP is optional adapter access over whitelisted
service-layer operations. CLI and CI remain the reviewable oracle.

MCP `tools/call` arguments may include an optional `session_id`. When supplied,
the adapter records bounded operator-session event metadata under
`.cosheaf/operator-sessions/<session-id>/events.jsonl` after invoking the
existing whitelisted tool. Calls without `session_id` keep the previous
stateless behavior.

Recorded MCP session events include tool name, session mode, argument names
and counts, normalized status, bounded result summary, timestamp, and warning
codes. They do not store full context packs, full artifact YAML, provider
payloads, raw stdout/stderr, secrets, hidden reasoning, or private query text
in public-only sessions.

MCP must not expose arbitrary shell, arbitrary filesystem access, accepted
writes, promotion, human-review creation, verifier-result mutation, hosted
provider calls, private context leakage, or automatic proof authority.

For the CLI-first fallback path, use `docs/CODEX_OPERATOR_RUNBOOK.md` and
`docs/OPERATOR_WORKSPACE_DEMO.md`.
