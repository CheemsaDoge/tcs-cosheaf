# ADR 0019: Hosted Provider Gateway

## Status

Accepted

## Context

`v0.2.0` shipped a local-MVP baseline with deterministic retrieval, context
packs, local task/orchestrator dry-runs, fake provider contracts, evaluation,
optional verifier surfaces, and Git-backed knowledge governance. ADR 0015 and
ADR 0016 then corrected the post-release direction: CLI remains the first
agent interface, hosted provider workers are planned capability, and MCP is an
optional adapter rather than the primary path.

The project should not frame local-only execution as the permanent product
boundary. Local-only execution is still required as offline, CI, and fallback
mode, but real research workflows may need explicitly approved hosted model
workers. The risk is adding those workers before the safety boundary is clear.

Existing code already includes:

- provider-neutral request/response/capability models and a deterministic fake
  provider in `cosheaf.agent.model_provider`;
- agent-access DTOs for model calls and provider run records;
- `ContextSendPolicyService.provider_preview(...)`, which previews provider
  context without sending full text or calling a provider.

This ADR defines the hosted provider gateway design before implementation.

## Decision

Add a hosted provider gateway as planned, first-class capability for
`v0.2.1`, with these constraints:

1. Hosted API calls are supported by design, but never default-on.
2. Local-only mode remains fallback, offline, and CI/testing mode, not the
   product boundary.
3. The gateway abstracts OpenAI-compatible transports first and leaves room
   for future provider adapters.
4. Fake provider behavior remains mandatory for tests and default CI.
5. Private KB policy controls what context can be previewed or sent.
6. Provider output may become WorkerBundle, proposal, draft artifact, or
   review context only. It must never become accepted knowledge directly.
7. Logs must redact secrets and record safe provider/model/cost/latency
   metadata.
8. Provider send preview is mandatory before any real call that could include
   private KB context.

The provider gateway should be a service-layer boundary, not a direct CLI-only
implementation. CLI commands may call the service. Optional MCP tools, if added
later, must also call the service rather than shelling out.

## Gateway Contract

The future gateway should separate these steps:

```text
operator / CLI / orchestrator
  -> provider configuration check
  -> context-send preview
  -> policy and consent check
  -> provider capability negotiation
  -> model request dispatch
  -> structured response validation
  -> WorkerBundle/proposal/draft output
  -> validate/gate/review/promotion remain separate
```

The gateway must accept typed request objects and return typed result or error
objects. Expected denials must use stable error semantics rather than
tracebacks. Missing API keys, disabled providers, unavailable transports,
private-context policy denials, rate limits, timeouts, and malformed model
outputs are not passes.

## Provider Modes

### Fake

The fake provider is required in CI and default tests. It must:

- perform no network calls;
- require no secrets;
- return deterministic responses;
- preserve unsupported-parameter metadata;
- be suitable for worker-bundle and orchestration tests.

### OpenAI-Compatible

The first hosted transport should be OpenAI-compatible rather than tied to a
single SDK where possible. The transport must:

- be optional and default-off;
- require explicit configuration and an API key at runtime;
- avoid logging API keys, bearer tokens, request headers, or hidden reasoning;
- record provider id, model id, timeout, latency, status, token or cost
  metadata when available, and redaction state;
- support timeout and cancellation;
- report unsupported parameters through capability negotiation;
- validate structured WorkerBundle/proposal output before returning it to an
  orchestrator or CLI caller.

### Future Providers

Additional adapters may be added later only behind the same gateway contract.
Provider-specific features must not change knowledge governance. If a provider
does not support a requested option, the gateway must drop it only when policy
allows that fallback and must record the downgrade.

## Context And Privacy Policy

Public-mode provider calls may use public-scope context only. Private KB
context requires all of the following:

1. policy mode allows private research context;
2. `public_only=false`;
3. explicit operator consent for private-context use;
4. provider send preview was generated immediately before the call;
5. preview labels artifact ids, root scopes, estimated token counts, and risk
   flags;
6. logs avoid full private artifact text unless a future explicit audit policy
   allows it.

Provider send preview is not a provider call and does not authorize a provider
call by itself. It is a required checkpoint before a private-context call can
be considered.

## Output Discipline

Provider output is untrusted. It may be stored only as:

- WorkerBundle or reducer-oriented output;
- draft proposal;
- draft artifact through controlled write paths;
- review context or review request that is not human review.

Provider output must not:

- write directly to `kb/accepted/`;
- mark `review.state: human_reviewed`;
- modify verifier results;
- change gate verdicts;
- run accepted promotion;
- bypass validation, gate, human review, or explicit promotion.

Validation and gate success remain evidence for review. AI/provider review is
not human review. Skipped or unavailable provider results are not passes.

## Logging And Redaction

Provider run records and logs should record enough metadata for audit without
capturing secrets:

- provider id and model id;
- request fingerprint rather than raw prompt where possible;
- policy mode, public/private flags, and consent state;
- provider status, latency, timeout, retry count, and cancellation state;
- token usage, cost estimate, or unavailable markers when the provider exposes
  them;
- response validation status and output target kind;
- redaction status.

Logs must not include API keys, bearer tokens, credentials, full environment
dumps, hidden reasoning, or unapproved private context.

## Consequences

Provider gateway implementation should proceed after this ADR in small PRs:

1. provider gateway core with fake and mocked OpenAI-compatible transport;
2. provider CLI commands for config check, preview-send, and fake-run;
3. hosted worker contracts using validated WorkerBundle output;
4. orchestration integration behind explicit policy and consent;
5. regression tests for secrets, private-context policy, malformed output, and
   no-real-network CI behavior.

Documentation should describe local-only mode as fallback/testing mode. It
should not describe hosted providers as production-ready or default-enabled.

## Non-Goals

This ADR does not:

- implement provider runtime code;
- add an SDK dependency;
- add CLI commands;
- add real hosted API calls;
- require API keys in tests or CI;
- add MCP provider tools;
- change artifact schema, gate behavior, verifier behavior, or promotion
  policy;
- permit accepted writes or AI human-review spoofing;
- claim automatic theorem proving, Lean semantic alignment, or production
  hosted multi-agent operation.
