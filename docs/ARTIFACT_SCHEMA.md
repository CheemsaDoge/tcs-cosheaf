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

## Common Fields

The base artifact schema currently defines these common fields. Planned
additions are listed separately so readers can distinguish design intent from
implemented schema/model support:

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

## Artifact Failure Log

`failure_log` is the artifact-level home for failed proof attempts, dead
reduction directions, construction failures, counterexample-search dead ends,
formalization stalls, retrieval misses, and verifier attempts that should not
be repeated without new evidence.

The field is optional and backward compatible:

- artifacts that omit `failure_log` remain valid;
- omitted `failure_log` behaves like an empty list;
- existing artifact lifecycle, review, verifier, gate, and promotion semantics
  remain unchanged.

Each failure-log entry is research memory. It is not proof, verifier success,
human review, source metadata, checked counterexample evidence, gate success,
or accepted-promotion evidence by itself.

Entry fields:

| Field | Required | Meaning | Authority boundary |
| --- | --- | --- | --- |
| `failure_id` | yes | Dot-separated identifier for one failed attempt memory entry. | Identifies memory only, not evidence, review, or promotion authority. |
| `attempted_at` | yes | Timezone-aware timestamp for the attempt or reconstructed attempt. | Timestamp metadata only; it does not prove review or completeness. |
| `recorded_by` | yes | Human, agent, provider, verifier, or import label that recorded the entry. | Provenance label only; it does not create human review. |
| `origin` | yes | `human`, `agent`, `provider`, `verifier`, or `imported_bundle`. | Origin is not trust level. `origin: human` is separate from `review.state: human_reviewed`. |
| `attempt_kind` | yes | `proof_attempt`, `reduction_attempt`, `construction_attempt`, `counterexample_search`, `formalization_attempt`, `verifier_attempt`, `retrieval_attempt`, or `other`. | Routing/classification metadata only. |
| `target` | no | Current artifact, another local artifact ID, or explicit `external:<ref>` target. | Does not create a dependency, proof obligation, or refutation. |
| `direction` | yes | Short attempted direction. | Retrieval hint only. |
| `summary` | yes | What was tried. | Explanatory text only. |
| `failed_because` | yes | Why the attempt failed, stalled, or was abandoned. | Does not refute the artifact without separate checked or reviewed evidence. |
| `evidence_paths` | no | Repository-local supporting paths. | References only; referenced files keep their own authority and must not be direct accepted-write targets. |
| `related_verifier_results` | no | Verifier evidence IDs or repository-local verifier result paths. | Links only; skipped remains skipped, failed remains failed, and no result is converted to pass. |
| `related_counterexample_candidates` | no | Candidate IDs or repository-local candidate references. | Candidate references only; not checked refutations. |
| `next_possible_directions` | no | Follow-up directions that may be worth trying. | Advisory only. |
| `status` | yes | `open`, `superseded`, `invalidated`, `resolved`, or `archived`. | Status of the memory entry only. `resolved` does not mean proven, refuted, reviewed, or accepted. |
| `limitations` | yes | Non-empty anti-overclaiming note. | Required reminder that the entry does not bypass validation, gates, review, verifier evidence, or promotion. |

The model/schema rejects unsafe repository paths, invalid IDs,
timezone-naive timestamps, empty required text fields, and structured fields
that would try to grant human review, verifier pass, checked counterexample
status, accepted status, or promotion readiness.

WorkerBundle v2 `failed_attempts` and artifact `failure_log` have different
scope. WorkerBundle failures are run-scoped worker output and can be noisy,
agent/provider-originated, or transient. Artifact failure logs are durable,
artifact-local metadata added through a controlled path. A later bridge may
convert WorkerBundle failures into proposed failure-log entries, but that
bridge must preserve origin and cannot create accepted knowledge, human review,
or verifier evidence.

Accepted public KB artifacts may include failure memory only through ordinary
public-KB policy: complete source metadata where required, human review where
required, validation/gate success, accepted or explicit external dependencies,
and explicit promotion. Validation and gate success do not replace human
review, and unreviewed agent/provider failure logs must not enter accepted
public knowledge.

