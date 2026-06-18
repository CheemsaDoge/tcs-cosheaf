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
| Failure memory is used as authority or leaks private context | Failure-log writes reject human-review, verifier-pass, checked-counterexample, accepted-status, and accepted-path claims; public-only context excludes private failure-log text | `test_failure_log_add_rejects_authority_claim_fields`, `test_failure_log_add_rejects_accepted_evidence_path`, `test_provider_origin_failure_log_cannot_claim_accepted_status`, and `test_public_only_context_excludes_private_failure_log_text` |
| Optional MCP exposes arbitrary shell | The MCP surface remains read-only and whitelist-based | `test_optional_mcp_surface_exposes_no_arbitrary_shell` |
| Real provider is triggered accidentally | Real transport must be default-off and require explicit provider config, context preview, send consent, and network permission | `test_http_transport_fails_closed_without_explicit_config_or_network` plus existing preview/consent tests |
| Real provider CLI is triggered accidentally | `provider real-run` must fail closed without `--confirm-send`, `--allow-network`, inline preview, endpoint/key config, an environment-provided key, and private-context consent when needed | `test_provider_real_run_requires_confirm_send`, `test_provider_real_run_requires_allow_network`, `test_provider_real_run_requires_inline_context_preview`, `test_provider_real_run_requires_config_and_api_key`, and `test_provider_real_run_requires_private_context_consent` |
| Real provider sends private context without approval | Private context requires private-research policy, `public_only=false`, and explicit private-context consent | `test_hosted_provider_private_context_requires_policy_and_consent` and context-policy preview tests |
| Real provider returns malformed or policy-violating output | Output must schema-validate and policy-validate before becoming WorkerBundle, draft, proposal, or review context | `test_http_transport_maps_network_invalid_json_and_malformed_output` plus existing hosted-worker validation tests |
| Real provider or transport fails operationally | Timeout, cancellation, rate limit, HTTP error, invalid JSON, schema rejection, and related failures must become typed provider errors or rejected outputs | `test_http_transport_maps_timeout_rate_limit_and_http_errors`, `test_gateway_maps_cancelled_transport_to_provider_error`, and no live provider tests in CI |
| Unsupported provider parameters are ignored silently | Capability negotiation must record unsupported parameters or return a blocking provider error | `test_openai_compatible_provider_reports_unsupported_parameters` |
| Checked counterexample evidence is used as authority or leaks private context | Controlled checked-evidence staging rejects authority claims, accepted paths, and path traversal; public-only context excludes private checked-evidence text | `test_checked_evidence_stage_rejects_authority_claim_fields`, `test_checked_evidence_stage_rejects_accepted_evidence_path`, `test_checked_evidence_stage_rejects_path_traversal`, and `test_public_only_context_excludes_private_checked_evidence_text` |
| Research-run records spoof review/promotion authority or store unsafe data | Research-run append paths reject authority claims, unsafe paths, and secret-looking summaries; run records remain provenance only | `test_research_run_append_output_rejects_authority_claims` and `test_research_run_rejects_unsafe_paths_and_secret_summaries` |
| Operator-session records leak secrets or private/public boundary data before handoff | Operator-session scan reports block on secrets, environment dumps, hidden reasoning, provider payloads, accepted-write attempts, authority claims, absolute private paths, and public-only private references | `test_operator_session_scan_clean_session_writes_runtime_report`, `test_operator_session_scan_detects_public_only_leaks_and_blocks_handoff`, and `test_operator_session_scan_missing_session_returns_structured_error` |
| Operator handoff hides scanner blockers, skipped checks, or missing checks | Handoff build runs the scanner first, fails closed on blockers, preserves skipped as skipped, and records missing check kinds | `test_operator_handoff_builds_review_context_bundle`, `test_operator_handoff_fails_closed_when_scan_has_blockers`, and `test_operator_handoff_requires_finalized_session` |
| Operator handoff export is mistaken for human review or writes outside review context | Export writes only `reviews/operator/` YAML, dry-run writes nothing, accepted targets are rejected, and blocked scanner status fails closed | `test_operator_handoff_export_dry_run_reports_target_without_writing`, `test_operator_handoff_export_writes_review_context_yaml`, `test_operator_handoff_export_rejects_accepted_write_target`, and `test_operator_handoff_export_fails_closed_when_handoff_scanner_blocked` |
| Research loop claims accepted/promotion/human-review authority | Loop models carry authority notice; attempts reject accepted KB paths and authority-overclaim fields; loop statuses are runtime-only; no verifier/human-review/promotion authority is granted | `test_authority_overclaim_rejected`, `test_accepted_path_rejected`, and `test_invalid_status_transition_after_finalize` |
| Research loop storage leaks private data or bypasses Git ignore | Loop/attempt storage and scan reports stay under ignored `.cosheaf/research-loops/`; public mode rejects private content; the loop scanner blocks secrets, private public-mode material, provider payloads, accepted-write attempts, hidden reasoning, and authority claims | `test_public_mode_rejects_private_refs`, `test_storage_paths_are_deterministic`, `test_research_loop_scan_blocks_leaks_and_reports_metrics`, and `test_research_loop_scan_service_clean_loop` |
| Campaign output is mistaken for proof, review, or acceptance | Campaign models carry authority notices; attempts and imported operator results reject accepted KB paths, public-mode private references, hidden-reasoning fields, and authority-overclaim fields; campaign scans fail closed on unsafe runtime output and the budget controller reports no shell/provider/accepted writes; runtime storage stays under ignored `.cosheaf/campaigns/` | `tests/test_campaigns.py` |
| Reviewable workflow output is mistaken for proof, review, or acceptance | Workflow records, draft proposals, scanner reports, and handoff packets carry authority notices and remain review context only; they do not create accepted knowledge, human review, verifier pass, gate pass, source metadata, accepted refutation, or promotion authority | `tests/test_workflow.py` and `tests/test_workflow_handoff.py` |
| Workflow handoff hides leaks, source fabrication, authority claims, or skipped-result ambiguity | Workflow handoff build scans runtime inputs first, scan fails closed on blocking findings, export reruns the scanner, and skipped workflow results remain warning/non-pass evidence | `test_workflow_handoff_build_show_scan_and_export_dry_run`, `test_workflow_handoff_scan_blocks_private_leakage`, `test_workflow_handoff_scan_blocks_accepted_write_attempt`, `test_workflow_handoff_scan_blocks_human_review_overclaim`, `test_workflow_handoff_scan_blocks_source_metadata_fabrication`, and `test_workflow_handoff_preserves_skipped_not_pass_warning` |
| Checker results are mistaken for proof, review, or acceptance | Checker run records carry authority notices, `skipped` remains non-pass, policy checkers block private leaks and overclaims, and `python_local_check` only runs explicit repository-local Python scripts | `tests/test_checker_registry.py` and `tests/test_checker_cli.py` |
| Workflow cross-check or gap reports are mistaken for proof, review, source metadata, accepted status, or promotion | Cross-check reports carry explicit non-authority fields, authority-scanner guards block overclaims, exports stay under `reviews/workflow/`, handoff bundles include review gaps only, and gap reports mark gaps as advisory review guidance | `tests/test_workflow_crosscheck.py` |

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
- Research loop records are review context only. Loop attempts must not write
  `kb/accepted/`, create human review, mutate verifier results, mark gate
  pass, or claim promotion authority. Structured failure memory is research
  memory, not proof, accepted evidence, verifier pass, checked counterexample
  evidence, human review, gate success, accepted status, or promotion evidence.
  Public-only loop attempts must not expose private references.
