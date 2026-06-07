# Artifact Schema

## Purpose

This document describes the research artifact vocabulary, lifecycle assumptions,
and initial machine-readable schema files. The schemas are intentionally
lightweight at this stage: they define file-level contracts that are enforced by
the Pydantic model layer, repository validation, and artifact lifecycle CLI
commands.

## Planned Artifact Types

- `definition`: Introduces a term, object, property, model, or notation.
- `claim`: States a proposition that may be informal, intermediate, or pending stronger classification.
- `theorem`: States a claim intended to be accepted as proven.
- `conjecture`: States a claim believed plausible but not proven.
- `proof`: Provides evidence intended to establish a theorem, claim, or construction property.
- `proof_attempt`: Records a partial, failed, or exploratory proof path.
- `construction`: Describes a mathematical or computational object built from specified inputs.
- `algorithm`: Describes an executable or analyzable procedure.
- `reduction`: Describes a reduction between problems, models, or artifact statements.
- `counterexample`: Records an object or argument disproving a claim or constraining a conjecture.
- `experiment`: Records an empirical, computational, or exploratory test.
- `review`: Records human or agent review findings.
- `verifier`: Describes a checker, proof assistant invocation, script, SAT/SMT query, or other validation mechanism.
- `issue`: Records a known problem, open question, inconsistency, or follow-up item.

## Planned Common Fields

The base artifact schema currently defines these common fields:

- `id`
- `type`
- `title`
- `domain`
- `status`
- `created_at`
- `updated_at`
- `authors`
- `depends_on`
- `supersedes`
- `tags`
- `statement`
- `evidence`
- `sources`
- `formalizations`
- `alignment`
- `verification_policy`
- `review`
- `risk`

## Source Metadata

Artifacts may carry structured source metadata in `sources`. The field is
optional for draft artifacts and for legacy single-root repositories, but it is
required by policy for accepted artifacts in configured public KB roots when
`accepted_requires_source = true`.

Each source entry supports:

- `kind`: `paper`, `book`, `survey`, `lecture_note`, `website`,
  `internal_note`, or `other`
- `title`
- `authors`
- `year`
- `doi`
- `arxiv`
- `url`
- `theorem_number`
- `page`
- `notes`

For accepted public artifacts, at least one source is required, and each source
must have a non-empty title, at least one author, a year, and at least one
citation locator from `doi`, `arxiv`, `url`, `theorem_number`, or `page`.
External dependency references in `depends_on` are not a substitute for source
metadata.

## Formalization Links

Artifacts may carry formal declaration references in `formalizations`. These
references point to external formal libraries such as CSLib or mathlib without
copying proof bodies into YAML and without making those libraries framework
dependencies.

Each formalization reference includes:

- `id`
- `system`: currently `lean4`
- `library`
- `library_ref`
- `import_path`
- `symbol`
- `declaration_kind`: `definition`, `theorem`, `lemma`, `instance`,
  `structure`, or `other`
- `status`: `planned`, `linked`, `checked`, `broken`, or `deprecated`
- `check_mode`: `external_library_ref` or `local_file`
- `expected_type`: optional, defaults to an empty string
- `notes`: optional, defaults to an empty string

Formalization reference IDs use the same dot-separated lowercase slug format as
artifact IDs. `library_ref` is a formal library manifest ID such as
`cslib-main` or `mathlib-main`; it is not a Lean module path. `library`,
`import_path`, and `symbol` must be non-empty after trimming whitespace.
Manifest IDs are pinned in formal library manifest files such as
`formal-libs/lean-libraries.example.yaml`, whose schema is
`schemas/formal_library.schema.json`.

Formal library manifests are metadata for external-library references. They do
not fetch CSLib/mathlib, run Lean or lake, check symbol existence, or prove
informal/formal semantic alignment.

Formal declaration references must not be stored in `evidence`. The `evidence`
field remains for executable or otherwise evidence-like inputs; formal-library
references belong in `formalizations`.

`alignment` records semantic review between the informal statement and the
formal declaration. Lean can check a formal file or declaration, but a Lean
pass does not automatically prove that the informal artifact statement uses the
same conventions or states the same theorem. Alignment review is separate from
Lean checking. `reviewed_at`, when present, must be timezone-aware. Alignment
statuses `human_reviewed` and `rejected` require a non-empty reviewer.

`verification_policy` records whether the artifact expects a formal link, Lean
check, or alignment review. Current levels are `source_reviewed`,
`source_reviewed_with_formal_link`, `machine_checked`, and `lean_required`.
Policy values are schema/model validated and G10 statically checks consistency
between the policy, `formalizations`, and `alignment`. G10 can produce ordinary
blocking gatekeeper issues, so accepted promotion is affected only through the
existing rule that blocking gatekeeper issues prevent promotion.
`source_reviewed_with_formal_link` requires `require_formal_link: true`;
`lean_required` requires both `require_formal_link: true` and
`require_lean_check: true`.

## ID Format

Artifact and issue IDs are globally unique, dot-separated identifiers. The
first segment must be a lowercase slug. Later segments may be lowercase slugs
or numeric version/index segments such as `0001`.

Examples:

- `claim.example.complete-graph-edge-count`
- `construction.graph-toy.0001`
- `issue.graph-toy-search.0001`

Local `depends_on` and `supersedes` entries use the same artifact ID format.
`depends_on` may also contain explicit external references beginning with
`external:`. External dependency references are not local artifact IDs and are
not required to resolve to files in this repository.

