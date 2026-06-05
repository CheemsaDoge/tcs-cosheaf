# Formalization Links

## Purpose

The Formal Link Layer lets an artifact point to formal declarations in external
Lean libraries such as CSLib or mathlib. It is a metadata layer for references,
not a proof-import layer and not a replacement for those libraries.

Cosheaf remains a Git-backed research knowledge base and workflow harness. It
does not vendor CSLib, mathlib, or Lean proofs, and it does not attempt to
rebuild their library ecosystems inside artifact YAML.

## Artifact Fields

Artifacts may now include:

- `formalizations`: references to external formal declarations.
- `alignment`: review metadata for semantic alignment between the informal
  statement and the formal declaration.
- `verification_policy`: a per-artifact policy describing whether a formal
  link, Lean check, or alignment review is expected.

These fields are optional. Existing artifacts that omit them remain valid.

## Formalization References

Each `formalizations` entry records a complete declaration reference:

- `id`: stable local identifier for the link.
- `system`: currently `lean4`.
- `library`: source library name, for example `CSLib` or `mathlib`.
- `library_ref`: library-level reference such as a module, package, commit, or
  catalog key.
- `import_path`: Lean import path.
- `symbol`: declaration name.
- `declaration_kind`: `definition`, `theorem`, `lemma`, `instance`,
  `structure`, or `other`.
- `status`: `planned`, `linked`, `checked`, `broken`, or `deprecated`.
- `check_mode`: `external_library_ref` or `local_file`.
- `expected_type`: optional expected Lean type or a short type summary.
- `notes`: optional reviewer or maintainer notes.

YAML stores these references, not Lean proof bodies. A `formalizations` entry
must not be used as a place to paste library proofs. Link IDs use the same
dot-separated lowercase slug format as artifact IDs. `library`, `library_ref`,
`import_path`, and `symbol` must be non-empty after trimming whitespace.

## Alignment Review

Lean can check a formal declaration, but a Lean pass does not automatically
prove that an informal artifact statement is semantically aligned with that
declaration. Alignment review is a separate human or maintainer review step.

The `alignment` object records:

- `status`: `none`, `requested`, `human_reviewed`, or `rejected`.
- `reviewer`: reviewer identifier when applicable.
- `reviewed_at`: timezone-aware review timestamp or `null`.
- `convention_notes`: convention mismatches or assumptions to inspect.
- `limitations`: known gaps in the alignment claim.

Statuses `human_reviewed` and `rejected` require a non-empty reviewer.
`reviewed_at`, when present, must include timezone information.

For example, a graph-theory theorem may depend on whether loops, parallel
edges, finite graphs, or graph-isomorphism conventions match between the
informal statement and the Lean declaration.

## Verification Policy

The `verification_policy` object records current expectations:

- `source_reviewed`: source metadata and ordinary review are enough.
- `source_reviewed_with_formal_link`: the artifact should carry a formal link,
  but the link is not necessarily checked in CI.
- `machine_checked`: executable evidence or verifier output is expected.
- `lean_required`: a future policy level for artifacts that require Lean
  checking.

The boolean fields `require_formal_link`, `require_lean_check`, and
`require_alignment_review` state the per-artifact expectation explicitly.
`source_reviewed_with_formal_link` requires `require_formal_link: true`.
`lean_required` requires both `require_formal_link: true` and
`require_lean_check: true`.

In this MVP, these policy values are recorded and schema-validated, but they do
not change accepted promotion semantics.

## Relationship To Evidence

Formal library references must not be stored in the existing `evidence` field.
`evidence` remains for repository-local executable evidence, external evidence
paths, and verifier inputs. Formal declaration references belong in
`formalizations` so reviewers can distinguish citation, formal-link, alignment,
and executable-check concepts.

## Lean Adapter Boundary

The current Lean verifier adapter supports only optional plain Lean file
checking through a locally available `lean` command. It does not add Lean,
CSLib, mathlib, or lake as dependencies. It does not fetch libraries and does
not require network access.

When optional Lean tooling is unavailable, Lean verification remains
`skipped`, not `pass`. Skipped verifier output must not be used to claim a
successful formal check.

The Formal Link Layer does not make the Lean adapter check external library
references in this PR. It records links so future tooling and review workflows
have a stable metadata surface.

## Future Work

- G10 Formal Link Gate policy enforcement.
- External Lean library reference checking using `import_path` and `symbol`.
- Public KB artifacts with planned or reviewed formalization links.
- Context-pack display of formalization and alignment metadata.
- Index/query support for formalization references.
- A future `LeanLibraryRefAdapter` or equivalent checker surface.

## Current Limitations

- No CSLib or mathlib dependency is added.
- No network access is required or used.
- No external Lean library checkout is inspected.
- No natural-language autoformalization is implemented.
- No automatic informal/formal alignment proof is implemented.
- No G10 Formal Link Gate is implemented.
- No index/query support is added for formalization metadata.
- No context-pack display is added for formalization metadata.
- No accepted-promotion semantics change in this MVP.
