"""Pure orchestrator state-machine DTOs.

These models define the replayable state contract for future orchestration.
They do not execute workers, call hosted services, write files, or merge
accepted knowledge.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cosheaf.agent.task import WorkerType
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path


class OrchestratorState(StrEnum):
    """Explicit lifecycle states for one orchestrator run."""

    CREATED = "created"
    PLANNED = "planned"
    RUNNING = "running"
    WAITING_FOR_WORKER = "waiting_for_worker"
    WAITING_FOR_GATE = "waiting_for_gate"
    WAITING_FOR_REVIEW = "waiting_for_review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


TERMINAL_STATES = frozenset(
    {
        OrchestratorState.COMPLETED,
        OrchestratorState.FAILED,
        OrchestratorState.ABANDONED,
    }
)

ALLOWED_TRANSITIONS: dict[OrchestratorState, frozenset[OrchestratorState]] = {
    OrchestratorState.CREATED: frozenset(
        {
            OrchestratorState.PLANNED,
            OrchestratorState.BLOCKED,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.PLANNED: frozenset(
        {
            OrchestratorState.RUNNING,
            OrchestratorState.WAITING_FOR_REVIEW,
            OrchestratorState.BLOCKED,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.RUNNING: frozenset(
        {
            OrchestratorState.WAITING_FOR_WORKER,
            OrchestratorState.WAITING_FOR_GATE,
            OrchestratorState.WAITING_FOR_REVIEW,
            OrchestratorState.BLOCKED,
            OrchestratorState.COMPLETED,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.WAITING_FOR_WORKER: frozenset(
        {
            OrchestratorState.RUNNING,
            OrchestratorState.WAITING_FOR_GATE,
            OrchestratorState.WAITING_FOR_REVIEW,
            OrchestratorState.BLOCKED,
            OrchestratorState.COMPLETED,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.WAITING_FOR_GATE: frozenset(
        {
            OrchestratorState.RUNNING,
            OrchestratorState.WAITING_FOR_REVIEW,
            OrchestratorState.BLOCKED,
            OrchestratorState.COMPLETED,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.WAITING_FOR_REVIEW: frozenset(
        {
            OrchestratorState.RUNNING,
            OrchestratorState.BLOCKED,
            OrchestratorState.COMPLETED,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.BLOCKED: frozenset(
        {
            OrchestratorState.PLANNED,
            OrchestratorState.RUNNING,
            OrchestratorState.FAILED,
            OrchestratorState.ABANDONED,
        }
    ),
    OrchestratorState.COMPLETED: frozenset(),
    OrchestratorState.FAILED: frozenset(),
    OrchestratorState.ABANDONED: frozenset(),
}


class OrchestratorStateModel(BaseModel):
    """Shared strict base for orchestrator DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic machine-readable mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON for this model."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class TaskNode(OrchestratorStateModel):
    """One auditable task node in a future orchestrator DAG."""

    node_id: str
    worker_type: WorkerType
    description: str
    depends_on: list[str] = Field(default_factory=list)
    input_artifacts: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)

    @field_validator("node_id")
    @classmethod
    def _validate_node_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="description")

    @field_validator("depends_on")
    @classmethod
    def _validate_depends_on(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            validate_artifact_id(value.strip()) for value in values
        )

    @field_validator("input_artifacts")
    @classmethod
    def _validate_input_artifacts(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            validate_artifact_id(value.strip()) for value in values
        )

    @field_validator("expected_outputs")
    @classmethod
    def _normalize_expected_outputs(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_non_empty_text(value, field_name="expected output")
            for value in values
        )


class TaskDAG(OrchestratorStateModel):
    """Deterministic task DAG for one proposed orchestrator plan."""

    nodes: list[TaskNode] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_graph(self) -> TaskDAG:
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("task DAG node IDs must be unique")

        known = set(node_ids)
        for node in self.nodes:
            for dependency in node.depends_on:
                if dependency not in known:
                    raise ValueError(
                        "unknown task node dependency "
                        f"{dependency!r} for node {node.node_id!r}"
                    )

        _reject_cycles(self.nodes)
        return self