## Status Values

The initial artifact status values are:

- `raw`
- `draft`
- `locally_tested`
- `adversarially_tested`
- `machine_checked`
- `human_reviewed`
- `accepted`
- `refuted`
- `obsolete`
- `superseded`

## Lifecycle Paths

The lifecycle path rules are part of the artifact contract:

- `kb/draft/<type-plural>/<artifact-id>.yaml` may store `raw`, `draft`,
  `locally_tested`, `adversarially_tested`, `machine_checked`,
  `human_reviewed`, `refuted`, `obsolete`, or `superseded` artifacts. It never
  stores `accepted` artifacts.
- `kb/accepted/<type-plural>/<artifact-id>.yaml` stores only `accepted`
  artifacts.
- `kb/refuted/<artifact-id>.yaml` stores only `refuted` artifacts.
- `kb/obsolete/<artifact-id>.yaml` stores only `obsolete` or `superseded`
  artifacts.

The lifecycle CLI derives canonical paths from artifact type, status, and ID.
Draft and pre-accepted artifacts are created under `kb/draft/` by default.
Moving an artifact to `refuted`, `obsolete`, or `superseded` moves it to the
terminal-status area. Direct accepted creation is refused, and direct
`move-status ... accepted` is refused. Accepted promotion uses
`cosheaf artifact promote <artifact-id>` rather than a silent file move.

Promotion validates the repository, runs the gatekeeper, refuses target verifier
`fail` or `error` results, requires `review.state` to be `human_reviewed` or
`accepted`, requires dependencies to be accepted local artifacts or explicit
external references, updates `status` to `accepted`, refreshes `updated_at`, and
writes deterministic YAML under `kb/accepted/<type-plural>/<artifact-id>.yaml`.

`review` and `issue` records have separate loader models and are not artifact
lifecycle records for `cosheaf artifact create` or `cosheaf artifact promote`.

## Inline Review State

Artifact `review.state` currently accepts:

- `none`
- `requested`
- `in_review`
- `approved`
- `changes_requested`
- `human_reviewed`
- `accepted`

Only `human_reviewed` and `accepted` satisfy the accepted-artifact promotion
review requirement.

## Schema Files

The initial JSON Schema files are:

- `schemas/artifact.schema.json`
- `schemas/issue.schema.json`
- `schemas/review.schema.json`
- `schemas/verifier.schema.json`
- `schemas/formal_library.schema.json`

## Pydantic Models

The initial Pydantic v2 model layer lives under `cosheaf/core/`:

- `cosheaf.core.artifact.BaseArtifact`
- `cosheaf.core.artifact.Evidence`
- `cosheaf.core.artifact.ReviewRef`
- `cosheaf.core.artifact.SourceMetadata`
- `cosheaf.core.artifact.FormalizationRef`
- `cosheaf.core.artifact.AlignmentReview`
- `cosheaf.core.artifact.VerificationPolicy`
- `cosheaf.core.formal_library.FormalLibrary`
- `cosheaf.core.formal_library.FormalLibraryManifest`
- `cosheaf.core.artifact.Risk`
- `cosheaf.core.status.ArtifactType`
- `cosheaf.core.status.ArtifactStatus`

The model layer validates artifact IDs, enum values, timezone-aware timestamps,
dependency references, evidence records, source metadata shape, formalization
link shape, alignment review state, verification policy values, review state,
and risk state.
Path/status rules are exposed as pure helper functions; they do not scan the
repository.

## Example Files

The initial example YAML files are:

- `examples/issues/issue.example.yaml`
- `examples/claims/claim.example.yaml`
- `examples/proofs/proof.example.yaml`
- `examples/constructions/graph.example.yaml`
- `examples/reviews/review.example.yaml`

## Current Implementation Status

Machine-readable JSON Schema files exist, along with example YAML artifacts and
initial Pydantic v2 models. Filesystem-backed loading, repository scanning,
schema/model validation through `cosheaf validate`, single-file validation
through `cosheaf artifact validate <path>`, deterministic artifact creation
through `cosheaf artifact create`, safe pre-accepted and terminal status moves
through `cosheaf artifact move-status`, accepted promotion through
`cosheaf artifact promote`, and gatekeeper report generation through
`cosheaf gate` are implemented. The reproducibility metadata gate is
implemented for executable evidence through verifier-result metadata. Direct
accepted creation and direct `move-status ... accepted` remain blocked. G8 PR
checklist enforcement can validate a local PR body markdown file through
`cosheaf gate run --pr-checklist <path>` and remains skipped when no checklist
source is available. G9 source metadata enforcement checks accepted public
artifacts in configured workspaces when `accepted_requires_source = true` while
preserving draft, private, and legacy single-root behavior.

The Formal Link Layer is implemented as optional schema/model metadata, an
example artifact, G10 static metadata validation, context-pack display, and
SQLite/query metadata surfaces. It records Lean-library
declaration references plus optional formal library manifest metadata without
adding CSLib/mathlib dependencies, without requiring network access, and
without changing accepted promotion semantics beyond ordinary gatekeeper
blocking behavior. G10 does not execute Lean, does not fetch or inspect
external Lean libraries, and does not prove informal/formal semantic
alignment. Context packs and query APIs expose the same metadata without
claiming that Lean verified the informal statement. The implementation does
not add formal-link CLI commands or verifier execution for external library
references.
