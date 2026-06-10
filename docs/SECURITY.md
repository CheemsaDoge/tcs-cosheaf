# Security

TCS-Cosheaf is a local, Git-backed research knowledge system. Its agent-facing
surfaces must preserve the same review, gate, verifier, public/private, and
promotion boundaries as ordinary repository work.

## Agent-Access Threat Model

The regression suite in `tests/security/` maps these threats to executable
checks:

| Threat | Required boundary | Regression coverage |
| --- | --- | --- |
| Agent writes accepted knowledge directly | Controlled draft-write commands reject accepted status and accepted paths | `test_cli_draft_write_rejects_accepted_status` |
| Agent writes into readonly public KB | Controlled draft/source-note writes reject readonly roots | `test_cli_draft_write_rejects_readonly_public_root` |
| Public context leaks private artifacts | Public provider previews include public scope only | `test_public_provider_preview_excludes_private_artifact` |
| Hosted provider receives private context by default | Private provider context requires private-research policy and explicit consent | `test_hosted_provider_private_context_requires_policy_and_consent` |
| Provider logs expose secrets | Provider output and run logs redact common secret values and secret-looking metadata keys | `test_provider_logs_redact_secret_values` |
| Model output is malformed | Hosted worker output is rejected unless it validates as the expected structured payload | `test_malformed_provider_worker_output_is_rejected` |
| Prompt or tool instructions override governance | Provider output cannot request accepted writes or bypass policy | `test_provider_output_cannot_override_accepted_write_policy` |
| Promotion bypasses review/gate workflow | Direct accepted status movement is refused and promotion still requires review and gates | `test_promotion_remains_explicit_review_and_gate_gated` |
| Optional MCP exposes arbitrary shell | The MCP surface remains read-only and whitelist-based | `test_optional_mcp_surface_exposes_no_arbitrary_shell` |

## Hard Boundaries

- No agent, provider, worker, or optional MCP surface may write directly to
  `kb/accepted/`.
- Accepted knowledge enters through explicit review, validation, gates, and
  `cosheaf artifact promote`.
- Validation, gate, provider, MCP, verifier, Lean, SAT, SMT, or retrieval
  output is not human review.
- Skipped or unavailable verifier/provider/tool results are not passes.
- Public-mode retrieval, context, provider preview, and optional MCP resources
  must not include private artifact IDs, private artifact text, private-derived
  summaries, credentials, or secrets.
- Hosted-provider paths must be default-off, explicit, policy-scoped, and
  fake or mocked in tests.
- Real API keys, tokens, raw secrets, hidden reasoning, or unredacted provider
  logs must not be committed.
- Optional MCP is an adapter over typed services. It must not expose arbitrary
  shell, environment dumps, arbitrary filesystem access, direct promotion,
  human-review marking, or accepted-path writes.

## CI Expectations

Security regressions must run with the normal test suite and require no network
or real provider credential. Tests may use the deterministic fake provider or
injected mocked transport only.

If a security check cannot run, report it as unavailable or skipped with the
exact reason. Do not describe skipped security checks as passes.
