# TCS-Cosheaf Development Plan V9

Status: active accelerated line after the published `v0.4.0` Strategy
Planner + Research Task Graph closeout.

Target:

```text
v0.5.0 Operator MCP + Codex Application Layer
```

## Goal

Turn Cosheaf from a CLI-first research substrate into a safe
operator-facing tool layer that Codex-style agents can use through MCP or CLI
without gaining accepted-write, human-review, or promotion authority.

MCP is an adapter layer, not a new authority layer. Cosheaf remains the source
of truth and governance layer.

## Non-Negotiable Rules

1. One task = one issue = one branch = one PR.
2. Branch, PR, and issue names must not use `codex/`, `codex-`, or any
   agent-specific prefix.
3. Do not push directly to `main`.
4. No accepted KB writes through MCP.
5. No promotion through MCP in this line.
6. No mark-human-reviewed tool.
7. No provider-default, hosted LLM default, or API-key requirement.
8. No real network, API, or provider calls in default tests or CI.
9. MCP tools must call shared service-layer logic or existing safe
   CLI-equivalent code, not arbitrary shell.
10. If a command cannot run, report it truthfully. Skipped is not pass.
11. Public/private and readonly/writable boundaries must be tested with
    negative fixtures.
12. Runtime outputs stay under ignored `.cosheaf/` paths unless a task
    explicitly writes review-context exports.

## Baseline Verified At Start

The kickoff audit is recorded in
[`POST_V040_STATE_AUDIT.md`](POST_V040_STATE_AUDIT.md).

At the start of this line:

- package metadata and `cosheaf.__version__` report `0.4.0`;
- the annotated `v0.4.0` tag and GitHub release are published;
- release smoke from `@v0.4.0` passes;
- workspace-template active pins use `@v0.4.0`;
- public KB CI installs `@v0.4.0`;
- no open PRs or issues block the next line;
- strategy plans remain guidance only;
- research-run records remain provenance only;
- checked counterexample evidence remains review evidence only; and
- validation and gate success remain workflow checks, not human review or
  accepted status.

## Scope

### In Scope

- Optional MCP server package/entrypoint.
- Read-only MCP tools for workspace, validation, gate, memory, context,
  strategy, run evidence, and eval smoke.
- Controlled draft-write MCP tools that wrap existing controlled-write
  semantics.
- Codex operator runbook and MCP configuration examples.
- Workspace-template end-to-end demo proving Codex/MCP style usage.
- Public KB policy smoke proving MCP cannot bypass public review policy.
- Optional ChatGPT Skill/operator package as documentation, not runtime
  authority.

### Out Of Scope

- Production hosted multi-agent SaaS.
- Default hosted provider calls.
- Provider/MCP tool that sends private KB to external models by default.
- Accepted promotion through MCP.
- Human-review creation through MCP.
- Automatic proof, automatic Lean alignment, or automatic accepted refutation.
- Web UI.
- Multi-user permission system.
- Replacing GitHub PR review.

## Accelerated Phase Plan

### Phase A: Kickoff Audit And V9 Landing

Task A.1: `post-v040-v050-kickoff`

Repository: `tcs-cosheaf`.

Allowed changes:

- `docs/POST_V040_STATE_AUDIT.md`
- `docs/CODEX_DEVELOPMENT_PLAN_V9.md`
- `docs/ADR/0026-operator-mcp-codex-application-layer.md`
- `docs/ROADMAP.md`
- `context/CURRENT_MILESTONE.md`
- `context/PROJECT_STATE.md`

No runtime behavior, dependencies, schemas, version bump, or KB artifact writes.

### Phase B: Read-Only Operator MCP Server Core

Task B.1: `operator-mcp-readonly-core`

Goal: add the optional read-only MCP server core for Codex-style operators.

Required tools:

- `workspace_info`
- `validate`
- `gate`
- `gate_pr_checklist`
- `memory_cards`
- `memory_search`
- `context_build`
- `context_show`
- `strategy_plan`
- `strategy_show`
- `strategy_graph`
- `strategy_next`
- `run_show`
- `run_evidence_report`
- `eval_strategy_planner`
- `eval_research_run_loop`

Rules:

- Tools are read-only or runtime-output-only.
- No accepted KB writes, promotion, human-review creation, arbitrary shell, or
  hosted provider calls.
- Responses are structured JSON with stable error codes.
- Public-only mode must not leak private artifact IDs or text.
- Tests use in-process or fake fixtures only.

### Phase C: Controlled Draft-Write MCP Tools

Task C.1: `operator-mcp-controlled-writes`

Goal: add controlled MCP write tools that wrap existing safe write semantics
and explicitly refuse accepted, promotion, and human-review authority.

Controlled-write tools:

