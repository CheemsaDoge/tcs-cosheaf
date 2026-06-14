# Current Milestone

## Milestone

`v0.2.3` Verification Evidence Hardening implementation.

## Goal

Move from the published `v0.2.2` Provider Transport + Agent Workflow
Hardening release into `v0.2.3` Verification Evidence Hardening. The immediate
audit is complete; the current goal is to add verifier evidence record v1
without changing verifier, gatekeeper, or promotion semantics.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving,
automatic Lean autoformalization, automatic accepted promotion,
AI-as-human-review, provider/MCP authority expansion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.2`.
- Remote tags `v0.1.1`, `v0.2.0`, `v0.2.1`, and `v0.2.2` exist.
- The GitHub release `v0.2.2 Provider Transport + Agent Workflow Hardening`
  is published and is not a production-readiness claim.
- `tcs-cosheaf-workspace-template` pins active demo, Makefile, CLI-agent,
  provider-preview, and fake-provider smoke paths to `@v0.2.2`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.2.2`.
- `docs/CODEX_DEVELOPMENT_PLAN_V4.md` is historical/completed after the
  `v0.2.2` release closeout.
- `docs/CODEX_DEVELOPMENT_PLAN_V5.md` is the current durable plan.
- ADR 0022 records the `v0.2.3` Verification Evidence Hardening decision.
- `docs/VERIFIER_EVIDENCE_AUDIT.md` records the current verifier adapter,
  result-state, logging, gate, promotion, Lean `#check`, and sidecar boundary.
- `tcs-cosheaf` is the framework package for CLI, schema, validation, gates,
  index/query, context packs, local task/orchestrator dry-runs, service-layer
  entry points, provider gateway, hosted-worker dispatch, evaluation,
  verifier adapters, and observability scaffolding.
- `tcs-kb-public` is the reusable public KB and must stay public, citable,
  source-reviewed, and human-reviewed before accepted knowledge is added.
- `tcs-cosheaf-workspace-template` is the user-facing entry point with readonly
  public KB plus writable private KB overlay.

## v0.2.3 Scope

`v0.2.3` is Verification Evidence Hardening. It should deepen reviewable
evidence around optional verifier and failure workflows:

- Verifier evidence model and normalized result taxonomy.
- Explicit distinction between `verifier_request`, `verifier_result`,
  `candidate_counterexample`, and `checked_counterexample`.
- SAT optional backend ergonomics, command metadata, timeout handling, and
  unavailable-tool skips.
- SMT optional backend ergonomics, `sat`/`unsat`/`unknown` handling, command
  metadata, timeout handling, and unavailable-tool skips.
- Plain Lean and external Lean library reference checker ergonomics, with
  `#check` documented as symbol/import resolution only.
- Failure and counterexample evidence workflows that preserve failed attempts
  and candidates without treating them as proof or checked refutation.
- Promotion-readiness reporting that explains missing evidence without
  bypassing validation, gates, review, verifier requirements, or promotion.
- Three-repository readiness checks for framework, workspace-template, and
  public KB.

## Explicit Boundaries

- CLI remains the first agent interface and the human/CI oracle.
- Real provider calls remain default-off and require explicit configuration,
  credentials, policy scope, context preview, network permission, and operator
  consent.
- No real provider calls run in CI or default tests.
- `v0.2.3` does not expand provider authority, add provider MCP tools, add
  controlled-write MCP, or make MCP the primary path.
- Worker/provider output may become draft/proposal/bundle/review context only.
- A `verifier_request` is not a `verifier_result`.
- A `candidate_counterexample` is not a `checked_counterexample`.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, verifier evidence where applicable, and explicit
  promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier, provider, SAT, SMT, or Lean results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Current Task

The current implementation task is C.2 verifier evidence record v1.

This task adds a typed, serializable `VerifierEvidenceRecord` and
`schemas/verifier_evidence.schema.json` for verifier output records. It keeps
current normalized result states as `pass`, `fail`, `error`, and `skipped`;
keeps skipped verifier output distinct from pass; and preserves the boundary
that Lean `#check` is import/symbol resolution only, not semantic alignment.

The record is not human review, does not auto-promote accepted knowledge, and
does not change the fresh gatekeeper run used by promotion.

## Completion Criteria For This Planning Milestone

- `docs/CODEX_DEVELOPMENT_PLAN_V5.md` exists and is identified as the current
  durable plan.
- ADR 0022 exists and records the verification/evidence hardening decision.
- `docs/CODEX_DEVELOPMENT_PLAN_V4.md` is marked historical/completed after the
  `v0.2.2` closeout.
- README/roadmap/release checklist/current milestone do not overclaim
  automatic theorem proving, Lean semantic alignment, production readiness,
  provider/MCP authority, or accepted promotion.
- No runtime, schema, gate, verifier, promotion, provider, MCP, KB artifact, or
  public/private policy changes are made in the planning PR.

## Next Focus

After the verifier evidence record v1 lands, proceed to C.3: add a read-only
promotion-readiness report that explains gate, review, dependency, source, and
verifier evidence status without promoting artifacts or converting skipped
results into passes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
