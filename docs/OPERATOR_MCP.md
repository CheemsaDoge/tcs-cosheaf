# Operator MCP

This is the operator-facing entrypoint for MCP documentation.

The implemented adapter and threat model are documented in
`docs/MCP_SERVER.md`. MCP is optional adapter access over whitelisted
service-layer operations. CLI and CI remain the reviewable oracle.

MCP must not expose arbitrary shell, arbitrary filesystem access, accepted
writes, promotion, human-review creation, verifier-result mutation, hosted
provider calls, private context leakage, or automatic proof authority.

For the CLI-first fallback path, use `docs/CODEX_OPERATOR_RUNBOOK.md` and
`docs/OPERATOR_WORKSPACE_DEMO.md`.
