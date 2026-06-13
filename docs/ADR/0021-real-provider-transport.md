# ADR 0021: Real Provider Transport Boundary

Status: Accepted

Date: 2026-06-13

## Context

`v0.2.1` includes a provider-neutral gateway, deterministic fake provider,
OpenAI-compatible injected-transport path for mocked tests, provider
config-check/preview/fake-run CLI commands, and hosted-worker dispatch through
fake or mocked provider boundaries.

It does not include a built-in real hosted HTTP transport, hosted worker CLI
commands, provider MCP tools, or a provider `real-run` command. ADR 0020 sets
the post-`v0.2.1` direction: harden provider transport and agent workflows
without weakening accepted-knowledge, human-review, public/private, or CI
boundaries.

This ADR defines the first real transport boundary before implementation.

## Decision

The first real transport will be an OpenAI-compatible HTTP transport.

The transport must be optional, default-off, and unavailable unless the caller
explicitly configures it. It must not become the default provider path, and it
must not run in CI or default tests.

Real provider sends require all of these conditions:

1. Provider configuration selects the OpenAI-compatible real HTTP transport.
2. The provider is explicitly enabled.
3. A model id is explicitly configured or passed through the typed request.
4. Timeout and retry policy are explicit.
5. API key material is read from an environment variable or secret manager
   reference only.
6. The key value is never committed, serialized, logged, included in
   exceptions, or printed through CLI output.
7. A context-send preview exists for the exact issue/request scope.
8. The operator explicitly confirms send consent.
9. A network permission flag or equivalent policy gate is set.
10. Private KB context is sent only when `policy_mode=private_research`,
    `public_only=false`, and explicit private-context consent are all present.

The transport must return typed provider results or provider errors. It must
not raise expected operational failures as uncaught tracebacks.

## Capability Negotiation

Unsupported provider parameters must not be silently treated as successful.

The implementation must produce one of:

- a structured capability-negotiation result that records unsupported
  parameters and safe downgrades; or
- a typed provider error that blocks the call.

Safe downgrade is allowed only when policy explicitly permits it and the run
record preserves the downgrade. Unsupported tool use, unsupported hidden
reasoning capture, or unsupported private-context handling must fail closed.

## Failure Modes

The real transport must model these expected failure modes:

- timeout;
- cancellation;
- connection failure;
- TLS or certificate failure;
- DNS failure;
- rate limit;
- authentication failure;
- authorization failure;
- HTTP error status;
- provider-side structured error payload;
- invalid JSON;
- malformed model output;
- schema rejection;
- policy rejection;
- redaction failure;
- log write failure.

Failure status must be preserved as provider error or rejected output. It must
not be coerced into WorkerBundle success, verifier success, gate success,
human review, or accepted knowledge.

## Logging And Redaction

Run records may include:

- provider id;
- model id;
- policy mode;
- consent flags;
- public/private context flags;
- context-preview reference;
- request fingerprint;
- timeout/retry/cancellation metadata;
- latency;
- token and cost metadata when available;
- response validation status;
- redaction status;
- repository-local log paths.

Run records and logs must not include:

- API keys;
- bearer tokens;
- request authorization headers;
- full environment dumps;
- hidden reasoning;
- unapproved private context;
- raw private artifact text;
- unredacted provider response bodies unless a future explicit audit policy
  permits them.

If redaction cannot be applied, the result must fail closed rather than write
an unsafe run record.

## CLI Surface Requirements

This ADR does not add a real-run CLI command. A future real-run CLI, if added,
must be deliberately hard to trigger:

```text
cosheaf provider real-run --input-json <path> --provider openai-compatible --confirm-send --allow-network --json
```

That future command must fail closed when any required condition is missing:

- no `--confirm-send`;
- no explicit network permission;
- no configured/enabled provider;
- missing API key source;
- missing or stale context preview;
- private context without private-research policy and consent;
- unsupported provider parameters;
- malformed provider output.

It must write only redacted run records under ignored runtime paths such as
`.cosheaf/providers/`. It must not write draft or accepted artifacts directly.

## Test And CI Boundary

CI and default tests must not use live network, API keys, or real provider
accounts. Tests must use deterministic fake providers, injected mocked
transports, or local fake HTTP servers that do not leave the test process.

Tests for the real transport implementation must cover success, timeout,
cancellation, rate limit, HTTP error, authentication failure, invalid JSON,
malformed output, schema rejection, unsupported parameters, missing consent,
missing network permission, missing key, and redaction.

## Consequences

The implementation task after this ADR may add an optional transport object,
but it must not add a default real provider path, live-network CI, committed
secrets, direct accepted writes, or hidden review authority.

Any new public DTO fields, stable error codes, or CLI command names introduced
during implementation must update `context/INTERFACE_REGISTRY.md` in the same
PR.

## Non-Goals

This ADR does not:

- implement runtime code;
- add dependencies;
- add SDKs;
- add provider real-run CLI;
- add hosted worker CLI commands;
- add provider MCP tools;
- call real providers;
- authorize private-context sending by default;
- write accepted knowledge;
- mark AI/provider output as human review;
- change artifact schema, gates, verifier behavior, review policy, promotion
  policy, or public/private KB policy.
