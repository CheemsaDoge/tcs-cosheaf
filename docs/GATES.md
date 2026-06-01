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

Runs configured verifier adapters and normalizes results. Missing optional external tools should produce skipped verifier results, not core system crashes.

### Reproducibility Metadata Gate

Checks that artifacts and verifier results include the planned metadata needed to reproduce or interpret generated outputs.

### PR Checklist Gate

Checks that the PR records required review items, public interface updates, ADR updates, and verification status.

## Gate Result Semantics

Gate results should distinguish pass, fail, skipped, and not implemented. A skipped result must explain why the gate could not run. A failed result must preserve enough evidence for review.

## Current Implementation Status

`cosheaf validate` now implements the schema/model gate, ID uniqueness gate,
status/path gate, dependency gate, and evidence path gate over YAML records
discovered under `kb/`, `issues/`, and `examples/`.

`cosheaf artifact validate <path>` validates a single YAML file with
file-local schema/model, status/path, and evidence path checks. Whole-repository
checks such as ID uniqueness and dependency existence run through
`cosheaf validate`.

The verifier gate, reproducibility metadata gate, and PR checklist gate remain
specified but not implemented. `cosheaf gate` remains a scaffold-only command.
