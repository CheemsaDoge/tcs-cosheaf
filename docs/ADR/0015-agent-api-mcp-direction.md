# ADR 0015: Agent API MCP Direction

## Status

Proposed

## Context

`v0.2.0` established a bounded local-MVP baseline: deterministic retrieval,
context packs, local task/orchestrator dry-runs, fake provider contracts,
evaluation, optional source ingestion staging, optional Lean `#check`, and
reviewable Git-backed knowledge governance.

After that release, the repository still contained next-focus language that
made local orchestrator hardening sound like the permanent next product
boundary. The post-`v0.2.0` rollback audit classified that language in
`context/CURRENT_MILESTONE.md` and `docs/ROADMAP.md` as `REWRITE`, not
`REVERT`. The local orchestrator code is useful substrate, but the next
roadmap direction must include mainstream agent access through MCP, Skill, and
controlled hosted model API workers.

The risky alternatives are:

- treating Cosheaf as permanently local-only;
- adding hosted provider calls before policy and service boundaries exist;
- exposing arbitrary shell or accepted-path writes through MCP;
- letting model output, AI review, retrieval scores, or generated sidecars
  become accepted knowledge.

## Decision

Set `v0.2.1` direction to Agent Access + Hosted API Provider + MCP/Skill.

The direction is:

1. MCP is the first-class external-agent machine interface.
2. Skill is an optional operator guide for agent users. It is not a source of
   truth and does not grant permissions.
3. Hosted model API/provider support is scheduled work, implemented through an
   explicit provider gateway and worker contracts.
4. Local-only execution remains the fallback, offline, and CI/testing mode. It
   is not the permanent product boundary.
5. External agents may act as orchestrators or bounded workers through MCP and
   shared service-layer interfaces.
6. The internal orchestrator may call hosted API workers only when policy,
   configuration, consent, and context-send rules permit.
7. CLI remains the human and CI oracle.
8. Service-layer functions should be shared by CLI, MCP, internal
   orchestrator, and provider-backed workers.

## Required Boundaries

Agent access must not weaken the knowledge lifecycle:

- Worker output may produce draft proposals, worker bundles, typed sub-results,
  or review context only.
- Accepted knowledge still requires validation, gate checks, human review where
  policy requires it, and explicit promotion.
- MCP must not expose arbitrary shell, direct promotion, or accepted-path
  writes.
- Controlled write tools, when added later, must be explicit and limited to
  draft/proposal/bundle surfaces.
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
only local orchestrator hardening or as excluding hosted provider work.

Future implementation should proceed in small tasks:

- install longplan v3 as current repository plan;
- document the agent-access architecture and threat model;
- extract a service layer used by CLI, MCP, orchestrator, and providers;
- define typed agent-access request/response schemas;
- add context-send policy and provider preview before real provider calls;
- add MCP read-only tools before controlled write tools;
- add provider gateway and hosted workers behind explicit opt-in and fake or
  mocked tests;
- package the Skill/operator guide after the service and MCP boundaries are
  clear.

This direction does not make TCS-Cosheaf production-ready software. It also
does not add a web UI, multi-user authentication, automatic theorem proving,
automatic accepted promotion, or full Lean/mathlib/CSLib integration.

## Non-Goals

This ADR does not implement MCP, provider transport, service extraction, Skill
packaging, hosted workers, or schemas. It records the direction needed before
those tasks proceed.

It also does not change artifact schema, gate semantics, verifier behavior,
promotion policy, public/private KB rules, or any accepted artifact.
