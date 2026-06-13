# Current Milestone

## Milestone

`v0.2.2` Provider Transport + Agent Workflow Hardening release candidate.

## Goal

Prepare `tcs-cosheaf` as a conservative `v0.2.2` release candidate after the
published `v0.2.1` CLI Agent Access + Hosted Provider Gateway prerelease. The
release-candidate scope is provider transport and agent workflow hardening:
explicit default-off real-provider transport, context-send privacy policy,
provider log scanning, failure/counterexample preservation, deterministic
provider/failure evals, and three-repository smoke coverage.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving, automatic
Lean autoformalization, automatic accepted promotion, AI-as-human-review, or
automatic informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.2` on this
  release-candidate branch.
- Remote tag `v0.1.1` exists and remains the downstream Formal Link Layer
  metadata baseline.
- Remote tag `v0.2.0` exists as the bounded local-MVP framework release. It is
  a baseline, not a production-ready claim.
- Remote tag `v0.2.1` exists and is published as a conservative GitHub
  prerelease, not a production-readiness claim.
- Remote tag `v0.2.2` should be created only after the release-candidate PR
  and required checks pass.
- `tcs-cosheaf-workspace-template` currently pins CLI-agent/provider demo
  workflows to `@v0.2.1`; it should move to `@v0.2.2` only after the tag is
  published and downstream verification runs.
- `tcs-kb-public` CI currently installs `tcs-cosheaf` from `@v0.2.1`; it should
  move to `@v0.2.2` only after the tag is published and repository-local
  validation, gate, PR-checklist, and policy guard checks pass.
- `tcs-cosheaf` is the framework package for CLI, schema, validation, gates,
  index/query, context packs, local task/orchestrator dry-runs, service-layer
  entry points, provider gateway, hosted-worker dispatch, evaluation, and
  observability scaffolding.
- `tcs-kb-public` is the reusable public KB and must stay public, citable,
  source-reviewed, and human-reviewed before accepted knowledge is added.
- `tcs-cosheaf-workspace-template` is the user-facing entry point with readonly
  public KB plus writable private KB overlay.

## v0.2.2 Scope

`v0.2.2` packages hardening around the existing deterministic substrate:

- Optional stdlib OpenAI-compatible HTTP transport object, default-off and
  explicitly configured/injected.
- Explicit `cosheaf provider real-run --input-json <path> --provider
  openai-compatible --confirm-send --allow-network --json` path that fails
  closed without inline context preview, send consent, network permission,
  endpoint/API-key environment configuration, and required private-context
  consent.
- Provider context-send policy matrix: public mode uses public scope only,
  private context requires private-research policy plus consent,
  workspace/framework cards are excluded, and previews remain metadata-only.
- Provider log redaction and deterministic leak-scanner regression coverage.
- WorkerBundle v2 preservation for assumptions, uncertainty, failed attempts,
  candidate counterexamples, verification requests, dependency questions, risk
  flags, and next steps as review-only material.
- Role contracts that require structured uncertainty, failures, verifier
  requests, candidate-vs-verified counterexamples, formal symbol-resolution vs
  semantic-alignment separation, and no-claim-invention librarian summaries.
- Provider malformed-output recovery with typed
  `provider_output_validation_failed` paths and optional logged schema-reminder
  retry.
- Python-level provider workflow eval suite.
- Python-level failure/counterexample workflow eval suite.
- Three-repository ecosystem smoke matrix.
- Workspace-template real-provider setup docs and public-only provider preview
  smoke.
- Public KB source-note/backlog refresh and exactly one draft-only foundation
  tightening since the `v0.2.1` compatibility update.
- Optional read-only MCP review. No controlled-write MCP, provider MCP tools,
  arbitrary shell, or accepted writes were added.

## Explicit Boundaries

- CLI is the first agent interface and the human/CI oracle.
- Service-layer functions are the shared implementation boundary for CLI,
  hosted workers, internal orchestrator code, tests, and optional future MCP.
- Hosted provider support is controlled, default-off, and fake or mocked in
  tests.
- Real provider calls require explicit configuration, credentials, policy
  scope, context preview, network permission, and operator consent.
- No real provider calls run in CI or default tests.
- MCP remains optional adapter work. Controlled-write MCP is not planned unless
  separately approved.
- Skill is an optional operator runbook, not a source of truth or permission
  expansion.
- Worker/provider output may become draft/proposal/bundle/review context only.
- WorkerBundle verification requests are not verifier results, and candidate
  counterexamples are not accepted refutations.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, verifier evidence where applicable, and explicit
  promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier or provider results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Completion Criteria

- Package metadata and `cosheaf.__version__` are set to `0.2.2`.
- `docs/releases/v0.2.2.md` exists and states conservative release-candidate
  boundaries.
- README, roadmap, release checklist, release notes, and current milestone
  agree on `v0.2.2` as Provider Transport + Agent Workflow Hardening release
  candidate scope.
- Docs do not describe the current system as permanently local-only.
- Docs do not claim production hosted multi-agent readiness, automatic theorem
  proving, automatic accepted promotion, AI-as-human-review, or
  Lean/mathlib/CSLib semantic alignment.
- MCP remains optional and not required for `v0.2.2`.
- Required local commands are run and reported honestly.
- Ecosystem smoke runs against local framework, workspace-template, and public
  KB checkouts. Network rows remain skipped unless explicitly enabled and must
  not be counted as passes.

## Next Focus

After the `v0.2.2` release-candidate PR passes and merges:

1. Publish the `v0.2.2` tag/release only if the maintainer release process
   approves it.
2. Update `tcs-cosheaf-workspace-template` to pin/demo `@v0.2.2` and rerun its
   demo/showcase/provider-preview checks.
3. Update `tcs-kb-public` to validate/gate/policy-guard against `@v0.2.2`.
4. Continue post-`v0.2.2` work through small issue/branch/PR increments without
   weakening review, gate, promotion, or public/private policy boundaries.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
