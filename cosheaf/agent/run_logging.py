"""Structured local run logging helpers.

Run logs are audit metadata only. They do not store stdout/stderr contents,
hidden reasoning, verifier authority, gate authority, review authority, or
accepted-promotion evidence.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cosheaf.agent.orchestrator_state import OrchestratorRun, WorkerCall
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path

SECRET_KEYWORDS = frozenset(
    {
        "api-key",
        "apikey",
        "auth",
        "authorization",
        "bearer",
        "client-secret",
        "credential",
        "key",
        "password",
        "secret",
        "token",
    }
)
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(sk-[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9_]+|xox[baprs]-[A-Za-z0-9-]+)"
)
REDACTED = "<redacted>"


class RunLogModel(BaseModel):
    """Shared strict base for run-log DTOs."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Return deterministic JSON output."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2) + "\n"


class RunLogWorkerCall(RunLogModel):
    """Sanitized worker-call metadata for structured logs."""

    call_id: str
    task_node_id: str
    worker_role: str
    status: str
    command: list[str] = Field(default_factory=list)
    cwd: str = "."
    exit_code: int | None = None
    bundle_path: str | None = None

    @field_validator("call_id", "task_node_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("worker_role", "status")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("run-log text field must be non-empty")
        return stripped

    @field_validator("command")
    @classmethod
    def _validate_command(cls, values: list[str]) -> list[str]:
        return [str(value) for value in values]

    @field_validator("cwd", "bundle_path")
    @classmethod
    def _validate_repo_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _repo_local_or_dot(value)


class StructuredRunLog(RunLogModel):
    """Machine-readable local run log for observability."""

    schema_version: Literal[1] = 1
    run_id: str
    issue_id: str
    plan_id: str | None = None
    task_ids: list[str] = Field(default_factory=list)
    worker_roles: list[str] = Field(default_factory=list)
    retrieved_artifacts: list[str] = Field(default_factory=list)
    full_artifact_pulls: list[str] = Field(default_factory=list)
    verifier_results: list[str] = Field(default_factory=list)
    gate_results: list[str] = Field(default_factory=list)
    output_bundle_paths: list[str] = Field(default_factory=list)
    start_time: datetime
    end_time: datetime
    status: str
    stop_reason: str
    worker_calls: list[RunLogWorkerCall] = Field(default_factory=list)

    @field_validator("run_id", "issue_id")
    @classmethod
    def _validate_ids(cls, value: str) -> str:
        return validate_artifact_id(value.strip())

    @field_validator("plan_id")
    @classmethod
    def _validate_plan_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_artifact_id(value.strip())

    @field_validator("task_ids", "retrieved_artifacts")
    @classmethod
    def _validate_artifact_id_list(cls, values: list[str]) -> list[str]:
        return _dedupe(validate_artifact_id(value.strip()) for value in values)

    @field_validator(
        "full_artifact_pulls",
        "verifier_results",
        "gate_results",
        "output_bundle_paths",
    )
    @classmethod
    def _validate_path_list(cls, values: list[str]) -> list[str]:
        return _dedupe(_repo_local_or_dot(value) for value in values)

    @field_validator("worker_roles")
    @classmethod
    def _validate_roles(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]

    @field_validator("status", "stop_reason")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("run-log text field must be non-empty")
        return stripped


def write_orchestrator_run_log(
    path: Path,
    run: OrchestratorRun,
) -> StructuredRunLog:
    """Write a deterministic sanitized run log beside an orchestrator run."""
    log = structured_log_from_orchestrator_run(run)
    path.write_text(log.to_json(), encoding="utf-8", newline="\n")
    return log


def structured_log_from_orchestrator_run(
    run: OrchestratorRun,
) -> StructuredRunLog:
    """Create a sanitized structured log from an orchestrator run DTO."""
    plan = run.plan
    nodes = list(plan.task_dag.nodes) if plan is not None else []
    worker_calls = [_worker_call_log(call) for call in run.worker_calls]
    output_bundle_paths = [
        call.bundle_path for call in run.worker_calls if call.bundle_path is not None
    ]
    retrieved_artifacts: list[str] = []
    for node in nodes:
        retrieved_artifacts.extend(node.input_artifacts)
    stop_reason = (
        run.stop_conditions[0].reason
        if run.stop_conditions
        else "completed"
        if run.state.value == "completed"
        else run.state.value
    )
    return StructuredRunLog(
        run_id=run.run_id,
        issue_id=run.issue_id,
        plan_id=plan.plan_id if plan is not None else None,
        task_ids=[f"task.{node.node_id}" for node in nodes],
        worker_roles=[node.worker_type.value for node in nodes],
        retrieved_artifacts=retrieved_artifacts,
        full_artifact_pulls=[],
        verifier_results=[],
        gate_results=[],
        output_bundle_paths=output_bundle_paths,
        start_time=run.created_at,
        end_time=run.updated_at,
        status=run.state.value,
        stop_reason=stop_reason,
        worker_calls=worker_calls,
    )


def redact_command(command: list[str]) -> list[str]:
    """Return command argv with common secret shapes and secret flags redacted."""
    redacted: list[str] = []
    redact_next = False
    for argument in command:
        if redact_next:
            redacted.append(REDACTED)
            redact_next = False
            continue

        key, separator, value = argument.partition("=")
        if separator and _contains_secret_keyword(key):
            redacted.append(f"{key}={REDACTED}")
            continue

        if _is_secret_flag(argument):
            redacted.append(argument)
            redact_next = True
            continue

        redacted.append(SECRET_VALUE_PATTERN.sub(REDACTED, argument))
    return redacted


def _worker_call_log(call: WorkerCall) -> RunLogWorkerCall:
    return RunLogWorkerCall(
        call_id=call.call_id,
        task_node_id=call.task_node_id,
        worker_role=call.worker_type.value,
        status=call.status,
        command=redact_command(list(call.command)),
        cwd=call.cwd,
        exit_code=call.exit_code,
        bundle_path=call.bundle_path,
    )


def _is_secret_flag(argument: str) -> bool:
    normalized = argument.strip().lstrip("-").replace("_", "-").lower()
    return normalized in SECRET_KEYWORDS or _contains_secret_keyword(normalized)


def _contains_secret_keyword(value: str) -> bool:
    normalized = value.strip().lstrip("-").replace("_", "-").lower()
    return any(keyword in normalized for keyword in SECRET_KEYWORDS)


def _repo_local_or_dot(value: str) -> str:
    if value == ".":
        return value
    normalized = normalize_repo_path(value)
    if (
        not normalized
        or normalized == ".."
        or normalized.startswith("../")
        or Path(value).is_absolute()
    ):
        raise ValueError("run-log path must be repository-local")
    return normalized


def _dedupe(values: Any) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
