# Post-v0.2.0 Rollback Audit

Issue: #191

Task: Phase R / Task R.1 from the maintainer-provided
`longplan_v3_fixed_cli_first.md`.

## Scope

This audit compares current `main` with the `v0.2.0` release baseline and
classifies every post-release changed file as `KEEP`, `REWRITE`,
`KEEP AS OPTIONAL / RECLASSIFY`, `REVERT`, or `NEEDS_HUMAN_DECISION`.

This audit is documentation only. It does not change runtime behavior, schemas,
tests, gate behavior, verifier adapters, KB artifacts, accepted-promotion
policy, workspace-template behavior, or release tags.

## Baseline

- Baseline tag: `v0.2.0`
- Baseline commit: `9b1c3fa6f52de487e91db0282a5cf991e3e671e6`
- Current audited `main`: `bd9b6a4209066b5d9bbd8aaba2d71b49c6c7403d`

`v0.2.0` is the local-MVP release baseline. It is not a production-ready
claim, and it is not the older `v0.1.1` Formal Link Layer support baseline.

## Fixed CLI-First Direction

The fixed plan changes the post-`v0.2.0` direction from the older MCP-first v3
plan to a CLI-first plan:

- CLI is the primary agent interface.
- Service-layer work should support CLI first, then hosted provider and
  optional MCP adapter reuse.
- Hosted provider support is planned work, but it remains default-off,
  fake/mocked in tests, explicit for real calls, and unable to write accepted
  knowledge.
- MCP is optional and later. It must not be a `v0.2.1` blocker.
- Existing MCP code is not automatically unsafe merely because it exists, but
  it must be described as an optional adapter and not as the mainline release
  path.
- Skill is an operator runbook, not a source of truth or authority expansion.

## Required Git Evidence

Commands used for this audit:

```powershell
git fetch --tags
git log --oneline v0.2.0..main
git diff --name-status v0.2.0..main
git diff --stat v0.2.0..main
git rev-list -n 1 v0.2.0
git rev-parse main
```

Post-`v0.2.0` commits on `main`:

```text
bd9b6a4 Add MCP prompts and resource templates
b8b7b05 Add read-only MCP server v1
13a3928 Document MCP design and security model
8cb1ea3 Add context send policy preview
4e5fdba Define agent access schemas
30becbf Extract typed service layer
9bab548 Document agent access architecture
7ba544c Install longplan v3 as current repo plan
841d032 Rewrite roadmap toward agent API and MCP
f85c9f6 Audit post-v0.2.0 changes for longplan v3
b43ebe9 Expand default context eval cases
bef6c72 Expand default retrieval eval cases
14f9f43 Document git index lock recovery
12d9d6f Harden worker bundle proposed paths
8a036a4 Document stuck Actions check recovery
3e1c455 Harden orchestrator state path validation
f1c4333 Align v0.2.0 state documentation
```

Changed-file summary:

```text
52 files changed, 9281 insertions(+), 178 deletions(-)
```

No files under `kb/`, `issues/`, or `reviews/` changed in
`v0.2.0..main`.

## Issue State

- GitHub issue #169, `Audit orchestrator state model contract`, is `CLOSED`.
  It is stale as a mainline driver and should not send the project back to a
  local-orchestrator-only track. Treat any remaining value there as schema or
  test hardening backlog only.
- GitHub issue #170, `Audit post-v0.2.0 changes for longplan v3`, is
  `CLOSED`. It produced the older MCP-first audit and is superseded by this
  fixed CLI-first audit.
- GitHub issue #191 tracks this audit refresh.

## Classification Summary

