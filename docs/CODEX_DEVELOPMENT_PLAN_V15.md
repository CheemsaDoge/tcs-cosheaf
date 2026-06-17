# TCS-Cosheaf Development Plan V15

Target: `v0.10.0 Cross-Check Evidence + Checker Registry`

Status: completed and published as the conservative `v0.10.0` Cross-Check
Evidence + Checker Registry release. Phase A through Phase F have landed after
the V14 `v0.9.0` reviewable-workflow line and downstream workspace/public-KB
closeout.

## Goal

Add a typed checker registry and cross-check evidence reports that help a human
reviewer compare multiple weak signals around a research claim. The output is a
review aid. It is not proof, human review, source metadata, accepted status, or
promotion authority.

## Non-Goals

- No automatic theorem proving.
- No automatic accepted-artifact promotion.
- No human-review creation.
- No default hosted provider calls.
- No schema or artifact status change in Phase A.
- No claim that Lean, SAT, SMT, CSLib, mathlib, or informal/formal alignment
  has succeeded unless a real checker ran and recorded evidence.

## Phase Structure

1. Phase A: post-v0.9.0 audit and V15 landing.
2. Phase B: typed checker registry core. Landed in issue #436.
3. Phase C: cross-check evidence report in workflow output. Landed in issue #438.
4. Phase D: proof-obligation and gap taxonomy. Landed in issue #438.
5. Phase E: eval plus workspace/public-KB policy smoke. Landed in framework
   issue #440, workspace-template PR #85, and public KB PR #99.
6. Phase F: `v0.10.0` release candidate and publication closeout. F.1 landed
   in issue #442 / PR #443; F.2 landed in issue #444 plus downstream
   workspace-template PR #87 and public KB PR #101.

## Phase A Scope

Phase A is this documentation landing:

- `docs/POST_V090_STATE_AUDIT.md`;
- this V15 plan;
- `docs/ADR/0031-cross-check-evidence-checker-registry.md`;
- roadmap, milestone, and project-state updates.

It verifies:

- package version is `0.9.0`;
- `v0.9.0` release notes say published;
- V14 workflow CLI surfaces exist on current `main`;
- workflow handoff remains review context only;
- workspace-template active pin is `v0.9.0`;
- public KB CI pin is `v0.9.0`;
- no accepted-write, human-review, source-metadata, verifier/gate, or promotion
  authority widened.

## Phase B Outline

Implement the typed registry core without changing accepted knowledge policy.
The registry should describe available checker families, normalized result
status, supported inputs, timeout/log metadata, and skipped/error/pass/fail
semantics. Missing optional tools remain `skipped`, never `pass`.

## Phase C Outline

Attach cross-check evidence reports to reviewable workflows as runtime or
review-context output. Reports may summarize checker attempts, contradictions,
gaps, and skipped checks. They must not update artifact status or write
accepted KB paths.

Current implementation surface:

- `cosheaf workflow cross-check <workflow-id> --json`;
- `cosheaf workflow evidence-report <workflow-id> --json`;
- `cosheaf workflow export-crosscheck <workflow-id> --out reviews/workflow/<name>.json --json`;
- runtime files under `.cosheaf/workflows/<workflow-id>/crosscheck.json` and
  `crosscheck.md`.

## Phase D Outline

Add a proof-obligation and gap taxonomy that distinguishes:

- missing source;
- missing human review;
- missing verifier evidence;
- checker unavailable;
- checker failed;
- informal/formal alignment unresolved;
- dependency unresolved;
- private/public boundary issue;
- accepted-promotion blocker.

The taxonomy is advisory and review-oriented.

Current implementation surface:

- `cosheaf gap list <workflow-id> --json`;
- `cosheaf gap export <workflow-id> --out reviews/workflow/<name>.json --json`;
- runtime file `.cosheaf/workflows/<workflow-id>/gaps.json`;
- workflow handoff `review_gaps` summary.

## Phase E Outline

Add deterministic eval and three-repository smoke coverage for cross-check
evidence. Workspace-template may get a demo target. Public KB policy must reject
cross-check reports as source metadata, accepted proof, human review, verifier
pass, gate pass, accepted status, accepted refutation, or promotion authority.

Current framework-side implementation surface:

- `cosheaf eval checker-crosscheck --json`;
- default cases under `evals/checker_crosscheck/cases.yaml`;
- Python APIs in `cosheaf.evals.checker_crosscheck`;
- ecosystem smoke row `framework.checker-crosscheck-eval`.

Downstream closeout has landed:

- workspace-template PR #85 adds the cross-check demo path;
- public KB PR #99 updates the policy guard so cross-check reports, evidence
  reports, gap reports, checker sidecars, and checker/cross-check eval reports
  cannot become source metadata, human review, verifier pass, gate pass,
  accepted status, accepted theorem/refutation, or promotion authority.

## Phase F Outline

Prepare and publish a conservative `v0.10.0` release only after framework
verification, downstream pin/demo/policy alignment, post-tag smoke, and release
documentation all pass.

Phase F.1 prepared package metadata, release notes, and current-status docs for
`0.10.0`. Phase F.2 published the annotated tag and GitHub release, ran
post-tag release smoke, and aligned downstream workspace-template/public KB
pins to `@v0.10.0`.

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
public KB policy guard commands.
