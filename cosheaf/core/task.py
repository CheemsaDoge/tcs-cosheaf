"""Core task record models used by the local agent harness."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path


class WorkerType(StrEnum):
    """Protocol-level worker roles supported by the agent harness."""

    REASONER = "reasoner"
    VERIFIER = "verifier"
    COUNTEREXAMPLER = "counterexampleer"
    CONSTRUCTION_SEARCHER = "construction_searcher"
    FORMALIZER = "formalizer"
    LITERATURE_SCOUT = "literature_scout"
    ORCHESTRATOR = "orchestrator"


class TaskStatus(StrEnum):
    """Minimal lifecycle states for an agent task."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


BudgetValue = bool | int | float | str

DEFAULT_EXPECTED_OUTPUTS = (
    "gate_ready_yaml",
    "worker_notes",
)


class AgentTask(BaseModel):
    """Minimal agent harness task record.

    Worker types are only a protocol contract. Creating or completing a task
    never invokes an LLM, external service, or concrete worker runtime.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    task_id: str
    issue_id: str
    worker_type: WorkerType
    status: TaskStatus
    input_context: list[str] = Field(default_factory=list)
    budget: dict[str, BudgetValue] = Field(default_factory=dict)
    expected_outputs: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @property
    def id(self) -> str:
        """Return the task identifier for loader-wide ID handling."""
        return self.task_id

    @classmethod
    def create(
        cls,
        *,
        issue_id: str,
        worker_type: WorkerType | str,
        now: datetime | None = None,
        task_id: str | None = None,
        input_context: list[str] | None = None,
        budget: dict[str, BudgetValue] | None = None,
        expected_outputs: list[str] | None = None,
    ) -> AgentTask:
        """Create an open task with a deterministic default task ID."""
        worker = WorkerType(worker_type)
        timestamp = _normalize_timestamp(now or _utc_now())
        resolved_task_id = task_id or create_task_id(issue_id, worker)
        return cls(
            task_id=resolved_task_id,
            issue_id=issue_id,
            worker_type=worker,
            status=TaskStatus.OPEN,
            input_context=input_context if input_context is not None else [],
            budget=budget if budget is not None else {},
            expected_outputs=(
                expected_outputs
                if expected_outputs is not None
                else list(DEFAULT_EXPECTED_OUTPUTS)
            ),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def mark_completed(self, *, now: datetime | None = None) -> AgentTask:
        """Return a completed copy of this task."""
        updated_at = _normalize_timestamp(now or _utc_now())
        if updated_at < self.created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")
        return self.model_copy(
            update={
                "status": TaskStatus.COMPLETED,
                "updated_at": updated_at,
            }
        )

    @field_validator("task_id", "issue_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value)

    @field_validator("input_context")
    @classmethod
    def _normalize_input_context(cls, values: list[str]) -> list[str]:
        return [normalize_repo_path(value) for value in values]

    @field_validator("created_at", "updated_at")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        return _normalize_timestamp(value)

    @field_validator("updated_at")
    @classmethod
    def _validate_update_order(cls, value: datetime, info: Any) -> datetime:
        created_at = info.data.get("created_at")
        if isinstance(created_at, datetime) and value < created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")
        return value


def create_task_id(issue_id: str, worker_type: WorkerType | str) -> str:
    """Return the deterministic default task ID for an issue and worker role."""
    validated_issue_id = validate_artifact_id(issue_id)
    worker = WorkerType(worker_type)
    worker_slug = worker.value.replace("_", "-")
    return validate_artifact_id(f"task.{validated_issue_id}.{worker_slug}")


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)
