# Roadmap

TCS-Cosheaf is in Phase 8 release hardening and showcase preparation after the
`v0.1.1` Formal Link Layer support baseline. The project is still pre-MVP.
This roadmap records durable direction and named milestones; live issue state
belongs in GitHub issues.

## Current Milestone: Phase 8 Release Hardening / Showcase

Goal: make the three-repository workflow reviewable, reproducible, and easy to
demonstrate without overclaiming production readiness, automatic theorem
proving, Lean autoformalization, or hosted agent behavior.

Current release-hardening work focuses on:

- An actionable three-repository release checklist.
- Stale documentation cleanup after the external Lean library reference adapter
  and Phase 7 evaluation/observability work landed.
- Workspace-template showcase/demo documentation.
- Clear external-tool onboarding notes for manual developer tools.
- A bounded proposal for the next `v0.2.0` milestone.

## Completed Baseline

Completed framework scaffold pieces include:

- Typed artifact models and initial schemas.
- Filesystem-backed artifact loading and deterministic YAML writing.
- Repository validation CLI.
- Artifact creation, lifecycle movement, and controlled accepted-artifact
  promotion workflow.
- Workspace-aware readonly public KB plus writable private KB root loading.
- Dependency graph and deterministic index rebuild outputs.
- Read-only SQLite query API over rebuilt index output, including artifact,
  status, type, domain, dependency, reverse-dependency, formalization, and
  formal-policy queries through `ArtifactIndexQuery`.
- Gatekeeper reports with machine-readable JSON and human-readable Markdown.
- Local G8 PR checklist gate for explicit PR body markdown files.
- G9 accepted-public source metadata gate.
- G10 Formal Link Gate for formal-link metadata and verifier-result
  consistency.
- Ranked context-pack generation for issue-scoped agent work.
- Deterministic artifact-card retrieval, lexical and SQLite FTS/BM25 search,
  memory graph/PageRank, Personalized PageRank, and context-pack v2
  integration.
- Local task, worker contract, orchestrator state-machine contract,
  deterministic planner, worker-bundle v2 reducer, local worker runner, and
  local-only orchestrator dry-run.
- Provider-neutral model interface with deterministic fake-provider tests.
- Verifier adapter protocol, Python checker adapter, minimal optional SAT
  DIMACS adapter, minimal optional SMT-LIB adapter, minimal optional plain Lean
  adapter, and optional external Lean library reference checker.
- Optional MarkItDown local source-ingestion staging adapter.
- Optional Headroom experiment scaffold and CodeGraph developer-tool probe.
- Retrieval/context evaluation harnesses, structured run logging, and optional
  OpenTelemetry run-log export scaffolding.
- Graph-theory, SAT/CNF, and formal-link pilot workflows that remain draft or
  example material and do not bypass review or promotion.
- GitHub Actions CI and collaboration templates.

## Formal Link Boundary

The framework now has an optional external Lean library reference checker. It
can generate a temporary Lean file with:

```lean
import <module>
#check <symbol>
```

and run either `lean <tempfile>` or configured `lake env lean <tempfile>` when
the tool is available. This support is intentionally narrow:

- Missing Lean/lake is `skipped`, not `pass`.
- A successful `#check` only means the import and symbol resolved.
- It does not fetch CSLib/mathlib, manage external library checkouts, copy Lean
  proof bodies, autoformalize natural language, or prove informal/formal
  semantic alignment.
- Alignment review remains human-reviewed metadata.

## Public KB Direction

The public KB should grow through small source-reviewed and human-reviewed PRs.
Do not resume theorem/proof-sketch expansion until backlog, source-note, and
review policy are in place for the relevant area.

Near-term public KB work should remain:

- Foundation backlog maintenance.
- Source-note convention cleanup.
- Small accepted foundation definitions with complete source metadata and
  human review.
- No mass imports.
- No private conjectures or unreviewed LLM output under accepted public paths.

## Next Named Milestones

### v0.2.0 Proposal

`v0.2.0` should be proposed as a bounded milestone after Phase 8 hardening. The
candidate scope should emphasize:

- Librarian v1 usability and evaluation.
- Local orchestrator ergonomics without hosted LLM defaults.
- Source/review workflow hardening.
- More useful formal-link/reference-check workflows without claiming semantic
  proof.

### Verification Depth

- Improve external Lean library reference checking ergonomics without vendoring
  CSLib or mathlib.
- Expand SAT backend coverage beyond the minimal optional DIMACS invocation
  path.
- Expand SMT backend coverage beyond the minimal optional SMT-LIB invocation
  path.
- Expand Lean support beyond the minimal optional plain-file and
  external-reference invocation paths.
- Keep all external formal tools optional; unavailable tools must produce
  skipped verifier results.

### Query, Review, And Showcase Ergonomics

- Improve CLI-facing query ergonomics on top of existing index/query APIs when
  users need non-Python inspection flows.
- Improve release/demo smoke coverage across all three repositories.
- Keep README/showcase docs conservative and newcomer-friendly.

## Non-Goals For MVP

- Web UI.
- Model training.
- Automatic theorem-proving agent.
- Full Lean autoformalization.
- CSLib/mathlib replacement or vendoring.
- Automatic informal/formal semantic alignment checking.
- Multi-user permission system.
- Claims about project adoption, production usage, users, stars, or downloads.
