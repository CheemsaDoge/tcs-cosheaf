# ADR 0016: CLI-First Agent Access Architecture And Threat Model

## Status

Accepted

## Context

ADR 0015 records the post-`v0.2.0` direction change: TCS-Cosheaf should support
agent access through CLI first, hosted provider workers when explicitly
configured, and optional MCP adapters later. The repository needs a durable
authority model and threat model before expanding CLI JSON, provider gateway,
Skill, or optional MCP surfaces.

The main risk is not that agents or hosted providers exist. The main risk is
letting any agent-access path bypass the repository's existing truth boundary:
Git-backed artifacts, validation, gates, human review where required, and
explicit accepted promotion.

## Decision

Adopt this agent-access architecture:

1. CLI is the primary external-agent interface.
2. Service layer is the shared implementation boundary.
3. Hosted API provider support is a planned worker capability, default-off and
   fake/mocked in tests.
4. MCP is an optional adapter over services, not the primary path and not a
   release blocker.
5. Skill is an optional operator guide. It is not a source of truth and grants
   no permission by itself.
6. Controlled writes are limited to draft, proposal, task, run, and bundle
   surfaces.
7. Accepted promotion remains outside agent authority.

## Architecture

The intended control flow is:

```text
human / CI / coding agent
  -> CLI
  -> service layer
  -> storage / validation / gate / retrieval / context / task / verifier logic

internal orchestrator
  -> service layer
  -> local workers or provider-backed workers
  -> worker bundles / reducer results / review context

hosted provider worker
  -> provider gateway
  -> explicit policy and consent boundary
  -> worker bundle / draft proposal / review context

optional MCP adapter
  -> whitelisted service calls
  -> same bounded logic
```

The CLI is the first oracle used by humans, CI, and coding agents. Optional MCP
and provider paths should reuse typed services rather than shelling out to the
CLI as their core implementation. The Skill package should describe how an
operator or external agent should use CLI first, and MCP only when the adapter
is appropriate, but repository files and typed interfaces remain authoritative.

## Threat Model

### CLI Agent

Risks:

- broad repository dumps;
- direct edits to accepted paths;
- false claims that validation/gate output is human review;
- malformed draft or bundle writes.

Mitigations:

- stable bounded `--json` outputs for agent-facing commands;
- explicit controlled write commands for draft/proposal/bundle surfaces;
- repository-local path validation;
- refusal of accepted-path writes;
- final validation/gate/test reporting.

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

### Optional MCP

Risks:

- arbitrary shell or filesystem access through over-broad tools;
- direct accepted writes or direct promotion;
- resource reads exposing private KB records by default;
- tool outputs being treated as human review or proof.

Mitigations:

- expose whitelisted service calls only;
- keep MCP optional and adapter-scoped;
- make write tools typed and limited to draft/proposal/bundle surfaces;
- preserve public/private scope metadata in resources and results;
- never expose direct accepted promotion or accepted-path writes through MCP.

### Skill

Risks:

- a Skill becomes stale relative to repository policy;
- an external agent treats Skill text as permission to bypass gates;
- a Skill instructs broad file reads or private-context sending.

Mitigations:

- treat Skill as guidance only;
- keep repository docs, schemas, service contracts, CLI behavior, optional MCP
  definitions, and gate behavior authoritative;
- make forbidden actions explicit in the Skill package;
- require Skill examples to preserve accepted-promotion and private-KB
  boundaries.

### Private KB Leakage

Risks:

- retrieval, context packs, CLI JSON, optional MCP resources, provider
  requests, logs, PR summaries, or generated review context leak private
  artifact text or IDs;
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

Future tasks should stabilize typed services and CLI JSON before broad
provider or optional MCP behavior. Provider workers and optional MCP tools
should call services, not duplicate CLI logic or invoke arbitrary shell
commands.

This ADR authorizes architecture direction only. It does not implement runtime
behavior, add public interfaces, change artifact schema, change gates, change
verifier adapters, change accepted-promotion policy, or add hosted provider
dependencies.

## Non-Goals

This ADR does not:

- implement provider transport;
- implement controlled draft-write CLI;
- package a Skill;
- run hosted API calls;
- require MCP for `v0.2.1`;
- add production multi-user permissions;
- add automatic theorem proving, autoformalization, or semantic-alignment
  automation.
