"""Local-only orchestrator runner.

This module wires the deterministic planner to the existing local command
runner. It does not call hosted model providers, perform network access, merge
worker output, request human review, or promote accepted knowledge.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cosheaf.agent.local_runner import (
    LocalWorkerRunConfig,
    LocalWorkerRunError,
    LocalWorkerRunner,
)
from cosheaf.agent.orchestrator_planner import (
    OrchestratorPlannerError,
    plan_for_issue,
)
from cosheaf.agent.orchestrator_state import (
    OrchestratorRun,
    OrchestratorState,
    StopCondition,
    TaskNode,
    WorkerCall,
)
from cosheaf.agent.orchestrator_stub import OrchestratorStub, TaskHarnessError
from cosheaf.agent.task import AgentTask
from cosheaf.agent.worker_bundle_v2 import (
    WorkerBundleV2Error,
    reduce_worker_bundle_v2,
)
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import repo_relative_posix
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic


class OrchestratorLocalRunError(ValueError):
    """Raised for expected local orchestrator run failures."""


@dataclass(frozen=True)
class OrchestratorLocalRunConfig:
    """Configuration for one deterministic local-only orchestrator run."""

    issue_id: str
    timeout_seconds: int = 60
    worker_command: Sequence[str] | None = None
    proposal_path: str | Path | None = None
    run_id: str | None = None
    now: datetime | None = None

    def __post_init__(self) -> None:
        validate_artifact_id(self.issue_id)
        if self.timeout_seconds <= 0:
            raise OrchestratorLocalRunError("timeout_seconds must be positive")
        if self.run_id is not None:
            validate_artifact_id(self.run_id)
        if self.worker_command is not None:
            if isinstance(self.worker_command, str) or not self.worker_command:
                raise OrchestratorLocalRunError(
                    "worker_command must be an explicit argv list"
                )
            for argument in self.worker_command:
                if not isinstance(argument, str) or argument == "":
                    raise OrchestratorLocalRunError(
                        "worker_command arguments must be non-empty strings"
                    )


@dataclass(frozen=True)
class OrchestratorLocalRunResult:
    """Filesystem outputs and final state for one orchestrator run."""

    run: OrchestratorRun
    run_root: Path
    record_path: Path


class OrchestratorLocalRunner:
    """Execute deterministic local worker tasks for a planned issue."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context
        self.task_harness = OrchestratorStub(context)
        self.local_runner = LocalWorkerRunner(context)

    def run_issue(
        self,
        config: OrchestratorLocalRunConfig,
    ) -> OrchestratorLocalRunResult:
        """Plan and run local worker commands for one issue."""
        now = _normalize_timestamp(config.now or _utc_now())
        run_id = config.run_id or validate_artifact_id(f"run.{config.issue_id}")
        try:
            plan = plan_for_issue(self.context, config.issue_id)
        except OrchestratorPlannerError as exc:
            raise OrchestratorLocalRunError(str(exc)) from exc

        run_root = self.context.resolve(
            Path(".cosheaf")
            / "orchestrator"
            / config.issue_id
            / "runs"
            / run_id
        )
        record_path = run_root / "run.yaml"
        if run_root.exists():
            raise OrchestratorLocalRunError(
                f"orchestrator run already exists: {run_id}"
            )
        run_root.mkdir(parents=True, exist_ok=False)

        run = (
            OrchestratorRun.create(
                run_id=run_id,
                issue_id=config.issue_id,
                now=now,
            )
            .transition(OrchestratorState.PLANNED, now=now, plan=plan)
            .transition(OrchestratorState.RUNNING, now=now)
        )

        worker_calls: list[WorkerCall] = []
        reducer_results = []
        stop_conditions: list[StopCondition] = []

        for index, node in enumerate(plan.task_dag.nodes, start=1):
            task = self._ensure_task_for_node(config.issue_id, node, now=now)
            bundle_path = self._bundle_path(config, run_id, node)
            command = (
                list(config.worker_command)
                if config.worker_command is not None
                else _default_worker_command(
                    bundle_path=bundle_path,
                    task=task,
                    node=node,
                    proposal_path=self._proposal_path(config, run_id, node),
                    created_at=now,
                )
            )
            try:
                local_result = self.local_runner.run_task(
                    task.task_id,
                    LocalWorkerRunConfig(
                        command=command,
                        timeout_seconds=config.timeout_seconds,
                        run_id=validate_artifact_id(f"{run_id}.{node.node_id}"),
                        started_at=now,
                    ),
                )
            except LocalWorkerRunError as exc:
                raise OrchestratorLocalRunError(str(exc)) from exc
            worker_calls.append(
                WorkerCall(
                    call_id=validate_artifact_id(f"call.{node.node_id}"),
                    task_node_id=node.node_id,
                    worker_type=node.worker_type,
                    status=local_result.status,
                    command=command,
                    cwd=".",
                    started_at=now,
                    completed_at=now,
                    exit_code=local_result.returncode,
                    stdout_path=repo_relative_posix(
                        self.context.repo_root,
                        local_result.stdout_path,
                    ),
                    stderr_path=repo_relative_posix(
                        self.context.repo_root,
                        local_result.stderr_path,
                    ),
                    bundle_path=repo_relative_posix(
                        self.context.repo_root,
                        self.context.resolve(bundle_path),
                    ),
                    notes=f"local-only worker call {index}",
                )
            )
            if local_result.status != "completed":
                stop_conditions.append(
                    StopCondition(
                        reason="worker_failed",
                        description=(
                            f"{node.node_id} finished with status "
                            f"{local_result.status}"
                        ),
                    )
                )
                break

            try:
                reducer_results.append(
                    reduce_worker_bundle_v2(
                        self.context,
                        bundle_path,
                        reducer_id=validate_artifact_id(f"reducer.{node.node_id}"),
                    )
                )
            except WorkerBundleV2Error as exc:
                stop_conditions.append(
                    StopCondition(
                        reason="worker_bundle_invalid",
                        description=str(exc),
                    )
                )
                break

        terminal_state = (
            OrchestratorState.FAILED if stop_conditions else OrchestratorState.COMPLETED
        )
        final_run = run.transition(
            terminal_state,
            now=_utc_now(),
            worker_calls=worker_calls,
            reducer_results=reducer_results,
            stop_conditions=stop_conditions,
        )
        write_yaml_deterministic(record_path, final_run)
        return OrchestratorLocalRunResult(
            run=final_run,
            run_root=run_root,
            record_path=record_path,
        )

    def _ensure_task_for_node(
        self,
        issue_id: str,
        node: TaskNode,
        *,
        now: datetime,
    ) -> AgentTask:
        task_id = validate_artifact_id(f"task.{node.node_id}")
        try:
            return self.task_harness.load_task(task_id)
        except TaskHarnessError as exc:
            if "task not found" not in str(exc):
                raise OrchestratorLocalRunError(str(exc)) from exc
            return self.task_harness.create_task(
                issue_id=issue_id,
                worker_type=node.worker_type,
                now=now,
                task_id=task_id,
            )

    def _bundle_path(
        self,
        config: OrchestratorLocalRunConfig,
        run_id: str,
        node: TaskNode,
    ) -> Path:
        return (
            Path(".cosheaf")
            / "orchestrator"
            / config.issue_id
            / "runs"
            / run_id
            / "bundles"
            / f"{node.node_id}.yaml"
        )

    def _proposal_path(
        self,
        config: OrchestratorLocalRunConfig,
        run_id: str,
        node: TaskNode,
    ) -> str:
        if config.proposal_path is not None:
            return str(config.proposal_path)
        return (
            Path(".cosheaf")
            / "orchestrator"
            / config.issue_id
            / "runs"
            / run_id
            / "proposals"
            / f"{node.node_id}.yaml"
        ).as_posix()


