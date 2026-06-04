# Architecture

## Overview

TCS-Cosheaf is organized as a layered system. Each layer should expose narrow interfaces upward and avoid depending on higher layers.

## Layers

### Knowledge Layer

Defines the artifact model, artifact status concepts, artifact type vocabulary, and domain-level invariants.

### Configuration Layer

Loads optional repository-local workspace configuration from `cosheaf.toml`.
When the file is absent, configuration falls back to the legacy single-root
repository behavior with one writable KB root at `kb/`.

The workspace configuration model contains a workspace name, public/private
policy fields, and one or more KB roots. Each KB root has a `name`,
repository-relative `path`, `readonly` flag, and integer `priority`.

### Storage/Index Layer

Loads artifacts from Git-backed paths, builds deterministic indexes, and records repository-local metadata needed by other layers.

When `cosheaf.toml` exists, storage discovers YAML records under each configured
KB root plus repository-local `issues/` and `examples/`. Loaded records retain
their source KB root name, root path, readonly flag, and path relative to the KB
root. When `cosheaf.toml` is absent, storage keeps the previous discovery roots:
`kb/`, `issues/`, and `examples/`.

Current index outputs are:

- `.cosheaf/index.sqlite`
- `.cosheaf/artifact_manifest.json`

Index rebuilds load repository YAML records, normalize artifact rows, write
SQLite from scratch, and emit a deterministic JSON manifest ordered by artifact
ID and dependency tuple. Artifact rows include the source KB root name.

The SQLite query API is a read-only convenience layer over
`.cosheaf/index.sqlite`. YAML remains the source of truth; callers should
rebuild the index after YAML changes before querying. Query results are ordered
deterministically and expose artifact metadata, domain membership, dependency
edges, reverse dependency edges, and the indexed source KB root.

### Graph Layer

Builds a directed artifact dependency graph from `depends_on`. Edge direction is
artifact-to-dependency, for example `claim -> dependency`. The graph layer
detects missing dependencies, directed cycles, and accepted artifacts that depend
on draft or otherwise pre-accepted artifacts.

### Verification Layer

Runs verifier adapters and normalizes verifier outcomes. Optional external tools must remain optional; missing tools should produce skipped verifier results instead of crashing the core system.

### Gate/Review Layer

Combines schema checks, repository invariants, dependency checks, verifier outcomes, reproducibility metadata, and PR checklist checks into gate results.

Workspace-aware dependency checks additionally reject public artifacts that
depend on private artifacts. Status/path checks evaluate artifact lifecycle
paths relative to each configured KB root, so `kb/public/accepted/...` and
`kb/private/accepted/...` both use accepted-path semantics inside their own
roots.

### Agent Harness Layer

Builds bounded context packs for Codex and other agents, records task assumptions, and keeps task execution anchored to repository files rather than conversation state.

Current agent harness outputs are:

- `context/TASKS/<issue-id>/` context packs.
- `.cosheaf/tasks/<task-id>.yaml` runtime task records.

Context packs use deterministic relevance ranking. The ranking includes direct
issue artifact references, one-hop dependency neighbors, artifact domains that
match issue text or tags, and artifact tags that match issue tags. Each listed
artifact includes explainable ranking reasons. Accepted artifacts are preferred
over draft artifacts within the same relevance class. Refuted, obsolete, and
superseded artifacts are included only when relevant and are marked as known
failures, not current truth.

The task harness defines protocol-level worker types only. Creating, listing,
or completing tasks does not call LLMs, external services, or concrete worker
runtimes. The orchestrator stub validates that tasks are issue-scoped, records
deterministic default task IDs, and can mark a task completed only after a local
worker output bundle passes the worker contract.

Worker output bundles are local YAML manifests. Artifact and review outputs
must reference repository-local YAML records that pass the existing schema gate.
Bundles must not target `kb/accepted/`, and task completion does not merge
anything into accepted knowledge.

### CLI Layer

Provides public commands for validation, gate execution, graph inspection,
context generation, workspace inspection, lifecycle artifact writes, and
verifier invocation.

Lifecycle write commands are workspace-aware. In configured workspaces,
`cosheaf artifact create` writes to the writable private KB root by default, and
`cosheaf artifact move-status` refuses to modify records loaded from readonly
KB roots.

## Module Dependency Direction

The intended module dependency direction is:

```text
core -> config -> storage -> graph -> gates -> verification -> agent -> cli
```

Lower-level modules must not import higher-level modules. Public interface changes must be recorded in `context/INTERFACE_REGISTRY.md`.

## Determinism

Indexes, generated outputs, context packs, and gate reports must be deterministic for the same repository state and tool availability.

## Architectural Decisions

Architectural decisions must be recorded under `docs/ADR/` using ADR format.
