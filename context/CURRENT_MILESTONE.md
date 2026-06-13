# Current Milestone

## Milestone

Post-`v0.2.1` v4 plan landing and `v0.2.2` provider/workflow hardening prep.

## Goal

Keep the published `v0.2.1` framework prerelease, downstream workspace
template, and public KB compatibility state internally consistent while
landing the post-`v0.2.1` v4 development plan. The next target is
`v0.2.2 Provider Transport + Agent Workflow Hardening`: explicit,
default-off real-provider transport work, stronger provider/context privacy
boundaries, failure/counterexample workflow hardening, and regression evals
without weakening review, gate, promotion, or public/private policy.

The `v0.2.1` tag packages the CLI-first agent-access surface, controlled
draft/staging write CLI, provider gateway, fake/mocked hosted-worker path,
operator guidance, security regressions, and agent workflow evals that landed
after the `v0.2.0` local-MVP baseline.

This milestone does not claim production hosted multi-agent readiness. It does
not add a web UI, multi-user permissions, automatic theorem proving, automatic
Lean autoformalization, automatic accepted promotion, or automatic
informal/formal semantic alignment.

## Current Baseline

- Framework package metadata and `cosheaf.__version__` record `0.2.1` on
  `main`.
- Remote tag `v0.1.1` exists and remains the downstream Formal Link Layer
  metadata baseline.
- Remote tag `v0.2.0` exists as the bounded local-MVP framework release. It is
  a baseline, not a production-ready claim.
- Remote tag `v0.2.1` exists and is published as a conservative GitHub
  prerelease, not a production-readiness claim.
- `tcs-cosheaf-workspace-template` pins CLI-agent/provider demo workflows to
  `@v0.2.1`.
- `tcs-kb-public` CI installs `tcs-cosheaf` from `@v0.2.1` and has run its
  validation, gate, PR-checklist, and repository-local policy guard checks
  against that tag.
- `tcs-cosheaf` is the framework package for CLI, schema, validation, gates,
  index/query, context packs, local task/orchestrator dry-runs, service-layer
  entry points, provider gateway, hosted-worker dispatch, evaluation, and
  observability scaffolding.
- `tcs-kb-public` is the reusable public KB and must stay public, citable,
  source-reviewed, and human-reviewed before accepted knowledge is added.
- `tcs-cosheaf-workspace-template` is the user-facing entry point with readonly
  public KB plus writable private KB overlay.

## v0.2.1 Scope

`v0.2.1` packages the access layer around the existing deterministic substrate:

- CLI-first agent access with deterministic `--json` output for core
  read/check commands.
- Stable agent-access DTOs and `ErrorResult` codes.
- Controlled draft artifact, source-note staging, bundle submission, and draft
  review-request CLI commands.
- CLI operator workflow docs and optional operator Skill package.
- Provider gateway with deterministic fake provider and OpenAI-compatible
  mocked transport boundary.
- Provider CLI commands for list, config-check, context-send preview, and
  fake-run, plus an explicit real-run path that fails closed without inline
  preview, send consent, network permission, endpoint/key configuration, and
  required private-context consent.
- Role-specific hosted worker service for fake or mocked provider calls.
- Internal orchestrator dispatch to hosted workers only when explicitly
  configured.
- WorkerBundle v2 preserves assumptions, uncertainty, failed attempts,
  candidate counterexamples, verification requests, dependency questions, risk
  flags, and next steps as review-only reducer warnings.
- Role contracts require structured uncertainty, failures, verifier requests,
  candidate-vs-verified counterexamples, formal symbol-resolution versus
  semantic-alignment separation, and no-claim-invention librarian summaries.
- Security regression coverage for agent/provider/optional-MCP governance
  boundaries.
- Python-level agent workflow eval suite for CLI, provider, context privacy,
  bundle validity, gate regression, and optional read-only MCP smoke.

## Explicit Boundaries

- CLI is the first agent interface and the human/CI oracle.
- Service-layer functions are the shared implementation boundary for CLI,
  hosted workers, internal orchestrator code, tests, and optional future MCP.
- Hosted provider support is controlled, default-off, and fake or mocked in
  tests.
- Optional real hosted HTTP transport exists as an explicitly injected stdlib
  OpenAI-compatible transport object and is not default-enabled.
- Provider `real-run` CLI exists as a deliberately hard-to-trigger operator
  path and is not used by CI or default demos.
- Real provider calls require explicit configuration, credentials, policy
  scope, context preview, and operator consent.
- MCP remains optional adapter work. It is not a `v0.2.1` blocker.
- Skill is an optional operator runbook, not a source of truth or permission
  expansion.
- Worker/provider output may become draft/proposal/bundle/review context only.
- WorkerBundle verification requests are not verifier results, and candidate
  counterexamples are not accepted refutations.
- Accepted knowledge still requires validation, gates, human review where
  policy requires it, and explicit promotion.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier or provider results are not passes.
- Public KB accepted artifacts still require complete source metadata and
  human review.
- Formal links remain metadata unless a checker actually records a result.
- A successful Lean `#check` remains symbol/import resolution, not
  informal/formal semantic alignment.

## Completion Criteria

- Package metadata and `cosheaf.__version__` are set to `0.2.1`.
- `docs/releases/v0.2.1.md` exists and states conservative release boundaries.
- README, roadmap, release checklist, release notes, and current milestone
  agree on `v0.2.1` as a published CLI Agent Access + Hosted Provider Gateway
  prerelease.
- Docs do not describe the current system as local-only.
- Docs do not claim production hosted multi-agent readiness, automatic theorem
  proving, automatic accepted promotion, or Lean/mathlib/CSLib semantic
  alignment.
- MCP remains optional and not required for `v0.2.1`.
- Required local commands are run and reported honestly.
- Workspace-template and public KB compatibility are checked against the
  published `v0.2.1` tag.

## Next Focus

After the `v0.2.1` prerelease and downstream compatibility checks:

1. Treat [`docs/POST_V021_STATE_AUDIT.md`](../docs/POST_V021_STATE_AUDIT.md)
   as the current post-release evidence baseline.
2. Treat [`docs/CODEX_DEVELOPMENT_PLAN_V4.md`](../docs/CODEX_DEVELOPMENT_PLAN_V4.md)
   and ADR 0020 as the current next-stage plan.
3. Treat ADR 0021 as the real-provider transport boundary and threat model.
4. Treat `OpenAICompatibleHttpTransport` as the optional stdlib HTTP transport
   implementation: it remains explicit, default-off, injected/configured, and
   absent from default CI/provider demos.
5. Continue with provider malformed-output recovery and provider output
   reliability work.
6. Continue post-`v0.2.1` hardening through small issue/branch/PR increments.
7. Improve CLI-agent, provider fake/mocked, context-pack, evaluation, and
   failure/counterexample workflows without weakening review, gate, promotion,
   or public/private policy boundaries.
8. Treat MCP as optional adapter work and do not implement controlled-write MCP
   without a separate approved issue.

Maintain the current maintainer override: do not add `codex` prefixes to issue
names, branch names, or pull request titles, even when older examples show that
prefix.
