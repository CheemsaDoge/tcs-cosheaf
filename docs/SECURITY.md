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
| Public context leaks private artifacts | Public provider previews include public scope only and policy filtering runs before ranking can include private results | `test_public_provider_preview_excludes_private_artifact`, `test_public_provider_preview_excludes_private_before_ranking_scores`, and `test_provider_preview_policy_matrix_allows_only_explicit_scopes` |
| Hosted provider receives private context by default | Private provider context requires private-research policy and explicit consent | `test_hosted_provider_private_context_requires_policy_and_consent` and `test_provider_preview_policy_matrix_denials_have_stable_error_codes` |
| Provider preview hides full-artifact pulls | Provider preview reports card count, full-artifact count, and content mode while keeping the implemented preview boundary metadata-only and cards-only | `test_provider_preview_policy_matrix_allows_only_explicit_scopes`, `test_provider_preview_cli_matrix_for_fake_and_openai_provider_metadata`, and `test_orchestrator_run_provider_fake_json_dispatches_hosted_workers` |
| Provider logs expose secrets | Provider output and run logs redact common secret values and secret-looking metadata keys, and generated provider logs can be scanned for leaked API keys, bearer tokens, environment dumps, hidden reasoning, unapproved private context, and absolute private paths | `test_provider_logs_redact_secret_values`, `test_synthetic_provider_log_leaks_are_detected`, `test_redacted_provider_log_shape_passes_scanner`, and `test_scanner_accepts_generated_redacted_provider_log` |
| Model output is malformed | Hosted worker output is rejected unless it validates as the expected structured payload | `test_malformed_provider_worker_output_is_rejected` |
| Prompt or tool instructions override governance | Provider output cannot request accepted writes or bypass policy | `test_provider_output_cannot_override_accepted_write_policy` |
| Promotion bypasses review/gate workflow | Direct accepted status movement is refused and promotion still requires review and gates | `test_promotion_remains_explicit_review_and_gate_gated` |
| Optional MCP exposes arbitrary shell | The MCP surface remains read-only and whitelist-based | `test_optional_mcp_surface_exposes_no_arbitrary_shell` |
| Real provider is triggered accidentally | Real transport must be default-off and require explicit provider config, context preview, send consent, and network permission | `test_http_transport_fails_closed_without_explicit_config_or_network` plus existing preview/consent tests |
| Real provider CLI is triggered accidentally | `provider real-run` must fail closed without `--confirm-send`, `--allow-network`, inline preview, endpoint/key config, an environment-provided key, and private-context consent when needed | `test_provider_real_run_requires_confirm_send`, `test_provider_real_run_requires_allow_network`, `test_provider_real_run_requires_inline_context_preview`, `test_provider_real_run_requires_config_and_api_key`, and `test_provider_real_run_requires_private_context_consent` |
| Real provider sends private context without approval | Private context requires private-research policy, `public_only=false`, and explicit private-context consent | `test_hosted_provider_private_context_requires_policy_and_consent` and context-policy preview tests |
| Real provider returns malformed or policy-violating output | Output must schema-validate and policy-validate before becoming WorkerBundle, draft, proposal, or review context | `test_http_transport_maps_network_invalid_json_and_malformed_output` plus existing hosted-worker validation tests |
| Real provider or transport fails operationally | Timeout, cancellation, rate limit, HTTP error, invalid JSON, schema rejection, and related failures must become typed provider errors or rejected outputs | `test_http_transport_maps_timeout_rate_limit_and_http_errors`, `test_gateway_maps_cancelled_transport_to_provider_error`, and no live provider tests in CI |
| Unsupported provider parameters are ignored silently | Capability negotiation must record unsupported parameters or return a blocking provider error | `test_openai_compatible_provider_reports_unsupported_parameters` |

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
- Real provider transport must additionally require an explicit
  context-preview reference, operator send consent, explicit network
  permission, configured provider/model/timeout policy, and an environment
  variable key source in the current implementation. Future secret-manager
  support would need its own explicit design and tests.
- Real API keys, tokens, raw secrets, hidden reasoning, or unredacted provider
  logs must not be committed.
- Real provider run records must fail closed if redaction cannot be applied.
- Optional MCP is an adapter over typed services. It must not expose arbitrary
  shell, environment dumps, arbitrary filesystem access, direct promotion,
  human-review marking, or accepted-path writes.

## Context-Send Matrix

Provider send previews enforce the current stable policy matrix before any
ranking result can be exposed to a provider path:

| Policy mode | `public_only` | Private consent | Preview scopes | Result |
| --- | --- | --- | --- | --- |
| `public` | `true` | `false` or `true` | `public` | allowed |
| `public` | `false` | `false` or `true` | none | `private_context_requires_policy` |
| `private_research` | `true` | `false` or `true` | `public` | allowed |
| `private_research` | `false` | `false` | none | `private_context_requires_consent` |
| `private_research` | `false` | `true` | `public`, `private` | allowed |

The v4 plan name `public_research` maps to the current serialized mode
`public`. `workspace` and `framework` cards are excluded from provider-send
previews unless a later explicit design changes the matrix. Preview output is
metadata-only: artifact IDs, card counts, full-artifact counts, content mode,
root scopes, token estimates, and risk flags. It must not include full artifact
statements, issue text, secrets, or provider credentials. Current provider
previews are expected to report `full_artifact_count=0` and
`content_mode=cards_only`; any future nonzero count must remain explicit,
audited, and policy-reviewed before it can be used for provider sending.

## CI Expectations

Security regressions must run with the normal test suite and require no network
or real provider credential. Tests may use the deterministic fake provider or
injected mocked transport only.

The optional OpenAI-compatible HTTP transport is tested with injected local
fixtures. CI must still use fake, injected mocked, or local non-live-network
fixtures. Live provider accounts, live provider network, and real API keys
remain outside default tests. Provider `real-run` CLI tests must mock or inject
the transport and must not contact a live provider.

Provider log leak-scanner tests use synthetic fixtures and generated redacted
run records only. The scanner is a regression guard for committed or generated
provider logs; it is not a substitute for provider redaction, context-send
policy, human review, validation, gates, or promotion checks.

If a security check cannot run, report it as unavailable or skipped with the
exact reason. Do not describe skipped security checks as passes.
