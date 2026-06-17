# Current Milestone

Milestone: **v0.9.0 Reviewable Research Workflow MVP**

Status: **published release with V14 workflow follow-ups in progress**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V14.md

Current package version: `0.9.0`

Current release: <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>

Current focus:

- extend the published initial `cosheaf workflow` surface into a persistent
  runtime workflow core;
- convert workflow output into reviewable draft proposals without entering
  accepted knowledge;
- produce workflow review handoff packets with fail-closed scanner guards;
- keep workflow records as review context only;
- record downstream pin/policy drift separately instead of claiming ecosystem
  closeout is complete.

Completed after publication:

- persistent workflow storage under `.cosheaf/workflows/`;
- `workflow show`;
- persisted `workflow step`;
- bounded `workflow run`;
- persisted workflow readiness reports.
- `workflow draft-proposal` dry-run, review-context output, and private draft
  artifact output.
- `workflow handoff build/show/scan/export` review-context packets and scanner
  guards.

Remaining V14 implementation gaps:

- `cosheaf eval reviewable-workflow --json`;
- downstream workspace-template and public-KB v0.9 policy/pin closeout.

Authority boundary: workflow output, draft proposals, handoff scan reports,
handoff bundles, and handoff exports remain review context or draft artifacts
only. They are not proof, source metadata, human review, verifier pass, gate
pass, accepted status, accepted theorem/refutation, or promotion authority.
