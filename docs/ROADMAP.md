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
- Dependency graph and deterministic index rebuild outputs.
- Gatekeeper reports with machine-readable JSON and human-readable Markdown.
- Ranked context pack generation for issue-scoped agent work.
- Local task, worker contract, and orchestrator stubs.
- Verifier adapter protocol, Python checker adapter, and SAT/SMT/Lean skeleton
  adapters.
- Reproducibility metadata gate for executable evidence verifier results.
- Branch protection and review policy documentation.
- First graph-theory pilot workflow with draft artifact evidence and a local
  Python checker.
- GitHub Actions CI and collaboration templates.

## Active Issues

- [#13 Add second pilot: small SAT/SMT-checkable gadget](https://github.com/CheemsaDoge/tcs-cosheaf/issues/13)

## Next Named Milestones

### MVP Usability

- Replace the PR checklist placeholder gate with real checks.

### Verification Depth

- Implement real SAT solver invocation and result parsing.
- Implement real SMT solver invocation and result parsing.
- Implement real Lean command invocation and result parsing.
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
