# Current Milestone

Milestone: **v0.10.0 Cross-Check Evidence + Checker Registry**

Status: **V15 Phase E framework checker/cross-check eval in progress**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V15.md

Current package version: `0.9.0`

Current release: <https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.9.0>

Current focus:

- use the typed checker registry from Phase B;
- attach workflow cross-check reports and gap reports as review context only;
- run deterministic checker/cross-check eval coverage for reviewer-facing
  evidence boundaries;
- preserve skipped-not-pass semantics for unavailable optional tools;
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
