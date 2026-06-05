# Roadmap

TCS-Cosheaf is preparing a v0.1.1 Formal Link Layer support release while
still remaining pre-MVP. This roadmap is intentionally concrete and tied to
named milestones or active GitHub issues. It should not be read as a commitment
to dates, adoption, or production readiness.

## Current Milestone: v0.1.1 Formal Link Layer Support

Goal: tag the framework after Formal Link Layer metadata, G10 static metadata
validation, context-pack display, deterministic index storage, and read-only
query APIs have landed, while preserving the metadata-only boundary.

Completed scaffold pieces include:

- Typed artifact models and initial schemas.
- Filesystem-backed artifact loading and deterministic YAML writing.
- Repository validation CLI.
- Artifact creation and lifecycle status movement CLI for non-accepted
  transitions.
- Controlled accepted-artifact promotion workflow.
- Dependency graph and deterministic index rebuild outputs.
- Read-only SQLite query API over rebuilt index output, including artifact,
  status, type, domain, dependency, reverse-dependency, formalization, and
  formal-policy queries through
  `ArtifactIndexQuery`.
- Gatekeeper reports with machine-readable JSON and human-readable Markdown.
- Local G8 PR checklist gate for explicit PR body markdown files.
- Ranked context pack generation for issue-scoped agent work.
- Formal Link Layer artifact fields `formalizations`, `alignment`, and
  `verification_policy`.
- G10 Formal Link Gate for static consistency between formal-link metadata,
  alignment review, and verification policy.
- Context-pack formal-link display that does not claim Lean verification.
- Deterministic `formalizations` and `artifact_formal_policy` SQLite tables.
- Local task, worker contract, and orchestrator stubs.
- Verifier adapter protocol, Python checker adapter, minimal optional SAT
  DIMACS adapter, minimal optional SMT-LIB adapter, and minimal optional Lean
  plain-file adapter.
- Reproducibility metadata gate for executable evidence verifier results.
- Branch protection and review policy documentation.
- First graph-theory pilot workflow with draft artifact evidence and a local
  Python checker.
- Second SAT/CNF pilot workflow with optional SAT evidence and a Python fallback
  checker.
- GitHub Actions CI and collaboration templates.

## Active Issues

Live issue state is tracked in GitHub issues. This roadmap records durable
direction and named milestones; it should not be used as a manually maintained
list of currently open issues.

## Next Named Milestones

### MVP Usability

- Improve PR checklist ergonomics for hosted PR workflows without making local
  gates depend on GitHub API access.

### Verification Depth

- Add external Lean library reference checking for recorded `import_path` and
  `symbol` metadata without vendoring CSLib or mathlib.
- Expand SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Expand SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Expand Lean support beyond the minimal optional plain-file invocation path.
- Keep all external formal tools optional; unavailable tools must produce
  skipped verifier results.

### Query and Review Ergonomics

- Improve artifact search and graph inspection workflows.
- Add CLI-facing query ergonomics on top of the existing
  `ArtifactIndexQuery` Python API if users need non-Python inspection flows.

## Non-Goals for MVP

- Web UI.
- Model training.
- Automatic theorem-proving agent.
- Full Lean autoformalization.
- CSLib/mathlib replacement or vendoring.
- Automatic informal/formal semantic alignment checking.
- Multi-user permission system.
- Claims about project adoption, production usage, users, stars, or downloads.
