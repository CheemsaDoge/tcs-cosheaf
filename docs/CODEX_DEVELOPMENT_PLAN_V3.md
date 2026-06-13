# TCS-Cosheaf Development Plan v3: CLI-First Agent Access

This is the current durable Codex execution plan for post-`v0.2.0`
TCS-Cosheaf work. It supersedes `docs/CODEX_DEVELOPMENT_PLAN.md`.

The fixed v3 direction is CLI-first:

- CLI is the first agent interface.
- Service layer is the shared implementation boundary.
- Hosted provider support is planned, controlled, default-off, and fake or
  mocked in tests.
- MCP is optional adapter work and not a `v0.2.1` blocker.
- Skill is an operator runbook, not a source of truth.
- `v0.2.0` remains the audit and rollback baseline. Do not return to
  `v0.1.1` for this phase.

## Global Rules

1. One task = one issue = one branch = one PR.
2. Do not push directly to `main`.
3. Do not use `codex/`, `codex-`, or other agent-specific prefixes in issue
   titles, branch names, or PR titles.
4. Do not implement more than the current task in one PR.
5. If repository state conflicts with this plan, do a state audit before
   implementation.
6. Do not treat validation/gate success as human review.
7. Do not let any agent, CLI command, MCP tool, Skill, or hosted worker write
   directly to accepted knowledge.
8. Real provider calls must not run in CI.
9. Tests must use fake or mocked providers.
10. Real provider calls require explicit configuration, explicit consent, and
    explicit policy scope.
11. MCP must not become mandatory for `v0.2.1`.
12. CLI must remain the first path for coding agents.

## Repository Boundaries

`tcs-cosheaf` owns framework code and docs:

- CLI and service layer;
- schemas and typed models;
- validation and gates;
- index, memory, retrieval, and context packs;
- local task/orchestrator dry-runs;
- provider gateway and hosted worker contracts when scheduled;
- optional MCP adapter;
- Skill package when scheduled.

`tcs-kb-public` owns public reusable knowledge:

- public, citable, source-reviewed content;
- human-reviewed accepted artifacts only;
- no private conjectures;
- no unreviewed LLM output in accepted public knowledge;
- no runtime/provider/MCP code.

`tcs-cosheaf-workspace-template` owns user workspace entry:

- readonly public KB root;
- writable private KB overlay;
- CLI-agent workflow demos;
- fake provider demos when provider work exists;
- no public/private repository merging.

## Non-Negotiable Invariants

Knowledge lifecycle:

- Accepted artifacts require validation, gates, review where policy requires
  it, and explicit promotion.
- Worker output must not write directly to `kb/accepted/`.
- AI review is not human review.
- Validation/gate success is not accepted status.
- Skipped verifier results are not passes.
- Accepted artifacts must not depend on draft/private artifacts.
- Public KB must not depend on private KB.
- Private KB may depend on public accepted artifacts.

CLI/service permissions:

- Read-only CLI commands are safe by default.
- Write CLI commands must write only draft/proposal/bundle/source-note staging
  unless they are the existing explicit accepted-promotion path.
- Write commands must reject accepted paths and readonly public roots.
- Agent-facing JSON output must not leak secrets.
- No command may default to whole-repo private dumps.

Hosted provider permissions:

- CI must not call real providers.
- Tests must use fake or mocked providers.
- API keys come from environment or secret manager, never repo files.
- Provider logs must redact secrets and hidden reasoning.
- Private context send requires policy filter, preview, and consent.
- Provider output must become WorkerBundle, typed result, draft, or proposal
  only.

Optional MCP permissions:

- MCP is optional.
- MCP tools must be whitelisted service calls.
- MCP must not expose arbitrary shell.
- MCP must not expose direct promotion or accepted writes.
- Controlled-write MCP, if added, must require explicit allow-write.

## Required Reading Per Task

For `tcs-cosheaf` tasks, read:

