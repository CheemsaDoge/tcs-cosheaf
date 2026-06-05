# Architecture

## Overview

TCS-Cosheaf is organized as a layered system. Each layer should expose narrow interfaces upward and avoid depending on higher layers.

## Layers

### Knowledge Layer

Defines the artifact model, artifact status concepts, artifact type vocabulary,
formalization-link metadata, and domain-level invariants.

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
ID and dependency tuple. Artifact rows include the source KB root name. Formal
link metadata is indexed into `formalizations` and `artifact_formal_policy`
tables and into compact manifest fields.

The SQLite query API is a read-only convenience layer over
`.cosheaf/index.sqlite`. YAML remains the source of truth; callers should
rebuild the index after YAML changes before querying. Query results are ordered
deterministically and expose artifact metadata, domain membership, dependency
edges, reverse dependency edges, formalization references, formal policy rows,
and the indexed source KB root. Query methods do not rebuild indexes
implicitly.

### Formal Link Layer

Records references from artifacts to external formal declarations, currently
Lean 4 declarations in libraries such as CSLib or mathlib. This layer stores
library, import-path, symbol, declaration-kind, status, check-mode, expected
type, and notes metadata under `formalizations`.

Formal links are references, not copied proof bodies. Cosheaf does not replace
CSLib, mathlib, or other formal libraries, and artifact YAML should not vendor
Lean proofs. Semantic alignment between an informal artifact statement and a
formal declaration is recorded separately under `alignment`; a Lean pass does
not automatically prove informal/formal alignment.

`verification_policy` records whether a formal link, Lean check, or alignment
review is expected for an artifact. G10 Formal Link Gate enforces static
consistency between `verification_policy`, `formalizations`, and `alignment`.
This gate does not execute Lean, fetch external libraries, prove
informal/formal alignment, or change accepted-promotion semantics. Formal-link
context-pack display and SQLite/query support are metadata-only surfaces built
on the same artifact fields; they do not change G10 behavior.

### Graph Layer

Builds a directed artifact dependency graph from `depends_on`. Edge direction is
artifact-to-dependency, for example `claim -> dependency`. The graph layer
detects missing dependencies, directed cycles, and accepted artifacts that depend
on draft or otherwise pre-accepted artifacts.

### Verification Layer

Runs verifier adapters and normalizes verifier outcomes. Optional external
tools must remain optional; missing tools should produce skipped verifier
results instead of crashing the core system. The Python checker adapter runs
repository-local checker scripts. The SAT adapter supports a minimal optional
DIMACS CNF invocation path when a supported backend is available, while keeping
SAT solver binaries optional and recording skipped results when no backend is
available. The SMT adapter similarly supports a minimal optional SMT-LIB
invocation path through a supported backend, currently external `z3` when
available, while keeping solver binaries optional and recording skipped results
when no backend is available. The Lean adapter supports a minimal optional plain
Lean file invocation path through a supported backend, currently external
`lean` when available, while keeping Lean optional and recording skipped results
when no backend is available. No verifier adapter performs natural-language
autoformalization. The Lean adapter does not fetch or check CSLib/mathlib
references recorded in `formalizations`.

### Gate/Review Layer

Combines schema checks, repository invariants, dependency checks, verifier
outcomes, reproducibility metadata, source metadata, and PR checklist checks
into gate results.

Alignment review remains separate from verifier execution. Missing optional
Lean tooling remains a skipped verifier result, not a pass. The gate layer
records formal-link fields through schema/model validation and G10 static
metadata validation. G10 may block ordinary gatekeeper runs when policy
metadata is inconsistent, which means accepted promotion is blocked through the
existing gatekeeper blocking-issue mechanism. It does not add a new promotion
policy path.

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
- `.cosheaf/tasks/<task-id>/runs/<run-id>/` local worker run records with
  separate stdout and stderr files.

Context packs use deterministic relevance ranking. The ranking includes direct
issue artifact references, one-hop dependency neighbors, artifact domains that
match issue text or tags, and artifact tags that match issue tags. Each listed
artifact includes explainable ranking reasons. Accepted artifacts are preferred
over draft artifacts within the same relevance class. Refuted, obsolete, and
superseded artifacts are included only when relevant and are marked as known
failures, not current truth.

When a relevant artifact carries formal-link metadata or policy-relevant formal
settings, context packs include compact formalization, alignment, verification
policy, and G10-relevant hint lines. These lines are handoff metadata only:
they do not load gate reports, do not claim a current G10 verdict, and do not
claim Lean verification.

The task harness defines protocol-level worker types only. Creating, listing,
or completing tasks does not call LLMs or external services. The orchestrator
stub validates that tasks are issue-scoped, records deterministic default task
IDs, and can mark a task completed only after a local worker output bundle
passes the worker contract.

The local worker runner is not an LLM runtime or model-provider integration. It
executes only an explicit argv command with `shell=False`, defaults to the
repository root as its working directory, rejects working directories outside
the repository, rejects bundle paths outside the repository before command
execution, enforces a timeout, captures stdout and stderr, and writes a
deterministic run record under the task's `.cosheaf` run directory. Optional
bundle handling validates worker output bundles after command execution; it
does not merge outputs or promote accepted knowledge.

Worker output bundles are local YAML manifests. Artifact and review outputs
must reference repository-local YAML records that pass the existing schema gate.
Bundle manifests may also be passed as repository-local directories containing
`bundle.yaml`. Bundles must not target `kb/accepted/`, and task completion does
not merge anything into accepted knowledge.

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
