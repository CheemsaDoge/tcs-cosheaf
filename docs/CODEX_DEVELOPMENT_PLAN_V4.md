# TCS-Cosheaf Development Plan v4

Status: current post-`v0.2.1` durable plan

This plan follows the `v0.2.1` CLI Agent Access + Hosted Provider Gateway
prerelease. It uses the post-release audit in
[`docs/POST_V021_STATE_AUDIT.md`](POST_V021_STATE_AUDIT.md) as its baseline.

The next target is:

```text
v0.2.2 Provider Transport + Agent Workflow Hardening
```

The goal is to make real-provider use explicit, reviewable, and safe without
turning TCS-Cosheaf into a production hosted multi-agent platform.

## Baseline

At the start of this plan:

- `tcs-cosheaf` package metadata and `cosheaf.__version__` are `0.2.1`.
- `v0.2.1` is published as a GitHub prerelease, not production-ready software.
- `tcs-cosheaf-workspace-template` pins demos and provider fake smoke to
  `tcs-cosheaf@v0.2.1`.
- `tcs-kb-public` CI installs `tcs-cosheaf@v0.2.1`.
- CLI is the primary agent interface.
- Fake and mocked provider paths exist.
- Built-in real hosted HTTP transport is not implemented.
- Hosted worker CLI commands are not implemented.
- Provider MCP tools are not implemented.
- MCP is optional adapter work and is not required for ordinary CLI-first
  agent work.
- Controlled-write MCP is not planned unless a separate maintainer-approved
  issue explicitly reopens that scope.

## Non-Negotiable Invariants

Knowledge lifecycle:

- Accepted artifacts require validation, gates, review where policy requires
  it, and explicit promotion.
- Worker/provider output must not write directly to `kb/accepted/`.
- AI/provider review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier or provider results are not passes.
- Public KB accepted artifacts require source metadata and human review.
- Public KB artifacts must not depend on private KB artifacts.
- Private KB artifacts may depend on public accepted artifacts.

Provider and privacy:

- Real provider calls must be default-off.
- Real provider calls require explicit configuration, explicit consent, and an
  explicit policy scope.
- CI and default tests must use fake or mocked providers only.
- API keys must come from environment variables or a secret manager, never
  repository files.
- Logs must redact API keys, bearer tokens, environment dumps, hidden
  reasoning, and unapproved private context.
- A context-send preview must run before any real send.
- Private context may be sent only under private-research policy with explicit
  private-context consent.
- Provider output may become WorkerBundle, draft proposal, draft artifact, or
  review context only.

CLI and service layer:

- CLI remains the first agent interface and the human/CI oracle.
- Agent-facing CLI output should keep deterministic `--json` surfaces.
- The service layer is the shared implementation boundary for CLI, hosted
  workers, internal orchestrator code, tests, and optional future MCP.
- Controlled write CLI surfaces remain limited to draft, proposal, bundle,
  source-note, and review-staging outputs unless the existing promotion command
  is explicitly in scope.

MCP:

- MCP is optional and not a `v0.2.2` blocker.
- Read-only MCP may be maintained as compatibility adapter work.
- Controlled-write MCP is not planned unless a separate approved issue
  explicitly reopens it.
- MCP must not expose arbitrary shell, direct promotion, accepted writes,
  provider real-run, secrets, or environment dumps.

## Phase A: State Audit And Plan Landing

### A.1 Post-v0.2.1 Three-Repo State Audit

Status: complete.

Result: [`docs/POST_V021_STATE_AUDIT.md`](POST_V021_STATE_AUDIT.md).

The audit confirmed the `v0.2.1` prerelease state, downstream pins, empty
open-issue/PR state except for the audit issue itself, optional MCP boundary,
no global local-only overclaim, no closeout accepted-artifact additions, and
no default or CI real-provider calls.

### A.2 Land Development Plan v4

Status: this document.

This task records the v4 plan, points roadmap/milestone state at the next
focus, and adds an ADR for the post-`v0.2.1` provider/workflow hardening line.
It does not implement runtime behavior.

## Phase B: Real Provider Transport Boundary

### B.1 Real Provider Transport ADR And Threat Model

Status: complete in ADR 0021.

Define the first real OpenAI-compatible HTTP transport before implementation.
The ADR and security docs must decide:

