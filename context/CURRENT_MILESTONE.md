# Current Milestone

Milestone: **v0.9.0 Reviewable Research Workflow MVP**

Status: **published release with V14 workflow-core follow-up in progress**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V14.md

Current package version: `0.9.0`

Current release: <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>

Current focus:

- extend the published initial `cosheaf workflow` surface into a persistent
  runtime workflow core;
- keep workflow records as review context only;
- record downstream pin/policy drift separately instead of claiming ecosystem
  closeout is complete.

Completed after publication:

- persistent workflow storage under `.cosheaf/workflows/`;
- `workflow show`;
- persisted `workflow step`;
- bounded `workflow run`;
- persisted workflow readiness reports.

Remaining V14 implementation gaps:

- draft proposal generation;
- workflow handoff build/scan/export;
- `cosheaf eval reviewable-workflow --json`;
- downstream workspace-template and public-KB v0.9 policy/pin closeout.

Authority boundary: workflow output remains review context only. It is not
proof, source metadata, human review, verifier pass, gate pass, accepted
status, accepted refutation, or promotion authority.
