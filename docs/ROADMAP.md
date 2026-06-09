# Roadmap

TCS-Cosheaf is at the published `v0.2.0` local-MVP release baseline after the
`v0.1.1` Formal Link Layer support baseline. The project is still not
production-ready. This roadmap records durable direction and named milestones;
live issue state belongs in GitHub issues.

## Current Baseline: v0.2.0 Local MVP Release

The `v0.2.0` tag packages the already-implemented deterministic local workflow
as a pin-able framework version without adding new capability or overclaiming
production readiness, automatic theorem proving, Lean autoformalization, or
hosted agent behavior.

Completed release work includes:

- Package metadata and release notes for `v0.2.0`.
- Full framework verification for the tag.
- Workspace-template install/pin verification against the tag.
- Public KB validation/gate regression against the tag.
- A post-`v0.2.0` rollback audit that identified no code or KB revert scope,
  but did identify MCP-first roadmap language that needed rewrite.

## Next Focus: v0.2.1 CLI Agent Access

The next implementation direction is `v0.2.1` CLI Agent Access + Hosted
Provider Gateway.

This does not mean turning the project into a production hosted multi-agent
platform. It means adding a controlled agent-facing access layer around the
existing deterministic substrate:

- CLI is the primary agent interface for coding agents.
- CLI output for agent-facing commands should become stable, structured, and
  machine-readable where needed.
- The service layer is the shared implementation boundary for CLI, hosted
  provider workers, internal orchestrator code, and optional future MCP.
- Hosted model API/provider support is scheduled provider-gateway work,
  implemented behind explicit configuration, consent, policy scope, fake or
  mocked tests, and no-real-API-in-CI rules.
- Local-only execution remains fallback, offline, and CI/testing mode. It is
  not the permanent product boundary.
- External agents can operate Cosheaf through CLI first.
- The internal orchestrator may call hosted API workers only when policy,
  configuration, consent, and context-sending rules permit.
- MCP is an optional adapter for assistants that need resources/tools rather
  than shell access. It is not required for `v0.2.1`.
- Skill is an optional operator runbook, not a source of truth and not an
  authority expansion.

Real API calls are planned by design, but they must not run in CI. CI and
default tests must use fake or mocked providers. Missing credentials or
unavailable optional tools must be reported as unavailable or skipped, never as
pass.

ADR 0015 records this direction change.

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
- Read-only MCP stdio surface. This exists as optional adapter work and must
  not be treated as the primary agent path or a release blocker.
- Graph-theory, SAT/CNF, and formal-link pilot workflows that remain draft or
  example material and do not bypass review or promotion.
- GitHub Actions CI and collaboration templates.

## Agent Access Boundaries

Agent access must preserve existing governance:

- CLI commands are the first path for external coding agents.
- Controlled write surfaces must be explicit and limited to
  draft/proposal/bundle/task/run surfaces.
- MCP, if used, must not expose arbitrary shell, direct promotion, or
  accepted-path writes.
- Skill is an operator manual. It must not widen permissions or become a
  source of truth.
- Hosted workers may return worker bundles, typed sub-results, or draft
  proposals only.
- External agents must not directly edit accepted paths.
- Internal orchestration must not bypass reducer, validation, gates, review, or
  promotion.
- Provider calls must use explicit policy scope, timeout, cancellation, and
  audit metadata.
- Private KB context must not be sent to a provider unless the policy mode and
  operator consent explicitly allow it.
- API keys and secrets must not be committed or logged.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier or provider results are not passes.

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

### v0.2.0 Local MVP

`v0.2.0` is the bounded local-MVP milestone after release hardening. It turns
the existing local, deterministic surfaces into a coherent pin-able framework
version without changing the knowledge-governance boundary.

Out of scope for `v0.2.0`:

- Production hosted multi-agent runtime.
- Automatic theorem proving.
- Automatic accepted-artifact promotion.
- Web UI.
- Multi-user authentication or permissions.
- Full CSLib/mathlib ingestion, vendoring, or semantic-alignment automation.

ADR 0014 records this scope decision.

### v0.2.1 CLI Agent Access + Hosted Provider Gateway

`v0.2.1` targets the access layer around the existing local-MVP substrate:

- Fixed CLI-first execution plan installation as current project memory.
- Workspace-template pin audit against the `v0.2.0` baseline.
- Shared service layer used by CLI first, then hosted workers and optional MCP.
- Stable JSON/error contracts for agent-facing CLI commands.
- Controlled draft/proposal/bundle write CLI surfaces.
- CLI operator workflow docs and demo.
- Provider gateway design, fake/mocked test surface, and OpenAI-compatible
  transport behind explicit opt-in.
- Hosted worker contracts and execution service that produce validated worker
  bundles, not accepted knowledge.
- Skill/operator package that instructs agents how to use CLI first and MCP as
  optional adapter.
- Optional MCP adapter work after CLI/provider stabilization.

Out of scope for `v0.2.1` unless separately approved:

- Default-on hosted API calls.
- CI that requires network access, API keys, or real provider calls.
- Direct accepted writes by CLI draft tools, MCP tools, hosted workers,
  external agents, or the internal orchestrator.
- Replacing human review with AI review.
- Web UI, SaaS behavior, multi-user auth, or production operations.

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

## Non-Goals

TCS-Cosheaf does not aim to provide:

- A production hosted multi-agent system by default.
- A web UI.
- Model training.
- Automatic theorem proving.
- Full Lean autoformalization.
- CSLib/mathlib replacement or vendoring.
- Automatic informal/formal semantic alignment checking.
- Automatic accepted-artifact promotion.
- Multi-user permission system.
- Claims about project adoption, production usage, users, stars, or downloads.
