"""Deterministic agent task orchestration stubs.

This module intentionally does not call LLMs, network services, or concrete
worker runtimes. It only records task metadata and validates completion bundles.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import NoReturn

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError
from yaml import YAMLError

from cosheaf.agent.task import AgentTask, BudgetValue, WorkerType
from cosheaf.agent.worker_contract import (
    OutputBundleError,
    WorkerOutputBundle,
    validate_output_bundle,
)
from cosheaf.storage.loader import IssueRecord, LoadedRecord, LoadError, load_artifacts
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

TASKS_DIR = Path(".cosheaf") / "tasks"


class TaskHarnessError(ValueError):
    """Raised for expected task harness failures."""


class AcceptedKnowledgeMergeProhibitedError(TaskHarnessError):
    """Raised if a caller asks the stub to merge accepted knowledge."""


@dataclass(frozen=True)
class TaskCompletionResult:
    """Result of marking a task complete after bundle validation."""

    task: AgentTask
    bundle: WorkerOutputBundle
    task_path: Path


class OrchestratorStub:
    """Minimal filesystem-backed orchestrator for task records."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context

    def create_task(
        self,
        *,
        issue_id: str,
        worker_type: WorkerType | str,
        now: datetime | None = None,
        task_id: str | None = None,
        budget: dict[str, BudgetValue] | None = None,
    ) -> AgentTask:
        """Create an open task after confirming the issue exists."""
        issue_record = self._find_issue(issue_id)
        task = AgentTask.create(
            issue_id=issue_id,
            worker_type=worker_type,
            now=now,
            task_id=task_id,
            input_context=[issue_record.source_path.as_posix()],
            budget=budget,
        )
        path = self.task_path(task.task_id)
        if path.exists():
            raise TaskHarnessError(f"task already exists: {task.task_id}")

        write_yaml_deterministic(path, task)
        return task

    def list_tasks(self) -> tuple[AgentTask, ...]:
        """Load task records in deterministic task ID order."""
        task_dir = self.context.resolve(TASKS_DIR)
        if not task_dir.exists():
            return ()

        tasks = [self.load_task_path(path) for path in task_dir.glob("*.yaml")]
        return tuple(sorted(tasks, key=lambda task: task.task_id))

    def complete_task(
        self,
        *,
        task_id: str,
        bundle_path: str | Path,
        now: datetime | None = None,
    ) -> TaskCompletionResult:
        """Validate a bundle and mark the task completed without merging output."""
        task = self.load_task(task_id)
        try:
            bundle = validate_output_bundle(self.context, bundle_path, task=task)
        except OutputBundleError as exc:
            raise TaskHarnessError(f"task output bundle invalid: {exc}") from exc

        completed = task.mark_completed(now=now)
        path = self.task_path(task_id)
        write_yaml_deterministic(path, completed)
        return TaskCompletionResult(task=completed, bundle=bundle, task_path=path)

    def load_task(self, task_id: str) -> AgentTask:
        """Load one task record by ID."""
        path = self.task_path(task_id)
        if not path.is_file():
            raise TaskHarnessError(f"task not found: {task_id}")
        return self.load_task_path(path)

    def load_task_path(self, path: Path) -> AgentTask:
        """Load one task record file."""
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except YAMLError as exc:
            raise TaskHarnessError(f"{path}: invalid task YAML: {exc}") from exc
        except OSError as exc:
            raise TaskHarnessError(f"{path}: cannot read task file: {exc}") from exc

        if not isinstance(raw, dict):
            raise TaskHarnessError(f"{path}: task file must be a YAML mapping")

        try:
            return AgentTask.model_validate(raw)
        except ValidationError as exc:
            raise TaskHarnessError(f"{path}: invalid task record: {exc}") from exc

    def task_path(self, task_id: str) -> Path:
        """Return the runtime task file path for a task ID."""
        return self.context.resolve(TASKS_DIR / f"{task_id}.yaml")

    def merge_accepted_knowledge(self) -> NoReturn:
        """Refuse accepted-knowledge merges from the orchestrator stub."""
        raise AcceptedKnowledgeMergeProhibitedError(
            "orchestrator stub cannot merge accepted knowledge"
        )

    def _find_issue(self, issue_id: str) -> LoadedRecord:
        try:
            records = tuple(load_artifacts(self.context))
        except LoadError as exc:
            raise TaskHarnessError(f"cannot load repository records: {exc}") from exc

        for record in records:
            if isinstance(record.record, IssueRecord) and record.id == issue_id:
                return record
        raise TaskHarnessError(f"issue not found: {issue_id}")
