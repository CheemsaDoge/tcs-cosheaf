# Current Milestone

## Milestone

`v0.2.3` Verification Evidence Hardening implementation.

## Goal

Move from the published `v0.2.2` Provider Transport + Agent Workflow
Hardening release into `v0.2.3` Verification Evidence Hardening. The immediate
audit and verifier evidence record v1 are complete; the current goal is to add
read-only promotion-readiness reporting without changing accepted-promotion
semantics.

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

The current implementation task is C.3 promotion-readiness reporting.

This task adds `cosheaf promotion readiness --artifact <artifact-id> --json`
and `cosheaf promotion readiness --issue <issue-id> --json`, backed by a
read-only promotion-readiness report model. The report explains gate, review,
dependency, source metadata, readonly-root, draft-status, and target verifier
evidence conditions without promoting artifacts or changing accepted status.

The report is not human review, does not auto-promote accepted knowledge, does
not replace `cosheaf artifact promote`, and does not make skipped verifier
output pass. AI/provider output still cannot satisfy human-review requirements.

## Completion Criteria For This Task

- `cosheaf promotion readiness --artifact <artifact-id> --json` works for a
  target artifact and is read-only.
- `cosheaf promotion readiness --issue <issue-id> --json` works for an issue's
  direct `related_artifacts` and is read-only.
- Reports distinguish missing review, failed verifier, skipped verifier,
  missing source metadata, dependency risk, private dependency, draft status,
  readonly KB roots, and repository gatekeeper blockers.
- Skipped verifier output blocks checker-required readiness claims and remains
  distinct from pass.
- Documentation and interface registry describe the command without claiming
  automatic theorem proving, Lean semantic alignment, production readiness,
  AI-as-human-review, or automatic accepted promotion.

## Next Focus

After the promotion-readiness report lands, proceed to Phase D optional
SAT/SMT/Lean backend depth. Keep all external tools optional, fake-backend
tested, and skipped-not-pass.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
