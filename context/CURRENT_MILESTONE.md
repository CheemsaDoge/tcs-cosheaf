# Current Milestone

Milestone: **v0.10.0 Cross-Check Evidence + Checker Registry**

Status: **V15 published; V16 kickoff is next**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V15.md

Current package version: `0.10.0`

Latest published release:
<https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.10.0>

`v0.10.0` publication closeout status: tag, GitHub release, post-tag release
smoke, workspace-template pin update, and public KB CI pin update are complete.
The next task is the V16 post-`v0.10.0` audit and plan landing; do not start
campaign runtime implementation before that audit.

Current focus:

- keep package metadata, release notes, roadmap, milestone, project state, and
  release checklist aligned with the published `v0.10.0` state;
- prepare the V16 audit/plan/ADR for external operator campaigns as a docs-only
  kickoff task;
- preserve skipped-not-pass semantics for unavailable optional tools; and
- keep accepted promotion, human review, source metadata, verifier, and gate
  semantics unchanged.

Current V15 surface on the development line:

- `cosheaf checker ...` typed checker sidecar commands;
- `cosheaf workflow cross-check <workflow-id> --json`;
- `cosheaf workflow evidence-report <workflow-id> --json`;
- `cosheaf workflow export-crosscheck <workflow-id> --out reviews/workflow/<name>.json --json`;
- `cosheaf gap list <workflow-id> --json`;
- `cosheaf gap export <workflow-id> --out reviews/workflow/<name>.json --json`;
- `cosheaf eval checker-crosscheck --json`.

Completed V15 closeout:

- framework checker/cross-check eval and ecosystem smoke landed in issue #440;
- workspace-template cross-check demo landed in downstream PR #85;
- public KB cross-check report policy guard landed in downstream PR #99;
- `v0.10.0` release-candidate metadata landed in issue #442 / PR #443;
- the annotated `v0.10.0` tag and GitHub release are published;
- post-tag release smoke from `@v0.10.0` passed;
- workspace-template active pins moved to `@v0.10.0` in PR #87;
- public KB CI/docs pins moved to `@v0.10.0` in PR #101.

Completed V14 closeout:

- persistent workflow storage under `.cosheaf/workflows/`;
- `workflow show`;
- persisted `workflow step`;
- bounded `workflow run`;
- persisted workflow readiness reports;
- `workflow draft-proposal` dry-run, review-context output, and private draft
  artifact output;
- `workflow handoff build/show/scan/export` review-context packets and scanner
  guards;
- `cosheaf eval reviewable-workflow --json` framework benchmark coverage;
- workspace-template `make reviewable-workflow-demo`;
- public KB workflow packet policy guard for source metadata, accepted proof,
  and human review misuse.

Authority boundary: workflow output, draft proposals, handoff scan reports,
handoff bundles, handoff exports, eval reports, cross-check reports, gap
reports, and checker registry metadata remain review context or draft
artifacts only. They are not proof, source metadata, human review, verifier
pass without a real checker result, gate pass, accepted status, accepted
theorem/refutation, or promotion authority.
