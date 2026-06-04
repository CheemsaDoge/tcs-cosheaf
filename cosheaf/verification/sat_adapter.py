"""Optional SAT verifier adapter with minimal DIMACS invocation support."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import Literal, Protocol

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

SAT_EVIDENCE_KINDS = frozenset({"sat", "sat_solver", "sat_checker"})
DEFAULT_TIMEOUT_SECONDS = 30.0
CHECKER_MARKER = "CHECKER_DATA:\n"
SatSolverOutcome = Literal["sat", "unsat", "unknown"]


@dataclass(frozen=True)
class SatEvidenceSpec:
    """One SAT evidence item to verify."""

    path: str
    timeout_seconds: float
    index: int


@dataclass(frozen=True)
class SatBackendResult:
    """Normalized output from one SAT backend invocation."""

    exit_code: int | None
    stdout: str
    stderr: str
    result: SatSolverOutcome


class SatBackend(Protocol):
    """Small protocol implemented by optional SAT backends."""

    @property
    def name(self) -> str:
        """Return stable backend name metadata."""
        ...

    def is_available(self) -> bool:
        """Return whether the backend is currently usable."""
        ...

    def command(self, cnf_path: Path) -> tuple[str, ...]:
        """Return the command or equivalent invocation metadata."""
        ...

    def version(self) -> str | None:
        """Return backend version metadata when cheaply available."""
        ...

    def solve(
        self,
        cnf_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> SatBackendResult:
        """Run the backend against a DIMACS CNF path."""
        ...


class ExternalSatCommandBackend:
    """SAT backend that runs an optional external solver binary."""

    def __init__(self, solver_command: str = "kissat") -> None:
        self.name = solver_command
        self.solver_command = solver_command

    def is_available(self) -> bool:
        """Return whether the solver command is discoverable on PATH."""
        return shutil.which(self.solver_command) is not None

    def command(self, cnf_path: Path) -> tuple[str, ...]:
        """Return the solver command for a DIMACS CNF file."""
        return (self.solver_command, cnf_path.as_posix())

    def version(self) -> str | None:
        """Return solver version text when the command supports it."""
        if not self.is_available():
            return None
        try:
            completed = subprocess.run(
                (self.solver_command, "--version"),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        version = (completed.stdout or completed.stderr).strip().splitlines()
        return version[0].strip() if version else None

    def solve(
        self,
        cnf_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> SatBackendResult:
        """Run the solver and parse a normalized SAT outcome."""
        completed = subprocess.run(
            self.command(cnf_path),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return SatBackendResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            result=_parse_solver_result(
                stdout=completed.stdout,
                stderr=completed.stderr,
                exit_code=completed.returncode,
            ),
        )


class SatAdapter:
    """Optional SAT solver verifier for repository-local DIMACS CNF evidence."""

    name = "sat"

    def __init__(
        self,
        solver_command: str = "kissat",
        *,
        backend: SatBackend | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.backend = backend or ExternalSatCommandBackend(solver_command)
        self.timeout_seconds = timeout_seconds

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether the artifact has SAT evidence."""
        return bool(self._specs_for(artifact))

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Verify the first SAT evidence item or return a normalized skip/error."""
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
                message="No SAT evidence found.",
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
        spec: SatEvidenceSpec,
    ) -> VerificationResult:
        started_at = _now()
        command = self.backend.command(Path(spec.path))
        cnf_path_or_error = _resolve_evidence_path(repo, spec.path)
        if isinstance(cnf_path_or_error, str):
            return _error_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                started_at=started_at,
                command=command,
                message=cnf_path_or_error,
                backend=self.backend,
            )
        cnf_path = cnf_path_or_error

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
                message=f"SAT backend is not available: {self.backend.name}",
            )

        if not cnf_path.is_file():
            return _error_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                started_at=started_at,
                command=command,
                message=f"SAT evidence file not found: {spec.path}",
                backend=self.backend,
            )

        stdout_path, stderr_path = _log_paths(repo, artifact.id, spec.index)
        command = self.backend.command(Path(spec.path))
        try:
            backend_result = self.backend.solve(
                Path(spec.path),
                cwd=repo.repo_root,
                timeout_seconds=spec.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            message = f"SAT backend timed out after {spec.timeout_seconds:g} second(s)"
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
                result="unknown",
                message=message,
                backend=self.backend,
            )
        except OSError as exc:
            message = f"SAT backend command failed to start: {exc}"
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
                result="unknown",
                message=message,
                backend=self.backend,
            )

        _write_logs(
            stdout_path,
            stderr_path,
            backend_result.stdout,
            backend_result.stderr,
        )
        try:
            expected = _expected_solver_outcome(artifact)
        except ValueError as exc:
            message = f"SAT expected-result metadata is invalid: {exc}"
            return _executed_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=_now(),
                command=command,
                exit_code=backend_result.exit_code,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                result=backend_result.result,
                message=message,
                backend=self.backend,
            )
        status, message = _status_and_message(
            expected=expected,
            actual=backend_result.result,
            exit_code=backend_result.exit_code,
        )
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
            result=backend_result.result,
            message=message,
            backend=self.backend,
        )

    def _specs_for(self, artifact: BaseArtifact) -> tuple[SatEvidenceSpec, ...]:
        specs: list[SatEvidenceSpec] = []
        for index, evidence in enumerate(artifact.evidence):
            if evidence.kind not in SAT_EVIDENCE_KINDS:
                continue
            if not evidence.path:
                continue
            specs.append(
                SatEvidenceSpec(
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
        return f"SAT evidence path must stay inside repository: {evidence_path}"
    return resolved


def _status_and_message(
    *,
    expected: SatSolverOutcome | None,
    actual: SatSolverOutcome,
    exit_code: int | None,
) -> tuple[VerificationStatus, str]:
    if actual == "unknown":
        return (
            VerificationStatus.ERROR,
            f"SAT backend returned unknown result with exit code {exit_code}",
        )
    if expected is not None and actual != expected:
        return (
            VerificationStatus.FAIL,
            f"SAT backend mismatch: expected {expected}, got {actual}",
        )
    if expected is None:
        return (
            VerificationStatus.PASS,
            f"SAT backend completed with result: {actual}",
        )
    return (
        VerificationStatus.PASS,
        f"SAT backend result matched expected satisfiability: {actual}",
    )


def _expected_solver_outcome(artifact: BaseArtifact) -> SatSolverOutcome | None:
    if CHECKER_MARKER not in artifact.statement:
        return None
    raw_data = artifact.statement.split(CHECKER_MARKER, 1)[1]
    try:
        data = yaml.safe_load(dedent(raw_data))
    except yaml.YAMLError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(data, dict):
        return None
    expected = data.get("expected")
    if not isinstance(expected, dict):
        return None
    satisfiable = expected.get("satisfiable")
    if satisfiable is True:
        return "sat"
    if satisfiable is False:
        return "unsat"
    return None


def _parse_solver_result(
    *,
    stdout: str,
    stderr: str,
    exit_code: int | None,
) -> SatSolverOutcome:
    combined = f"{stdout}\n{stderr}".lower()
    if "unsat" in combined or exit_code == 20:
        return "unsat"
    if "sat" in combined or exit_code == 10:
        return "sat"
    return "unknown"


def _log_paths(repo: RepoContext, artifact_id: str, index: int) -> tuple[Path, Path]:
    log_dir = repo.resolve(".cosheaf/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_safe_name(artifact_id)}-sat-{index}"
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
    spec: SatEvidenceSpec,
    started_at: datetime,
    command: tuple[str, ...],
    message: str,
    backend: SatBackend,
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
    spec: SatEvidenceSpec,
    status: VerificationStatus,
    started_at: datetime,
    ended_at: datetime,
    command: tuple[str, ...],
    exit_code: int | None,
    stdout_path: Path,
    stderr_path: Path,
    result: SatSolverOutcome,
    message: str,
    backend: SatBackend,
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
        environment=f"backend={backend.name}; result={result}",
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
        verifier=SatAdapter.name,
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
