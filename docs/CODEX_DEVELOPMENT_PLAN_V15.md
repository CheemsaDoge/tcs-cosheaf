# TCS-Cosheaf Development Plan V15

Target: `v0.10.0 Cross-Check Evidence + Checker Registry`

Status: planned. This plan starts after the V14 `v0.9.0` reviewable-workflow
line and its downstream workspace/public-KB closeout are complete.

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
2. Phase B: typed checker registry core.
3. Phase C: cross-check evidence report in workflow output.
4. Phase D: proof-obligation and gap taxonomy.
5. Phase E: eval plus workspace/public-KB policy smoke.
6. Phase F: `v0.10.0` release candidate and publication closeout.

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

## Phase E Outline

Add deterministic eval and three-repository smoke coverage for cross-check
evidence. Workspace-template may get a demo target. Public KB policy must reject
cross-check reports as source metadata, accepted proof, human review, verifier
pass, gate pass, accepted status, accepted refutation, or promotion authority.

## Phase F Outline

Prepare and publish a conservative `v0.10.0` release only after framework
verification, downstream pin/demo/policy alignment, post-tag smoke, and release
documentation all pass.

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
