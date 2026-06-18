# Architecture Refactor Audit

Date: 2026-06-19

Issue: #492

Branch: `arch-dependency-audit`

Scope: Longplan A0.1. This audit changes documentation only. It does not change
runtime behavior, command names, schemas, accepted-promotion semantics, review
policy, verifier policy, or gate behavior.

## Baseline Inspected

- Package version: `1.0.0`.
- Main CLI entrypoint: `cosheaf/cli.py`.
- Additional domain CLI modules mounted by `cosheaf/cli.py`: `actions`,
  `checkers`, `gap_cli`, `librarian`, `orchestrator_fsm`, and `workflow`.
- Current service boundary: `cosheaf.services` plus
  `cosheaf.services.models`, `cosheaf.services.context_policy`, and
  `cosheaf.services.model_calls`.
- Stable public interface inventory: `context/INTERFACE_REGISTRY.md` and
  `cosheaf interface list --json`.

## 1. CLI Commands Calling Low-Level Modules Directly

Most commands still construct `RepoContext` in the CLI layer. That is acceptable
for the CLI, but a future server should not need to import Typer command
functions or private CLI helpers.

The following command groups still have direct CLI-to-domain or CLI-to-low-level
calls instead of a reusable application facade:

| Command group | Current low-level or domain path | Refactor risk |
| --- | --- | --- |
| `artifact move-status`, `artifact promote` | private helpers in `cosheaf/cli.py` call storage, gates, lifecycle path helpers, and YAML writers directly | High, because this is accepted-promotion authority |
| `promotion readiness` | calls `cosheaf.gates.promotion_readiness` directly | Medium, read-only but policy-sensitive |
| `index rebuild` | calls `cosheaf.storage.index.rebuild_index` directly | Low |
| `graph show` | calls storage loader plus graph builder directly | Low |
| `ingest convert` | calls ingestion adapter and repo path policy directly | Medium, source-boundary-sensitive |
| `research-run ...` | calls research-run helpers directly from `cosheaf/cli.py` | Medium |
| `strategy ...` | calls strategy planner/storage helpers directly | Medium |
| `benchmark ...`, `compare ...`, `report ...` | calls the corresponding domain modules directly | Low to medium, sidecar/report-only |
| `memory graph ...` | calls memory graph helpers directly | Low |
| `operator session ...`, `operator handoff ...` | calls operator-session model/storage/security helpers directly | Medium, leak/authority scanner-sensitive |
| `research-loop ...` | calls `cosheaf.research.loop` directly | Medium, authority/policy-sensitive |
| `campaign ...` | calls `cosheaf.campaigns.storage` directly | Medium, authority/policy-sensitive |
| `counterexample evidence ...` | calls verifier evidence helpers directly | Medium |
| `mcp serve` | constructs the MCP server directly | CLI/adapter-only |

Domain CLI modules already separated from `cosheaf/cli.py` still mostly call
their domain modules directly. Examples: `cosheaf.workflow.cli`,
`cosheaf.checkers.cli`, `cosheaf.gap_cli`, `cosheaf.actions.cli`,
`cosheaf.librarian.cli`, and `cosheaf.orchestrator_fsm.cli`.

## 2. Use Cases Already Behind `cosheaf.services`

The existing service layer covers several important operator-facing use cases:

- Workspace inspection: `WorkspaceService.info`.
- Repository and artifact validation: `ValidationService`.
- Gatekeeper execution: `GateService`.
- Artifact-card and memory search: `MemorySearchService`.
- Context build/show: `ContextPackService`.
- Deterministic orchestrator planning: `OrchestratorPlanService`.
- Task create/list/complete/run: `TaskService`.
- Worker bundle validation/reduction/submit: `BundleValidationService`.
- Controlled draft artifact/source-note/review-request/failure-memory writes:
  `DraftWriteService`.
- Provider-send context policy preview: `ContextSendPolicyService`.
- Provider gateway calls: `ModelCallService`.

These services preserve existing boundaries: they do not grant accepted-write,
human-review, verifier-pass, gate-pass, or promotion authority.

## 3. Missing Reusable App-Level Entrypoints