Read-only CLI inspection is available through:

```bash
cosheaf artifact failures <artifact-id> --json
```

The command returns artifact path, root scope metadata, failure count, the
stored `failure_log` entries, and an explicit non-authority notice. It does not
write files, create verifier results, mark human review, run gates, or promote
artifacts.

Controlled append support for draft/pre-accepted writable artifacts is available
through:

```bash
cosheaf artifact failure add --artifact <artifact-id> --input-json <path> --json
cosheaf artifact failure add --artifact <artifact-id> --input-json <path> --dry-run --json
```

The input JSON must be one `FailureLogEntry`. The command appends to the target
artifact's `failure_log` only when the artifact is writable and is not accepted.
It refuses direct `kb/accepted/` mutation, readonly KB roots, accepted artifact
status, and input that attempts to claim human review, accepted status, verifier
pass, or checked counterexample authority. Dry-runs validate and report without
writing. Actual writes refresh `updated_at` and report
`accepted_write_performed=false`.

WorkerBundle-derived conversion is available through:

```bash
cosheaf artifact failure plan-from-bundle --bundle <path> --target-artifact <artifact-id> --json
cosheaf artifact failure add-from-bundle --bundle <path> --target-artifact <artifact-id> --dry-run --json
```

`plan-from-bundle` is read-only. It maps WorkerBundle v2 `failed_attempts` into
proposed `FailureLogEntry` values with `origin: imported_bundle`.
`add-from-bundle` applies the same conversion through the controlled write path.
Typed WorkerBundle `counterexample_candidates` are linked by candidate ID in
`related_counterexample_candidates` only; they are not copied into
`failed_because` as checked refutations and do not become verifier results,
human review, accepted knowledge, or promotion evidence.

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
not fetch CSLib/mathlib, run Lean or lake by themselves, check symbol
existence, or prove informal/formal semantic alignment. Optional verifier
adapters may use formalization metadata to run separate checks when explicitly
applicable.

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
Policy values are schema/model validated and G10 checks consistency between the
policy, `formalizations`, `alignment`, local formal library manifests, and
normalized verifier results when `require_lean_check: true`. G10 can produce
ordinary blocking gatekeeper issues, so accepted promotion is affected only
through the existing rule that blocking gatekeeper issues prevent promotion.
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
- `cosheaf.core.artifact.FailureLogEntry`
- `cosheaf.core.formal_library.FormalLibrary`
- `cosheaf.core.formal_library.FormalLibraryManifest`
- `cosheaf.core.artifact.Risk`
- `cosheaf.core.status.ArtifactType`
- `cosheaf.core.status.ArtifactStatus`

The model layer validates artifact IDs, enum values, timezone-aware timestamps,
dependency references, evidence records, source metadata shape, formalization
link shape, alignment review state, verification policy values, review state,
failure-log shape, and risk state.
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
example artifact, G10 metadata and verifier-result consistency validation,
context-pack display, SQLite/query metadata surfaces, and an optional external
Lean library reference checker. It records Lean-library declaration references
plus optional formal library manifest metadata without adding CSLib/mathlib
dependencies, without requiring network access, and without changing accepted
promotion semantics beyond ordinary gatekeeper blocking behavior. G10 does not
execute Lean, does not fetch or inspect external Lean libraries, and does not
prove
informal/formal semantic alignment. Context packs and query APIs expose the
same metadata without claiming that Lean verified the informal statement. The
optional external reference checker can generate a temporary Lean file with
`import <import_path>` and `#check <symbol>` for linked external-library
references when Lean or lake is available; a pass means only that the import
and symbol resolved.

Artifact-level `failure_log` is implemented as optional Pydantic model and JSON
Schema metadata. It defaults to an empty list, validates timezone-aware
`attempted_at` timestamps, non-empty required text, failure IDs, optional local
or explicit external targets, repository-local non-accepted evidence paths,
origin labels, attempt kinds, and failure-log entry status values. It remains
research memory only and does not change review, verifier, gate, or promotion
authority.
