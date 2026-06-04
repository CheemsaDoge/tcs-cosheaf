# Current Milestone

## Milestone

v0.1.0 release candidate cleanup.

## Goal

Clear release-state contradictions before tagging the framework as `v0.1.0`.
The project remains a pre-MVP scaffold, but its version metadata, license
metadata, roadmap, release checklist, and durable state docs should describe
the same implemented surface.

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
- Read-only SQLite query API over rebuilt index output exists for artifact,
  status, type, domain, dependency, reverse-dependency, and source-root queries.
- `cosheaf validate` and `cosheaf gate` run implemented local checks; G8 can
  validate explicit PR body markdown files and is skipped when no PR checklist
  source is available.
- Python checker, minimal optional SAT DIMACS verifier, minimal optional
  SMT-LIB verifier, and minimal optional Lean verifier adapters exist.
- Issue-scoped context pack generation exists.
- GitHub Actions CI runs `lint`, `typecheck`, `test`, `validate`, and `gate`
  as separate Python 3.11 checks.
- Project metadata, README license text, and `LICENSE` use Apache-2.0
  consistently.
- `RELEASE_CHECKLIST.md` records release readiness, tag, known limitations, and
  follow-up repository pinning requirements.
- Project state and interface registry remain mutually consistent.

## Next Focus

- Hosted PR checklist source discovery beyond explicit local markdown files.
- Expand SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Expand SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Lean support beyond the minimal optional plain-file invocation path.
- Tag `v0.1.0` only after the release-cleanup PR passes CI and human review.
- Pin public KB and workspace-template CI/docs to `tcs-cosheaf@v0.1.0` only
  after that tag exists.
