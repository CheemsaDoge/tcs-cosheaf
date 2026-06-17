# Current Milestone

Milestone: **v0.9.0 Reviewable Research Workflow MVP**

Status: **published release with documentation closeout and gap audit in progress**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V14.md

Current package version: `0.9.0`

Current release: <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>

Closeout focus:

- keep README, roadmap, release notes, project state, and handoff docs aligned
  with the real published v0.9.0 state;
- record that the current `cosheaf workflow` CLI is an initial thin surface,
  not a complete issue-to-handoff workflow engine;
- record downstream pin drift separately instead of claiming ecosystem
  closeout is complete.

Remaining V14 implementation gaps:

- persistent workflow storage under `.cosheaf/workflows/`;
- `workflow show` and bounded `workflow run`;
- draft proposal generation;
- workflow handoff build/scan/export;
- `cosheaf eval reviewable-workflow --json`;
- downstream workspace-template and public-KB v0.9 policy/pin closeout.

Authority boundary: workflow output remains review context only. It is not
proof, source metadata, human review, verifier pass, gate pass, accepted
status, accepted refutation, or promotion authority.