- Research-loop operator task packets and imported operator results are
  review context only. They must reject accepted-write references,
  hidden-reasoning fields, true claimed authority flags, human-review claims,
  verifier-pass claims, gate-pass claims, and promotion claims. `run --dry-run`
  must not write source-of-truth files, and non-dry-run loop execution remains
  refused until an explicit deterministic implementation exists.
- Research-loop attempt memory and scan reports are runtime review context
  only. Attempt-memory indexes must stay under ignored `.cosheaf/` paths and
  cannot become proof, source metadata, human review, verifier pass, gate pass,
  accepted status, accepted refutation, or promotion authority. Loop scans must
  fail closed on blocking findings before any future handoff export path.
- Campaign records, attempts, scorecards, and event logs are runtime review
  context only. They stay under ignored `.cosheaf/campaigns/` paths and cannot
  become proof, source metadata, human review, verifier pass, gate pass,
  accepted status, accepted theorem/refutation status, or promotion authority.
  Campaign attempts must reject accepted KB paths and public-only private
  references.
- Campaign operator task packets and imported operator results are runtime
  review context only. `operator_task_v2` packets are bounded instructions for
  an external operator; `operator_result_v2` packets must keep authority claims
  false and must reject accepted KB writes, unsafe paths, public-only private
  references, hidden reasoning, human-review claims, verifier/gate pass claims,
  accepted-status or accepted-refutation claims, and promotion claims. The
  current campaign surface includes deterministic pause/resume, runtime scan,
  budget-controller commands, review handoff export, and deterministic campaign
  eval fixtures, but it does not run provider calls, execute shell commands, or
  write accepted KB content. Campaign handoffs and eval reports are review or
  regression context only.
