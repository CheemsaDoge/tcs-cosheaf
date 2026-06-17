# Current Milestone

Milestone: **v0.10.0 Cross-Check Evidence + Checker Registry**

Status: **V15 planning landed after V14 closeout**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V15.md

Current package version: `0.9.0`

Current release: <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>

Current focus:

- design the typed checker registry and cross-check evidence report boundary;
- keep cross-check output as review context only;
- preserve skipped-not-pass semantics for unavailable optional tools;
- keep accepted promotion, human review, source metadata, verifier, and gate
  semantics unchanged.

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
handoff bundles, handoff exports, eval reports, future cross-check reports, and
checker registry metadata remain review context or draft artifacts only. They
are not proof, source metadata, human review, verifier pass without a real
checker result, gate pass, accepted status, accepted theorem/refutation, or
promotion authority.
