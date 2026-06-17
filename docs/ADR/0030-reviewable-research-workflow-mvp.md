# ADR 0030: Reviewable Research Workflow MVP

## Status

Accepted for v0.9.0.

## Context

v0.8.0 delivered librarian, orchestrator FSM, whitelisted action registry, non-dry-run local loop execution, worker profiles, and deterministic memory feedback. The next useful capability is a single end-to-end reviewable research workflow: issue -> librarian context -> FSM plan -> bounded local loop -> evidence/failures -> draft artifact proposal -> review handoff -> benchmark/eval.

## Decision

v0.9.0 establishes the reviewable-workflow line and publishes an initial
`cosheaf workflow` CLI surface. The intended architecture remains a deterministic
workflow record that can eventually connect librarian context, orchestrator FSM,
whitelisted local actions, research-loop evidence, draft proposal generation,
and review handoff packets.

The published `v0.9.0` implementation was the first slice, not the complete
architecture. It exposed `workflow start`, `workflow step`, and
`workflow readiness`. A post-release V14 B.1 follow-up adds the persistent
workflow core: `.cosheaf/workflows/<workflow-id>/` runtime records,
`workflow show`, persisted `workflow step`, bounded `workflow run`, and
persisted readiness reports. Later V14 C.1, D.1, and E.1 follow-ups add
draft-proposal commands, workflow-handoff commands, scanner integration, and
framework reviewable-workflow eval coverage.

Workflow records, draft proposals, and review handoffs remain review context
only. No accepted writes, human review creation, verifier/gate mutation, source
metadata authority, accepted-refutation authority, or promotion authority are
granted by this ADR or by the v0.9.0 release.
