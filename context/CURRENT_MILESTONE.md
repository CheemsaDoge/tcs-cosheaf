# Current Milestone

Milestone: **V18 / v1.0.0 AI Math Collaborator MVP**

Status: **V18 Phase F.2 v1.0.0 publication closeout complete**

Plan: docs/CODEX_DEVELOPMENT_PLAN_V18.md

Current package version: `1.0.0`

Latest published release:
<https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v1.0.0>

`v1.0.0` publication closeout status: tag, GitHub release, post-tag release
smoke, workspace-template pin update, and public KB CI/docs pin update are
complete.

Current focus:

- maintain the published `v1.0.0` AI Math Collaborator MVP baseline;
- keep downstream workspace-template and public KB pins aligned to `v1.0.0`;
- preserve skipped-not-pass semantics for unavailable optional tools; and
- keep accepted promotion, human review, source metadata, verifier, and gate
  semantics unchanged.

Post-v1.0.0 Longplan A architecture work:

- issue #492 / branch `arch-dependency-audit` records the current CLI,
  service, DTO, and authority-boundary audit before any refactor;
- `docs/ARCHITECTURE_REFACTOR_AUDIT.md` is the A0.1 audit artifact; and
- `docs/ADR/0035-app-boundary.md` proposes `cosheaf.app` as the next stable
  application-usecase boundary without changing runtime behavior in A0.1.

Planned V18 surface:

- post-v0.12.0 audit and v1.0 scope freeze (A.1, landed);
- CLI/API polish and deprecation cleanup (B.1, landed);
- canonical workspace-template AI math collaborator demo (C.1, landed in
  workspace-template PR #95);
- documentation and operator packaging (D.1, landed);
- security, authority, and benchmark release audit (E.1, landed);
- `v1.0.0` release candidate and publication closeout (F.1/F.2 landed).

Current V18 F.2 surface:

- package metadata and `cosheaf.__version__` record `1.0.0`;
- `docs/releases/v1.0.0.md` records the published release scope and authority
  boundary;
- the public `v1.0.0` tag and GitHub release are published;
- post-tag release smoke from `@v1.0.0` passed; and
- workspace-template PR #97 and public KB PR #109 moved active pins to
  `@v1.0.0`.

Frozen v1.0.0 scope:

- package existing workflow, checker, gap, campaign, memory, benchmark,
  compare, and static-report surfaces as a stable MVP;
- make workspace-template the canonical demo path;
- keep CLI as the oracle and MCP/skills/provider surfaces optional;
- defer web UI, default hosted providers, automatic theorem proving,
  autoformalization, automatic promotion, and multi-user permissions to
  v1.1+ or later.

Landed V18 B.1 surface:

- `cosheaf interface list --json` emits a deterministic stable-interface
  discovery payload;
- `cosheaf interface list` emits a text summary of the same stable v1.0 CLI
  surface;
- `cosheaf research-run ...` is the preferred research-run provenance root
  command; and
- `cosheaf run ...` remains a compatibility alias for existing scripts.

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

Current V17 F.2 surface:

- package metadata and `cosheaf.__version__` record `0.12.0`;
- `docs/releases/v0.12.0.md` records the published release scope and
  authority boundary;
- the public `v0.12.0` tag and GitHub release are published;
- post-tag release smoke from `@v0.12.0` passed; and
- workspace-template PR #93 and public KB PR #107 moved active pins to
  `@v0.12.0`.

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

V18 non-goals:

- no autonomous AI mathematician;
- no default hosted LLM runtime;
- no automatic theorem proving;
- no automatic accepted promotion;
- no AI-as-human-review;
- no production SaaS, web UI, or multi-user permission system; and
- no broad feature expansion before v1.0.0 release unless it fixes a release
  blocker.

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