def _default_worker_command(
    *,
    bundle_path: Path,
    task: AgentTask,
    node: TaskNode,
    proposal_path: str,
    created_at: datetime,
) -> list[str]:
    return [
        sys.executable,
        "-c",
        _DEFAULT_WORKER_SCRIPT,
        bundle_path.as_posix(),
        task.task_id,
        node.worker_type.value,
        node.node_id,
        proposal_path,
        _format_timestamp(created_at),
    ]


_DEFAULT_WORKER_SCRIPT = r"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

bundle_path = Path(sys.argv[1])
task_id = sys.argv[2]
worker_role = sys.argv[3]
node_id = sys.argv[4]
proposal_path = sys.argv[5]
created_at = sys.argv[6]
bundle_path.parent.mkdir(parents=True, exist_ok=True)
bundle = {
    "bundle_id": f"bundle.{node_id}",
    "task_id": task_id,
    "worker_role": worker_role,
    "created_at": created_at,
    "summary": f"Local dry-run worker completed {node_id}.",
    "used_artifacts": [],
    "used_sources": [],
    "claims": [
        "This is a deterministic dry-run bundle for review workflow testing."
    ],
    "proposed_artifacts": [
        {
            "path": proposal_path,
            "summary": "Dry-run proposal path; no artifact is written.",
        }
    ],
    "verification_requests": [
        "Run validation, gates, and human review before promotion."
    ],
    "failures_or_counterexamples": [
        "No hosted LLM, network call, Lean check, or proof was performed."
    ],
    "risk_flags": ["dry_run_only", "needs_human_review"],
    "next_steps": ["Inspect worker logs and request review if useful."],
    "confidence": "low",
}
bundle_path.write_text(
    yaml.safe_dump(bundle, sort_keys=False),
    encoding="utf-8",
)
print(f"worker_bundle_v2={bundle_path.as_posix()}")
"""


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OrchestratorLocalRunError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )
