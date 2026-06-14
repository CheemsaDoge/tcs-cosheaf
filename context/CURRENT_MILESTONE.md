# Current Milestone

## Milestone

`v0.2.3` Verification Evidence Hardening implementation.

## Goal

Move from the published `v0.2.2` Provider Transport + Agent Workflow
Hardening release into `v0.2.3` Verification Evidence Hardening. The verifier
evidence audit, verifier evidence record v1, read-only promotion-readiness
report, optional SAT result-depth fixtures, optional SMT result-depth fixtures,
Lean external reference ergonomics, typed counterexample candidate records, and
failure-preserving review-request generation are complete. Workspace and public
KB integration follow-up is complete through the verifier-evidence workspace
demo, public KB source/backlog hygiene, and one draft-only foundation artifact
tightening. The v0.2.3 ecosystem readiness matrix is complete. The current
goal is the v0.2.3 release readiness audit without expanding provider or MCP
authority.

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

The current implementation line is v0.2.3 release hardening. The active task is
the v0.2.3 release readiness audit. It is documentation/status only: it does
not bump the package version, create a tag or release, change runtime behavior,
expand provider/MCP authority, run real provider calls by default, turn
generated review requests into human review, or treat skipped verifier results
as passes.

## Recently Completed Tasks

D.3 Lean external reference ergonomics improved optional external Lean
`#check` debugging without adding a mandatory Lean or lake dependency. The
task added fake-backend tests for missing import and missing symbol stderr log
preservation, clearer manifest diagnostics for unknown `library_ref` values,
and documentation that a successful external Lean `#check` means only import
and symbol resolution.

The task does not fetch CSLib, mathlib, or any Lean library, does not vendor
Lean code, does not claim theorem proving, does not claim informal/formal
semantic alignment, does not write accepted knowledge, and keeps missing
Lean/lake as `skipped`, not `pass`.

E.1 typed counterexample candidate records added optional WorkerBundle v2
`counterexample_candidates` with candidate ID, optional target claim,
construction summary, evidence paths, verifier-request IDs, status, and
limitations. E.1 keeps legacy string `counterexamples` backward-compatible.
Reducers preserve typed candidates as review warnings and never convert them
into accepted refutations, verifier results, human review, or promotion
authority. `checked_false` and `checked_true` candidate statuses require
evidence paths in the bundle schema, but they still do not change accepted
artifact status.

E.2 failure-preserving review request generation added
`cosheaf review request-from-bundle --bundle <path>`. It validates WorkerBundle
v2 manifests and writes or previews draft informational review requests under
`reviews/requests/`, preserving assumptions, uncertainty, failed attempts,
verifier requests, legacy and typed counterexample candidates, dependency
questions, risk flags, next steps, confidence, and candidate limitations as
findings. It rejects accepted-path and human-reviewed-authority spoofing before
writing anything and never creates verifier results, human review, accepted
knowledge, or promotion authority.

G.1 verifier evidence eval suite added `cosheaf.evals.verifier_evidence` and
`evals/verifier_evidence/cases.yaml`. The deterministic Python-level harness
scores pass/failed/skipped verifier evidence readiness boundaries, typed
candidate counterexample review-only behavior, and Lean external `#check`
symbol-resolution-only limitations. It uses fake evidence records and typed
fixtures only: no SAT, SMT, Lean, lake, hosted provider, MCP, accepted write,
human review, or promotion is performed.

G.2 three-repository readiness matrix extends `scripts/ecosystem_smoke.py
--matrix` with framework verifier-evidence eval smoke, an optional verifier
availability probe, workspace-template verifier-evidence demo coverage, and a
separate public KB verifier-policy self-test. The matrix keeps network rows
opt-in, counts optional verifier absence as skipped rather than pass, and
continues to identify the failing repository and command for failures.

## Next Focus

Proceed with the v0.2.3 release-candidate task only after the readiness audit
PR merges and the required verification ladder passes. The release-candidate
task should update package metadata to `0.2.3`, convert
`docs/releases/v0.2.3.md` from audit draft to final release notes, rerun the
ecosystem readiness matrix, and prepare the tag/release and downstream pin
updates. Candidate counterexamples must remain candidates until explicitly
checked and reviewed, generated review requests must remain draft review
context, and readiness/eval work must keep skipped results separate from
passes.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
