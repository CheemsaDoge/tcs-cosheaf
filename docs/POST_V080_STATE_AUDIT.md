# Post-v0.8.0 State Audit

Date: 2026-06-18

This audit records the v0.8.0 baseline used by the V14 reviewable-workflow
plan. It is historical context now that `v0.9.0` has been published.

## Verified Baseline

- `docs/releases/v0.8.0.md` exists and records the Deterministic Execution
  Kernel + Librarian + FSM release.
- The public GitHub release exists:
  <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.8.0>.
- The current framework package has advanced beyond this baseline and records
  `0.9.0`.

## v0.8.0 Role In V14

The V14 line was intended to build on the v0.8.0 deterministic kernel:

- librarian v0;
- orchestrator FSM v1;
- whitelisted local action registry;
- bounded local action execution;
- worker profiles;
- deterministic memory feedback.

## Superseded Current-State Notes

Any document that still describes v0.8.0 or v0.7.0 as the active release line
is stale. The active framework release line is `v0.9.0`, but the current
workflow implementation is still an initial surface rather than the complete
V14 issue-to-handoff workflow engine.

## Authority Boundary

The v0.8.0 baseline and v0.9.0 workflow line do not grant accepted writes,
human review, verifier pass, gate pass, source metadata authority, accepted
refutation authority, promotion authority, automatic theorem proving, Lean
semantic alignment, default hosted-provider execution, or arbitrary shell
execution.
