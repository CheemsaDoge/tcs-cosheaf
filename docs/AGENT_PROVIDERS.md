# Agent Providers

This document defines the hosted provider gateway boundary for TCS-Cosheaf.
The current implementation includes a provider-neutral gateway core, a
deterministic fake path, an OpenAI-compatible adapter over an injected
transport for mocked tests, and provider CLI commands for configuration
checks, context-send previews, deterministic fake runs, and a role-specific
hosted worker service bridge. It does not add API keys, import hosted provider
SDKs, or make real hosted calls available by default.

## Current Status

Implemented today:

- provider-neutral model request, response, capability, and fake-provider
  contracts in `cosheaf.agent.model_provider`;
- agent-access DTOs and schemas for provider request/result/run-record shapes;
- provider context-send preview through
  `ContextSendPolicyService.provider_preview(...)`;
- `ProviderGateway` and `ModelCallService` for fake calls and
  OpenAI-compatible calls through injected transport only;
- `HostedWorkerService` for role-specific fake or mocked provider worker
  calls that validate output as WorkerBundle v2 or typed review-only
  sub-results;
- WorkerBundle v2 schema validation for provider `worker_bundle` outputs;
- timeout, retry, cancellation, and rate-limit result handling;
- provider run logs under `.cosheaf/providers/` with secret redaction and
  attempt, retry, unsupported-parameter, latency, token, and cost metadata;
- provider CLI commands for listing supported provider modes, checking
  configuration without printing secrets, previewing context-send payload
  shape, and running the deterministic fake provider;
- fake-provider and mocked OpenAI-compatible tests that run without network
  access or API keys.

Not implemented yet:

- built-in real OpenAI-compatible HTTP transport;
- hosted worker CLI commands;
- provider-backed orchestrator dispatch;
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

## Provider CLI

The current provider CLI surface is agent-facing and conservative:

- `cosheaf provider list --json` lists the currently supported CLI modes.
- `cosheaf provider config-check --json` checks provider configuration
  without printing secret values. It reports only whether an API-key
  environment variable is present.
- `cosheaf provider preview-send --issue <issue-id> --provider <provider>
  --json` previews the context-send payload shape without sending artifact
  text to a provider. The preview includes artifact count, root scopes,
  estimated token count, private-context inclusion, and risk flags.
- `cosheaf provider fake-run --input-json <path> --json` runs the
  deterministic fake provider and writes redacted provider logs under
  `.cosheaf/providers/`.

`fake-run` is allowed in CI and performs no hosted network call. There is no
`real-run` CLI command in this task. The only provider names accepted by the
current CLI are `fake` and `openai`; future names such as `anthropic`,
`google`, and `local` are model identifiers only until a later task implements
and tests their CLI/provider behavior. Unsupported provider names return the
stable `provider_unsupported` error code.

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

Public-mode calls may use public KB scope only. Private context may be sent
only when:

- policy mode is private research;
- `public_only=false`;
- the operator explicitly grants private-context consent;
- a provider send preview was generated;
- the preview exposes root scopes, artifact ids, estimated tokens, and risk
  flags.

The preview is a checkpoint, not authorization by itself. A real call still
requires policy and consent.

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

## OpenAI-Compatible Transport

The first hosted transport should be OpenAI-compatible and optional. It should
be tested through mocked transport by default, not through live network calls.
Unsupported parameters must be surfaced through capability negotiation or a
structured error, not silently treated as a successful request.

The current OpenAI-compatible adapter accepts an injected transport object. This
keeps CI deterministic and allows tests to exercise provider success, retry,
timeout, cancellation, rate-limit, error, metadata, and redaction paths without
network access. A real HTTP transport remains a separate explicitly configured
future task.

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
