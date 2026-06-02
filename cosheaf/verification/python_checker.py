"""Python checker verifier adapter."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class PythonCheckerSpec:
    """One python_checker evidence command specification."""

    path: str
    command: tuple[str, ...] | None
    timeout_seconds: float
    index: int


class PythonCheckerAdapter:
    """Verifier adapter that runs Python checker evidence commands."""

    name = "python_checker"

    def __init__(
        self,
        *,
        python_executable: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.timeout_seconds = timeout_seconds

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether the artifact has python_checker evidence."""
        return bool(self._specs_for(artifact))

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Run python_checker evidence and return one normalized result."""
        specs = self._specs_for(artifact)
        if not specs:
            started_at = _now()
            return VerificationResult(
                verifier=self.name,
                artifact_id=artifact.id,
                status=VerificationStatus.SKIPPED,
                started_at=started_at,
                ended_at=started_at,
                command=None,
                cwd=None,
                exit_code=None,
                stdout_path=None,
                stderr_path=None,
                evidence_paths=(),
                timeout_seconds=None,
                input_paths=(),
                output_paths=(),
                tool_name="python",
                tool_version=_python_version(),
                seed=None,
                environment=f"python_executable={self.python_executable}",
                message="No python_checker evidence found.",
            )

        return self._run_spec(
            artifact=artifact,
            repo=repo,
            spec=specs[0],
        )

    def _run_spec(
        self,
        *,
        artifact: BaseArtifact,
        repo: RepoContext,
        spec: PythonCheckerSpec,
    ) -> VerificationResult:
        started_at = _now()
        stdout_path, stderr_path = _log_paths(repo, artifact.id, spec.index)
        artifact_source = _artifact_source_path(repo, artifact)
        command = spec.command or (
            self.python_executable,
            spec.path,
            artifact_source,
        )
        cwd = str(repo.repo_root)

        script_path = repo.resolve(spec.path)
        if not script_path.exists():
            message = f"missing checker script: {spec.path}"
            _write_logs(stdout_path, stderr_path, "", message + "\n")
            ended_at = _now()
            return _result(
                artifact=artifact,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=ended_at,
                command=command,
                cwd=cwd,
                exit_code=None,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                repo=repo,
                evidence_paths=(spec.path,),
                timeout_seconds=spec.timeout_seconds,
                input_paths=(spec.path, artifact_source),
                tool_name="python",
                tool_version=_python_version(),
                environment=f"python_executable={self.python_executable}",
                message=message,
            )

        try:
            completed = subprocess.run(
                command,
                cwd=repo.repo_root,
                capture_output=True,
                text=True,
                timeout=spec.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = _process_output(exc.stdout)
            stderr = _process_output(exc.stderr)
            message = (
                f"python checker timed out after {spec.timeout_seconds:g} second(s)"
            )
            _write_logs(stdout_path, stderr_path, stdout, stderr + message + "\n")
            ended_at = _now()
            return _result(
                artifact=artifact,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=ended_at,
                command=command,
                cwd=cwd,
                exit_code=None,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                repo=repo,
                evidence_paths=(spec.path,),
                timeout_seconds=spec.timeout_seconds,
                input_paths=(spec.path, artifact_source),
                tool_name="python",
                tool_version=_python_version(),
                environment=f"python_executable={self.python_executable}",
                message=message,
            )
        except OSError as exc:
            message = f"python checker command failed to start: {exc}"
            _write_logs(stdout_path, stderr_path, "", message + "\n")
            ended_at = _now()
            return _result(
                artifact=artifact,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=ended_at,
                command=command,
                cwd=cwd,
                exit_code=None,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                repo=repo,
                evidence_paths=(spec.path,),
                timeout_seconds=spec.timeout_seconds,
                input_paths=(spec.path, artifact_source),
                tool_name="python",
                tool_version=_python_version(),
                environment=f"python_executable={self.python_executable}",
                message=message,
            )

        _write_logs(stdout_path, stderr_path, completed.stdout, completed.stderr)
        ended_at = _now()
        status = (
            VerificationStatus.PASS
            if completed.returncode == 0
            else VerificationStatus.FAIL
        )
        message = (
            "python checker passed"
            if completed.returncode == 0
            else f"python checker failed with exit code {completed.returncode}"
        )
        return _result(
            artifact=artifact,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            command=command,
            cwd=cwd,
            exit_code=completed.returncode,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            repo=repo,
            evidence_paths=(spec.path,),
            timeout_seconds=spec.timeout_seconds,
            input_paths=(spec.path, artifact_source),
            tool_name="python",
            tool_version=_python_version(),
            environment=f"python_executable={self.python_executable}",
            message=message,
        )

    def _specs_for(self, artifact: BaseArtifact) -> tuple[PythonCheckerSpec, ...]:
        specs: list[PythonCheckerSpec] = []
        for index, evidence in enumerate(artifact.evidence):
            kind = _evidence_value(evidence, "kind") or _evidence_value(
                evidence,
                "type",
            )
            if kind != "python_checker":
                continue
            path = _evidence_value(evidence, "path")
            if not path:
                continue
            raw_command = _evidence_value(evidence, "command")
            raw_timeout = _evidence_value(evidence, "timeout_seconds")
            specs.append(
                PythonCheckerSpec(
                    path=path,
                    command=_normalize_command(raw_command),
                    timeout_seconds=_normalize_timeout(
                        raw_timeout,
                        self.timeout_seconds,
                    ),
                    index=index,
                )
            )
        return tuple(specs)


def _evidence_value(evidence: object, name: str) -> Any:
    if isinstance(evidence, dict):
        return evidence.get(name)
    return getattr(evidence, name, None)


def _normalize_command(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    try:
        command = tuple(str(part) for part in value)
    except TypeError:
        return None
    return command or None


def _normalize_timeout(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        return default
    return timeout if timeout > 0 else default


def _artifact_source_path(repo: RepoContext, artifact: BaseArtifact) -> str:
    records = load_artifacts(repo)
    matches = [
        record.source_path.as_posix()
        for record in records
        if record.id == artifact.id
    ]
    if matches:
        return sorted(matches)[0]
    return artifact.id


def _log_paths(repo: RepoContext, artifact_id: str, index: int) -> tuple[Path, Path]:
    log_dir = repo.resolve(".cosheaf/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_safe_name(artifact_id)}-python_checker-{index}"
    return log_dir / f"{stem}.stdout.log", log_dir / f"{stem}.stderr.log"


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in ".-_" else "_" for char in value)


def _write_logs(
    stdout_path: Path,
    stderr_path: Path,
    stdout: str,
    stderr: str,
) -> None:
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")


def _result(
    *,
    artifact: BaseArtifact,
    status: VerificationStatus,
    started_at: datetime,
    ended_at: datetime,
    command: tuple[str, ...],
    cwd: str,
    exit_code: int | None,
    stdout_path: Path,
    stderr_path: Path,
    repo: RepoContext,
    evidence_paths: tuple[str, ...],
    timeout_seconds: float,
    input_paths: tuple[str, ...],
    tool_name: str,
    tool_version: str | None,
    environment: str,
    message: str,
) -> VerificationResult:
    stdout_relative = _repo_relative(repo, stdout_path)
    stderr_relative = _repo_relative(repo, stderr_path)
    return VerificationResult(
        verifier=PythonCheckerAdapter.name,
        artifact_id=artifact.id,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        cwd=cwd,
        exit_code=exit_code,
        stdout_path=stdout_relative,
        stderr_path=stderr_relative,
        evidence_paths=evidence_paths,
        timeout_seconds=timeout_seconds,
        input_paths=input_paths,
        output_paths=(stdout_relative, stderr_relative),
        tool_name=tool_name,
        tool_version=tool_version,
        seed=None,
        environment=environment,
        message=message,
    )


def _repo_relative(repo: RepoContext, path: Path) -> str:
    return path.relative_to(repo.repo_root).as_posix()


def _process_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _now() -> datetime:
    return datetime.now(UTC)


def _python_version() -> str:
    return sys.version.split()[0]
