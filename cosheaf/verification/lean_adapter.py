"""Optional Lean verifier adapter with minimal command invocation support."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

LEAN_EVIDENCE_KINDS = frozenset({"lean", "lean4", "lean_checker", "lean_proof"})
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class LeanEvidenceSpec:
    """One Lean evidence item to check."""

    path: str
    timeout_seconds: float
    index: int


@dataclass(frozen=True)
class LeanBackendResult:
    """Normalized output from one Lean backend invocation."""

    exit_code: int | None
    stdout: str
    stderr: str


class LeanBackend(Protocol):
    """Small protocol implemented by optional Lean backends."""

    @property
    def name(self) -> str:
        """Return stable backend name metadata."""
        ...

    def is_available(self) -> bool:
        """Return whether the backend is currently usable."""
        ...

    def command(self, lean_path: Path) -> tuple[str, ...]:
        """Return the command or equivalent invocation metadata."""
        ...

    def version(self) -> str | None:
        """Return backend version metadata when cheaply available."""
        ...

    def check(
        self,
        lean_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> LeanBackendResult:
        """Run the backend against a Lean file."""
        ...


class ExternalLeanCommandBackend:
    """Lean backend that runs an optional external Lean binary."""

    def __init__(self, lean_command: str = "lean") -> None:
        self.name = lean_command
        self.lean_command = lean_command

    def is_available(self) -> bool:
        """Return whether the Lean command is discoverable on PATH."""
        return shutil.which(self.lean_command) is not None

    def command(self, lean_path: Path) -> tuple[str, ...]:
        """Return the Lean command for a plain Lean file."""
        return (self.lean_command, lean_path.as_posix())

    def version(self) -> str | None:
        """Return Lean version text when the command supports it."""
        if not self.is_available():
            return None
        try:
            completed = subprocess.run(
                (self.lean_command, "--version"),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        version = (completed.stdout or completed.stderr).strip().splitlines()
        return version[0].strip() if version else None

    def check(
        self,
        lean_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> LeanBackendResult:
        """Run Lean and return raw process output."""
        completed = subprocess.run(
            self.command(lean_path),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return LeanBackendResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


class LeanAdapter:
    """Optional Lean verifier for repository-local plain Lean evidence."""

    name = "lean"

    def __init__(
        self,
        lean_command: str = "lean",
        *,
        backend: LeanBackend | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.backend = backend or ExternalLeanCommandBackend(lean_command)
        self.timeout_seconds = timeout_seconds

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether the artifact has Lean evidence."""
        return bool(self._specs_for(artifact))

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Verify the first Lean evidence item or return a normalized skip/error."""
        specs = self._specs_for(artifact)
        started_at = _now()
        if not specs:
            return _result(
                artifact=artifact,
                repo=repo,
                status=VerificationStatus.SKIPPED,
                started_at=started_at,
                ended_at=started_at,
                command=None,
                exit_code=None,
                stdout_path=None,
                stderr_path=None,
                evidence_paths=(),
                timeout_seconds=None,
                input_paths=(),
                output_paths=(),
                tool_name=self.backend.name,
                tool_version=None,
                environment=None,
                message="No Lean evidence found.",
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
        spec: LeanEvidenceSpec,
    ) -> VerificationResult:
        started_at = _now()
        command = self.backend.command(Path(spec.path))
        lean_path_or_error = _resolve_evidence_path(repo, spec.path)
        if isinstance(lean_path_or_error, str):
            return _error_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                started_at=started_at,
                command=command,
                message=lean_path_or_error,
                backend=self.backend,
            )
        lean_path = lean_path_or_error

        if not lean_path.is_file():
            return _error_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                started_at=started_at,
                command=command,
                message=f"Lean evidence file not found: {spec.path}",
                backend=self.backend,
            )

        if not self.backend.is_available():
            return _result(
                artifact=artifact,
                repo=repo,
                status=VerificationStatus.SKIPPED,
                started_at=started_at,
                ended_at=_now(),
                command=(command[0],) if command else (self.backend.name,),
                exit_code=None,
                stdout_path=None,
                stderr_path=None,
                evidence_paths=(spec.path,),
                timeout_seconds=spec.timeout_seconds,
                input_paths=(spec.path,),
                output_paths=(),
                tool_name=self.backend.name,
                tool_version=self.backend.version(),
                environment=None,
                message=f"Lean backend is not available: {self.backend.name}",
            )

        stdout_path, stderr_path = _log_paths(repo, artifact.id, spec.index)
        command = self.backend.command(Path(spec.path))
        try:
            backend_result = self.backend.check(
                Path(spec.path),
                cwd=repo.repo_root,
                timeout_seconds=spec.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            message = f"Lean backend timed out after {spec.timeout_seconds:g} second(s)"
            _write_logs(stdout_path, stderr_path, "", message + "\n")
            return _executed_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=_now(),
                command=command,
                exit_code=None,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                message=message,
                backend=self.backend,
            )
        except OSError as exc:
            message = f"Lean backend command failed to start: {exc}"
            _write_logs(stdout_path, stderr_path, "", message + "\n")
            return _executed_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=_now(),
                command=command,
                exit_code=None,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                message=message,
                backend=self.backend,
            )

        _write_logs(
            stdout_path,
            stderr_path,
            backend_result.stdout,
            backend_result.stderr,
        )
        status, message = _status_and_message(backend_result.exit_code)
        return _executed_result(
            artifact=artifact,
            repo=repo,
            spec=spec,
            status=status,
            started_at=started_at,
            ended_at=_now(),
            command=command,
            exit_code=backend_result.exit_code,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            message=message,
            backend=self.backend,
        )

    def _specs_for(self, artifact: BaseArtifact) -> tuple[LeanEvidenceSpec, ...]:
        specs: list[LeanEvidenceSpec] = []
        for index, evidence in enumerate(artifact.evidence):
            if evidence.kind not in LEAN_EVIDENCE_KINDS:
                continue
            if not evidence.path:
                continue
            specs.append(
                LeanEvidenceSpec(
                    path=evidence.path,
                    timeout_seconds=self.timeout_seconds,
                    index=index,
                )
            )
        return tuple(specs)


def _resolve_evidence_path(repo: RepoContext, evidence_path: str) -> Path | str:
    path = Path(evidence_path)
    resolved = path.resolve() if path.is_absolute() else repo.resolve(path)
    try:
        resolved.relative_to(repo.repo_root)
    except ValueError:
        return f"Lean evidence path must stay inside repository: {evidence_path}"
    return resolved


def _status_and_message(exit_code: int | None) -> tuple[VerificationStatus, str]:
    if exit_code == 0:
        return VerificationStatus.PASS, "Lean backend completed successfully."
    if exit_code is None:
        return (
            VerificationStatus.ERROR,
            "Lean backend did not report an exit code.",
        )
    return (
        VerificationStatus.FAIL,
        f"Lean backend returned nonzero exit code {exit_code}",
    )


def _log_paths(repo: RepoContext, artifact_id: str, index: int) -> tuple[Path, Path]:
    log_dir = repo.resolve(".cosheaf/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_safe_name(artifact_id)}-lean-{index}"
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


def _error_result(
    *,
    artifact: BaseArtifact,
    repo: RepoContext,
    spec: LeanEvidenceSpec,
    started_at: datetime,
    command: tuple[str, ...],
    message: str,
    backend: LeanBackend,
) -> VerificationResult:
    return _result(
        artifact=artifact,
        repo=repo,
        status=VerificationStatus.ERROR,
        started_at=started_at,
        ended_at=_now(),
        command=command,
        exit_code=None,
        stdout_path=None,
        stderr_path=None,
        evidence_paths=(spec.path,),
        timeout_seconds=spec.timeout_seconds,
        input_paths=(spec.path,),
        output_paths=(),
        tool_name=backend.name,
        tool_version=backend.version(),
        environment=None,
        message=message,
    )


def _executed_result(
    *,
    artifact: BaseArtifact,
    repo: RepoContext,
    spec: LeanEvidenceSpec,
    status: VerificationStatus,
    started_at: datetime,
    ended_at: datetime,
    command: tuple[str, ...],
    exit_code: int | None,
    stdout_path: Path,
    stderr_path: Path,
    message: str,
    backend: LeanBackend,
) -> VerificationResult:
    stdout_relative = _repo_relative(repo, stdout_path)
    stderr_relative = _repo_relative(repo, stderr_path)
    return _result(
        artifact=artifact,
        repo=repo,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        exit_code=exit_code,
        stdout_path=stdout_relative,
        stderr_path=stderr_relative,
        evidence_paths=(spec.path,),
        timeout_seconds=spec.timeout_seconds,
        input_paths=(spec.path,),
        output_paths=(stderr_relative, stdout_relative),
        tool_name=backend.name,
        tool_version=backend.version(),
        environment=f"backend={backend.name}",
        message=message,
    )


def _result(
    *,
    artifact: BaseArtifact,
    repo: RepoContext,
    status: VerificationStatus,
    started_at: datetime,
    ended_at: datetime,
    command: tuple[str, ...] | None,
    exit_code: int | None,
    stdout_path: str | None,
    stderr_path: str | None,
    evidence_paths: tuple[str, ...],
    timeout_seconds: float | None,
    input_paths: tuple[str, ...],
    output_paths: tuple[str, ...],
    tool_name: str | None,
    tool_version: str | None,
    environment: str | None,
    message: str,
) -> VerificationResult:
    return VerificationResult(
        verifier=LeanAdapter.name,
        artifact_id=artifact.id,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        cwd=str(repo.repo_root) if command else None,
        exit_code=exit_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        evidence_paths=evidence_paths,
        timeout_seconds=timeout_seconds,
        input_paths=input_paths,
        output_paths=output_paths,
        tool_name=tool_name,
        tool_version=tool_version,
        seed=None,
        environment=environment,
        message=message,
    )


def _repo_relative(repo: RepoContext, path: Path) -> str:
    return path.relative_to(repo.repo_root).as_posix()


def _now() -> datetime:
    return datetime.now(UTC)
