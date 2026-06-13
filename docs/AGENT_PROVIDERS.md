# Agent Providers

This document defines the hosted provider gateway boundary for TCS-Cosheaf.
The current implementation includes a provider-neutral gateway core, a
deterministic fake path, an OpenAI-compatible adapter over an injected
transport for mocked tests, an optional stdlib OpenAI-compatible HTTP
transport object, and provider CLI commands for configuration checks,
context-send previews, deterministic fake runs, and a role-specific hosted
worker service bridge. It does not add API keys, import hosted provider SDKs,
or make real hosted calls available by default. The explicit provider
`real-run` command exists, but it is intentionally hard to trigger and remains
outside demos and CI.

## Current Status

Implemented today:

- provider-neutral model request, response, capability, and fake-provider
  contracts in `cosheaf.agent.model_provider`;
- agent-access DTOs and schemas for provider request/result/run-record shapes;
- provider context-send preview through
  `ContextSendPolicyService.provider_preview(...)`;
- `ProviderGateway` and `ModelCallService` for fake calls and
  OpenAI-compatible calls through explicitly injected transport only;
- `OpenAICompatibleHttpTransport`, an optional stdlib HTTP transport object
  that is inert unless an operator explicitly configures and injects it;
- `HostedWorkerService` for role-specific fake or mocked provider worker
  calls that validate output as WorkerBundle v2 or typed review-only
  sub-results;
- WorkerBundle v2 schema validation for provider `worker_bundle` outputs;
- timeout, retry, cancellation, and rate-limit result handling;
- provider run logs under `.cosheaf/providers/` with secret redaction and
  attempt, retry, unsupported-parameter, latency, token, and cost metadata;
- provider log leak scanning helpers in `cosheaf.security.provider_logs` for
  deterministic regression checks over generated run records;
- provider CLI commands for listing supported provider modes, checking
  configuration without printing secrets, previewing context-send payload
  shape including card/full-artifact counts, running the deterministic fake
  provider, and running one explicit OpenAI-compatible real provider call when
  all consent/network/config gates are satisfied;
- explicit orchestrator dispatch to role-specific hosted workers through
  `cosheaf orchestrator run --issue <issue-id> --provider <provider>`;
- fake-provider, mocked OpenAI-compatible, and stdlib HTTP-transport tests that
  run without live provider network access or API keys.

Not implemented yet:

- hosted worker CLI commands;
- provider MCP tools.

## Direction

Hosted API calls are planned and supported by design. Local-only execution is
the fallback, offline, and CI/testing mode; it is not the permanent product
boundary.

The provider gateway must preserve the existing knowledge-governance boundary:

- accepted knowledge still requires validation, gates, human review where
  required, and explicit promotion;
- provider output can become WorkerBundle, draft proposal, draft artifact, or
  review context only;
- AI/provider review is not human review;
- skipped or unavailable provider results are not passes;
- public/private KB scope metadata must remain visible.

## Provider Gateway Flow

The intended flow is:

```text
configuration check
  -> context-send preview
  -> policy and consent check
  -> capability negotiation
  -> model call
  -> response validation
  -> WorkerBundle/proposal/draft output
  -> ordinary validate/gate/review/promotion
```

The gateway is the service-layer boundary. Current CLI commands expose safe
inspection, preview, and fake-run paths. The hosted worker service now uses
the same gateway for fake and mocked provider calls, and optional MCP adapters
may wrap the same services later. The gateway must not bypass validation,
gates, review, reducer logic, or promotion.

## Hosted Worker Bridge

`HostedWorkerService` connects role contracts to provider calls without making
provider output a source of truth. It supports these roles:

- `reasoner`
- `verifier`
- `counterexampleer`
- `explorer`
- `formalizer`
- `librarian_summarizer`

Roles that map directly to protocol `WorkerType` return WorkerBundle v2:
`reasoner`, `verifier`, `counterexampleer`, and `formalizer`. Roles without a
direct bundle role return typed review-only sub-results: `explorer` and
`librarian_summarizer`.

WorkerBundle v2 preserves review-only research state, including assumptions,
uncertainty, verification requests, failed attempts, candidate
counterexamples, dependency questions, risk flags, and next steps.
Verification requests are not verifier results, and candidate counterexamples
are not accepted refutations. Reducers keep these fields as labeled review
warnings; they do not update accepted knowledge, mark review state, or promote
artifacts.

Role contracts now make those expectations explicit in provider prompts:
reasoners separate conjectures, proof ideas, and assumptions; verifiers
separate natural-language concerns from tool results; counterexampleers
separate candidates from verified counterexamples; formalizers separate symbol
resolution from semantic alignment; and librarian summarizers must not invent
claims.

The service returns `HostedWorkerOutput` instead of raising for expected
provider or validation failures. Invalid provider output is rejected with
`provider_output_validation_failed`. Unsafe authority claims are rejected with
`hosted_worker_policy_violation`, including verifier claims that mark accepted
or human-reviewed state, reasoner claims that turn conjectures into theorems,
and formalizer claims that Lean checked semantic alignment.