| File | Classification | Reason |
| --- | --- | --- |
| `README.md` | KEEP | Records the `v0.2.0` local-MVP status and current limitations without making MCP a blocker. |
| `RELEASE_CHECKLIST.md` | KEEP | Keeps conservative release boundaries and says hosted LLM execution is not part of default workflows. |
| `context/CURRENT_MILESTONE.md` | REWRITE | Still says the next target is Agent Access + Hosted API Provider + MCP/Skill and calls MCP first-class. It must be rewritten to CLI-first, hosted-provider planned, MCP optional. |
| `context/INTERFACE_REGISTRY.md` | KEEP AS OPTIONAL / RECLASSIFY | Registers real service and MCP interfaces that now exist. Keep factual entries if the implementation is kept, but reclassify MCP as optional and not a milestone blocker. |
| `context/PROJECT_STATE.md` | KEEP | Preserves ordered release history and conservative provider boundaries. A later state entry may record the fixed CLI-first plan, but no revert is required. |
| `cosheaf/agent/orchestrator_state.py` | KEEP | Adds path-boundary hardening useful for CLI/provider/MCP safety. |
| `cosheaf/agent/worker_bundle_v2.py` | KEEP | Adds proposed-path hardening and keeps worker output away from unsafe paths. |
| `cosheaf/cli.py` | KEEP | Wires existing CLI to typed services and exposes factual read-only MCP commands. Keep, but future CLI-first work must stabilize JSON contracts. |
| `cosheaf/mcp/__init__.py` | KEEP AS OPTIONAL / RECLASSIFY | Existing read-only MCP package can stay as optional adapter code if docs stop making it the mainline. |
| `cosheaf/mcp/server.py` | KEEP AS OPTIONAL / RECLASSIFY | Read-only MCP implementation is whitelisted and does not expose arbitrary shell, provider calls, or accepted writes. Treat as optional, not required. |
| `cosheaf/services/__init__.py` | KEEP | Typed services are directly compatible with CLI-first work and later provider/MCP reuse. |
| `cosheaf/services/context_policy.py` | KEEP | Context-send preview supports provider safety without making real provider calls. |
| `cosheaf/services/models.py` | KEEP | DTOs support CLI JSON, service reuse, provider preview, and bundle validation surfaces. |
| `docs/ADR/0015-agent-api-mcp-direction.md` | REWRITE | Records MCP as first-class external-agent interface. Must be replaced or revised to CLI-first with MCP optional. |
| `docs/ADR/0016-agent-access-architecture.md` | REWRITE | Records MCP as primary external-agent machine interface. Must be revised to CLI-first service/provider direction. |
| `docs/ADR/0017-mcp-agent-interface.md` | REWRITE | MCP security boundaries are useful, but the ADR must be reframed as optional adapter design rather than current mainline prerequisite. |
| `docs/AGENT_ACCESS.md` | REWRITE | Says MCP is the primary machine interface and discusses when to prefer MCP over CLI. Must become CLI-first. |
| `docs/ARCHITECTURE.md` | KEEP | Documents current service and local-runner boundaries without making MCP first-class. |
| `docs/CODEX_DEVELOPMENT_PLAN.md` | REWRITE | Historical plan pointer currently names old `CODEX_DEVELOPMENT_PLAN_V3.md` as controlling. It must point to the fixed CLI-first plan once installed. |
| `docs/CODEX_DEVELOPMENT_PLAN_V3.md` | REWRITE | Current in-repo v3 plan is MCP-first and conflicts with the fixed CLI-first plan. |
| `docs/MCP_SERVER.md` | REWRITE | Threat model is useful, but the document calls MCP the planned machine interface. Reframe as optional adapter. |
| `docs/OPERATOR_NOTES.md` | KEEP | Records real operator pitfalls for GitHub, PATH, proxy, index locks, identity, and generated outputs. |
| `docs/POST_V020_ROLLBACK_AUDIT.md` | REWRITE | This file is being refreshed from old v3 to fixed CLI-first direction. |
| `docs/ROADMAP.md` | REWRITE | Still says MCP becomes first-class and Skill explains MCP-first usage. Must be rewritten to CLI-first, provider planned, MCP optional. |
| `evals/context/cases.yaml` | KEEP | Expands deterministic context evaluation coverage without changing truth or governance. |
| `evals/retrieval/cases.yaml` | KEEP | Expands deterministic retrieval evaluation coverage without changing truth or governance. |
| `schemas/agent_access/context_build_request.schema.json` | KEEP | Agent-access schema supports stable service/CLI contracts. |
| `schemas/agent_access/context_build_result.schema.json` | KEEP | Agent-access schema supports stable service/CLI contracts. |
| `schemas/agent_access/create_task_request.schema.json` | KEEP | Agent-access schema supports typed task creation contracts. |
| `schemas/agent_access/create_task_result.schema.json` | KEEP | Agent-access schema supports typed task creation contracts. |
| `schemas/agent_access/draft_artifact_write_request.schema.json` | KEEP | Draft-write schema is compatible with CLI-first controlled writes; accepted writes remain out of scope. |
| `schemas/agent_access/draft_artifact_write_result.schema.json` | KEEP | Draft-write result schema is compatible with CLI-first controlled writes. |
| `schemas/agent_access/error_result.schema.json` | KEEP | Stable error-result shape is required for CLI-first agent use. |
| `schemas/agent_access/gate_run_result.schema.json` | KEEP | Gate result schema supports agent-readable gate output without weakening human review. |
| `schemas/agent_access/memory_search_request.schema.json` | KEEP | Search request schema supports deterministic agent-facing retrieval. |
| `schemas/agent_access/memory_search_result.schema.json` | KEEP | Search result schema supports deterministic agent-facing retrieval. |
| `schemas/agent_access/model_call_request.schema.json` | KEEP | Provider request schema is useful for planned hosted provider work; it does not enable real calls by itself. |
| `schemas/agent_access/model_call_result.schema.json` | KEEP | Provider result schema is useful for planned hosted provider work; it does not mark outputs accepted. |
| `schemas/agent_access/provider_run_record.schema.json` | KEEP | Provider run-record schema supports audit/redaction requirements for planned hosted provider work. |
| `schemas/agent_access/validate_result.schema.json` | KEEP | Validate result schema supports stable CLI JSON contracts. |
| `schemas/agent_access/worker_bundle_submit_request.schema.json` | KEEP | Bundle submit schema supports controlled worker-bundle flow. |
| `schemas/agent_access/worker_bundle_submit_result.schema.json` | KEEP | Bundle submit result schema supports controlled worker-bundle flow. |
| `schemas/agent_access/workspace_info_result.schema.json` | KEEP | Workspace info schema supports stable CLI JSON contracts. |
| `tests/test_agent_access_models.py` | KEEP | Tests schema/DTO behavior needed for CLI-first and provider-safe access. |
| `tests/test_context_eval.py` | KEEP | Tests expanded deterministic context eval cases. |
| `tests/test_context_send_policy.py` | KEEP | Tests provider context preview and policy filtering without real provider calls. |
| `tests/test_mcp_server.py` | KEEP AS OPTIONAL / RECLASSIFY | Tests current read-only MCP safety. Keep if optional MCP code stays, but do not treat as v0.2.1 blocker. |
| `tests/test_orchestrator_state.py` | KEEP | Tests path-boundary hardening and state invariants. |
| `tests/test_retrieval_eval.py` | KEEP | Tests expanded deterministic retrieval eval cases. |
| `tests/test_schema_files_exist.py` | KEEP | Keeps schema file coverage aligned with added agent-access schemas. |
| `tests/test_services.py` | KEEP | Service tests support CLI-first implementation reuse. |
| `tests/test_worker_bundle_v2.py` | KEEP | Tests worker-bundle path hardening and output discipline. |

