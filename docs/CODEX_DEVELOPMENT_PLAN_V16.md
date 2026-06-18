# TCS-Cosheaf Development Plan V16

Target: `v0.11.0 External AI Operator Harness + Bounded Multi-Run Campaigns`

Status: Phase A has landed after the published `v0.10.0` Cross-Check Evidence +
Checker Registry release and downstream workspace/public-KB pin closeout. Phase
B.1 `campaign-model-core`, Phase C.1 `external-operator-protocol-v2`, Phase
D.1 `campaign-runner-budget-controller`, and Phase E.1
`campaign-eval-and-handoff` have landed. Downstream workspace-template campaign
demo and public KB campaign-output policy guard coverage have landed. Phase
F.1 `release-v0110-readiness-and-rc` is the current release-candidate
increment.

## Goal

Add a bounded campaign harness that lets an external operator run many attempts
against one issue while Cosheaf controls context, budgets, outputs, scans,
checks, and review handoff.

The boundary is deliberate:

- External AI operator: tool user.
- Cosheaf: deterministic controller, recorder, scanner, budget enforcer, and
  review handoff builder.

V16 should not embed a hosted LLM as an internal autonomous system owner.

## Non-Goals

- No automatic theorem proving.
- No automatic accepted-artifact promotion.
- No human-review creation.
- No default hosted provider, network call, API key, or model call in CI.
- No arbitrary shell execution through campaign runtime.
- No accepted KB writes from campaign, workflow, operator, or checker output.
- No schema, CLI, or version changes in Phase A.
- No claim that campaign success is proof, source metadata, human review,
  accepted status, accepted theorem/refutation, or promotion authority.

## Global Invariants

- Campaign outputs are review context only.
- Attempt success is not accepted status.
- Operator output cannot create human review.
- Validate, gate, checker, benchmark, or campaign success is not accepted
  knowledge.
- Public mode must not leak private KB content.
- Runtime outputs remain under ignored `.cosheaf/` paths unless exported as
  explicit review context.
- YAML artifact records remain the source of truth. Campaign records,
  scorecards, weights, reports, and packets are sidecars.
- Skipped, unsupported, unavailable, and inconclusive results are not passes.

## Phase Structure

1. Phase A: post-`v0.10.0` audit and V16 landing. Landed in issue #446.
2. Phase B: campaign model and storage. B.1 `campaign-model-core` landed in
   issue #448 / PR #449.
3. Phase C: external operator task/result protocol v2. C.1
   `external-operator-protocol-v2` has landed.
4. Phase D: campaign runner and budget controller. D.1
   `campaign-runner-budget-controller` has landed.
5. Phase E: campaign review/handoff and eval. E.1
   `campaign-eval-and-handoff` has landed in issue #454 / PR #455. Downstream
   workspace-template issue #88 / PR #89 and public KB issue #102 / PR #103
   completed campaign demo and policy guard coverage.
6. Phase F: `v0.11.0` release candidate and publication closeout. F.1 is
   current.

## Phase A Scope

Phase A is documentation only:

- `docs/POST_V0100_STATE_AUDIT.md`;
- this V16 plan;
- `docs/ADR/0032-external-operator-campaign-harness.md`;
- roadmap, milestone, and project-state updates.

It verifies:

- package version is `0.10.0`;
- the `v0.10.0` tag and GitHub release are published;
- checker registry CLI exists and is tested;
- workflow cross-check reports exist and are tested;
- proof-obligation/gap taxonomy exists and is surfaced in workflow reports;
- workspace-template active pins use `v0.10.0`;
- public KB CI pins use `v0.10.0`;
- open issue/PR state across the three repositories; and
- accepted-write, human-review, source-metadata, verifier/gate, and promotion
  authority remain unchanged.

## Phase B Outline

Add durable model/storage for bounded multi-run research campaigns. The first
model set should cover:

- `ResearchCampaign`;
- `CampaignAttempt`;
- `CampaignBudget`;
- `CampaignStopCondition`;
- `CampaignScorecard`;
- `CampaignOperatorPolicy`;
- `CampaignRiskFinding`;
- `CampaignComparison`.

Runtime storage should stay under ignored `.cosheaf/campaigns/<campaign-id>/`
paths. Initial CLI should include:

- `cosheaf campaign start --issue <issue-id> --json`;
- `cosheaf campaign show <campaign-id> --json`;
- `cosheaf campaign append-attempt <campaign-id> --input-json <path> --json`;
- `cosheaf campaign scorecard <campaign-id> --json`;
- `cosheaf campaign finalize <campaign-id> --json`.

Acceptance for Phase B: a campaign can record many attempts and produce an
inspectable scorecard without creating authority over accepted knowledge.

## Phase C Outline

Define stable task/result packets for Codex-style external operators:

- `operator_task_v2.json`;
- `operator_result_v2.json`;
- `cosheaf campaign export-task <campaign-id> --json --out <path>`;
- `cosheaf campaign import-result <campaign-id> --input-json <path> --json`;
- `cosheaf campaign next <campaign-id> --json`.

Result import must reject human-review, promotion, verifier-pass,
accepted-status, accepted-refutation, accepted KB write, unsafe path, and
private-leak overclaims.

Acceptance for Phase C: an external operator can receive a bounded task and
return a structured result without internal provider integration.

## Phase D Outline

Add campaign-level loop control, stop policies, and safety gates:

- `cosheaf campaign run <campaign-id> --max-attempts <n> --json`;
- `cosheaf campaign pause <campaign-id> --json`;
- `cosheaf campaign resume <campaign-id> --json`;
- `cosheaf campaign scan <campaign-id> --json`.

Budget controls should cover maximum attempts, runtime minutes, repeated
failures, draft outputs, checker errors, and private findings. Stop conditions
should be explicit and reviewable, including budget exhaustion, unsafe output,
repeated failure without justification, and human pause.

Acceptance for Phase D: a campaign can run bounded attempts while refusing
unsafe or repetitive paths.

Phase D.1 implements deterministic controller checks only. `campaign run`
calls the scanner and applies pause, unsafe-output, repeated-failure, attempt
budget, and draft-output budget stop policies. It records no shell execution,
provider calls, accepted writes, human review, verifier pass, gate pass, or
promotion authority. Provider-backed or shell-backed campaign loops remain
out of scope for D.1.

## Phase E Outline

Add campaign eval cases and review handoff summaries:

- `cosheaf campaign handoff <campaign-id> --out <dir> --json`;
- `cosheaf eval campaign --json`;
- workspace-template `make campaign-demo`;
- public KB policy rejection for campaign outputs as accepted proof, source
  metadata, human review, verifier/gate pass, accepted status, accepted
  theorem/refutation, or promotion authority;
- ecosystem smoke row for campaign eval/demo/policy coverage.

Acceptance for Phase E: campaign output becomes reviewable handoff context, not
accepted knowledge.

Phase E.1 implements the framework-side review handoff and eval surfaces only:
`campaign handoff`, `eval campaign`, default campaign eval cases, and the
framework ecosystem matrix row. Downstream workspace-template campaign demo
and public KB campaign-output policy guard coverage have landed before the
`v0.11.0` release candidate.

## Phase F Outline

Prepare and publish a conservative `v0.11.0` release only after campaign
implementation, downstream demo/policy alignment, post-tag smoke, and release
documentation all pass.

Phase F.1 will prepare package metadata, release notes, and current-status
docs for `0.11.0`. Phase F.2 will publish the annotated tag and GitHub release,
run post-tag release smoke, and align downstream workspace-template/public KB
pins to `@v0.11.0`.

## Required Verification Pattern

For implementation PRs:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

For downstream closeout, also run the relevant workspace-template demo and
public KB policy guard commands. Skipped rows must be listed as skipped and
must not be counted as passes.