The repository has services, but no stable `cosheaf.app` namespace. Missing app
entrypoints for Longplan A1 are:

- request/result wrappers for workspace info, validation, gate run, context
  build/show, memory search, draft writes, review request writes, bundle submit,
  bundle reduce, and promotion readiness;
- a read-only app wrapper for `index rebuild` and `graph show`;
- a lifecycle app wrapper for non-accepted `artifact move-status`;
- a carefully bounded promotion app wrapper, if promotion is exposed at all;
- app wrappers around research-run, workflow, research-loop, campaign,
  benchmark, compare, and static-report domain surfaces;
- a unified error conversion path for domain-specific expected errors outside
  the current service exceptions; and
- a stable app import surface that future server and website code can call
  without importing `cosheaf.cli`.

## 4. Logic Trapped In `cosheaf/cli.py`

`cosheaf/cli.py` is currently both public CLI and a mixed orchestration module.
The main trapped logic is:

- Typer registration for 30+ root command groups.
- `artifact move-status` and `artifact promote` lifecycle implementation,
  including promotion validation, gatekeeper blockers, verifier blockers,
  review checks, dependency checks, public source metadata checks, and
  deterministic accepted writes.
- JSON conversion helpers for validation, gate, context, provider, and
  orchestrator output.
- Provider real-run consent/config/preflight parsing and provider log payload
  conversion.
- Operator-session reference validation helpers.
- Context payload counting/private-context detection helpers.
- Human rendering and exit-code handling mixed with result construction.

The promotion helpers are intentionally conservative and should not be moved
casually. They are the highest-risk app-boundary target.

## 5. Stable JSON DTOs Already Exist

`cosheaf.services.models` already provides a useful DTO base:

- `AgentAccessModel`
- `ErrorResult`
- `WorkspaceInfoResult`
- `ValidateResult`
- `GateRunResult`
- `MemorySearchRequest` / `MemorySearchResult`
- `ContextBuildRequest` / `ContextBuildResult`
- `WorkerBundleSubmitRequest` / `WorkerBundleSubmitResult`
- `DraftArtifactWriteRequest` / `DraftArtifactWriteResult`
- `ProviderContextPreview` / `ProviderContextPreviewItem`
- `ModelCallRequest` / `ModelCallResult`
- `AGENT_ACCESS_STABLE_ERROR_CODES`
- `AGENT_ACCESS_SCHEMA_MODELS`

Known DTO gaps for Longplan A1.2:

- no `WorkspaceInfoRequest`;
- no `ValidateRequest`;
- no `GateRunRequest`;
- no `ReviewRequestWriteRequest` / `ReviewRequestWriteResult`;
- no app-level `DraftWriteRequest` that covers source-note and review-request
  writes, not just artifact writes;
- no app-level `PromotionReadinessRequest` / `PromotionReadinessResult`; and
- no common `AppResult` union or app error adapter for domain-specific errors.

## 6. Stable Commands Listed In The Interface Registry

`cosheaf interface list --json` reports these stable v1.0 public command
surfaces:

- `workspace`
- `validate`
- `gate`
- `index`
- `context`
- `artifact`
- `promotion`
- `workflow`
- `checker`
- `gap`
- `research-loop`
- `research-run`
- `campaign`
- `memory`
- `benchmark`
- `compare`
- `report`
- `operator session`
- `provider`
- `mcp`

Compatibility aliases:

- `cosheaf gate` -> `cosheaf gate run`
- `cosheaf run` -> `cosheaf research-run`

Optional/default-off adapter surfaces:

- `provider real-run`
- `mcp`
- external verifier execution

## 7. Modules Unsafe For Future Server To Call Directly

Future `cosheaf.server` code should call `cosheaf.app`, not these surfaces
directly:

- `cosheaf.cli`: Typer parsing, terminal rendering, `raise typer.Exit`, and
  private helpers are CLI concerns.
- `cosheaf.mcp.server`: adapter protocol surface, not app logic.
- `cosheaf.actions.builtins` and `cosheaf.actions.workers`: may execute local
  commands through the action registry; server use needs explicit policy.
- `cosheaf.agent.local_runner`: local command execution; server use needs a
  separate execution policy.
