# ADR 0006: G10 Formal Link Gate

## Status

Accepted

## Context

ADR 0005 introduced artifact metadata for formal links:
`formalizations`, `alignment`, and `verification_policy`. Those fields let
artifacts reference external Lean declarations without copying proof bodies,
adding CSLib/mathlib dependencies, or requiring Lean in CI.

After the metadata layer exists, the gatekeeper needs to catch inconsistent
policy states early. For example, an artifact can say it requires a formal link
while carrying no formalization references, or say it requires alignment review
while alignment is still requested or rejected.

This enforcement must stay metadata-only. The gatekeeper must not execute Lean,
fetch external libraries, install CSLib/mathlib, or claim that a Lean check
proves informal/formal semantic alignment.

## Decision

Add G10 Formal Link Gate as a static gatekeeper check over loaded artifact
metadata.

G10 validates consistency among:

- `verification_policy`
- `formalizations`
- `alignment`

G10 produces blocking issues for policy contradictions such as missing required
formal links, missing required checked formalizations, missing required
human-reviewed alignment, rejected alignment on accepted artifacts, and required
formal links whose only formalizations are `broken` or `deprecated`.

G10 produces nonblocking warnings for review-relevant but nonfatal states such
as formal links present without a requiring policy, planned formalizations on
accepted artifacts, requested alignment review on accepted artifacts, broken or
deprecated links when another active link exists, and checked external-library
references that do not yet have verifier-result linkage.

## Consequences

- `cosheaf gate run` reports G10 alongside G1-G9.
- Blocking G10 issues make the gatekeeper verdict fail and therefore block
  accepted promotion through the existing gatekeeper mechanism.
- Warning-only G10 output does not fail the gatekeeper and is not a proof
  failure.
- G10 does not change artifact schema fields.
- G10 does not add a new CLI command.
- G10 does not execute Lean or inspect external Lean libraries.
- G10 does not prove informal/formal alignment.
- Future external-library checking can build on the existing metadata and gate
  report surface without changing this decision.

## Non-Goals

- Do not implement Lean execution.
- Do not implement CSLib/mathlib dependencies.
- Do not fetch external Lean libraries or require network access.
- Do not add index/query support for formalization metadata.
- Do not add context-pack display for formalization metadata.
- Do not change accepted-promotion policy beyond ordinary gatekeeper blocking
  behavior.
- Do not implement the future `LeanLibraryRefAdapter`.
