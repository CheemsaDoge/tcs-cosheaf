# Gates

## Purpose

Gates enforce repository invariants before artifacts or behavior changes are accepted.

## Initial Gates

### Schema Gate

Checks that every discovered YAML record parses and conforms to the current
Pydantic model contracts for artifacts, issues, or reviews.

### ID Uniqueness Gate

Checks that loaded record IDs are globally unique across the repository
discovery roots.

### Status/Path Gate

Checks that accepted artifacts live only under `kb/accepted/` and draft or pre-accepted artifacts live only under `kb/draft/`.

### Dependency Gate

Checks that artifact dependencies are valid and that accepted artifacts do not depend on draft artifacts.

### Evidence Path Gate

Checks that referenced evidence paths exist, are repository-local, and are appropriate for the artifact status.
Evidence entries marked with `kind: external` or paths starting with `external:`
are treated as external references and are not required to resolve locally.

### Verifier Gate

Runs configured verifier adapters and normalizes results. Missing optional
external tools should produce skipped verifier results, not core system crashes.

The verifier adapter interface is defined by `VerifierAdapter`, with:

- `name: str`
- `can_verify(artifact, repo) -> bool`
- `verify(artifact, repo) -> VerificationResult`

`VerificationResult` records verifier name, artifact ID, normalized status,
timestamps, command metadata, working directory, exit code, stdout/stderr log
paths, evidence paths, and a review message. Status values are:

- `pass`: the verifier checked the artifact and accepted it.
- `fail`: the verifier checked the artifact and found an artifact-level failure.
- `error`: the verifier or runtime errored before producing a verification
  judgment.
- `skipped`: the verifier did not run, for example because an optional external
  tool is unavailable.

`skipped` is not `pass`, and `error` is not `fail`. External command-backed
verifiers must record the command and working directory they used.

### Reproducibility Metadata Gate

Checks that artifacts and verifier results include the planned metadata needed to reproduce or interpret generated outputs.

### PR Checklist Gate

Checks that the PR records required review items, public interface updates, ADR updates, and verification status.

## Gate Result Semantics

Gate results should distinguish pass, fail, skipped, and not implemented. A skipped result must explain why the gate could not run. A failed result must preserve enough evidence for review.

## Gatekeeper Reports

`cosheaf gate run` writes both machine-readable JSON and human-readable
Markdown reports. By default, reports are written under `.cosheaf/reports/` so
local runs do not create review noise:

- `.cosheaf/reports/<timestamp>-gate-report.json`
- `.cosheaf/reports/<timestamp>-gate-report.md`

Use `cosheaf gate run --persist-review` to also copy the same reports under
`reviews/gatekeeper/` for durable review artifacts.

The JSON report contains:

- `verdict`: `pass` or `fail`
- `blocking_issues`
- `nonblocking_issues`
- `summary`
- `started_at`
- `ended_at`
- `gates`

Any blocking issue makes the verdict `fail` and causes a nonzero CLI exit code.
Placeholder gates must be reported as `skipped` or `not_applicable`; they must
not be reported as `pass`.

## Current Implementation Status

`cosheaf validate` now implements the schema/model gate, ID uniqueness gate,
status/path gate, dependency gate, and evidence path gate over YAML records
discovered under `kb/`, `issues/`, and `examples/`.

`cosheaf artifact validate <path>` validates a single YAML file with
file-local schema/model, status/path, and evidence path checks. Whole-repository
checks such as ID uniqueness and dependency existence run through
`cosheaf validate`.

`cosheaf gate run` now runs:

- G1 schema gate
- G2 ID uniqueness gate
- G3 status/path gate
- G4 dependency gate
- G5 evidence path gate
- G6 verifier gate placeholder
- G7 reproducibility metadata gate placeholder
- G8 PR checklist gate placeholder

G6, G7, and G8 are intentionally reported as skipped placeholders until their
implementations exist. `cosheaf gate` with no subcommand also runs the
gatekeeper so the existing `make gate` target performs real gate enforcement.

The verification adapter protocol, verification result model, and instance-local
verifier registry now exist, but G6 still does not execute adapters.
