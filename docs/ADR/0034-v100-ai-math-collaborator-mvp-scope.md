# ADR 0034: v1.0.0 AI Math Collaborator MVP Scope

Status: accepted

Date: 2026-06-18

## Context

V14 through V17 published the end-to-end reviewable workflow, checker
discipline, bounded external-operator campaigns, deterministic memory updates,
benchmark suite v1, comparisons, and static reports. The system is now useful
enough to package as an MVP, but continued broad subsystem work would delay a
stable user-facing baseline and increase overclaim risk.

The project needs a v1.0.0 scope freeze before more feature work.

## Decision

V18 freezes v1.0.0 as an AI math collaborator MVP:

- a Git-backed research harness;
- CLI-first and locally reviewable;
- safe for human and external AI operator workflows;
- benchmarked and auditable; and
- explicit that outputs are draft/review context unless accepted by existing
  review, gate, verifier, and promotion workflows.

v1.0.0 will package existing V14-V17 capabilities with polish, a canonical
workspace demo, documentation, and release audits. It will not introduce a new
major runtime subsystem before release.

## Included In v1.0.0

- Existing workflow, checker, gap, campaign, memory, benchmark, compare, and
  static-report CLI surfaces.
- Existing optional verifier/provider/MCP/tooling surfaces under their current
  default-off or optional policies.
- Canonical workspace-template demo for the safe collaborator loop.
- Public KB policy guards preserving accepted-artifact review boundaries.
- Release audits proving authority, privacy, benchmark, and documentation
  boundaries.

## Deferred Beyond v1.0.0

- Web UI or hosted service.
- New hosted provider integration or default-on model calls.
- Automatic theorem proving or autoformalization.
- Full Lean/mathlib/CSLib semantic alignment.
- Automatic accepted promotion.
- Multi-user permissions.
- Large schema rewrites.

## Authority Boundary

The v1.0.0 MVP is not an autonomous theorem prover or accepted-truth engine.
Workflow outputs, campaign outputs, checker reports, benchmark reports, memory
weights, comparisons, static reports, provider output, and operator handoffs
are not proof, source metadata, human review, verifier pass without a real
checker result, gate pass, accepted status, accepted theorem/refutation, or
promotion authority.

Skipped, unsupported, unavailable, and inconclusive rows are not passes.

## Consequences

- The project can converge on a stable, demoable v1.0.0 baseline.
- Phase B-E work is limited to polish, demo, docs, and audit evidence.
- Broad feature requests move to v1.1+ unless they fix a release blocker.
- The workspace template becomes the primary user proof of MVP usability.

## Rejected Options

- Continue adding broad research-agent subsystems before v1.0.0.
- Rebrand sidecar memory or benchmark success as truth.
- Make hosted providers default-on for the MVP.
- Treat MCP as the primary authority instead of CLI.
- Claim Lean/mathlib/CSLib proof checking beyond optional reference checks.

