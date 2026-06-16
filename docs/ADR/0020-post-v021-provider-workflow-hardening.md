# ADR 0020: Post-v0.2.1 Provider And Workflow Hardening

Status: Accepted

Date: 2026-06-13

## Context

`v0.2.1` published the CLI Agent Access + Hosted Provider Gateway prerelease.
The release made CLI-first agent operation, controlled draft/staging writes,
provider gateway inspection, fake provider runs, mocked OpenAI-compatible
boundaries, hosted worker dispatch, security regressions, and agent workflow
evals pin-able as a prerelease.

The post-release audit in `docs/POST_V021_STATE_AUDIT.md` confirmed that:

- downstream repositories pin `tcs-cosheaf@v0.2.1`;
- MCP is optional and not required for ordinary CLI-first work;
- controlled-write MCP was closed for the v0.2.2 line unless a separate
  approved issue reopened the scope;
- the system is not documented as permanently local-only;
- no accepted artifacts were added during the `v0.2.1` closeout;
- real provider calls are not default-enabled and are not used in CI/default
  tests.

The next milestone should harden provider and agent workflow boundaries without
overclaiming production hosted-agent readiness.

## Decision

The next target is `v0.2.2 Provider Transport + Agent Workflow Hardening`.

The project will continue with a CLI-first architecture:

- CLI remains the first agent interface and the human/CI oracle.
- The service layer remains the shared implementation boundary for CLI,
  hosted workers, internal orchestrator code, tests, and optional future MCP.
- Real provider transport work is allowed only as explicit, default-off,
  opt-in functionality with context preview, policy scope, consent,
  redaction, and fake/mocked tests.
- The first real transport, if implemented, will be OpenAI-compatible HTTP.
- CI and default tests must not make real provider calls or require API keys.
- Provider output may become WorkerBundle, draft proposal, draft artifact, or
  review context only.
- Provider output must not write accepted knowledge, mark human review,
  promote artifacts, or bypass validation, gates, reducers, verifier results,
  review, or promotion.
- MCP remains optional adapter work.
- At this post-v0.2.1 decision point, controlled-write MCP was not planned
  unless a separate maintainer-approved issue explicitly reopened that scope.
  ADR 0026 later reopened a narrow draft/review/runtime MCP write scope for
  the v0.5.0 line without adding accepted-write, promotion, human-review,
  arbitrary-shell, or hosted-provider authority.

The first concrete task after landing the plan is a real-provider transport ADR
and threat model. Runtime implementation must wait until that boundary is
documented.

## Non-Goals

This decision does not authorize:

- production hosted multi-agent operation;
- default-on hosted API calls;
- real provider calls in CI or default tests;
- mandatory provider SDK dependencies;
- provider real-run commands without explicit consent and network gates;
- controlled-write MCP in the v0.2.2 provider-transport line;
- provider MCP tools;
- arbitrary shell through MCP;
- direct accepted writes;
- automatic accepted promotion;
- AI/provider review as human review;
- automatic theorem proving;
- Lean/mathlib/CSLib semantic-alignment claims;
- web UI, SaaS behavior, or multi-user permissions.

## Consequences

Future provider transport work must be split into small PRs:

1. Document the real transport boundary and threat model.
2. Implement optional transport with fake/mocked tests only.
3. Add any real-run CLI surface only after the transport is implemented and
   only behind explicit confirmation, network permission, configuration, key,
   and context-preview checks.

Workspace-template demos must remain fake-only by default. Public KB policy and
content work must stay separate from provider/MCP/runtime changes. Release
notes must remain conservative and must not claim production readiness.

At the time of this ADR, current documentation described controlled-write MCP
as not planned unless a new approved issue existed. ADR 0026 later reopened a
narrow draft/review/runtime MCP write scope for the v0.5.0 line. Superseded
historical plans may still mention older options as history, but they do not
authorize implementation outside their active milestone.