- Reviewable workflow records are review context only. Persistent workflow
  runtime storage, `workflow show`, persisted `workflow step`, bounded
  `workflow run`, readiness reports, draft proposals, workflow handoff packets,
  handoff scans, and handoff exports must not be treated as proof, source
  metadata, human review, verifier pass, gate pass, accepted status, accepted
  refutation, or promotion authority. Future eval work must preserve the same
  boundary.
- Workflow handoff scan reports are runtime review metadata only. They must
  fail closed on accepted-write attempts, private leakage, hidden reasoning,
  provider payload dumps, secrets/env dumps, human-review overclaims,
  verifier/gate pass overclaims, source-metadata fabrication, and accepted
  theorem/refutation claims without promotion. They do not create human review,
  verifier pass, gate pass, accepted status, source metadata, or promotion
  authority.
- Workflow handoff export is explicit review context only. It writes under
  `reviews/workflow/`, rejects accepted KB targets, reruns the handoff scanner,
  and does not create human review, promote artifacts, mutate verifier results,
  or mark accepted/refuted/proved status.
- Checker run records are runtime review context only. They are written under
  ignored `.cosheaf/checker-runs/` paths and do not create proof, source
  metadata, human review, verifier pass, gate pass, accepted status, accepted
  refutation, or promotion authority. Optional checker results such as SAT,
  SMT, or Lean availability must report missing tools as `skipped`, not pass.
  `python_local_check` is limited to explicit repository-local Python scripts
  and is not an arbitrary shell surface.
- Workflow cross-check reports and gap reports are review context only. They
  are written under ignored `.cosheaf/workflows/<workflow-id>/` runtime paths
  or explicit `reviews/workflow/` exports, and they must not create proof,
  source metadata, human review, verifier pass, gate pass, accepted status,
  accepted theorem/refutation status, or promotion authority. Checked-pass
  rows are not acceptance, skipped/inconclusive rows are not passes, and
  formalization or semantic-alignment gaps remain human-review questions.
- Checked counterexample evidence is review evidence only. It must not claim
  human review, accepted refutation, accepted status, verifier pass, gate pass,
  or promotion authority, and public-only context must not expose private
  checked-evidence text.
- Research-run records are provenance only. They must not store secrets,
  hidden reasoning, unsafe paths, authority-spoofing fields, accepted-write
  claims, or unapproved private KB text.
- Operator-session scan reports are runtime review metadata only. They must
  block handoff on detected leaks or authority claims, but they do not create
  human review, verifier pass, gate pass, accepted status, source metadata, or
  promotion authority.
- Operator handoff bundles are runtime review context only. They summarize
  finalized sessions, scanner status, check statuses, and references, but they
  do not export review records, create human review, promote artifacts, mutate
  verifier results, or mark accepted/refuted/proved status.
- Operator handoff export is explicit review context only. It writes under
  `reviews/operator/`, rejects accepted KB targets, and does not create human
  review, promote artifacts, mutate verifier results, or mark
  accepted/refuted/proved status.

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

Checked-evidence and research-run security regressions must remain local and
must not require hosted providers, API keys, MCP, network, SAT, SMT, Lean, or
lake. Skipped or unavailable optional-tool rows remain skipped, not pass.

Operator-session scanner tests use synthetic session/event fixtures only. The
scanner is a fail-closed guard before handoff; it is not a substitute for
validation, gates, source metadata, human review, or promotion checks.

Campaign tests use synthetic runtime fixtures only. Campaign scorecards,
operator task packets, imported operator results, scan reports, and budget
controller outputs are deterministic review context, not proofs, source
metadata, human review, verifier pass, gate pass, or accepted promotion
evidence.

Operator handoff tests use synthetic finalized-session fixtures only. Handoff
bundles are compact review context and are not a substitute for raw check
logs, validation, gates, source metadata, human review, or promotion checks.
Handoff export tests use synthetic handoff fixtures only and do not write
accepted KB content.

Workflow handoff tests use synthetic workflow runtime fixtures only. Handoff
bundles and scan reports are compact review context and are not substitutes
for raw workflow records, validation, gates, source metadata, human review, or
promotion checks. Handoff export dry-run writes nothing; non-dry-run export is
restricted to `reviews/workflow/` and must not write accepted KB content.

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