- `cosheaf.agent.providers` and `cosheaf.services.model_calls`: network-capable
  only when explicitly configured and consented.
- `cosheaf.storage.writer`: low-level deterministic YAML writes; app services
  should own write policy.
- `cosheaf.gates.gatekeeper.run_gatekeeper`: safe as an implementation detail,
  but app callers need stable request/result DTOs and error conversion.
- `cosheaf.gates.promotion_readiness` and promotion helpers: policy-sensitive;
  expose only read-only readiness first.

## 8. Behavior That Must Remain CLI-Only

The following behavior should not become generic app/server authority:

- terminal rendering and Rich formatting;
- Typer option parsing and `typer.Exit` control flow;
- debug tracebacks controlled by CLI flags;
- `mcp serve --stdio`;
- direct local command execution through `task run` or action workers;
- provider `real-run` network sends without explicit consent/configuration;
- interactive or environment-specific credential discovery; and
- any behavior that would mark human review, accepted status, verifier pass,
  gate pass, or promotion authority from AI/operator output.

## 9. Tests Protecting Authority Boundaries

Important existing test areas:

- Promotion and lifecycle: `tests/test_artifact_promotion_cli.py`,
  `tests/test_artifact_lifecycle_cli.py`,
  `tests/test_promotion_readiness_cli.py`,
  `tests/test_promotion_gate_verifier_regressions.py`, and
  `tests/security/test_agent_access_security_regression.py`.
- Controlled writes and human-review spoofing:
  `tests/test_cli_controlled_draft_writes.py`,
  `tests/test_services.py`, `tests/test_worker_bundle_v2.py`, and
  `tests/test_task_model.py`.
- Skipped-not-pass semantics:
  `tests/test_verification_result.py`,
  `tests/test_verifier_evidence_record.py`,
  `tests/test_counterexample_evidence_record.py`, SAT/SMT/Lean adapter tests,
  and eval tests under `tests/evals/`.
- Provider, private context, and network boundaries:
  `tests/test_context_send_policy.py`, `tests/test_provider_gateway.py`,
  `tests/test_orchestrator_hosted_runner.py`, and security tests under
  `tests/security/`.
- Workflow/research-loop/campaign authority scanners:
  `tests/test_workflow.py`, `tests/test_workflow_handoff.py`,
  `tests/test_research_loop.py`, `tests/test_campaigns.py`, and related eval
  tests.
- Public/private and readonly root policy:
  `tests/test_workspace_config.py`, `tests/test_cross_repo_integration.py`,
  and `tests/test_workspace_template_smoke.py`.
- DTO stability: `tests/test_agent_access_models.py`.

These tests should be run unchanged during A1/A2. New app facade tests should
compare app results with existing services or CLI-visible DTOs.

## 10. Safe Refactors For The Next PR

The safest next PR is Longplan A1.1:

1. Add `cosheaf/app/` as a thin facade over existing services.
2. Reuse existing services and DTOs; do not move promotion write logic yet.
3. Add compatibility tests that call the app facade and existing services on
   the same fixtures.
4. Expose read/check use cases first: workspace info, validation, gate run,
   context build/show, memory cards/search, bundle submit/reduce, controlled
   draft writes, and review-request writes.
5. Document that CLI behavior remains authoritative and unchanged.

Safe later CLI slimming target: `context`. It is small, service-backed, and
already emits stable JSON. `memory` is also a good candidate after `context`.

Do not start with `artifact promote`, provider `real-run`, local action/task
execution, MCP serving, campaign, or research-loop writes. Those are policy-
heavy and need app-level request/result models plus focused negative tests.

## Risks

- Moving promotion code too early could weaken accepted-artifact policy.
- Introducing parallel DTOs could create two inconsistent JSON contracts.
- Moving CLI groups without smoke tests could silently change command names,
  exit codes, or JSON fields.
- Treating domain runtime records as app authority could overclaim review,
  verifier, gate, or promotion status.
- Server-ready wrappers around local command execution or provider real-run
  could accidentally widen network or shell authority.

## Verification Required For This Audit PR

Run the required Longplan A0.1 commands before merging:

```bash
make lint
make typecheck
make test
make validate
make gate
git diff --check
```
