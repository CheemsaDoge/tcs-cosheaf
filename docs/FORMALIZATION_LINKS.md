[中文版](FORMALIZATION_LINKS.zh-CN.md) | [English](FORMALIZATION_LINKS.md)

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

These policy values are schema-validated and are also checked by G10 Formal
Link Gate for static metadata consistency. G10 contributes ordinary gatekeeper
blocking issues when required formal links, Lean checks, or alignment reviews
are missing. It does not change accepted promotion policy beyond the existing
rule that blocking gatekeeper issues prevent promotion.

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
references. It records links so future tooling and review workflows have a
stable metadata surface.

## G10 Formal Link Gate

G10 is a static metadata gate over `formalizations`, `alignment`, and
`verification_policy`. It does not execute Lean, install CSLib or mathlib,
fetch external libraries, or require network access.

G10 blocks artifacts whose policy requires a formal link, Lean check, or
alignment review when the corresponding metadata is absent or not reviewed. It
also blocks accepted artifacts with rejected alignment and required formal-link
policies whose only formalizations are `broken` or `deprecated`.

G10 warnings are nonblocking and are not proof failures. Warnings highlight
metadata that needs attention, such as planned formalizations on accepted
artifacts, requested alignment review on accepted artifacts, checked external
library references without verifier evidence linkage, or formal links present
when policy does not require them.

## Context Packs

Issue-scoped context packs include a compact formal-link summary for relevant
artifacts when formal metadata is present or policy-relevant. The summary shows
formal declaration references, alignment status, verification policy, and
static G10-relevant hints such as required formal links, required Lean checks,
required alignment review, rejected alignment, or planned formalizations.

This display is metadata-only. It helps agents see the formal-link surface, but
it does not load gate reports, does not claim the current G10 verdict, and does
not say that Lean has verified the informal artifact.

## SQLite Index And Query API

`cosheaf index rebuild` writes formal-link metadata into generated index
outputs:

- `.cosheaf/index.sqlite` table `formalizations`
- `.cosheaf/index.sqlite` table `artifact_formal_policy`
- `.cosheaf/artifact_manifest.json` formalization, alignment-status, and
  verification-policy fields per artifact

The SQLite query API can list formalizations by artifact, library, symbol,
status, or import path, and can list policy rows requiring formal links, Lean
checks, or alignment review. The query API is read-only: it reads an existing
`.cosheaf/index.sqlite` file and does not rebuild indexes implicitly.

These index and query surfaces remain metadata-only. They do not check whether
CSLib or mathlib symbols exist, do not fetch external libraries, and do not run
Lean.

## Future Work

- External Lean library reference checking using `import_path` and `symbol`.
- Public KB artifacts with planned or reviewed formalization links.
- A future `LeanLibraryRefAdapter` or equivalent checker surface.

## Current Limitations

- No CSLib or mathlib dependency is added.
- No network access is required or used.
- No external Lean library checkout is inspected.
- No natural-language autoformalization is implemented.
- No automatic informal/formal alignment proof is implemented.
- G10 is metadata-only and does not execute Lean.
- Index/query support is metadata-only and does not perform Lean or library
  existence checks.
- Context-pack display is metadata-only and does not claim Lean verification.
- No accepted-promotion policy change is added beyond normal gatekeeper
  blocking behavior.
