# ADR 0016: Agent Access Architecture And Threat Model

## Status

Proposed

## Context

ADR 0015 records the post-`v0.2.0` direction change: TCS-Cosheaf should support
agent access through MCP, Skill guidance, and hosted API workers while keeping
the deterministic local workflow as the baseline. Before implementing service
extraction, MCP tools, provider transports, or hosted workers, the repository
needs a durable authority model and threat model.

The main risk is not that agents or hosted providers exist. The main risk is
letting any agent-access path bypass the repository's existing truth boundary:
Git-backed artifacts, validation, gates, human review where required, and
explicit accepted promotion.

## Decision

Adopt this agent-access architecture:

1. MCP is the primary external-agent machine interface.
2. Skill is an optional operator guide. It is not a source of truth and grants
   no permission by itself.
3. Hosted API provider support is a planned core worker capability.
4. CLI remains the human and CI oracle.
5. The future service layer is shared by CLI, MCP, internal orchestrator, and
   provider-backed workers.
6. Controlled writes are limited to draft, proposal, task, run, and bundle
   surfaces.
7. Accepted promotion remains outside agent authority.

## Architecture

The intended control flow is:

```text
human / CI
  -> CLI
  -> service layer
  -> storage / validation / gate / retrieval / context / task / verifier logic

external agent
  -> MCP tools and resources
  -> service layer
  -> same bounded logic

internal orchestrator
  -> service layer
  -> local workers or provider-backed workers
  -> worker bundles / reducer results / review context

hosted provider worker
  -> provider gateway
  -> explicit policy and consent boundary
  -> worker bundle / draft proposal / review context
```

The CLI is still the oracle used by humans and CI. MCP and provider paths
should reuse typed services rather than shelling out to the CLI as their core
implementation. The Skill package should describe how an operator or external
agent should use MCP and CLI safely, but repository files and typed interfaces
remain authoritative.

## Threat Model

### MCP

Risks:

- arbitrary shell or filesystem access through over-broad tools;
- direct accepted writes or direct promotion;
- resource reads exposing private KB records by default;
- tool outputs being treated as human review or proof.

Mitigations:

- expose whitelisted service calls only;
- add read-only MCP tools before controlled-write tools;
- make write tools typed and limited to draft/proposal/bundle surfaces;
- preserve public/private scope metadata in resources and results;
- never expose direct accepted promotion or accepted-path writes through MCP.

### Hosted Provider

Risks:

- API keys or secrets appear in logs;
- private KB context is sent without policy and consent;
- provider output is treated as accepted knowledge;
- real provider calls run in CI;
- missing credentials are reported as success.

Mitigations:

- providers are default-off and explicit in configuration;
- provider calls require policy scope and operator consent;
- tests and CI use fake or mocked providers;
- logs record safe audit metadata, not secrets or hidden reasoning;
- unavailable provider capability is skipped or unavailable, never pass;
- provider output can create worker bundles, draft proposals, or review
  context only.

### Skill

Risks:

- a Skill becomes stale relative to repository policy;
- an external agent treats Skill text as permission to bypass gates;
- a Skill instructs broad file reads or private-context sending.

Mitigations:

- treat Skill as guidance only;
- keep repository docs, schemas, service contracts, CLI, MCP definitions, and
  gate behavior authoritative;
- make forbidden actions explicit in the Skill package;
- require Skill examples to preserve accepted-promotion and private-KB
  boundaries.

### External Agent

Risks:

- hallucinated capabilities or false verification claims;
- accidental private/public KB mixing;
- oversized context pulls;
- generated content entering accepted knowledge without review.

Mitigations:

- require typed, bounded service/MCP calls;
- keep context packs issue-scoped and budgeted;
- make public-only context explicit;
- preserve validation, gate, review, and promotion as separate steps;
- do not allow AI review to satisfy human-review policy.

### Private KB Leakage

Risks:

- retrieval, context packs, MCP resources, provider requests, logs, PR
  summaries, or generated review context leak private artifact text or IDs;
- private artifacts are copied into public KB roots;
- public artifacts begin depending on private artifacts.

Mitigations:

- retain KB root and readonly metadata through service results;
- support public-only retrieval and context;
- require explicit provider context-send policy before private context leaves
  the local workspace;
- redact secrets and avoid dumping full private context into durable logs by
  default;
- continue rejecting public-to-private dependencies and readonly public-root
  writes.

## Consequences

Future tasks should extract typed services before implementing MCP or hosted
providers. MCP tools and provider workers should call those services, not
duplicate CLI logic or invoke arbitrary shell commands.

This ADR authorizes architecture direction only. It does not implement runtime
behavior, add public interfaces, change artifact schema, change gates, change
verifier adapters, change accepted-promotion policy, or add hosted provider
dependencies.

## Non-Goals

This ADR does not:

- implement an MCP server;
- implement provider transport;
- implement a service layer;
- define final request/response schemas;
- package a Skill;
- run hosted API calls;
- add production multi-user permissions;
- add automatic theorem proving, autoformalization, or semantic-alignment
  automation.
