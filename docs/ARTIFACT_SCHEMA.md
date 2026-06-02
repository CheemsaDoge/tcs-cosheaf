# Artifact Schema

## Purpose

This document describes the research artifact vocabulary and the initial machine-readable schema files. The schemas are intentionally lightweight at this stage: they define file-level contracts for examples and future loaders, but no Pydantic models or CLI validation implementation exists yet.

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
- `review`
- `risk`

## ID Format

Artifact and issue IDs are globally unique, dot-separated identifiers. The
first segment must be a lowercase slug. Later segments may be lowercase slugs
or numeric version/index segments such as `0001`.

Examples:

- `claim.example.complete-graph-edge-count`
- `construction.graph-toy.0001`
- `issue.graph-toy-search.0001`

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

## Schema Files

The initial JSON Schema files are:

- `schemas/artifact.schema.json`
- `schemas/issue.schema.json`
- `schemas/review.schema.json`
- `schemas/verifier.schema.json`

## Pydantic Models

The initial Pydantic v2 model layer lives under `cosheaf/core/`:

- `cosheaf.core.artifact.BaseArtifact`
- `cosheaf.core.artifact.Evidence`
- `cosheaf.core.artifact.ReviewRef`
- `cosheaf.core.artifact.Risk`
- `cosheaf.core.status.ArtifactType`
- `cosheaf.core.status.ArtifactStatus`

The model layer validates artifact IDs, enum values, timezone-aware timestamps, dependency ID lists, evidence records, review state, and risk state. Path/status rules are exposed as pure helper functions; they do not scan the repository.

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
through `cosheaf artifact validate <path>`, and gatekeeper report generation
through `cosheaf gate` are implemented. The reproducibility metadata gate is
implemented for executable evidence through verifier-result metadata. PR
checklist enforcement is still reported as a skipped placeholder.
