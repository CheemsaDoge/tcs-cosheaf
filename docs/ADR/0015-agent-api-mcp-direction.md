# ADR 0015: CLI-First Agent Access Direction

## Status

Accepted

## Context

`v0.2.0` established a bounded local-MVP baseline: deterministic retrieval,
context packs, local task/orchestrator dry-runs, fake provider contracts,
evaluation, optional source ingestion staging, optional Lean `#check`, and
reviewable Git-backed knowledge governance.

After that release, the repository briefly drifted into an MCP-first roadmap.
The fixed post-`v0.2.0` plan corrects that direction. MCP may remain useful,
but CLI must be the first agent interface because coding agents can already
run commands, inspect diffs, verify exit codes, and open PRs. CLI is also the
surface CI already exercises.

The risky alternatives are:

- treating Cosheaf as permanently local-only;
- making MCP a release blocker before CLI contracts and provider boundaries
  are stable;
- adding hosted provider calls before policy and service boundaries exist;
- exposing arbitrary shell or accepted-path writes through any agent surface;
- letting model output, AI review, retrieval scores, or generated sidecars
  become accepted knowledge.

## Decision

Set `v0.2.1` direction to CLI Agent Access + Hosted Provider Gateway.

The direction is:

1. CLI is the primary agent interface for coding agents.
2. Agent-facing CLI commands should provide stable structured output and stable
   error codes where needed.
3. Service-layer functions should be shared by CLI, hosted workers, internal
   orchestrator code, and optional future MCP.
4. Hosted model API/provider support is scheduled work, implemented through an
   explicit provider gateway and worker contracts.
5. Local-only execution remains fallback, offline, and CI/testing mode. It is
   not the permanent product boundary.
6. The internal orchestrator may call hosted API workers only when policy,
   configuration, consent, and context-send rules permit.
7. MCP is an optional adapter for assistants that need resources/tools instead
   of shell access. It is not a `v0.2.1` blocker.
8. Skill is an optional operator runbook. It is not a source of truth and does
   not grant permissions.

## Required Boundaries

Agent access must not weaken the knowledge lifecycle:

- Worker output may produce draft proposals, worker bundles, typed sub-results,
  or review context only.
- Accepted knowledge still requires validation, gate checks, human review where
  policy requires it, and explicit promotion.
- CLI draft/proposal/bundle write commands must not write accepted paths.
- MCP, if used, must not expose arbitrary shell, direct promotion, or
  accepted-path writes.
- Hosted providers must be default-off and explicitly configured.
- Real provider calls must not run in CI. CI and default tests must use fake or
  mocked providers.
- Provider calls must record policy scope, timeout/cancellation behavior,
  provider/model metadata, and safe audit metadata.
- Secrets, API keys, hidden reasoning, and private context beyond the selected
  audit boundary must not be logged.
- Private KB context must not be sent to a provider without explicit policy
  mode and operator consent.
- Skipped or unavailable provider/verifier results are not passes.
- AI review is not human review.
- A Lean `#check` remains import/symbol resolution, not informal/formal
  semantic alignment.

## Consequences

Roadmap and milestone language should no longer describe the next phase as
local-only hardening or as MCP-first agent access.

Future implementation should proceed in small tasks:

- align roadmap and milestone docs with this ADR;
- audit workspace-template pins against `v0.2.0`;
- stabilize CLI JSON and error contracts;
- keep the service layer as shared implementation substrate;
- add controlled CLI draft/proposal/bundle write paths before broad agent
  write surfaces;
- design and implement hosted provider gateway with fake/mocked tests first;
- package the Skill/operator guide around CLI-first workflows;
- treat MCP as optional adapter work after CLI/provider stabilization.

This direction does not make TCS-Cosheaf production-ready software. It also
does not add a web UI, multi-user authentication, automatic theorem proving,
automatic accepted promotion, or full Lean/mathlib/CSLib integration.

## Non-Goals

This ADR does not implement provider transport, service extraction, Skill
packaging, hosted workers, MCP changes, or schemas. It records the direction
needed before those tasks proceed.

It also does not change artifact schema, gate semantics, verifier behavior,
promotion policy, public/private KB rules, or any accepted artifact.
