# Architecture

## Overview

TCS-Cosheaf is organized as a layered system. Each layer should expose narrow interfaces upward and avoid depending on higher layers.

## Layers

### Knowledge Layer

Defines the artifact model, artifact status concepts, artifact type vocabulary, and domain-level invariants.

### Storage/Index Layer

Loads artifacts from Git-backed paths, builds deterministic indexes, and records repository-local metadata needed by other layers.

### Verification Layer

Runs verifier adapters and normalizes verifier outcomes. Optional external tools must remain optional; missing tools should produce skipped verifier results instead of crashing the core system.

### Gate/Review Layer

Combines schema checks, repository invariants, dependency checks, verifier outcomes, reproducibility metadata, and PR checklist checks into gate results.

### Agent Harness Layer

Builds bounded context packs for Codex and other agents, records task assumptions, and keeps task execution anchored to repository files rather than conversation state.

### CLI Layer

Provides public commands for validation, gate execution, graph inspection, context generation, and verifier invocation.

## Module Dependency Direction

The intended module dependency direction is:

```text
core -> storage -> graph -> gates -> verification -> agent -> cli
```

Lower-level modules must not import higher-level modules. Public interface changes must be recorded in `context/INTERFACE_REGISTRY.md`.

## Determinism

Indexes, generated outputs, context packs, and gate reports must be deterministic for the same repository state and tool availability.

## Architectural Decisions

Architectural decisions must be recorded under `docs/ADR/` using ADR format.