- `draft_artifact_create_or_update`
- `source_note_draft_create`
- `worker_bundle_validate`
- `worker_bundle_stage`
- `review_request_from_bundle`
- `checked_counterexample_evidence_validate`
- `checked_counterexample_evidence_stage`
- `failure_log_add_draft`
- `research_run_start`
- `research_run_append_command`
- `research_run_append_artifact`
- `research_run_append_output`
- `research_run_finalize`
- `research_run_export_review_dry_run`
- `research_run_export_review`
- `strategy_update_from_run`
- `strategy_export_review_dry_run`
- `strategy_export_review`

Forbidden tools:

- `write_accepted`
- `promote_artifact`
- `mark_human_reviewed`
- `edit_public_kb_by_default`
- `run_hosted_provider_by_default`
- `arbitrary_shell`

Rules:

- All writes must target draft, proposal, review-context, or runtime paths
  already allowed by Cosheaf policy.
- Absolute paths, parent traversal, accepted KB paths, readonly roots, and
  private-to-public leaks must be rejected.
- Writes must include authority notices in outputs.
- Dry-run variants must exist for review exports and staged writes where
  practical.
- Every controlled write needs a negative test.
- Promotion and human-review creation remain absent, including as dry-run
  tools.

### Phase D: Codex Operator Runbook And Workspace Demo

Task D.1: `codex-operator-runbook-and-workspace-demo`

Repositories:

- `tcs-cosheaf`
- `tcs-cosheaf-workspace-template`

Required demo flow:

1. Inspect workspace.
2. Validate.
3. Gate.
4. Memory search.
5. Build context.
6. Create a strategy plan.
7. Start a research run.
8. Record commands, artifacts, and outputs.
9. Stage draft/review-context output only.
10. Rerun validate and gate.
11. Finalize the run.
12. Export review context or dry-run export.

The demo must not require hosted providers, API keys, MCP when CLI fallback is
selected, or public KB write access. It must not promote artifacts, change
accepted KB, or commit runtime outputs.

### Phase E: Public KB Policy Smoke And Optional Operator Skill

Task E.1: `public-kb-operator-policy-smoke`

Repository: `tcs-kb-public`.

Policy smoke must cover:

- Operator/MCP output cannot be treated as human review.
- Draft/review-context material cannot be accepted without source metadata and
  human review.
- Public KB remains readonly from downstream workspaces.
- Checked evidence remains review evidence only.
- Strategy plans remain guidance only.
- Skipped remains not pass.

Task E.2: `optional-cosheaf-operator-skill-package`

Repository: `tcs-cosheaf`.

The skill/operator package is documentation only. It is not runtime authority,
not required for Codex CLI, and must not include secrets or private KB content.

### Phase F: v0.5.0 Release

Task F.1: `release-v050-readiness-and-rc`

Prepare `v0.5.0` only after MCP/operator surfaces, workspace demo, and public
KB policy smoke merge.

The release candidate must verify:

- read-only MCP tools exist and are tested;
- controlled-write MCP tools reject accepted, promotion, and human-review
  paths;
- workspace demo passes;
- public KB policy smoke passes;
- no default hosted provider, API-key, or network dependency was added;
- no accepted-write or promotion semantics changed;
- no MCP tool bypasses service-layer policy; and
- open issues/PRs are closed or intentionally deferred.

Task F.2: `release-v050-publication-closeout`

Publish annotated `v0.5.0`, publish the GitHub release, run release smoke from
`@v0.5.0`, update workspace-template and public KB pins, and close out
framework docs.

Downstream pins move only after tag/release smoke succeeds. Network rows are
reported explicitly, skipped rows remain skipped, runtime outputs are not
committed, and no KB artifacts are promoted as part of release mechanics.

## Definition Of Done

`v0.5.0` is done when:

- read-only operator MCP tools cover workspace, validate, gate, memory,
  context, strategy, run evidence, and eval smoke;
- controlled-write MCP tools cover only draft/proposal/review/runtime writes;
- MCP refuses accepted writes, promotion, human-review creation, arbitrary
  shell, default hosted provider calls, private-to-public leaks, readonly-root
  writes, absolute paths, and parent traversal;
- CLI fallback remains documented and usable;
- workspace-template has an operator demo;
- public KB policy explicitly covers operator/MCP outputs;
- optional operator skill docs exist as a runbook only;
- release notes say the layer is optional and bounded; and
- workspace-template and public KB active pins align to the published
  `v0.5.0` tag after release smoke.

## Stop Rules

Stop and ask for a maintainer decision if a task would require:

- default real provider calls;
- embedding GPT, Claude, or another hosted model as default runtime;
- accepted writes through MCP;
- promotion through MCP;
- human-review creation through MCP;
- changing accepted-promotion semantics;
- treating MCP/operator output as proof, checked evidence, verifier pass, gate
  pass, human review, accepted status, or promotion authority;
- private-to-public content copying;
- broad public KB content growth unrelated to operator policy; or
- weakening validation, gate, security, skipped-not-pass, or private-leakage
  tests.
