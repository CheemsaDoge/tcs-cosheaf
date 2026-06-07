# ADR 0013: Provider-Neutral Worker Model Interface

## Status

Accepted

## Context

The agent harness now has local task records, deterministic context packs, a
local worker runner, an orchestrator state-machine contract, and a local-only
dry-run workflow. Future worker implementations may need model-provider calls,
but adding hosted providers directly would weaken the current safety boundary:

- hosted LLM workers are default-off;
- tests must not require network access, API keys, or hosted models;
- worker output is review context, not accepted knowledge;
- gates, verifier adapters, human review, and promotion remain explicit;
- unsupported provider parameters must be recorded, not hidden.

The risky alternative is to design worker code around one hosted provider SDK
first. That would make fake-provider testing harder and would blur provider
capabilities with orchestration semantics.

## Decision

Define a small provider-neutral Python API under
`cosheaf.agent.model_provider` before adding any real provider adapter.

The interface contains:

- `ModelRequest`
- `ModelResponse`
- `ProviderCapability`
- `ProviderName`
- `ModelProvider`
- `FakeModelProvider`

`ModelRequest` carries the provider-neutral config fields:

- `provider`
- `model`
- `temperature`
- `top_p`
- `reasoning_effort`
- `max_output_tokens`
- `tool_policy`
- `network_policy`

`FakeModelProvider` is the only implementation in this task. It returns a
deterministic local response, performs no network calls, imports no hosted
provider SDK, and records unsupported requested parameters in
`ProviderCapability.unsupported_parameters`.

## Consequences

Future worker contracts can depend on stable request, response, and capability
objects without choosing a hosted provider. Tests can exercise model-dependent
flows deterministically with the fake provider.

Provider capability negotiation is explicit. Unsupported parameters such as
temperature, top-p, reasoning effort, non-none tool policy, or explicit network
allowance can be surfaced as metadata instead of crashing or silently becoming
provider truth.

The fake provider is not a model-quality substitute. It is a deterministic test
and dry-run boundary.

## Non-Goals

- Do not add OpenAI, Anthropic, Google, local-model, or other provider SDKs.
- Do not add hosted model execution.
- Do not add API-key handling or provider credentials.
- Do not connect the orchestrator runner to hosted LLMs.
- Do not add network access.
- Do not run tools from model-provider requests.
- Do not write artifacts, reviews, gate reports, or accepted knowledge.
- Do not change gate, verifier, promotion, or public/private KB semantics.
- Do not claim automatic theorem proving or Lean/mathlib/CSLib checking.

## Follow-Up Requirements

Future hosted-provider PRs must remain separate issue/branch/PR units. They
must be opt-in, default-off, fake-provider-testable, and must record provider
capabilities, unsupported parameters, network policy, tool policy, command or
API metadata, errors, and skipped/unavailable states without weakening gates,
review, verifier, or promotion boundaries.
