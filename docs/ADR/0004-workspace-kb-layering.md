# ADR 0004: Workspace KB Layering

## Status

Accepted

## Context

TCS-Cosheaf needs to support a framework repository, a reusable public KB, and
user-private research overlays without asking users to manually merge those
repositories. The framework repository must preserve its existing single-repo
behavior while adding a path toward layered workspaces.

## Decision

Add optional root-level `cosheaf.toml` workspace configuration. A workspace has
a name, one or more KB roots, and public/private dependency policy fields. Each
KB root has a name, repository-relative path, readonly flag, and priority.

When `cosheaf.toml` is absent, the framework keeps legacy behavior with one
writable KB root at `kb/`.

When `cosheaf.toml` exists, storage discovery loads all configured KB roots
plus repository-local `issues/` and `examples/`. Loaded records retain source
KB root metadata. Validation and gatekeeper checks enforce global ID
uniqueness, public/private dependency direction, accepted-to-draft dependency
rules across roots, and status/path rules relative to each KB root. Lifecycle
write commands refuse readonly roots and create new artifacts in the writable
private root by default.

## Consequences

- Existing single-repository users keep working without a config file.
- User workspaces can layer readonly public KB content under writable private
  overlays.
- Public KB content cannot accidentally depend on private artifacts.
- Index manifests can show which KB root each artifact came from.
- Future external KB repository workflows can build on the same root metadata.

## Non-Goals

- This ADR does not create the full public KB repository.
- This ADR does not implement real SAT, SMT, or Lean verification.
- This ADR does not auto-promote private artifacts into public KB.
