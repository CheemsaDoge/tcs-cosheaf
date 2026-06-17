# ADR 0031: Cross-Check Evidence And Checker Registry

Status: proposed

Date: 2026-06-18

## Context

V14 produces reviewable workflow packets from issues, including draft proposal
and handoff context. The next useful step is not autonomous proof search. It is
a typed way to collect and compare checker signals while preserving the public
KB authority boundary.

Current checker-related surfaces already distinguish pass, fail, error, and
skipped verifier results. Optional Lean, SAT, SMT, and external Lean library
reference checks remain unavailable-by-default in normal CI, and skipped
results are not passes.

## Decision

V15 will introduce a typed checker registry and cross-check evidence reports.

The registry records checker identity, supported evidence kinds, command/log
metadata expectations, timeout behavior, and result semantics. It is a dispatch
and reporting layer over bounded checker adapters, not a proof engine.

Cross-check reports may aggregate multiple checker attempts and review signals
for a workflow or artifact candidate. They may record agreement, conflict,
missing evidence, unavailable tools, and review gaps. They do not write accepted
knowledge or replace source metadata and human review.

## Authority Boundary

Checker registry entries and cross-check reports are not:

- proof;
- source metadata;
- human review;
- verifier pass unless a real checker result says pass;
- gate pass;
- accepted status;
- accepted theorem/refutation;
- promotion authority.

A successful Lean `#check` or external-library reference check only means the
referenced import and symbol resolved. It does not prove informal/formal
semantic alignment.

## Consequences

- Missing optional tools must produce `skipped`, not `pass`.
- Reports must preserve raw command metadata and logs for real checker runs.
- Reports must stay in runtime, review-context, or private-draft paths unless a
  later reviewed policy explicitly allows another location.
- Public KB policy must reject cross-check reports as source metadata, accepted
  proof, human review, verifier/gate pass, accepted status, accepted refutation,
  or promotion authority.
- The registry should be deterministic and testable with fake backends in CI.

## Rejected Options

- Treating a cross-check report as human review.
- Treating a workflow packet as accepted proof.
- Making Lean, SAT, SMT, CSLib, mathlib, or hosted providers mandatory in CI.
- Auto-updating artifact formalization status or accepted status from checker
  output.
