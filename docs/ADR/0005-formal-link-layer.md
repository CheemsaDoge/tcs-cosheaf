# ADR 0005: Formal Link Layer

## Status

Accepted

## Context

TCS-Cosheaf artifacts need a way to point at formal declarations in external
Lean libraries such as CSLib or mathlib. The repository already has a minimal
optional Lean adapter for repository-local plain Lean files, but that adapter
is not a full library integration and CI must not require Lean, CSLib, mathlib,
lake, or network access.

TCS-Cosheaf should not become another Lean theorem library. CSLib and mathlib
should remain upstream formal proof libraries; Cosheaf should connect
source-reviewed TCS artifacts to those external declarations.

Using the existing `evidence` field for formal declaration references would
confuse executable evidence with formal-library metadata. It would also make it
too easy to treat a declaration link as a passed verifier result or as proof
that the informal statement is aligned with the formal declaration.

## Decision

Add optional artifact metadata fields:

- `formalizations: list[FormalizationRef]`
- `alignment: AlignmentReview`
- `verification_policy: VerificationPolicy`

`FormalizationRef` stores references to Lean declarations with library,
import-path, symbol, declaration-kind, status, check-mode, expected-type, and
notes metadata. The YAML stores declaration references, not Lean proof bodies.

`AlignmentReview` records separate semantic alignment review between the
informal artifact statement and the formal declaration. A Lean pass on a
declaration or local file is not treated as automatic informal/formal alignment.

`VerificationPolicy` records whether an artifact expects a formal link, Lean
check, or alignment review. In this MVP the policy is schema/model metadata
only and does not change accepted promotion semantics.

## Consequences

- Existing artifacts remain valid because the new fields have
  backward-compatible defaults.
- Formal links become a first-class artifact concept separate from evidence
  paths and source citations.
- Artifacts can reference CSLib, mathlib, or other Lean libraries without
  copying proofs into YAML.
- Optional Lean tooling remains optional. Missing Lean tooling is still
  `skipped`, never `pass`.
- Future library-checking or alignment-review gates have a stable public model
  to build on.
- Future checkers can use `import_path` and `symbol` without changing the
  artifact schema again.

## Non-Goals

- Do not add CSLib, mathlib, lake, or Lean as CI dependencies.
- Do not fetch external libraries or require network access.
- Do not implement full Lean library checking.
- Do not implement G10 Formal Link Gate enforcement.
- Do not add index/query support for formalization metadata.
- Do not add context-pack display for formalization metadata.
- Do not implement natural-language autoformalization.
- Do not prove informal statement alignment automatically.
- Do not change accepted promotion semantics in this PR.
