# Current Milestone

## Milestone

Post-`v0.2.0` direction correction toward CLI-first agent access and hosted
provider work.

## Goal

Replace stale MCP-first roadmap language with the fixed CLI-first direction
recorded in `docs/CODEX_DEVELOPMENT_PLAN_V3.md` and
`docs/POST_V020_ROLLBACK_AUDIT.md`.

The next milestone is not a local-only orchestrator hardening track and not an
MCP-first access track. It is a controlled agent-access track where:

- CLI is the first agent interface and the human/CI oracle.
- Typed services are the shared implementation boundary.
- Hosted provider support is planned, controlled, default-off, and fake or
  mocked in tests.
- MCP is an optional adapter, not a `v0.2.1` blocker.
- Skill is an operator runbook, not a source of truth or permission expansion.

This milestone update is documentation only. It does not add runtime behavior,
change artifact schema, change gate semantics, change verifier adapter
behavior, change accepted-promotion policy, modify public KB content, modify
workspace-template behavior, or add runtime dependencies.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.0`.
- Remote tag `v0.1.1` exists and remains the downstream Formal Link Layer
  metadata baseline.
- Remote tag `v0.2.0` exists as the bounded local-MVP framework release. It is
  published as a prerelease on GitHub to avoid production-readiness
  overclaiming.
- `v0.2.0` remains the post-release baseline for this plan. It is not a
  production-ready claim.
- `tcs-cosheaf` is the framework package for CLI, schema, validation, gates,
  index/query, context packs, local task/orchestrator dry-runs, verifier
  adapters, evaluation, and observability scaffolding.
- `tcs-kb-public` is the reusable public KB and must stay public, citable,
  source-reviewed, and human-reviewed before accepted knowledge is added.
- `tcs-cosheaf-workspace-template` is the user-facing entry point with readonly
  public KB plus writable private KB overlay.
- The fixed post-`v0.2.0` rollback audit identifies roadmap, milestone, ADR,
  plan, and agent-access docs that needed direction rewrite. It did not
  identify code, schema, KB, verifier, gate, or promotion behavior that
  required revert.

## v0.2.0 Baseline Scope

`v0.2.0` packages the deterministic local workflow that already exists:

- Librarian v1 usability and evaluation.
- Context pack v2 as the default card-first context handoff.
- Local orchestrator state machine and local-only dry-run ergonomics.
- Fake provider model interface for deterministic provider-neutral tests.
- Retrieval evaluation harness and regression metrics.
- Optional external Lean `#check` ergonomics with the narrow meaning that an
  import and symbol resolved when Lean/lake is available.

`v0.2.0` did not add production hosted multi-agent execution, automatic theorem
proving, automatic accepted promotion, web UI, multi-user authentication, full
CSLib/mathlib ingestion, or semantic-alignment automation.

## v0.2.1 Direction

The next target is `v0.2.1` CLI Agent Access + Hosted Provider Gateway. The
target direction is:

- CLI is the primary agent interface for coding agents and the stable oracle
  for humans and CI.
- Core read-only agent-facing CLI commands provide stable `--json` output and
  stable error codes where needed.
- Controlled CLI write commands may create only draft/staging artifacts,
  staged source notes, bundle-review submissions, and draft informational
  review requests.
- Service-layer functions are the shared implementation boundary for CLI,
  hosted workers, internal orchestrator code, and optional future MCP.
- Hosted provider support is scheduled capability, implemented through an
  explicit provider gateway and fake/mocked tests first.
- Local-only execution remains fallback, offline, and CI/testing mode. It is
  not the permanent product boundary.
- The internal orchestrator may call hosted API workers only when policy,
  configuration, consent, and context-sending rules permit.
- External coding agents can operate Cosheaf through CLI first.
- MCP remains optional adapter work for assistants that benefit from
  resources/tools and should not block CLI/provider stabilization.
- Skill remains an optional operator runbook and must not widen authority.

## API And CI Boundary

Real hosted API calls are planned, but they must not run in CI. CI and default
tests must use fake or mocked providers.

Hosted provider behavior must remain:

- default-off;
- explicit in configuration;
- explicit about policy scope and consent;
- unable to read private KB context unless the selected policy allows it;
- unable to write accepted knowledge;
- unable to bypass reducer, validation, gates, human review, or promotion;
- careful not to log API keys, secrets, hidden reasoning, or private context
  beyond the configured audit boundary.

Missing optional provider credentials or external tools must be reported as
unavailable or skipped, never as pass.

## Knowledge-Governance Boundary

The agent-access direction does not weaken knowledge governance:

- Worker output may become draft/proposal/bundle/review context only.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, and explicit promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Completion Criteria

- `context/CURRENT_MILESTONE.md` says the next direction is CLI-first agent
  access with hosted provider work scheduled and MCP optional.
- `docs/ROADMAP.md` no longer says MCP is the first-class or primary external
  agent interface.
- ADR 0015, ADR 0016, and ADR 0017 preserve useful boundaries while
  reclassifying MCP as optional.
- `docs/CODEX_DEVELOPMENT_PLAN_V3.md` is the fixed CLI-first durable execution
  plan.
- `docs/CODEX_DEVELOPMENT_PLAN.md` is clearly marked historical and
  superseded.
- Documentation preserves gate, review, promotion, public/private KB, and
  skipped-not-pass boundaries.
- Documentation states that real API calls are planned by design but not used
  in CI.
- Required local commands are run and reported honestly.

## Next Focus

After the optional Cosheaf operator Skill package lands, continue with Phase P
/ Task P.1 from `longplan_v3_fixed_cli_first.md`: design the hosted provider
gateway without adding real provider calls to CI or weakening review, gate, or
promotion boundaries.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
