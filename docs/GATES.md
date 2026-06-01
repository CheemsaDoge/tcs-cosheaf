# Gates

## Purpose

Gates enforce repository invariants before artifacts or behavior changes are accepted.

## Initial Gates

### Schema Gate

Checks that every artifact conforms to the project artifact schema.

### ID Uniqueness Gate

Checks that artifact IDs are globally unique across accepted and draft artifacts.

### Status/Path Gate

Checks that accepted artifacts live only under `kb/accepted/` and draft or pre-accepted artifacts live only under `kb/draft/`.

### Dependency Gate

Checks that artifact dependencies are valid and that accepted artifacts do not depend on draft artifacts.

### Evidence Path Gate

Checks that referenced evidence paths exist, are repository-local, and are appropriate for the artifact status.

### Verifier Gate

Runs configured verifier adapters and normalizes results. Missing optional external tools should produce skipped verifier results, not core system crashes.

### Reproducibility Metadata Gate

Checks that artifacts and verifier results include the planned metadata needed to reproduce or interpret generated outputs.

### PR Checklist Gate

Checks that the PR records required review items, public interface updates, ADR updates, and verification status.

## Gate Result Semantics

Gate results should distinguish pass, fail, skipped, and not implemented. A skipped result must explain why the gate could not run. A failed result must preserve enough evidence for review.

## Current Implementation Status

These gates are specified but not implemented yet. This repository currently contains documentation scaffolding only.
