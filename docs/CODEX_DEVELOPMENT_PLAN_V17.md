# TCS-Cosheaf Development Plan V17

Target: `v0.12.0 Research Memory Learning + Benchmark Suite v1`

Status: Phase D.1 comparative run reports after the published `v0.11.0` External
Operator Campaigns release and downstream workspace/public-KB pin closeout.

## Goal

Turn workflow and campaign history into deterministic memory updates and
measurable benchmark progress, so repeated attempts get smarter without making
AI output authoritative.

This is operational learning, not model training:

- workflow/campaign outcome: historical signal;
- Cosheaf memory: deterministic sidecar weights and explanations;
- YAML artifacts: source of truth, unchanged by memory updates;
- benchmarks: regression evidence, not accepted knowledge.

## Non-Goals

- No model training.
- No automatic theorem proving.
- No automatic accepted-artifact promotion.
- No human-review creation.
- No default hosted provider, network call, API key, or model call in CI.
- No arbitrary shell execution.
- No YAML artifact mutation from memory updates.
- No claim that benchmark success proves mathematical correctness.

## Global Invariants

- Memory weights are sidecar guidance, not truth.
- Memory updates must not modify YAML artifacts.
- Memory update success is not accepted status.
- Benchmark success is not human review or promotion authority.
- Public mode must not leak private KB content.
- Runtime outputs remain under ignored `.cosheaf/` paths unless exported as
  explicit review context.
- All memory updates must be deterministic, explainable, bounded, rebuildable,
  and reversible.
- Skipped, unsupported, unavailable, and inconclusive rows are not passes.

## Phase Structure

1. Phase A: post-`v0.11.0` audit and V17 landing. Landed in issue #460.
2. Phase B: memory update policy v1. Landed in issue #462.
3. Phase C: benchmark suite v1. Landed in issue #464.
4. Phase D: comparative run reports. Current issue #466.
5. Phase E: retrieval/workflow quality reports as static Markdown/JSON.
6. Phase F: `v0.12.0` release candidate and publication closeout.

## Phase A Scope

Phase A is documentation only:

- `docs/POST_V0110_STATE_AUDIT.md`;
- this V17 plan;
- `docs/ADR/0033-research-memory-learning-benchmark-v1.md`;
- roadmap, milestone, and project-state updates.

It verifies:

- package version is `0.11.0`;
- the `v0.11.0` tag and GitHub release are published;
- campaign CLI exists and is tested;
- campaign handoff and eval exist;
- workspace-template active pins use `v0.11.0`;
- public KB CI/docs pins use `v0.11.0`;
- open issue/PR state across the three repositories; and
- accepted-write, human-review, source-metadata, verifier/gate, and promotion
  authority remain unchanged.

## Phase B Outline

Add deterministic memory updates from workflow and campaign outcomes.

Initial concepts:

- `MemorySignal`;
- `MemoryEdgeUpdate`;
- `MemoryWeightStore`;
- `MemoryUpdatePolicy`;
- `MemoryUpdateRun`.

Allowed signals should stay reviewable and bounded, including retrieved,
used-in-plan, used-in-attempt, used-in-successful-draft, checker-pass,
checker-fail, gate-blocked, review-requested, human-accept-reference,
repeat-failure, and unsafe-output.

Initial CLI:

- `cosheaf memory update-from-workflow <workflow-id> --json`;
- `cosheaf memory update-from-campaign <campaign-id> --json`;
- `cosheaf memory explain <artifact-id> --json`;
- `cosheaf memory rebuild --json`.

Acceptance for Phase B: campaign/workflow history can update deterministic,
rebuildable sidecar memory without modifying YAML artifacts or creating
authority over accepted knowledge.

Phase B.1 implementation adds `cosheaf.memory.updates`, JSON sidecars under
`.cosheaf/memory/update-runs/`, aggregate `.cosheaf/memory/weights.json`, and
the four CLI commands listed above. It remains a sidecar-only policy surface:
it does not mutate YAML artifacts, write accepted knowledge, create human
review, fabricate source metadata, mutate verifier results, mark gates as
passing, call hosted providers, execute shell commands, or promote artifacts.

## Phase C Outline

Create a stable benchmark suite for retrieval, workflow, checking, campaign,
and authority-safety behavior.

Initial CLI:

- `cosheaf benchmark list --json`;
- `cosheaf benchmark run --suite <suite> --json`;
- `cosheaf benchmark report --run-id <run-id> --out <path>`.

Required suites:

- smoke;
- regression;
- authority_negative;
- private_boundary;
- research_loop;
- campaign;
- review_workflow.

Acceptance for Phase C: maintainers can measure whether changes improve or
damage the research harness without needing hosted providers or network access.

Phase C.1 implementation adds `cosheaf.benchmark`, runtime sidecars under
`.cosheaf/benchmark-runs/<run-id>/run.json`, and the three CLI commands listed
above. It aggregates existing deterministic eval harnesses instead of creating
a second fixture system. Benchmark output remains regression evidence only: it
does not mutate YAML artifacts, write accepted knowledge, create human review,
fabricate source metadata, mutate verifier results, mark gates as passing, call
hosted providers, use network access, execute shell commands, or promote
artifacts.

## Phase D Outline

Add side-by-side comparisons for workflows, campaigns, and benchmark runs.

Initial CLI:

- `cosheaf compare workflows <a> <b> --json`;
- `cosheaf compare campaigns <a> <b> --json`;
- `cosheaf compare benchmarks <a> <b> --json`.

Comparisons must be metric-scoped and safety-aware. A newer run is not
globally "better" merely because some score improved.

Phase D.1 implementation adds `cosheaf.compare` and `cosheaf compare
workflows/campaigns/benchmarks`. It reads existing runtime records only and
emits deterministic JSON comparison reports with metric deltas and explicit
safety regressions. Comparison output is analytical review context only: it
does not mutate YAML artifacts, write accepted knowledge, create human review,
fabricate source metadata, mutate verifier results, mark gates as passing, call
hosted providers, execute shell commands, or promote artifacts.

## Phase E Outline

Generate static Markdown/JSON reports, not a web app.

Initial CLI:

- `cosheaf report workflow <workflow-id> --out <dir>`;
- `cosheaf report campaign <campaign-id> --out <dir>`;
- `cosheaf report benchmark <run-id> --out <dir>`.

Reports are review context only. Public-mode report generation must not leak
private context.

## Phase F Outline

Prepare and publish a conservative `v0.12.0` release only after memory,
benchmark, comparison, static-report, downstream policy/demo alignment, and
release documentation pass.

Phase F.1 will prepare package metadata, release notes, and current-status docs
for `0.12.0`. Phase F.2 will publish the annotated tag and GitHub release, run
post-tag release smoke, and align downstream workspace-template/public KB pins
to `@v0.12.0`.

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

For release-candidate work, also run the relevant benchmark CLI. Skipped rows
must be listed as skipped and must not be counted as passes.