class Plan(OrchestratorStateModel):
    """Auditable plan attached to an orchestrator run."""

    plan_id: str
    issue_id: str
    objective: str
    task_dag: TaskDAG = Field(default_factory=TaskDAG)
    notes: str = ""

    @field_validator("plan_id", "issue_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("objective")
    @classmethod
    def _validate_objective(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="objective")

    @field_validator("notes")
    @classmethod
    def _strip_notes(cls, value: str) -> str:
        return value.strip()


class WorkerCall(OrchestratorStateModel):
    """Recorded intent or result metadata for one worker invocation."""

    call_id: str
    task_node_id: str
    worker_type: WorkerType
    status: str
    command: list[str] = Field(default_factory=list)
    cwd: str = "."
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exit_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    bundle_path: str | None = None
    notes: str = ""

    @field_validator("call_id", "task_node_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="worker status")

    @field_validator("command")
    @classmethod
    def _normalize_command(cls, values: list[str]) -> list[str]:
        return [
            _validate_non_empty_text(value, field_name="command argument")
            for value in values
        ]

    @field_validator("cwd", "stdout_path", "stderr_path", "bundle_path")
    @classmethod
    def _validate_paths(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_repo_local_path(value, allow_dot=True)

    @field_validator("started_at", "completed_at")
    @classmethod
    def _validate_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _normalize_timestamp(value)

    @field_validator("notes")
    @classmethod
    def _strip_notes(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def _validate_time_order(self) -> WorkerCall:
        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at must be greater than or equal to started_at")
        return self


class ReducerResult(OrchestratorStateModel):
    """Reducer decision metadata without accepted-promotion authority."""

    reducer_id: str
    status: str
    summary: str
    output_paths: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("reducer_id")
    @classmethod
    def _validate_reducer_id(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("status", "summary")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="reducer text")

    @field_validator("output_paths")
    @classmethod
    def _validate_output_paths(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_repo_local_path(value) for value in values
        )

    @field_validator("warnings")
    @classmethod
    def _normalize_warnings(cls, values: list[str]) -> list[str]:
        return _dedupe_preserving_order(
            _validate_non_empty_text(value, field_name="warning") for value in values
        )


class StopCondition(OrchestratorStateModel):
    """Auditable reason an orchestrator run should stop or pause."""

    reason: str
    description: str

    @field_validator("reason", "description")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        return _validate_non_empty_text(value, field_name="stop condition text")


class OrchestratorRun(OrchestratorStateModel):
    """Serializable state record for one future orchestrator run."""

    schema_version: Literal[1] = 1
    run_id: str
    issue_id: str
    state: OrchestratorState
    plan: Plan | None = None
    worker_calls: list[WorkerCall] = Field(default_factory=list)
    reducer_results: list[ReducerResult] = Field(default_factory=list)
    stop_conditions: list[StopCondition] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        issue_id: str,
        now: datetime | None = None,
    ) -> OrchestratorRun:
        """Create a run record in the initial created state."""
        timestamp = _normalize_timestamp(now or _utc_now())
        return cls(
            run_id=run_id,
            issue_id=issue_id,
            state=OrchestratorState.CREATED,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(
        self,
        new_state: OrchestratorState | str,
        *,
        now: datetime | None = None,
        plan: Plan | None = None,
        worker_calls: list[WorkerCall] | None = None,
        reducer_results: list[ReducerResult] | None = None,
        stop_conditions: list[StopCondition] | None = None,
    ) -> OrchestratorRun:
        """Return a validated copy in ``new_state``.

        This method mutates no files and performs no worker dispatch. It only
        enforces the local state transition graph.
        """
        resolved_state = OrchestratorState(new_state)
        if self.state in TERMINAL_STATES:
            raise ValueError(
                f"terminal orchestrator state {self.state.value!r} cannot transition"
            )
        if resolved_state not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(
                "invalid orchestrator transition "
                f"{self.state.value!r} -> {resolved_state.value!r}"
            )

        timestamp = _normalize_timestamp(now or _utc_now())
        if timestamp < self.updated_at:
            raise ValueError("updated_at cannot move backward across transitions")
        data = self.model_dump(mode="python")
        data.update(
            {
                "state": resolved_state,
                "updated_at": timestamp,
            }
        )
        if plan is not None:
            data["plan"] = plan
        if worker_calls is not None:
            data["worker_calls"] = worker_calls
        if reducer_results is not None:
            data["reducer_results"] = reducer_results
        if stop_conditions is not None:
            data["stop_conditions"] = stop_conditions
        return OrchestratorRun.model_validate(data)

    @field_validator("run_id", "issue_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_timestamps(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value)

    @field_validator("updated_at")
    @classmethod
    def _validate_update_order(cls, value: datetime, info: Any) -> datetime:
        created_at = info.data.get("created_at")
        if isinstance(created_at, datetime) and value < created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")
        return value


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _validate_non_empty_text(value: str, *, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must be non-empty")
    return stripped


def _validate_repo_local_path(value: str, *, allow_dot: bool = False) -> str:
    normalized = normalize_repo_path(value)
    is_absolute = Path(value).is_absolute() or PureWindowsPath(value).is_absolute()
    if (
        not normalized
        or is_absolute
        or normalized == ".."
        or normalized.startswith("../")
        or (normalized == "." and not allow_dot)
    ):
        raise ValueError("path must be repository-local")

    parts = PurePosixPath(normalized).parts
    if parts and parts[0] == "kb" and "accepted" in parts:
        raise ValueError(
            "orchestrator state must not reference direct accepted knowledge output"
        )
    return normalized


def _dedupe_preserving_order(values: Any) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _reject_cycles(nodes: list[TaskNode]) -> None:
    by_id = {node.node_id: node for node in nodes}
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in permanent:
            return
        if node_id in temporary:
            raise ValueError("task DAG must not contain a cycle")
        temporary.add(node_id)
        for dependency in by_id[node_id].depends_on:
            visit(dependency)
        temporary.remove(node_id)
        permanent.add(node_id)

    for node in nodes:
        visit(node.node_id)
