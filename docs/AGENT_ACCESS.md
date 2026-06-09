# Agent Access

## Purpose

Agent access is the post-`v0.2.0` architecture direction for making
TCS-Cosheaf usable by external coding agents, operator skills, internal
orchestrator runs, optional MCP adapters, and hosted model workers without
weakening the Git-backed knowledge governance model.

This document records architecture and threat-model guidance plus current
agent-access status. It does not by itself grant authority, change gates,
implement hosted provider transport, or create write permissions.

## Access Surfaces

TCS-Cosheaf has these intended access surfaces:

- CLI: the primary interface for coding agents, humans, and CI. Existing
  commands remain the stable way to validate behavior and verify repository
  state.
- Service layer: the typed implementation boundary shared by CLI first, then
  hosted provider workers, internal orchestrator runs, and optional MCP.
- Hosted provider gateway: planned worker capability. Real calls must be
  explicit, default-off, policy scoped, consented, and fake or mocked in tests.
- MCP: optional adapter for assistants that benefit from resources/tools
  rather than shell access. It is not required for ordinary Codex-style repo
  work.
- Skill: optional operator guide for Codex-like agents. A Skill explains how
  to use Cosheaf safely, but it is not a source of truth and grants no
  authority beyond the underlying CLI, service, provider, or optional MCP
  interfaces.

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

## CLI-First Workflow

External coding agents should use CLI first:

1. Read `AGENTS.md`, `context/CURRENT_MILESTONE.md`, and the relevant issue.
2. Run `cosheaf workspace info --json` when machine-readable workspace state
   is needed, or `cosheaf workspace info` for human inspection.
3. Run `cosheaf validate --json` and `cosheaf gate run --json` when an agent
   needs structured pass/fail data, and keep the human commands available for
   operator review.
4. Use `cosheaf memory ...` and `cosheaf context build <issue-id>` to assemble
   bounded context.
5. Write only draft/proposal/bundle/source-note staging outputs when a task
   explicitly permits writes.
6. Re-run the required validation/test/gate commands.
7. Produce a PR summary with exact commands and limitations.

Core read-only agent-facing CLI commands provide deterministic `--json` output
for version, workspace info, validation, gate runs, memory cards/search,
context build/show, and orchestrator planning. JSON mode emits no Rich or ANSI
markup, keeps public/private root scope visible where retrieval or context is
involved, and uses `ErrorResult` for expected machine-readable errors. MCP
remains optional and is not required for ordinary CLI-first agent workflows.

## Service-Layer Boundary

The service layer should remain the shared implementation boundary for CLI,
hosted provider workers, internal orchestrator code, and optional MCP.

Service functions should:

- accept typed request objects where public agent-access schemas are available;
- return typed results that are usable outside terminal rendering;
- preserve existing CLI semantics;
- avoid network access unless the specific provider or integration policy
  explicitly permits it;
- enforce repository-local path rules;
- enforce public/private KB scope rules;
- refuse accepted writes unless they are the existing explicit promotion path;
- report skipped or unavailable optional tooling honestly.

Optional MCP and provider code must not shell out to the CLI as their core
implementation. The CLI may render service results for humans and CI, while
the service layer remains the reusable logic boundary.

The public agent-access DTOs live in `cosheaf.services.models`, and their JSON
Schema files live under `schemas/agent_access/`. These DTOs are versioned with
`schema_version: 1` and cover workspace info, validation, gate runs, memory
search, context builds, task creation, worker-bundle submission, draft artifact
writes, provider model calls, provider run records, and standard error
results. They are serialization contracts for CLI/provider/optional-MCP
surfaces; they do not by themselves execute hosted API calls or authorize
accepted writes.

`ErrorResult` is the standard machine-readable error shape for public
agent-access responses. It contains:

- `code`: stable machine-readable error code;
- `message`: human-readable summary;
- `remediation`: concrete next step for the caller/operator;
- `blocking`: whether the caller must stop before proceeding;
- `related_path`: optional repository-local path associated with the error;
- `related_artifact`: optional artifact ID associated with the error;
- `details`: optional string-to-string metadata for narrow diagnostics.

The stable error-code list is exported as
`cosheaf.services.models.AGENT_ACCESS_STABLE_ERROR_CODES`. Current codes are:

