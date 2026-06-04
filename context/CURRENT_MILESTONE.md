# Current Milestone

## Milestone

Post-Task-014 MVP scaffold.

## Goal

Keep the pre-MVP repository scaffold coherent while the implemented storage,
graph, validation, gatekeeper, verifier, context-pack, and CI surfaces mature
toward the MVP.

## Completion Criteria

- Project rules are documented.
- Product scope is documented.
- Architecture layers and dependency direction are documented.
- Codex workflow is documented.
- Initial gates are documented.
- Planned artifact types are documented.
- Initial ADRs are recorded.
- Python package scaffolding and CLI entry points exist.
- Artifact schemas and example YAML records exist.
- Core artifact models and status helpers exist.
- Filesystem-backed loading, deterministic writing, dependency graph, and
  repository index rebuilds exist.
- `cosheaf validate` and `cosheaf gate` run implemented local checks; G8 can
  validate explicit PR body markdown files and is skipped when no PR checklist
  source is available.
- Python checker, minimal optional SAT DIMACS verifier, and optional SMT/Lean
  verifier skeleton adapters exist.
- Issue-scoped context pack generation exists.
- GitHub Actions CI runs `lint`, `typecheck`, `test`, `validate`, and `gate`
  as separate Python 3.11 checks.
- Project state and interface registry remain mutually consistent.

## Next Focus

- Hosted PR checklist source discovery beyond explicit local markdown files.
- Expand SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Real SMT/Lean solver invocation and result parsing.
- SQLite-backed query API beyond rebuild output.
