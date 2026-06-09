# Agent Access

## Purpose

Agent access is the post-`v0.2.0` architecture direction for making
TCS-Cosheaf usable by external agents, operator skills, internal orchestrator
runs, and hosted model workers without weakening the Git-backed knowledge
governance model.

This document is architecture and threat-model guidance only. It does not
implement an MCP server, hosted provider transport, service layer, new schema,
or runtime behavior.

## Access Surfaces

TCS-Cosheaf has four intended access surfaces:

- CLI: the human and CI oracle. Existing commands remain the stable way to
  validate behavior and verify repository state.
- Service layer: the future typed implementation boundary shared by CLI, MCP,
  internal orchestrator runs, and provider-backed workers.
- MCP: the primary machine interface for external agents. MCP tools must be
  whitelisted service calls, not arbitrary shell access.
- Skill: an optional operator guide for Codex-like agents. A Skill explains
  how to use Cosheaf safely, but it is not a source of truth and grants no
  authority beyond the underlying CLI, MCP, or service interface.

Hosted API providers are planned core worker capabilities. They must be called
through explicit provider-gateway and worker contracts, not through ad hoc
agent code or direct accepted-KB writes.

## Authority Model

Agent access does not expand accepted-knowledge authority.

Allowed controlled-write outputs are limited to:

- draft artifacts or draft proposals;
- worker output bundles;
- task or run records under runtime sidecar directories;
- review context that still requires the ordinary review path.

Forbidden outputs include:

- direct writes to `kb/accepted/`;
- direct accepted promotion;
- marking AI review as human review;
- changing validation, gate, verifier, or promotion results outside the
  ordinary CLI/service workflows;
- writing into readonly public KB roots;
- sending private KB context to hosted providers without explicit policy and
  operator consent.

Accepted knowledge still requires validation, gates, human review where policy
requires it, and explicit promotion. Validation or gate success is not human
review. AI review is not human review. Skipped verifier or provider results
are not passes.

## Service-Layer Boundary

The service layer should become the shared implementation boundary for CLI,
MCP, internal orchestrator, and provider workers.

Service functions should:

- accept typed request objects;
- return typed results that are usable outside terminal rendering;
- preserve existing CLI semantics;
- avoid network access unless the specific provider or integration policy
  explicitly permits it;
- enforce repository-local path rules;
- enforce public/private KB scope rules;
- refuse accepted writes unless they are the existing explicit promotion path;
- report skipped or unavailable optional tooling honestly.

MCP and provider code must not shell out to the CLI as their core
implementation. The CLI may render service results for humans and CI, while
the service layer remains the reusable logic boundary.

## MCP Boundary

MCP is the primary external-agent machine interface.

MCP tools should initially expose read-only or inspectable operations such as
workspace inspection, validation, gate execution, memory search, context-pack
construction, and orchestrator planning. Controlled-write tools may be added
only after read-only MCP behavior is stable and only for draft, proposal, task,
or bundle surfaces.

MCP must not expose:

- arbitrary shell execution;
- arbitrary filesystem read or write access;
- direct accepted promotion;
- direct writes to accepted paths;
- secrets, environment dumps, or provider credentials;
- private KB context outside the selected scope.

## Hosted Provider Boundary

Hosted model API calls are planned but must remain controlled.

Provider behavior must be:

- default-off;
- explicitly configured;
- scoped by policy and operator consent;
- fake or mocked in CI and default tests;
- unable to write accepted knowledge;
- unable to bypass reducer, gate, review, or promotion workflows;
- careful not to log API keys, secrets, hidden reasoning, or private context
  beyond the configured audit boundary.

A provider result can become worker output, a draft proposal, or review
context. It cannot become accepted knowledge by itself.

## Skill Boundary

The Skill package is an operator guide, not a control plane.

A Skill may tell an agent:

- when to prefer MCP over CLI;
- when CLI fallback is appropriate;
- how to build context safely;
- which writes are forbidden;
- what PR summaries and verification reports should include.

A Skill must not be treated as project truth. Repository files, schemas,
service contracts, CLI behavior, MCP tool definitions, gates, and review policy
remain authoritative.

## External-Agent Threat Model

External agents may misunderstand instructions, hallucinate capabilities,
over-send context, over-write files, or treat model output as truth. The
architecture assumes an agent can be useful but not trusted with accepted
knowledge authority.

Required mitigations:

- expose only whitelisted MCP tools;
- keep write tools narrow and typed;
- require repository-local path validation;
- keep accepted promotion outside agent authority;
- make private-context sending explicit and auditable;
- keep CI and tests on fake or mocked providers;
- keep CLI/gate outputs as the reviewable oracle.

## Private KB Leakage Threat Model

Private KB data can leak through context packs, retrieval results, provider
requests, MCP resources, logs, run records, PR summaries, or generated review
context.

Required mitigations:

- preserve public/private root metadata through storage, retrieval, services,
  MCP, and provider requests;
- default provider context to the smallest issue-scoped packet that satisfies
  the requested worker role;
- support public-only context where private context is not allowed;
- require explicit policy and consent before sending private context to hosted
  providers;
- redact secrets and provider credentials from logs;
- avoid logging hidden reasoning or full private context unless the selected
  audit policy explicitly permits it;
- never copy private artifacts into `tcs-kb-public` or readonly public roots.

## Current Status

As of this document, the repository has not implemented the future MCP server,
service-layer extraction, hosted provider gateway, or Skill package described
here. Existing local CLI, validation, gate, index, retrieval, context-pack,
task, orchestrator dry-run, fake provider, and optional verifier surfaces keep
their current behavior.
