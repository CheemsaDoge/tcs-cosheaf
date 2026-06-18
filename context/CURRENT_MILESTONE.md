# Current Milestone

Milestone: **V16 / v0.11.0 External AI Operator Harness + Bounded Multi-Run Campaigns**

Status: **V16 Phase E.1 campaign-eval-and-handoff landing**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V16.md

Current package version: `0.10.0`

Latest published release:
<https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.10.0>

`v0.10.0` publication closeout status: tag, GitHub release, post-tag release
smoke, workspace-template pin update, and public KB CI pin update are complete.
The V16 post-`v0.10.0` audit, V16 development plan, ADR 0032, Phase B.1
campaign model core, Phase C.1 external operator protocol v2, and Phase D.1
campaign runner budget controller have landed as durable repo memory. The
current task is the Phase E.1 campaign eval and handoff increment: deterministic
campaign handoff export, default campaign eval fixtures, and framework
ecosystem matrix coverage.

Current focus:

- land V16 Phase E.1 `campaign-eval-and-handoff`:
  `cosheaf campaign handoff`, `cosheaf eval campaign`, default campaign eval
  cases, the framework campaign-eval ecosystem matrix row, and updated campaign
  documentation;
- preserve skipped-not-pass semantics for unavailable optional tools; and
- keep accepted promotion, human review, source metadata, verifier, and gate
  semantics unchanged.

Planned V16 surface:

- durable campaign records and scorecards under ignored `.cosheaf/campaigns/`
  runtime paths (B.1, landed);
- external operator task/result packet v2 (C.1, landed);
- campaign budget and stop-condition controller (D.1, landed);
- campaign review handoff reports (E.1, current);
- deterministic `cosheaf eval campaign --json` (E.1, current); and
- downstream workspace-template campaign demo plus public KB policy guard.

V16 non-goals:

- no internal autonomous hosted-provider runtime;
- no default network, API-key, or model-call requirement;
- no arbitrary shell execution;
- no accepted KB write;
- no human-review creation;
- no source-metadata fabrication;
- no accepted-status, accepted theorem/refutation, verifier/gate, or promotion
  authority from campaign output.

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