- `accepted_write_forbidden`
- `artifact_file_validation_failed`
- `artifact_id_exists`
- `artifact_model_validation_failed`
- `artifact_path_exists`
- `context_build_failed`
- `context_show_failed`
- `draft_write_failed`
- `gate_issue`
- `invalid_artifact_id`
- `invalid_artifact_target_path`
- `invalid_timestamp`
- `memory_cards_failed`
- `memory_search_failed`
- `missing_required_domain`
- `no_writable_kb_root`
- `orchestrator_plan_failed`
- `private_context_requires_consent`
- `private_context_requires_policy`
- `provider_context_preview_failed`
- `provider_context_scope_violation`
- `repository_load_failed`
- `timestamp_missing_timezone`
- `unknown_context_policy_mode`
- `validation_failed`
- `validation_unexpected_error`
- `workspace_config_failed`

Backward compatibility note: `related_path` and `related_artifact` are optional
schema fields, so older payloads that omit them still validate. New serialized
`ErrorResult` payloads include those keys with `null` when no correlation is
available, so exact-key consumers should tolerate additional nullable fields.
Adding a new error code is a compatible extension only when the remediation and
blocking semantics remain explicit; changing the meaning of an existing code is
a breaking interface change.

`ContextSendPolicyService` is the provider-send preview boundary. It accepts a
`ContextBuildRequest` and returns either a safe `ProviderContextPreview` or a
structured `ErrorResult`. Public-mode previews use public KB scope only.
Private KB context is previewable only with `policy_mode=private_research`,
`public_only=false`, and explicit private-context permission. The preview lists
issue id, artifact ids, root scopes, estimated token counts, and risk flags; it
does not include full artifact text, issue text, provider credentials, API
keys, or secrets. The preview is not a provider call and does not authorize a
provider call by itself.

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

## Optional MCP Boundary

MCP is an optional adapter, not the primary agent path.

The current MCP surface is a minimal read-only stdio JSON-RPC implementation.
It exposes whitelisted read-only tools, scope-aware resource templates, and
governance-safe prompt templates. Prompts are static workflow guidance: they
include accepted/draft distinctions, require artifact IDs, forbid accepted
knowledge writes, and require final test/validate/gate checks. Prompt templates
do not include private KB content or artifact text.

MCP must not expose:

- arbitrary shell execution;
- arbitrary filesystem read or write access;
- direct accepted promotion;
- direct writes to accepted paths;
- secrets, environment dumps, or provider credentials;
- private KB context outside the selected scope.

Controlled-write MCP tools remain later optional work and must require explicit
allow-write configuration if implemented.

## Skill Boundary

The Skill package is an operator guide, not a control plane.

A Skill may tell an agent:

- how to use CLI first;
- when optional MCP may be appropriate;
- how to build context safely;
- which writes are forbidden;
- what PR summaries and verification reports should include.

A Skill must not be treated as project truth. Repository files, schemas,
service contracts, CLI behavior, optional MCP definitions, gates, and review
policy remain authoritative.

## External-Agent Threat Model

External agents may misunderstand instructions, hallucinate capabilities,
over-send context, over-write files, or treat model output as truth. The
architecture assumes an agent can be useful but not trusted with accepted
knowledge authority.

Required mitigations:

- keep CLI as the first auditable path;
- expose only whitelisted optional MCP tools;
- keep write tools narrow and typed;
- require repository-local path validation;
- keep accepted promotion outside agent authority;
- make private-context sending explicit and auditable;
- keep CI and tests on fake or mocked providers;
- keep CLI/gate outputs as the reviewable oracle.

## Private KB Leakage Threat Model

Private KB data can leak through context packs, retrieval results, CLI JSON,
provider requests, optional MCP resources, logs, run records, PR summaries, or
generated review context.

Required mitigations:

- preserve public/private root metadata through storage, retrieval, services,
  CLI, optional MCP, and provider requests;
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

As of this document, the repository has a thin typed service layer, versioned
agent-access DTO/JSON Schema contracts, a provider-send context preview policy
service, deterministic JSON output for core read-only CLI commands, and a
minimal read-only stdio MCP surface that is optional adapter code. The
repository has not implemented the hosted provider gateway, controlled-write
MCP tools, or Skill package described here. Existing local CLI, validation,
gate, index, retrieval, context-pack, task, orchestrator dry-run, fake
provider, and optional verifier surfaces keep their current behavior.