This bridge writes provider audit logs through the gateway under
`.cosheaf/providers/`, but it does not write proposed artifacts, write accepted
knowledge, create human review records, promote artifacts, or run a real
hosted network transport by itself.

## Orchestrator Hosted-Worker Dispatch

`cosheaf orchestrator run` now has an explicit hosted-worker path:

- `cosheaf orchestrator run --issue <issue-id> --provider fake --json`
- `cosheaf orchestrator run --issue <issue-id> --provider openai-compatible
  --confirm-send --json`

The `fake` path is deterministic and performs no hosted network call. It plans
the issue, previews the context-send shape, dispatches planned nodes to
`HostedWorkerService`, writes provider run-record copies under
`.cosheaf/orchestrator/<issue-id>/runs/<run-id>/providers/`, writes hosted
WorkerBundle v2 manifests under the run-local `bundles/` directory, writes
typed sub-results under `typed-results/`, and reduces only validated
WorkerBundle outputs.

The `openai-compatible` path is configurable but not default-runnable. It
requires `--confirm-send`, still goes through context-preview and consent
checks, and requires an injected or configured provider transport. The default
CLI path does not instantiate the stdlib HTTP transport and does not make a
network call in CI.

The hosted-worker orchestrator path never writes accepted knowledge, never
marks human review, never promotes artifacts, and does not treat provider
output as validation, gate, verifier, or human-review success.

## Provider CLI

The current provider CLI surface is agent-facing and conservative:

- `cosheaf provider list --json` lists the currently supported CLI modes.
- `cosheaf provider config-check --json` checks provider configuration
  without printing secret values. It reports only whether an API-key
  environment variable is present.
- `cosheaf provider preview-send --issue <issue-id> --provider <provider>
  --json` previews the context-send payload shape without sending artifact
  text to a provider. The preview includes artifact count, card count,
  full-artifact count, content mode, root scopes, estimated token count,
  private-context inclusion, and risk flags. Current provider previews are
  metadata-only and cards-only, so `full_artifact_count=0` and
  `content_mode=cards_only` are expected for the implemented provider-send
  boundary.
- `cosheaf provider fake-run --input-json <path> --json` runs the
  deterministic fake provider and writes redacted provider logs under
  `.cosheaf/providers/`.
- `cosheaf provider real-run --input-json <path> --provider openai-compatible
  --confirm-send --allow-network --json` runs one explicit OpenAI-compatible
  provider call from an input envelope with inline `context_preview` and
  `provider_config`. It writes redacted provider logs under
  `.cosheaf/providers/` and fails closed without send confirmation, network
  permission, inline preview, endpoint/API-key environment configuration, an
  environment-provided key, or required private-context consent.
- `cosheaf orchestrator run --issue <issue-id> --provider fake --json`
  runs the explicit hosted-worker orchestrator path with the deterministic
  fake provider.
- `cosheaf orchestrator run --issue <issue-id> --provider openai-compatible
  --confirm-send --json` uses the explicit OpenAI-compatible hosted-worker
  dispatch boundary only when a transport is configured or injected; the
  default CLI path reports missing transport rather than making a network call.

`fake-run` is allowed in CI and performs no hosted network call. `real-run`
is not allowed in CI/default tests with a live provider; its tests use mocked
transport injection. The only provider names accepted by the current provider
CLI are `fake` and `openai` for inspection/fake paths, plus
`openai-compatible` for the real-run command; `orchestrator run --provider`
accepts `fake`, `openai`, and `openai-compatible` as the explicit hosted-worker
dispatch names. Future names such as `anthropic`, `google`, and `local` are
model identifiers only until a later task implements and tests their
CLI/provider behavior. Unsupported provider names return the stable
`provider_unsupported` error code.

## Configuration Rules

Real hosted calls must be:

- default-off;
- explicitly configured;
- scoped by provider id, model id, timeout, retry policy, and context policy;
- unavailable when required credentials are missing;
- disabled in CI and default tests;
- fake or mocked in tests.

Configuration checks must never print secret values. They may report whether a
required secret is present, missing, or malformed.

## Context Policy

Provider calls must use the smallest issue-scoped context that satisfies the
worker role.

Public-mode calls may use public KB scope only. The v4 plan calls this
`public_research`; the current stable serialized value remains `public` for
backward compatibility. Private context may be sent only when:

- policy mode is private research;
- `public_only=false`;
- the operator explicitly grants private-context consent;
- a provider send preview was generated;
- the preview exposes root scopes, artifact ids, estimated tokens, card count,
  full-artifact count, content mode, and risk flags.

The preview is a checkpoint, not authorization by itself. A real call still
requires policy and consent.

The current provider-send preview matrix is deliberately conservative:

| Policy mode | `public_only` | Private consent | Allowed preview scopes | Denied code |
| --- | --- | --- | --- | --- |
| `public` | `true` | `false` or `true` | `public` | none |
| `public` | `false` | `false` or `true` | none | `private_context_requires_policy` |
| `private_research` | `true` | `false` or `true` | `public` | none |
| `private_research` | `false` | `false` | none | `private_context_requires_consent` |
| `private_research` | `false` | `true` | `public`, `private` | none |

