# ADR 0007: Formal Link Context And Query Surface

## Status

Accepted

## Context

ADR 0005 added Formal Link Layer artifact metadata, and ADR 0006 added G10 as
static metadata validation over that metadata. Agents and local tools still
need a deterministic way to see and query those references without loading the
full YAML corpus manually.

The repository already has deterministic context packs and a rebuilt SQLite
index. YAML remains the source of truth, and the SQLite index is an explicit
rebuild output.

## Decision

Surface formal-link metadata in two read-only places:

- context packs list compact `formalizations`, `alignment`, and
  `verification_policy` summaries for relevant artifacts when those fields are
  present or policy-relevant;
- `.cosheaf/index.sqlite` includes `formalizations` and
  `artifact_formal_policy` tables, and `ArtifactIndexQuery` exposes read-only
  formalization and policy query methods.

The manifest output includes compact formalization references,
`alignment_status`, and the formal-link `verification_policy` fields per
artifact. Rebuild remains from scratch and deterministic; no schema migration
path is needed for generated index output.

## Consequences

- Context packs can show planned, linked, checked, broken, or deprecated
  formal references without claiming Lean verification.
- Query clients can find formalization rows by artifact, library, symbol,
  status, or import path.
- Query clients can find artifacts whose policy requires a formal link, Lean
  check, or alignment review.
- Query APIs read the existing SQLite file and do not rebuild implicitly.
- G10 behavior is unchanged; it remains static metadata validation.

## Non-Goals

- Do not implement Lean execution.
- Do not add CSLib, mathlib, lake, or Lean dependencies.
- Do not fetch external libraries or require network access.
- Do not change G10 behavior.
- Do not change accepted-promotion semantics.
- Do not modify the public KB or workspace-template repositories.
- Do not add context-pack claims that a formal link has been Lean verified.
- Do not add CLI query commands in this increment because there is no existing
  query CLI surface to extend.
