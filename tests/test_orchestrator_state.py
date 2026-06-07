from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from cosheaf.agent.orchestrator_state import (
    OrchestratorRun,
    OrchestratorState,
    Plan,
    ReducerResult,
    StopCondition,
    TaskDAG,
    TaskNode,
    WorkerCall,
)
from cosheaf.agent.task import WorkerType

NOW = datetime(2026, 6, 7, 9, 30, tzinfo=UTC)
LATER = NOW + timedelta(minutes=5)


def _task_dag() -> TaskDAG:
    return TaskDAG(
        nodes=[
            TaskNode(
                node_id="node.plan.graph",
                worker_type=WorkerType.REASONER,
                description="Draft a bounded graph workflow plan.",
                input_artifacts=["definition.graph"],
                expected_outputs=["worker_notes"],
            ),
            TaskNode(
                node_id="node.verify.graph",
                worker_type=WorkerType.VERIFIER,
                description="Check the draft plan against local gates.",
                depends_on=["node.plan.graph"],
                expected_outputs=["gate_ready_yaml"],
            ),
        ]
    )


def _plan() -> Plan:
    return Plan(
        plan_id="plan.issue.graph.demo.0001",
        issue_id="issue.graph.demo",
        objective="Create a reviewable local-only graph workflow plan.",
        task_dag=_task_dag(),
    )


def test_orchestrator_state_values_are_explicit() -> None:
    assert {state.value for state in OrchestratorState} == {
        "created",
        "planned",
        "running",
        "waiting_for_worker",
        "waiting_for_gate",
        "waiting_for_review",
        "blocked",
        "completed",
        "failed",
        "abandoned",
    }


def test_orchestrator_run_serializes_deterministically() -> None:
    run = OrchestratorRun.create(
        run_id="run.issue.graph.demo.0001",
        issue_id="issue.graph.demo",
        now=NOW,
    ).transition(
        OrchestratorState.PLANNED,
        now=LATER,
        plan=_plan(),
        stop_conditions=[
            StopCondition(
                reason="gate_failed",
                description="Stop if any gate blocks the proposed output.",
            )
        ],
    )

    serialized = run.model_dump(mode="json")

    assert list(serialized) == [
        "schema_version",
        "run_id",
        "issue_id",
        "state",
        "plan",
        "worker_calls",
        "reducer_results",
        "stop_conditions",
        "created_at",
        "updated_at",
    ]
    assert serialized["schema_version"] == 1
    assert serialized["state"] == "planned"
    assert serialized["plan"]["task_dag"]["nodes"][0]["worker_type"] == "reasoner"
    assert serialized["stop_conditions"][0]["reason"] == "gate_failed"
    assert run.to_json() == run.to_json()
    assert OrchestratorRun.model_validate(serialized) == run


def test_valid_state_transition_sequence_is_pure_model_copy() -> None:
    run = OrchestratorRun.create(
        run_id="run.issue.graph.demo.0001",
        issue_id="issue.graph.demo",
        now=NOW,
    )
    planned = run.transition(OrchestratorState.PLANNED, now=LATER, plan=_plan())
    running = planned.transition(
        OrchestratorState.RUNNING,
        now=LATER + timedelta(minutes=1),
    )
    waiting = running.transition(
        OrchestratorState.WAITING_FOR_WORKER,
        now=LATER + timedelta(minutes=2),
        worker_calls=[
            WorkerCall(
                call_id="call.issue.graph.demo.reasoner",
                task_node_id="node.plan.graph",
                worker_type=WorkerType.REASONER,
                status="pending",
                command=["python", "-m", "fixture_worker"],
            )
        ],
    )
    completed = waiting.transition(
        OrchestratorState.COMPLETED,
        now=LATER + timedelta(minutes=3),
        reducer_results=[
            ReducerResult(
                reducer_id="reducer.issue.graph.demo.0001",
                status="accepted_for_review",
                summary="Reducer kept outputs as reviewable draft material.",
            )
        ],
    )

    assert run.state is OrchestratorState.CREATED
    assert planned.state is OrchestratorState.PLANNED
    assert running.state is OrchestratorState.RUNNING
    assert waiting.worker_calls[0].command == ["python", "-m", "fixture_worker"]
    assert completed.state is OrchestratorState.COMPLETED


def test_invalid_transition_fails() -> None:
    run = OrchestratorRun.create(
        run_id="run.issue.graph.demo.0001",
        issue_id="issue.graph.demo",
        now=NOW,
    )

    with pytest.raises(ValueError, match="invalid orchestrator transition"):
        run.transition(OrchestratorState.COMPLETED, now=LATER)


def test_terminal_state_cannot_transition() -> None:
    run = (
        OrchestratorRun.create(
            run_id="run.issue.graph.demo.0001",
            issue_id="issue.graph.demo",
            now=NOW,
        )
        .transition(OrchestratorState.ABANDONED, now=LATER)
    )

    with pytest.raises(ValueError, match="terminal"):
        run.transition(OrchestratorState.RUNNING, now=LATER + timedelta(minutes=1))


def test_transition_timestamp_cannot_move_backward() -> None:
    run = OrchestratorRun.create(
        run_id="run.issue.graph.demo.0001",
        issue_id="issue.graph.demo",
        now=NOW,
    ).transition(OrchestratorState.PLANNED, now=LATER, plan=_plan())

    with pytest.raises(ValueError, match="updated_at cannot move backward"):
        run.transition(OrchestratorState.RUNNING, now=NOW)


def test_task_dag_rejects_unknown_dependencies() -> None:
    with pytest.raises(ValidationError, match="unknown task node dependency"):
        TaskDAG(
            nodes=[
                TaskNode(
                    node_id="node.verify.graph",
                    worker_type=WorkerType.VERIFIER,
                    description="Check the draft output.",
                    depends_on=["node.missing"],
                )
            ]
        )


def test_task_dag_rejects_cycles() -> None:
    with pytest.raises(ValidationError, match="cycle"):
        TaskDAG(
            nodes=[
                TaskNode(
                    node_id="node.a",
                    worker_type=WorkerType.REASONER,
                    description="First cyclic node.",
                    depends_on=["node.b"],
                ),
                TaskNode(
                    node_id="node.b",
                    worker_type=WorkerType.VERIFIER,
                    description="Second cyclic node.",
                    depends_on=["node.a"],
                ),
            ]
        )


def test_models_reject_accepted_output_paths() -> None:
    with pytest.raises(ValidationError, match="accepted knowledge"):
        ReducerResult(
            reducer_id="reducer.issue.graph.demo.0001",
            status="unsafe",
            summary="This would bypass promotion policy.",
            output_paths=["kb/accepted/claims/claim.graph.demo.yaml"],
        )
