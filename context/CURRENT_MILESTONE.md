# Current Milestone

## Milestone

Post-`v0.2.0` direction correction toward `v0.2.1` Agent Access,
Hosted API Provider, MCP, and Skill.

## Goal

Replace local-only next-focus language with the post-`v0.2.0` architecture
direction recorded in `longplan_v3.md` and
`docs/POST_V020_ROLLBACK_AUDIT.md`. The next milestone is not a permanent
local-only orchestrator hardening track. It is a controlled agent-access track
that keeps the deterministic local workflow as the baseline while designing
safe MCP, Skill, service-layer, and hosted model API worker access.

This milestone update is documentation only. It does not add runtime behavior,
change artifact schema, change gate semantics, change verifier adapter
behavior, change accepted-promotion policy, modify public KB content, modify
workspace-template behavior, or add runtime dependencies.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.0`.
- Remote tag `v0.1.1` exists and remains the downstream formal-link metadata
  baseline.
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
- The post-`v0.2.0` rollback audit identifies `context/CURRENT_MILESTONE.md`
  and `docs/ROADMAP.md` as the documents that needed direction rewrite. It did
  not identify code, schema, KB, verifier, gate, or promotion behavior that
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

The next target is `v0.2.1` Agent Access + Hosted API Provider + MCP/Skill.
The target direction is:

- MCP is the first-class external-agent machine interface.
- Skill is an optional operator guide, not a source of truth and not an
  authority expansion.
- Hosted model API/provider support is a scheduled capability, implemented
  through explicit provider-gateway and worker contracts.
- Local-only execution remains the fallback and CI/testing mode. It is not the
  permanent product boundary.
- External agents may act as orchestrators or workers through controlled MCP
  and service-layer interfaces.
- The internal orchestrator may call hosted API workers only when policy,
  configuration, consent, and context-sending rules permit.
- CLI remains the human and CI oracle.
- Service-layer functions should become the shared implementation boundary for
  CLI, MCP, internal orchestrator, and provider-backed workers.

## API And CI Boundary

Real hosted API calls are supported by design as a planned capability, but they
must not run in CI. CI and default tests must use fake or mocked providers.

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

- `context/CURRENT_MILESTONE.md` no longer says the next focus is only local
  orchestrator hardening.
- `docs/ROADMAP.md` schedules API/provider integration as controlled v0.2.1
  work rather than deferring it indefinitely.
- `docs/ADR/0015-agent-api-mcp-direction.md` records the direction change.
- Documentation preserves gate, review, promotion, public/private KB, and
  skipped-not-pass boundaries.
- Documentation states that real API calls are supported by design but not used
  in CI.
- Required local commands are run and reported honestly.

## Next Focus

After this direction rewrite lands, continue with Phase R / Task R.3: install
`longplan_v3.md` as the current durable repository execution plan. After R.3,
begin Phase A with an agent-access architecture ADR and threat model before
implementing service-layer, MCP, or hosted-provider code.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