## Keep

The following post-`v0.2.0` work is compatible with the fixed plan and should
not be reverted:

- typed service layer and DTOs;
- agent-access JSON Schemas that can support stable CLI JSON contracts;
- context-send policy preview and provider audit DTOs;
- path-boundary hardening for orchestrator state and worker bundles;
- deterministic retrieval/context eval expansion;
- operator notes for recurring local GitHub, PATH, proxy, identity, and runtime
  output pitfalls;
- factual release/status documentation that does not make MCP first-class.

These changes help the CLI-first path and later hosted provider work. They do
not call real providers, write accepted knowledge, change promotion policy, or
weaken gates.

## Rewrite

The fixed plan requires targeted rewrite, not a hard reset. Rewrite these
documents before using them to drive new implementation:

- `context/CURRENT_MILESTONE.md`
- `docs/ROADMAP.md`
- `docs/CODEX_DEVELOPMENT_PLAN.md`
- `docs/CODEX_DEVELOPMENT_PLAN_V3.md`
- `docs/ADR/0015-agent-api-mcp-direction.md`
- `docs/ADR/0016-agent-access-architecture.md`
- `docs/ADR/0017-mcp-agent-interface.md`
- `docs/AGENT_ACCESS.md`
- `docs/MCP_SERVER.md`

Required rewrite direction:

- CLI is the first agent interface.
- Hosted provider is scheduled and controlled, not forbidden or default-on.
- MCP is optional and later, not a `v0.2.1` blocker.
- Skill is a runbook, not an authority surface.
- Existing governance remains unchanged: no direct accepted writes, no AI
  review as human review, no skipped-as-pass, no real provider calls in CI, and
  no private-context send without explicit policy and consent.

## Keep As Optional / Reclassify

The already-merged read-only MCP implementation and tests do not need an
immediate destructive revert because the current surface is limited:

- no arbitrary shell;
- no controlled writes;
- no accepted writes;
- no promotion tool;
- no hosted provider call;
- no secret or environment dump surface.

However, they must be reclassified as optional adapter work that happened ahead
of the fixed task order. They must not block CLI JSON contract, hosted provider
gateway, or workspace CLI-agent workflows.

## Revert Scope

No post-`v0.2.0` file currently requires immediate revert.

Do not reset `main` to `v0.2.0`. The useful service, schema, eval, safety, and
operator-note work should be preserved. The problem is direction drift in
documentation and milestone sequencing, not a corrupted runtime baseline.

## Needs Human Decision

One decision remains for maintainers:

- Keep the already-merged read-only MCP implementation as optional,
  ahead-of-plan adapter code, or later remove/rework it after CLI/provider
  stabilization.

This audit recommends keeping it for now as optional because it is constrained
and tested, but the next roadmap/milestone rewrite must make clear that MCP is
not the primary agent path and not a release blocker.

## Invariants Checked

- No runtime behavior changed by this audit document.
- No schema files changed by this audit document.
- No verifier adapter behavior changed by this audit document.
- No gate behavior changed by this audit document.
- No accepted-promotion policy changed by this audit document.
- No KB artifacts changed in `v0.2.0..main`.
- No public/private KB boundaries were weakened.
- No hosted provider implementation was added by this audit.
- No real provider call is required or run in CI by this audit.
- No automatic theorem proving, Lean semantic alignment, or production-ready
  claim was added.

## Follow-Up

Recommended next task: Phase R / Task R.2, branch
`roadmap-cli-agent-provider`.

R.2 should rewrite the roadmap, milestone, ADR, and plan documents listed
above toward CLI-first agent access with hosted provider work scheduled and MCP
optional. It should not change runtime behavior.
