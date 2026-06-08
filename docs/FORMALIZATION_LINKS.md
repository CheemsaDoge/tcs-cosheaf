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
- `library_ref`: manifest library ID, for example `cslib-main` or
  `mathlib-main`.
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
dot-separated lowercase slug format as artifact IDs. `library_ref` uses the
formal library manifest ID syntax, which is lowercase slug or dotted lowercase
slug segments such as `cslib-main` or `lean.mathlib-main`; it is not a Lean
module path. `library`, `import_path`, and `symbol` must be non-empty after
trimming whitespace.

## Formal Library Manifest

Formal library manifests pin external Lean library metadata once, so artifacts
do not repeat repository and commit information in every formalization link.
The example manifest lives at:

- `formal-libs/lean-libraries.example.yaml`

The manifest schema lives at:

- `schemas/formal_library.schema.json`

Each manifest entry records:

- `id`: stable manifest ID used by `formalizations[].library_ref`.
- `name`: human-readable library name.
- `system`: currently `lean4`.
- `git`: source repository URL for the external library.
- `commit`: pinned revision.
- `lean_version`: Lean version associated with the pin.
- `lake_manifest`: manifest file or fingerprint reference for the pin.
- `notes`: optional maintainer notes.

The manifest is metadata. Loading or validating it does not fetch CSLib,
mathlib, or any other library; it does not run `lean`, `lake`, or `#check`;
and it does not prove that an artifact statement is aligned with a formal
declaration. Artifact `library_ref` values can be checked against a manifest by
using the core helper API. The optional external Lean library reference checker
uses artifact formalization metadata; it still does not fetch, pin, or build
external library checkouts automatically.

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
- `lean_required`: a policy level for artifacts that require Lean checking
  metadata.

The boolean fields `require_formal_link`, `require_lean_check`, and
`require_alignment_review` state the per-artifact expectation explicitly.
`source_reviewed_with_formal_link` requires `require_formal_link: true`.
`lean_required` requires both `require_formal_link: true` and
`require_lean_check: true`.

These policy values are schema-validated and are also checked by G10 Formal
Link Gate for metadata and verifier-result consistency. G10 contributes
ordinary gatekeeper blocking issues when required formal links, Lean checks, or
alignment reviews are missing. It does not change accepted promotion policy
beyond the existing rule that blocking gatekeeper issues prevent promotion.

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

The Formal Link Layer does not make the plain-file Lean adapter check external
library references. It records links so separate verifier tooling and review
workflows have a stable metadata surface.

## External Lean Library Reference Checker

The optional `LeanLibraryRefAdapter` checks linked external Lean references
recorded in `formalizations`. It is separate from the plain-file `LeanAdapter`.

The adapter considers only formalization entries with:

- `system: lean4`
- `check_mode: external_library_ref`
- `status: linked` or `status: checked`

Planned formalizations are skipped by default. For a checkable entry, the
adapter creates a temporary Lean file outside the repository:

```lean
import <import_path>
#check <symbol>
```

It then runs either `lean <tempfile>` or, when configured, `lake env lean
<tempfile>`. The temporary file is removed after the run. Stdout and stderr are
captured under `.cosheaf/logs/`, and the normalized verifier result records the
command, cwd, timeout, exit code, tool metadata, input label, and log paths.

Missing Lean or lake returns `skipped`, not `pass`. A nonzero process exit is
`fail`; timeout or command startup failure is `error`. A `pass` means only that
Lean resolved the generated import and `#check` command in the configured
environment. It does not prove that the informal artifact statement is
semantically aligned with the formal declaration.

The checker does not fetch CSLib, mathlib, or any other library. It does not
update formalization status automatically and does not make existing public KB
artifacts require Lean in CI. Under the current one-result verifier adapter
contract, one `verify(...)` call checks the first applicable formalization for
an artifact.

## G10 Formal Link Gate

G10 is a metadata and verifier-result consistency gate over `formalizations`,
`alignment`, `verification_policy`, local formal library manifests, and the
G6 verifier results produced earlier in the same gatekeeper run. It does not
execute Lean, install CSLib or mathlib, fetch external libraries, or require
network access. External `#check` results, when produced by the optional
verifier adapter, remain G6 verifier evidence; G10 only checks whether that
evidence is present and passing when policy explicitly requires it.

G10 blocks artifacts whose policy requires a formal link, Lean check, or
alignment review when the corresponding metadata is absent or not reviewed. It
also blocks unknown `library_ref` manifest references, missing local manifest
metadata for artifacts that carry formalization links, accepted artifacts with
rejected alignment, and required formal-link policies whose only
formalizations are `broken` or `deprecated`. When
`require_lean_check: true`, `status: checked` is not enough by itself: a
matching Lean verifier result must have status `pass`. For
`external_library_ref` links, the matching result must be from
`lean_library_ref` for the same formalization ID. Skipped, failed, or errored
verifier results are not passes.

G10 warnings are nonblocking and are not proof failures. Warnings highlight
metadata that needs attention, such as planned formalizations on accepted
artifacts, requested alignment review on accepted artifacts, checked external
library references without verifier evidence linkage, or formal links present
when policy does not require them.

## Context Packs

Issue-scoped context packs include a compact formal-link summary for relevant
artifacts when formal metadata is present or policy-relevant. The summary shows
formal declaration references, alignment status, verification policy, and
G10-relevant policy hints such as required formal links, required Lean checks,
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
Lean. Run the optional verifier adapter separately when a symbol-resolution
check is needed.

## Future Work

- Public KB artifacts with planned or reviewed formalization links.
- CLI ergonomics for requesting external Lean reference checks directly.
- Multi-link reporting when an artifact carries more than one checkable
  formalization.

## Current Limitations

- No CSLib or mathlib dependency is added.
- No network access is required or used.
- No external Lean library checkout is fetched or managed automatically.
- No natural-language autoformalization is implemented.
- No automatic informal/formal alignment proof is implemented.
- G10 is metadata-only and does not execute Lean.
- Index/query support is metadata-only and does not perform Lean or library
  existence checks.
- Context-pack display is metadata-only and does not claim Lean verification.
- External `#check` pass means import and symbol resolution only.
- No accepted-promotion policy change is added beyond normal gatekeeper
  blocking behavior.