`workspace` and `framework` scope cards are excluded from provider-send
previews by the current matrix. Provider previews are metadata only: they list
artifact IDs, card counts, full-artifact counts, content mode, root scopes,
token estimates, and risk flags, and they do not include full artifact
statements or issue text. A nonzero full-artifact count would be a review
signal that the send boundary has widened; the current implementation keeps
provider previews at zero full pulls.

## Output Rules

Provider output is untrusted. It may be used as:

- WorkerBundle output;
- draft proposal;
- controlled draft artifact write input;
- review context or informational review request.

Provider output must not:

- write directly to `kb/accepted/`;
- mark AI output as `human_reviewed`;
- change verifier results or gate reports;
- promote artifacts;
- copy private KB content into public KB;
- claim Lean, SAT, SMT, CSLib, mathlib, or theorem-proving success unless the
  relevant checker actually ran and recorded that result.

## Logging And Redaction

Provider run records should capture:

- provider and model id;
- policy mode and consent state;
- public/private context flags;
- request fingerprint;
- timeout, retry, cancellation, and latency metadata;
- token usage and cost estimate when available;
- response validation status;
- redaction status;
- repository-local log paths when logs are written.

Logs must not include API keys, bearer tokens, provider credentials, full
environment dumps, hidden reasoning, or unapproved private context.

The `cosheaf.security.provider_logs` scanner provides a deterministic
regression check for generated provider logs and run records. It reports stable
finding kinds for API-key-shaped values, bearer tokens, environment-like dumps,
secret-looking key/value pairs, hidden reasoning markers, unapproved private
context markers, and avoidable absolute user/workspace paths. Existing redacted
provider logs should scan cleanly; synthetic leaked fixtures should fail tests.

## OpenAI-Compatible Transport

The first hosted transport should be OpenAI-compatible and optional. It should
be tested through mocked transport by default, not through live network calls.
Unsupported parameters must be surfaced through capability negotiation or a
structured error, not silently treated as a successful request.

The current OpenAI-compatible adapter accepts an injected transport object. This
keeps CI deterministic and allows tests to exercise provider success, retry,
timeout, cancellation, rate-limit, error, metadata, and redaction paths without
live provider network access. `OpenAICompatibleHttpTransport` is the optional
stdlib HTTP implementation for OpenAI-compatible chat completions, but it is
not wired into any default CLI path.

ADR 0021 defines the real transport boundary. The stdlib HTTP transport is:

- optional and default-off;
- explicitly enabled through provider configuration and injection;
- unable to run in CI or default tests;
- configured with an explicit model id, endpoint URL, timeout, retry policy,
  context policy, and API-key environment variable;
- blocked until a context-send preview exists for the exact request scope;
- blocked until operator send consent and explicit network permission are both
  present;
- blocked from private context unless `policy_mode=private_research`,
  `public_only=false`, and explicit private-context consent are all present;
- tested through fake, mocked, or local non-live-network fixtures by default;
- unable to write accepted knowledge, mark human review, promote artifacts, or
  turn provider output into verifier/gate success.

Expected real-transport failures must be structured provider errors or
rejected output, not uncaught tracebacks and not passes. Required failure modes
include timeout, cancellation, connection/TLS/DNS failures, rate limits,
authentication and authorization failures, HTTP errors, provider structured
errors, invalid JSON, malformed model output, schema rejection, policy
rejection, redaction failure, and log-write failure.

For `worker_bundle` outputs, malformed JSON or schema-invalid WorkerBundle v2
payloads return `provider_output_validation_failed`. When the configured retry
budget permits it, the OpenAI-compatible gateway may make one deterministic
output-validation retry with an added schema reminder. The retry is logged with
`output_validation_retry_count`, `output_validation_retry_code`,
`output_validation_retry_status`, and
`output_validation_retry_final_status`. A retry never coerces malformed output
into draft artifacts, accepted artifacts, verifier results, human review, or
promotion.

Run records may store provider/model id, policy and consent flags, context
preview reference, request fingerprint, timeout/retry/cancellation metadata,
latency, token/cost metadata when available, response validation status,
redaction status, and repository-local log paths. They must not store API
keys, bearer tokens, authorization headers, full environment dumps, hidden
reasoning, unapproved private context, raw private artifact text, or
unredacted provider responses unless a later explicit audit policy permits
that content.

The provider `real-run` command is hard to trigger and fails closed without
explicit send confirmation, explicit network permission, valid
configuration/key, inline context preview, and required public/private context
consent. It does not write draft or accepted artifacts directly from raw
provider output.

## Fake Provider Requirement

Every provider workflow must be testable with the fake provider. Fake-provider
tests are the default safety net for CI and local development because they:

- need no API key;
- make no network call;
- produce deterministic output;
- keep provider behavior from becoming a truth source.

## Non-Goals

This document does not authorize:

- default-on hosted API calls;
- CI that requires network access or API keys;
- direct accepted writes;
- AI review as human review;
- provider access to private KB context without policy and consent;
- provider logs containing secrets or unapproved private content;
- production hosted multi-agent operation.