- `AGENTS.md`
- `README.md`
- `pyproject.toml`
- `Makefile`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/GATES.md`
- `docs/ARTIFACT_SCHEMA.md`
- `docs/AGENT_ACCESS.md` if present
- `docs/MCP_SERVER.md` if present
- `docs/AGENT_PROVIDERS.md` if present
- `context/PROJECT_STATE.md`
- `context/INTERFACE_REGISTRY.md`
- `context/CURRENT_MILESTONE.md`
- `.github/workflows/`
- relevant `cosheaf/`, `schemas/`, and `tests/` paths

For `tcs-cosheaf-workspace-template` tasks, read:

- `AGENTS.md`
- `README.md`
- `cosheaf.toml`
- `docs/PUBLIC_KB_SETUP.md`
- `QUICKSTART.md` or `docs/QUICKSTART.md`
- `Makefile`
- `scripts/`
- `.github/workflows/`

For `tcs-kb-public` tasks, read:

- `AGENTS.md`
- `README.md`
- `docs/`
- `kb/public/`
- `context/`
- `.github/workflows/`

## Phase R: Direction Correction

### Task R.1: v0.2.0 Baseline Audit And Rollback Report

Repository: `tcs-cosheaf`

Branch: `rollback-audit-v020`

Status: complete.

Goal:

- Compare current `main` against `v0.2.0` /
  `9b1c3fa6f52de487e91db0282a5cf991e3e671e6`.
- Produce `docs/POST_V020_ROLLBACK_AUDIT.md`.
- Do not implement runtime behavior.

Required commands:

```bash
git fetch --tags
git log --oneline v0.2.0..main
git diff --name-status v0.2.0..main
git diff --stat v0.2.0..main
```

### Task R.2: Rewrite Roadmap And Milestone To CLI-First

Repository: `tcs-cosheaf`

Branch: `roadmap-cli-agent-provider`

Status: complete.

Goal:

- Replace stale MCP-first docs with CLI-first agent access and hosted provider
  direction.
- Keep MCP as optional adapter work.
- Do not change application code.

Allowed changes:

- `context/CURRENT_MILESTONE.md`
- `docs/ROADMAP.md`
- `docs/CODEX_DEVELOPMENT_PLAN.md`
- `docs/CODEX_DEVELOPMENT_PLAN_V3.md`
- `docs/ADR/0015-agent-api-mcp-direction.md`
- `docs/ADR/0016-agent-access-architecture.md`
- `docs/ADR/0017-mcp-agent-interface.md`
- `docs/AGENT_ACCESS.md`
- `docs/MCP_SERVER.md`
- `context/PROJECT_STATE.md` if needed
- `context/INTERFACE_REGISTRY.md` if factual interface descriptions need
  reclassification

Acceptance criteria:

- Roadmap no longer says MCP is the first-class or primary external-agent
  interface.
- Hosted provider integration is scheduled, not deferred indefinitely.
- MCP is not required for `v0.2.1`.
- Docs preserve gate/review/promotion boundaries.
- No runtime behavior changed.

### Task R.3: Workspace-Template Pin Correction Audit

Repository: `tcs-cosheaf-workspace-template`

Branch: `workspace-pin-v020-audit`

Goal:

- Align workspace-template with the current `v0.2.0` framework baseline before
  agent-access work.
- Detect and fix any remaining `v0.1.1` default install/demo pins.
- Keep public KB readonly and private overlay writable.
- Do not introduce provider/API/MCP behavior yet.

Required checks when available:

```bash
make demo
make validate
make gate
```

## Phase S: Service Layer And Stable CLI Contract

Goal: make CLI reliable for agents before provider or optional MCP expansion.

### Task S.1: Service Layer Audit And CLI Binding

Branch: `service-layer-cli-core`

Goal:

- Confirm typed services cover workspace, validation, gate, memory search,
  context pack, task, bundle validation, and draft-write workflows.
- Ensure CLI calls services where appropriate without changing existing human
  behavior.
- Do not implement provider or MCP behavior in this task.

### Task S.2: Stable CLI JSON Output

Branch: `cli-json-contracts`

Goal:

- Add or stabilize `--json` output for agent-facing commands.
- Provide stable error codes for expected failures.
- Keep text output backward compatible.

Core commands:

- `cosheaf workspace info --json`
- `cosheaf validate --json`
- `cosheaf gate run --json`
- `cosheaf memory search ... --json`
- `cosheaf context build ... --json`

### Task S.3: Controlled Draft/Bundle Write CLI

Branch: `cli-controlled-draft-writes`

Goal:

- Add narrow CLI write paths for draft/proposal/bundle surfaces.
- Reject accepted paths and readonly public roots.
- Support dry-run and exact written-path reporting.
- Do not promote artifacts or mark human review.

## Phase C: CLI Operator Workflow And Skill

### Task C.1: CLI Agent Operator Contract

Branch: `cli-agent-operator-contract`

Goal:

- Document the exact CLI workflow external coding agents must follow.
- Name allowed and forbidden commands.
- Preserve public/private, gate/review/promotion, and skipped-not-pass
  boundaries.

### Task C.2: End-To-End CLI Agent Demo

Repository: `tcs-cosheaf-workspace-template`

Branch: `cli-agent-e2e-demo`

Goal:

- Demonstrate a coding agent using only CLI to search context, write draft,
  submit bundle, validate, and gate.
- No hosted API required.
- No MCP required.
- No accepted writes.

### Task C.3: Cosheaf Operator Skill Package

Branch: `cosheaf-operator-skill-cli-first`

Goal:

- Add an optional Skill package that teaches agents to operate Cosheaf through
  CLI first.
- Mention MCP as optional future/adapter path.
- Do not grant accepted-write authority.

## Phase P: Hosted Model API Provider

### Task P.1: Provider Gateway Design ADR

Branch: `provider-gateway-design`

Goal:

- Define hosted model API calls as planned, controlled capability.
- Document data policy, consent, run records, redaction, and no-real-API-in-CI.
- Do not implement provider code.

### Task P.2: Provider Gateway Core

Branch: `provider-gateway-core`

Goal:

- Implement provider-neutral gateway with fake provider and mocked
  OpenAI-compatible transport tests.
- No real network in CI.
- Secrets must never be logged.

### Task P.3: Provider CLI Commands

Branch: `provider-cli-commands`

Goal:

- Expose provider list, config-check, preview-send, and fake-run commands.
- Do not add real-run in this task.

### Task P.4: Role-Specific Hosted API Workers

Branch: `hosted-api-workers`

Goal:

- Define role contracts for reasoner, verifier, counterexampleer, explorer,
  formalizer, and librarian summarizer.
- Hosted worker output must become WorkerBundle or typed sub-result only.

### Task P.5: Orchestrator Dispatch To Hosted Workers

Branch: `orchestrator-hosted-worker-dispatch`

Goal:

- Allow internal orchestrator to dispatch to hosted API workers when explicitly
  configured.
- Fake end-to-end path must run in CI.
- Real provider path remains opt-in and not CI.

## Phase W: Workspace Integration

### Task W.1: Workspace CLI-Agent Quickstart

Repository: `tcs-cosheaf-workspace-template`

Branch: `workspace-cli-agent-quickstart`

Goal:

- Make workspace-template the default place to run the CLI-agent workflow.
- Demonstrate JSON outputs.
- Preserve readonly public KB and writable private overlay.

### Task W.2: Workspace Provider Fake Smoke

Repository: `tcs-cosheaf-workspace-template`

Branch: `workspace-provider-fake-smoke`

Goal:

- Add fake hosted-worker/provider workflow for workspace users.
- Include `.env.example` only for variable names.
- No real API key and no accepted writes.

## Phase M: Optional MCP Adapter

MCP work is optional and later. Do not run these tasks before CLI/provider
stabilization unless the maintainer explicitly approves.

### Task M.1: MCP Necessity And Adapter ADR

Branch: `mcp-optional-adapter-adr`

Goal:

- Decide whether more MCP work is needed.
- Document MCP as optional adapter over services.
- No code changes.

### Task M.2: Optional Read-Only MCP Adapter

Branch: `mcp-readonly-adapter`

Goal:

- Keep or adjust read-only MCP service calls if needed.
- No arbitrary shell, no write tools, no provider calls.

### Task M.3: Optional Controlled-Write MCP Adapter

Branch: `mcp-controlled-write-adapter`

Goal:

- Add controlled draft/proposal/bundle writes through MCP only if approved.
- Require `--allow-write`.
- Reject accepted paths and readonly public roots.

## Phase E: Security, Evaluation, Release

### Task E.1: Agent-Access Security Regression Suite

Branch: `agent-access-security-regression`

Goal:

- Add negative tests for CLI-agent, provider, and optional MCP workflows.
- Cover accepted-write rejection, private leakage, provider redaction,
  malformed output rejection, and governance override attempts.

### Task E.2: Agent Workflow Evaluation Suite

Branch: `agent-workflow-eval`

Goal:

- Evaluate CLI-agent and provider-worker workflows with deterministic metrics.
- No network and no real model.

### Task E.3: v0.2.1 Release Candidate

Branch: `release-v021-cli-agent-provider-rc`

Status: completed and published as the `v0.2.1` prerelease. Continue with
post-`v0.2.1` hardening through small issue/branch/PR increments.

Goal:

- Prepare `v0.2.1` as the CLI Agent Access + Hosted Provider Gateway release
  candidate.
- Claims must be conservative.
- MCP remains optional and not required.

## Definition Of Done For Every PR

Before opening or summarizing a PR, check:

1. Scope did not expand beyond current task.
2. No accepted write unless the task explicitly concerns reviewed promotion and
   all policy checks pass.
3. No public/private dependency violation.
4. No skipped verifier treated as pass.
5. No AI output marked as human review.
6. No real hosted API default enabled.
7. No real API/network tests.
8. New CLI output has JSON tests if agent-facing.
9. New public interface updates `context/INTERFACE_REGISTRY.md`.
10. New architecture decision has ADR coverage.
11. New behavior has tests.
12. Docs and current milestone are updated when behavior changes.
13. Required local commands were run or honestly reported unavailable.

Required command ladder when available:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```

PR summaries must include:

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

## Stop Rules

Stop and request maintainer decision if a task requires:

- allowing agent/provider/MCP to write `kb/accepted/`;
- treating AI review as human review;
- sending private KB context to a real provider without explicit policy
  approval;
- adding a non-optional provider dependency;
- running real network/API tests in CI;
- changing public/private dependency policy;
- changing license;
- mass-importing public KB artifacts;
- making MCP mandatory for `v0.2.1`;
- removing CLI as the primary agent interface;
- storing hidden chain-of-thought;
- storing API keys, raw secrets, or unredacted provider logs;
- claiming production multi-user readiness;
- claiming automatic theorem proving or automatic informal/formal alignment.
