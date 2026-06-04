# Roadmap

TCS-Cosheaf is pre-MVP. This roadmap is intentionally concrete and tied to
named milestones or active GitHub issues. It should not be read as a commitment
to dates, adoption, or production readiness.

## Current Milestone: Pre-MVP Scaffold Hardening

Goal: keep the repository-grounded scaffold coherent while validation,
gatekeeper, verifier, context-pack, and collaboration workflows become reliable
enough for an end-to-end TCS pilot.

Completed scaffold pieces include:

- Typed artifact models and initial schemas.
- Filesystem-backed artifact loading and deterministic YAML writing.
- Repository validation CLI.
- Artifact creation and lifecycle status movement CLI for non-accepted
  transitions.
- Controlled accepted-artifact promotion workflow.
- Dependency graph and deterministic index rebuild outputs.
- Gatekeeper reports with machine-readable JSON and human-readable Markdown.
- Local G8 PR checklist gate for explicit PR body markdown files.
- Ranked context pack generation for issue-scoped agent work.
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

- None in this repository snapshot.

## Next Named Milestones

### MVP Usability

- Improve PR checklist ergonomics for hosted PR workflows without making local
  gates depend on GitHub API access.

### Verification Depth

- Expand SAT backend coverage beyond the minimal optional DIMACS invocation path.
- Expand SMT backend coverage beyond the minimal optional SMT-LIB invocation path.
- Expand Lean support beyond the minimal optional plain-file invocation path.
- Keep all external formal tools optional; unavailable tools must produce
  skipped verifier results.

### Query and Review Ergonomics

- Add a SQLite-backed query API beyond deterministic rebuild outputs.
- Improve artifact search and graph inspection workflows.

## Non-Goals for MVP

- Web UI.
- Model training.
- Automatic theorem-proving agent.
- Full Lean autoformalization.
- Multi-user permission system.
- Claims about project adoption, production usage, users, stars, or downloads.