- OpenAI-compatible HTTP is the first real transport.
- The transport is optional and default-off.
- CI and default tests never make real provider calls.
- API keys come from environment or secret manager only.
- Context preview and consent are mandatory.
- Private KB send requires `policy_mode=private_research` plus explicit
  private-context consent.
- Logs redact request/response material according to policy.
- Unsupported provider parameters return a structured negotiation result or
  error.
- Failure modes include timeout, cancellation, rate limit, HTTP error, invalid
  JSON, malformed model output, and schema rejection.
- Real-call commands must be hard to trigger accidentally.

No runtime code or new dependency belongs in B.1.

### B.2 Optional OpenAI-Compatible HTTP Transport

Next implementation task after ADR 0021. Implement the transport only after
B.1. It must stay optional, default-off, secret-redacted, timeout-aware, and
tested with mocked or local fake HTTP only. CI must not need an API key or live
network.

### B.3 Explicit Real Provider CLI Path

Add a deliberately hard-to-trigger CLI path only after B.2. It must require
explicit send confirmation, explicit network permission, valid config/key, and
a prior or inline context preview reference. Tests must mock the transport.

## Phase C: Provider Output And Worker Reliability

Harden WorkerBundle and hosted-worker outputs so failures, uncertainty,
counterexamples, verification requests, dependency questions, risk flags, and
next steps are preserved rather than swallowed. Counterexamples and failures
remain draft/proposal evidence until reviewed. Verifier requests are not
verifier results.

## Phase D: Context Privacy And Send Preview

Make provider context-send preview a trustworthy checkpoint. Public research
mode must exclude private roots. Private research mode still requires explicit
private-context consent. Previews should report artifact IDs, root scopes,
token estimates, risk flags, and full-artifact pull counts without including
full artifact text by default.

## Phase E: CLI-Agent And Provider Workflow Evaluation

Expand deterministic evals for provider workflows, malformed output, policy
denials, context scope violations, secret leakage, failure preservation, and
counterexample handling. Evals must use fake or mocked providers only.

## Phase F: Workspace Real-Provider Operator Docs

Document safe real-provider setup in the workspace template without making real
provider use part of the default demo. Default demos and smoke scripts must
remain fake-only.

## Phase G: Public KB Policy-Safe Content Path

Refresh public KB source-note and foundation backlog docs before more content
growth. Add at most one small public foundation artifact per scoped PR, and
prefer draft unless source metadata and human review evidence are complete.

## Phase H: Optional MCP Review

Re-evaluate read-only MCP only as optional adapter maintenance. Do not add new
MCP tools, provider MCP tools, arbitrary shell, controlled-write MCP, or
accepted-write behavior without separate maintainer approval.

## Phase I: v0.2.2 Release Candidate

Prepare `v0.2.2` only after the release readiness audit shows the implemented
scope is complete and conservative. Release notes may claim only implemented
and verified behavior. They must still state:

- no default real provider calls;
- no real provider calls in CI;
- no automatic accepted promotion;
- no AI review as human review;
- not a production hosted multi-agent platform;
- MCP remains optional;
- controlled-write MCP remains not planned unless separately approved.

## Per-PR Requirements

Each task should remain one issue, one branch, one PR, and one reviewable
increment. Pull request summaries should include:

```text
Goal:
Scope:
Files changed:
Tests run:
Commands unavailable:
Invariants checked:
Security/privacy impact:
Known limitations:
Follow-up tasks:
```

Every PR should attempt the repository command ladder when available:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

If a command cannot run, report the exact reason. Do not report skipped or
unavailable checks as passes.

## Completion Guardrails

Before completing each phase, check:

- no docs make MCP the primary or required agent path;
- no docs describe the product as permanently local-only;
- no real provider call enters CI/default tests;
- no API key, bearer token, environment dump, hidden reasoning, or unapproved
  private context enters committed logs;
- provider output cannot directly write accepted knowledge;
- AI/provider review is never marked as human review;
- skipped provider/verifier results are not passes;
- retrieval ranking cannot bypass public/private policy;
- workspace-template demos do not default to real API calls;
- public KB changes remain policy/content scoped;
- any new provider dependency is optional;
- public interface changes update `context/INTERFACE_REGISTRY.md`;
- new behavior has tests;
- release notes do not claim production readiness.
