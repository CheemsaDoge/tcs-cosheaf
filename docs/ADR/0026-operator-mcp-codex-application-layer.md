# ADR 0026: Operator MCP And Codex Application Layer

Status: Accepted for the `v0.5.0` implementation line.

Date: 2026-06-16

## Context

The published `v0.4.0` release adds Strategy Planner + Research Task Graph
support. Cosheaf can now record checked evidence, research-run provenance,
failure memory, context packs, and strategy plans through the CLI.

The remaining operator bottleneck is reliable access. Codex-style agents need
a bounded way to inspect workspace state, build context, use strategy plans,
record research runs, stage reviewable drafts, rerun validation/gates, and
open reviewable PRs without gaining accepted-write, human-review, or promotion
authority.

The repository already has a minimal read-only MCP stdio surface. It is useful
but narrower than the operator workflow required for `v0.5.0`.

## Decision

Cosheaf will implement an optional Operator MCP + Codex Application Layer for
`v0.5.0`.

The CLI remains the human and CI oracle. MCP is an adapter over existing
service-layer and CLI-equivalent policy boundaries. MCP tools must not shell
out to arbitrary commands and must not bypass validation, gate, workspace,
readonly-root, public/private, or accepted-promotion policy.

The implementation line will add:

- read-only MCP tools for workspace, validation, gate, memory, context,
  strategy, research-run evidence, and eval smoke;
- controlled-write MCP tools for draft/proposal/review-context/runtime outputs
  already allowed by Cosheaf policy;
- Codex operator runbooks and configuration examples;
- a workspace-template operator demo with CLI fallback; and
- public KB policy smoke for operator/MCP outputs.

## Authority Boundary

Operator MCP output is not:

- proof;
- verifier evidence;
- verifier pass;
- gate pass;
- human review;
- accepted status;
- accepted refutation;
- promotion authority;
- public KB source metadata.

MCP must not expose:

- accepted KB writes;
- artifact promotion;
- human-review creation or completion;
- arbitrary shell execution;
- default hosted provider calls;
- private KB export to external providers by default;
- public KB edits by default from downstream workspaces.

Controlled-write MCP tools may create only draft, proposal, review-context, or
runtime records that are already allowed by Cosheaf service-layer policy. Those
outputs must carry authority notices and remain subject to ordinary review,
validation, gates, verifier evidence where applicable, and explicit promotion.

## Consequences

The `v0.5.0` line will make Codex-operated Cosheaf easier to use without
changing accepted-knowledge authority. Tests must include negative fixtures for
accepted paths, readonly roots, parent traversal, absolute paths,
private-to-public leakage, skipped-not-pass, provider-default avoidance, and
human-review spoofing.

MCP support remains optional. CLI fallback must stay documented and usable.
Default tests and CI must not require hosted providers, API keys, network
calls, SAT, SMT, Lean, lake, or external MCP clients.

## Non-Goals

This ADR does not approve:

- production hosted multi-agent SaaS;
- default real provider calls;
- hosted model execution as the default runtime;
- accepted promotion through MCP;
- human-review creation through MCP;
- automatic theorem proving;
- automatic Lean/mathlib/CSLib semantic alignment;
- web UI;
- multi-user permission systems;
- replacing GitHub PR review.

## Follow-Ups

- Land `docs/CODEX_DEVELOPMENT_PLAN_V9.md` and
  `docs/POST_V040_STATE_AUDIT.md`.
- Expand the current read-only MCP surface to the V9 operator tool set.
  Completed by the read-only operator MCP core task.
- Add controlled-write MCP tools over existing safe write semantics.
  Completed by the controlled draft-write MCP tools task.
- Add operator runbook and workspace-template demo with CLI fallback.
- Add public KB operator/MCP policy smoke.
- Prepare and publish a conservative `v0.5.0` release only after downstream
  integration and release smoke pass.
