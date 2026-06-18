# Current Milestone

Milestone: **V17 / v0.12.0 Research Memory Learning + Benchmark Suite v1**

Status: **V17 Phase E.1 static research reports**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V17.md

Current package version: `0.11.0`

Latest published release:
<https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v0.11.0>

`v0.11.0` publication closeout status: tag, GitHub release, post-tag release
smoke, workspace-template pin update, and public KB CI/docs pin update are
complete. V17 starts from that published baseline and focuses on deterministic
sidecar memory updates, benchmark suite v1, comparative reports, and static
review reports.

Current focus:

- land V17 Phase E.1 `static-research-dashboard-reports`: static Markdown/JSON
  review directories for existing workflow, campaign, and benchmark records;
- preserve skipped-not-pass semantics for unavailable optional tools; and
- keep accepted promotion, human review, source metadata, verifier, and gate
  semantics unchanged.

Planned V17 surface:

- post-v0.11.0 audit and V17 plan/ADR (A.1, landed);
- deterministic memory update policy v1 (B.1, landed);
- benchmark suite v1 (C.1, landed);
- comparative workflow/campaign/benchmark reports (D.1, landed);
- static Markdown/JSON research reports (E.1, current);
- `v0.12.0` release candidate and publication closeout.

Current V17 B.1 surface:

- `cosheaf.memory.updates` sidecar DTOs and policy helpers;
- `.cosheaf/memory/update-runs/<run-id>.json`;
- `.cosheaf/memory/weights.json`;
- `cosheaf memory update-from-workflow <workflow-id> --json`;
- `cosheaf memory update-from-campaign <campaign-id> --json`;
- `cosheaf memory rebuild --json`; and
- `cosheaf memory explain <artifact-id> --json`.

Current V17 C.1 surface:

- `cosheaf.benchmark` benchmark suite aggregator;
- `.cosheaf/benchmark-runs/<run-id>/run.json`;
- `cosheaf benchmark list --json`;
- `cosheaf benchmark run --suite <suite> --json`; and
- `cosheaf benchmark report <run-id> --out <path> --json`.

Current V17 D.1 surface:

- `cosheaf.compare` deterministic comparison DTOs and helpers;
- `cosheaf compare workflows <before-id> <after-id> --json`;
- `cosheaf compare campaigns <before-id> <after-id> --json`; and
- `cosheaf compare benchmarks <before-id> <after-id> --json`.

Current V17 E.1 surface:

- `cosheaf.reports` static report DTOs and helpers;
- `cosheaf report workflow <workflow-id> --out <dir> --json`;
- `cosheaf report campaign <campaign-id> --out <dir> --json`; and
- `cosheaf report benchmark <run-id> --out <dir> --json`.

V17 non-goals:

- no model training;
- no default network, API-key, or model-call requirement;
- no arbitrary shell execution;
- no accepted KB write;
- no human-review creation;
- no source-metadata fabrication;
- no YAML artifact mutation from memory updates;
- no benchmark/comparison/static-report-as-truth or accepted-status claims; and
- no accepted-status, accepted theorem/refutation, verifier/gate, or promotion
  authority from memory, benchmark, comparison, or static-report output.

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

Completed V16 implementation and downstream closeout:

- Phase B.1 `campaign-model-core` landed in issue #448 / PR #449;
- Phase C.1 `external-operator-protocol-v2` landed;
- Phase D.1 `campaign-runner-budget-controller` landed;
- Phase E.1 `campaign-eval-and-handoff` landed in issue #454 / PR #455;
- workspace-template campaign demo landed in downstream issue #88 / PR #89;
- public KB campaign-output policy guard landed in downstream issue #102 / PR
  #103;
- `v0.11.0` release-candidate metadata landed in issue #456 / PR #457;
- the annotated `v0.11.0` tag and GitHub release are published;
- post-tag release smoke from `@v0.11.0` passed;
- workspace-template active pins moved to `@v0.11.0` in downstream issue #90 /
  PR #91; and
- public KB CI/docs pins moved to `@v0.11.0` in downstream issue #104 / PR
  #105.

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
