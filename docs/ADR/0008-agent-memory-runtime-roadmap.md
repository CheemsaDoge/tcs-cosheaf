# ADR 0008: Agent Memory Runtime Roadmap Placement

## Status

Accepted

## Context

The longplan adds deterministic librarian and orchestrator capabilities after
the current v0.1.1 Formal Link Layer scaffold. These capabilities need direct
access to existing framework concepts:

- typed artifacts and status/path rules,
- workspace KB roots and public/private policy,
- validation and gatekeeper results,
- deterministic indexes and dependency graphs,
- context-pack generation,
- verifier result semantics,
- worker task records and local run logs.

One option would be to create a fourth core repository for agent memory and
orchestration. Another option would be to place these capabilities in the
workspace template. A third option is to add them as bounded framework modules
inside `tcs-cosheaf`.

The three-repository model already has clear ownership:

- `tcs-cosheaf` owns framework behavior and reusable runtime surfaces.
- `tcs-kb-public` owns reviewed public knowledge.
- `tcs-cosheaf-workspace-template` owns the user-facing workspace entry point.

Adding a fourth core repository would create another source of version,
schema, and policy coordination before the MVP workflow is stable.

## Decision

Implement the deterministic librarian, memory policy, orchestrator state
machine, local worker runtime integration, provider-neutral worker interface,
and related evaluation/observability surfaces inside `tcs-cosheaf`.

Keep them modular and phase-gated:

- `tcs-cosheaf` will provide framework modules, typed models, CLIs, sidecar
  rebuilds, context-pack integration, and tests.
- `tcs-kb-public` will remain a knowledge repository and will not contain agent
  runtime code.
- `tcs-cosheaf-workspace-template` will consume framework commands and expose a
  safe user workflow; it will not own framework runtime implementations.
- Hosted provider adapters, if added later, must be optional and disabled by
  default.

The librarian is deterministic-first. Its default outputs are artifact cards,
rankings, and retrieval audit records, not new claims or accepted artifacts.

The orchestrator is state-machine-first. It may plan, route, run local workers,
and record reducer outputs, but accepted knowledge still enters only through
review, gates, and explicit promotion.

## Consequences

- Framework behavior can enforce public/private filtering, gate semantics, and
  verifier state consistently.
- CI can test memory and orchestration behavior against local fixtures without
  cloning remote repositories or requiring hosted services.
- Downstream workspaces get one coherent CLI surface instead of coordinating a
  fourth runtime repository.
- `tcs-kb-public` remains focused on source-reviewed knowledge.
- `tcs-cosheaf-workspace-template` remains a thin user-facing entry point.
- Framework scope increases, so each phase must stay modular, issue-driven,
  and covered by ADR/interface updates when public surfaces change.
- If future deployment needs a separate service boundary, it can be added after
  the framework contracts stabilize; that future service would consume stable
  framework APIs rather than defining policy itself.

## Non-Goals

- Do not create a fourth core repository in this phase.
- Do not add a production web UI.
- Do not add hosted LLM execution by default.
- Do not require API keys or network access in tests.
- Do not let workers or orchestrators write accepted artifacts directly.
- Do not make the librarian create new claims.
- Do not treat generated memory sidecars as source of truth.
- Do not implement automatic theorem proving or autoformalization.
- Do not claim Lean/mathlib/CSLib verification unless a checker actually runs
  and records a result.
- Do not treat any Lean `#check` result as informal/formal semantic alignment.

## Required Follow-Up Discipline

Each follow-up capability must land as a separate issue, branch, and PR.
Architecture or public-interface changes must update ADRs and
`context/INTERFACE_REGISTRY.md`. Tests must use local fixtures, fake providers,
or fake command backends where optional external tools are involved.
