# ADR 0010: Orchestrator State Machine

## Status

Accepted

## Context

The existing agent harness can create task records, run explicit local worker
commands, validate worker output bundles, and build deterministic context
packs. The longplan next adds an orchestrator layer, but the project must keep
automation boundaries explicit before adding planner or runner behavior.

The risky alternative is to add orchestration behavior directly to the runtime
stub and let future changes infer state from files, logs, or implicit command
order. That would make review, replay, and policy enforcement harder.

The project invariants require:

- no hosted LLM calls by default;
- no automatic theorem proving or autoformalization;
- no automatic accepted promotion;
- no direct accepted artifact writes from workers or reducers;
- skipped verifier results are not passes;
- validation, gates, and human review remain separate from orchestration state.

## Decision

Define orchestration as a typed state-machine contract first.

The Phase 4.1 interface adds strict serializable DTOs under
`cosheaf.agent.orchestrator_state`:

- `OrchestratorRun`
- `Plan`
- `TaskDAG`
- `TaskNode`
- `WorkerCall`
- `ReducerResult`
- `StopCondition`

`OrchestratorRun` uses explicit states:

- `created`
- `planned`
- `running`
- `waiting_for_worker`
- `waiting_for_gate`
- `waiting_for_review`
- `blocked`
- `completed`
- `failed`
- `abandoned`

State transitions are validated by the model. Terminal states cannot
transition further. The task DAG model rejects duplicate nodes, unknown
dependencies, and cycles. Worker-call and reducer-result path fields must stay
repository-local, and reducer output paths must not target accepted knowledge.

The schema record lives at `schemas/orchestrator_run.schema.json`.

## Consequences

Future planner, reducer, and local-worker integration PRs can persist and
replay orchestration state without inventing a new record shape. Tests can
exercise state transitions and serialization without executing workers or
requiring network access.

The current PR adds no CLI command, no task execution path, no model provider,
no accepted-promotion path, and no gate semantic change. It is a contract for
future orchestration behavior, not runtime autonomy.

Reducers may summarize or reference proposed outputs for review, but accepted
knowledge still enters only through validation, gates, human review, and
explicit promotion.

## Non-Goals

- Do not implement a planner in this ADR task.
- Do not execute local workers from the state model.
- Do not add hosted LLM execution.
- Do not add provider configuration or API-key handling.
- Do not let orchestrator state write accepted artifacts directly.
- Do not run promotion from an orchestrator transition.
- Do not treat state transitions as gate passes or human review.
- Do not claim Lean/mathlib/CSLib verification.

## Follow-Up Requirements

The deterministic task-DAG planner, reducer behavior, local-worker integration,
dry-run workflow, provider-neutral model interface, and hosted provider adapter
must remain separate issues and PRs.

Any future CLI, runtime sidecar, schema, or gate behavior that uses these
models must update tests and `context/INTERFACE_REGISTRY.md` in the same PR.
