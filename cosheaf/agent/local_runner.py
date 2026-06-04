"""Local command runner for existing agent task records.

The local runner executes explicit repository-local commands only. It does not
call hosted LLM APIs, network services, merge worker output, or promote
accepted knowledge.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Literal

from cosheaf.agent.orchestrator_stub import OrchestratorStub, TaskHarnessError
from cosheaf.agent.task import AgentTask
from cosheaf.agent.worker_contract import OutputBundleError, validate_output_bundle
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.paths import normalize_repo_path
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import write_yaml_deterministic

RunStatus = Literal["completed", "failed", "timed_out", "bundle_invalid"]


class LocalWorkerRunError(ValueError):
    """Raised for expected local worker runner failures."""


@dataclass(frozen=True)
class LocalWorkerRunConfig:
    """Configuration for one explicit local worker command run."""

    command: Sequence[str]
    timeout_seconds: int = 60
    cwd: str | Path | None = None
    bundle_path: str | Path | None = None
    run_id: str | None = None
    started_at: datetime | None = None

    def __post_init__(self) -> None:
        if isinstance(self.command, str) or not isinstance(self.command, Sequence):
            raise LocalWorkerRunError("command must be an explicit argv list")
        if not self.command:
            raise LocalWorkerRunError("command must be an explicit argv list")
        for argument in self.command:
            if not isinstance(argument, str):
                raise LocalWorkerRunError("command arguments must be strings")
            if argument == "":
                raise LocalWorkerRunError("command arguments must be non-empty")
        if self.timeout_seconds <= 0:
            raise LocalWorkerRunError("timeout_seconds must be positive")
        if self.run_id is not None:
            try:
                validate_artifact_id(self.run_id)
            except ValueError as exc:
                raise LocalWorkerRunError(f"invalid run_id: {exc}") from exc


@dataclass(frozen=True)
class LocalWorkerRunResult:
    """Filesystem outputs and normalized status for one local worker run."""

    task: AgentTask
    run_id: str
    status: RunStatus
    returncode: int | None
    run_dir: Path
    record_path: Path
    stdout_path: Path
    stderr_path: Path
    bundle_valid: bool | None


class LocalWorkerRunner:
    """Execute explicit local commands for existing task records."""

    def __init__(self, context: RepoContext) -> None:
        self.context = context
        self.orchestrator = OrchestratorStub(context)

    def run_task(
        self,
        task_id: str,
        config: LocalWorkerRunConfig,
    ) -> LocalWorkerRunResult:
        """Execute a task-local command and write a deterministic run record."""
        try:
            task = self.orchestrator.load_task(task_id)
        except TaskHarnessError as exc:
            raise LocalWorkerRunError(str(exc)) from exc

        cwd = self._resolve_cwd(config.cwd)
        cwd_record = _repo_relative_text(self.context, cwd)
        command = list(config.command)
        started_at = _normalize_timestamp(config.started_at or _utc_now())
        run_id = config.run_id or self._next_run_id(started_at)
        run_dir = self.context.resolve(
            Path(".cosheaf") / "tasks" / task.task_id / "runs" / run_id
        )
        if run_dir.exists():
            raise LocalWorkerRunError(f"run already exists: {run_id}")
        run_dir.mkdir(parents=True, exist_ok=False)
        stdout_path = run_dir / "stdout.txt"
        stderr_path = run_dir / "stderr.txt"
        record_path = run_dir / "run.yaml"

        status: RunStatus
        returncode: int | None
        stdout_text = ""
        stderr_text = ""
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                timeout=config.timeout_seconds,
                shell=False,
                capture_output=True,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            status = "timed_out"
            returncode = None
            stdout_text = _process_output_text(exc.stdout)
            stderr_text = _process_output_text(exc.stderr)
            timeout_message = f"timed out after {config.timeout_seconds} second(s)"
            stderr_text = _append_line(stderr_text, timeout_message)
        except OSError as exc:
            status = "failed"
            returncode = 127
            stderr_text = str(exc)
        else:
            returncode = completed.returncode
            stdout_text = _process_output_text(completed.stdout)
            stderr_text = _process_output_text(completed.stderr)
            status = "completed" if completed.returncode == 0 else "failed"

        bundle_record_path: str | None = None
        bundle_valid: bool | None = None
        if config.bundle_path is not None:
            bundle_record_path = self._bundle_record_path(config.bundle_path)
            if status == "completed":
                try:
                    validate_output_bundle(
                        self.context,
                        config.bundle_path,
                        task=task,
                    )
                except OutputBundleError as exc:
                    status = "bundle_invalid"
                    bundle_valid = False
                    stderr_text = _append_line(stderr_text, f"bundle invalid: {exc}")
                else:
                    bundle_valid = True

        finished_at = started_at if config.started_at is not None else _utc_now()
        stdout_path.write_text(stdout_text, encoding="utf-8", newline="\n")
        stderr_path.write_text(stderr_text, encoding="utf-8", newline="\n")
        write_yaml_deterministic(
            record_path,
            {
                "schema_version": 1,
                "task_id": task.task_id,
                "worker_type": task.worker_type.value,
                "command": command,
                "cwd": cwd_record,
                "started_at": _format_timestamp(started_at),
                "finished_at": _format_timestamp(finished_at),
                "timeout_seconds": config.timeout_seconds,
                "returncode": returncode,
                "stdout_path": stdout_path.name,
                "stderr_path": stderr_path.name,
                "bundle_path": bundle_record_path,
                "bundle_valid": bundle_valid,
                "status": status,
            },
        )

        return LocalWorkerRunResult(
            task=task,
            run_id=run_id,
            status=status,
            returncode=returncode,
            run_dir=run_dir,
            record_path=record_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            bundle_valid=bundle_valid,
        )

    def _resolve_cwd(self, cwd: str | Path | None) -> Path:
        if cwd is None:
            return self.context.repo_root

        path = Path(cwd)
        resolved = path.resolve() if path.is_absolute() else self.context.resolve(path)
        try:
            resolved.relative_to(self.context.repo_root)
        except ValueError:
            raise LocalWorkerRunError("cwd must stay inside repository") from None
        if not resolved.is_dir():
            raise LocalWorkerRunError(f"cwd does not exist: {_display_path(cwd)}")
        return resolved

    def _bundle_record_path(self, bundle_path: str | Path) -> str:
        path = Path(bundle_path)
        resolved = path.resolve() if path.is_absolute() else self.context.resolve(path)
        if resolved.is_dir():
            resolved = resolved / "bundle.yaml"
        try:
            relative = resolved.relative_to(self.context.repo_root)
        except ValueError:
            return normalize_repo_path(bundle_path)
        return relative.as_posix()

    def _next_run_id(self, started_at: datetime) -> str:
        date_part = started_at.strftime("%Y%m%d")
        time_part = started_at.strftime("%H%M%S")
        prefix = f"run.r{date_part}.t{time_part}z"
        candidate = validate_artifact_id(prefix)
        runs_root = self.context.resolve(Path(".cosheaf") / "runs")
        task_runs_root = self.context.resolve(Path(".cosheaf") / "tasks")
        if not (runs_root.exists() or task_runs_root.exists()):
            return candidate

        suffix = 1
        while True:
            existing = tuple(task_runs_root.glob(f"*/runs/{candidate}"))
            if not existing:
                return candidate
            suffix += 1
            candidate = validate_artifact_id(f"{prefix}.{suffix:04d}")


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise LocalWorkerRunError("timestamp must include timezone information")
    return value.astimezone(UTC).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def _repo_relative_text(context: RepoContext, path: Path) -> str:
    relative = path.relative_to(context.repo_root)
    rendered = relative.as_posix()
    return rendered or "."


def _process_output_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _append_line(existing: str, line: str) -> str:
    if not existing:
        return f"{line}\n"
    if existing.endswith("\n"):
        return f"{existing}{line}\n"
    return f"{existing}\n{line}\n"


def _display_path(path: str | Path) -> str:
    if isinstance(path, PureWindowsPath):
        return path.as_posix()
    return str(path)
