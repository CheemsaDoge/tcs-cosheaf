"""Optional external Lean library reference checker."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from cosheaf.core.artifact import BaseArtifact, FormalizationRef
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

DEFAULT_TIMEOUT_SECONDS = 30.0
CHECKABLE_FORMALIZATION_STATUSES = frozenset({"linked", "checked"})


@dataclass(frozen=True)
class LeanLibraryRefSpec:
    """One external Lean formalization reference to check."""

    formalization_id: str
    library: str
    library_ref: str
    import_path: str
    symbol: str
    status: str
    timeout_seconds: float
    index: int

    @property
    def label(self) -> str:
        """Return the stable result input label for this formalization."""
        return f"formalization:{self.formalization_id}"


@dataclass(frozen=True)
class LeanLibraryRefBackendResult:
    """Normalized output from one external Lean reference check."""

    exit_code: int | None
    stdout: str
    stderr: str


class LeanLibraryRefBackend(Protocol):
    """Small protocol implemented by optional Lean reference backends."""

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
    ) -> LeanLibraryRefBackendResult:
        """Run the backend against a generated Lean file."""
        ...


class ExternalLeanLibraryRefBackend:
    """Backend that checks generated Lean files with optional Lean or lake."""

    def __init__(
        self,
        lean_command: str = "lean",
        *,
        lake_command: str = "lake",
        use_lake: bool = False,
    ) -> None:
        self.lean_command = lean_command
        self.lake_command = lake_command
        self.use_lake = use_lake
        self.name = lake_command if use_lake else lean_command

    def is_available(self) -> bool:
        """Return whether the selected external command is discoverable."""
        command = self.lake_command if self.use_lake else self.lean_command
        return shutil.which(command) is not None

    def command(self, lean_path: Path) -> tuple[str, ...]:
        """Return the external Lean reference check command."""
        if self.use_lake:
            return (
                self.lake_command,
                "env",
                self.lean_command,
                lean_path.as_posix(),
            )
        return (self.lean_command, lean_path.as_posix())

    def version(self) -> str | None:
        """Return version text for the selected command when available."""
        if not self.is_available():
            return None
        version_command = self.lake_command if self.use_lake else self.lean_command
        try:
            completed = subprocess.run(
                (version_command, "--version"),
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
    ) -> LeanLibraryRefBackendResult:
        """Run the selected external command against a generated Lean file."""
        completed = subprocess.run(
            self.command(lean_path),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return LeanLibraryRefBackendResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


class LeanLibraryRefAdapter:
    """Optional checker for linked external Lean formalization references."""

    name = "lean_library_ref"

    def __init__(
        self,
        lean_command: str = "lean",
        *,
        lake_command: str = "lake",
        use_lake: bool = False,
        backend: LeanLibraryRefBackend | None = None,
        cwd: str | Path | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.backend = backend or ExternalLeanLibraryRefBackend(
            lean_command=lean_command,
            lake_command=lake_command,
            use_lake=use_lake,
        )
        self.cwd = Path(cwd).resolve() if cwd is not None else None
        self.timeout_seconds = timeout_seconds

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether the artifact has checkable external Lean links."""
        return bool(self._specs_for(artifact))

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Check the first linked/checked external Lean formalization reference."""
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
                cwd=None,
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
                message=(
                    "No linked or checked external Lean formalization found."
                ),
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
        spec: LeanLibraryRefSpec,
    ) -> VerificationResult:
        started_at = _now()
        cwd = self.cwd or repo.repo_root
        command_hint = self.backend.command(Path("<generated-lean-file>"))
        line_error = _validate_spec_lines(spec)
        if line_error is not None:
            return _result(
                artifact=artifact,
                repo=repo,
                status=VerificationStatus.ERROR,
                started_at=started_at,
                ended_at=_now(),
                command=command_hint,
                cwd=str(cwd),
                exit_code=None,
                stdout_path=None,
                stderr_path=None,
                evidence_paths=(spec.label,),
                timeout_seconds=spec.timeout_seconds,
                input_paths=(spec.label,),
                output_paths=(),
                tool_name=self.backend.name,
                tool_version=self.backend.version(),
                environment=_environment(spec, self.backend.name),
                message=line_error,
            )

        if not self.backend.is_available():
            return _result(
                artifact=artifact,
                repo=repo,
                status=VerificationStatus.SKIPPED,
                started_at=started_at,
                ended_at=_now(),
                command=(command_hint[0],) if command_hint else (self.backend.name,),
                cwd=str(cwd),
                exit_code=None,
                stdout_path=None,
                stderr_path=None,
                evidence_paths=(spec.label,),
                timeout_seconds=spec.timeout_seconds,
                input_paths=(spec.label,),
                output_paths=(),
                tool_name=self.backend.name,
                tool_version=self.backend.version(),
                environment=_environment(spec, self.backend.name),
                message=(
                    "Lean external library reference backend is not available: "
                    f"{self.backend.name}"
                ),
            )

        stdout_path, stderr_path = _log_paths(repo, artifact.id, spec.index)
        with tempfile.TemporaryDirectory(prefix="cosheaf-lean-ref-") as temp_dir:
            lean_path = Path(temp_dir) / "check.lean"
            lean_path.write_text(_lean_source(spec), encoding="utf-8")
            command = self.backend.command(lean_path)
            try:
                backend_result = self.backend.check(
                    lean_path,
                    cwd=cwd,
                    timeout_seconds=spec.timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                message = (
                    "Lean external library reference backend timed out after "
                    f"{spec.timeout_seconds:g} second(s); alignment not checked."
                )
                _write_logs(stdout_path, stderr_path, "", message + "\n")
                return _executed_result(
                    artifact=artifact,
                    repo=repo,
                    spec=spec,
                    status=VerificationStatus.ERROR,
                    started_at=started_at,
                    ended_at=_now(),
                    command=command,
                    cwd=cwd,
                    exit_code=None,
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    message=message,
                    backend=self.backend,
                )
            except OSError as exc:
                message = (
                    "Lean external library reference backend failed to start: "
                    f"{exc}; alignment not checked."
                )
                _write_logs(stdout_path, stderr_path, "", message + "\n")
                return _executed_result(
                    artifact=artifact,
                    repo=repo,
                    spec=spec,
                    status=VerificationStatus.ERROR,
                    started_at=started_at,
                    ended_at=_now(),
                    command=command,
                    cwd=cwd,
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
            status, message = _status_and_message(spec, backend_result.exit_code)
            return _executed_result(
                artifact=artifact,
                repo=repo,
                spec=spec,
                status=status,
                started_at=started_at,
                ended_at=_now(),
                command=command,
                cwd=cwd,
                exit_code=backend_result.exit_code,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                message=message,
                backend=self.backend,
            )

    def _specs_for(self, artifact: BaseArtifact) -> tuple[LeanLibraryRefSpec, ...]:
        specs: list[LeanLibraryRefSpec] = []
        for index, ref in enumerate(artifact.formalizations):
            if not _is_checkable_ref(ref):
                continue
            specs.append(
                LeanLibraryRefSpec(
                    formalization_id=ref.id,
                    library=ref.library,
                    library_ref=ref.library_ref,
                    import_path=ref.import_path,
                    symbol=ref.symbol,
                    status=ref.status,
                    timeout_seconds=self.timeout_seconds,
                    index=index,
                )
            )
        return tuple(specs)


def _is_checkable_ref(ref: FormalizationRef) -> bool:
    return (
        ref.system == "lean4"
        and ref.check_mode == "external_library_ref"
        and ref.status in CHECKABLE_FORMALIZATION_STATUSES
    )


def _validate_spec_lines(spec: LeanLibraryRefSpec) -> str | None:
    for field_name, value in (
        ("import_path", spec.import_path),
        ("symbol", spec.symbol),
    ):
        if "\n" in value or "\r" in value:
            return (
                f"{field_name} for {spec.formalization_id} must fit on one "
                "Lean command line; alignment not checked."
            )
        if not value.strip():
            return (
                f"{field_name} for {spec.formalization_id} must not be empty; "
                "alignment not checked."
            )
    return None


def _lean_source(spec: LeanLibraryRefSpec) -> str:
    return f"import {spec.import_path}\n#check {spec.symbol}\n"


def _status_and_message(
    spec: LeanLibraryRefSpec,
    exit_code: int | None,
) -> tuple[VerificationStatus, str]:
    if exit_code == 0:
        return (
            VerificationStatus.PASS,
            (
                "Lean external library reference checked: "
                f"{spec.formalization_id}; alignment not checked."
            ),
        )
    if exit_code is None:
        return (
            VerificationStatus.ERROR,
            (
                "Lean external library reference backend did not report an "
                f"exit code for {spec.formalization_id}; alignment not checked."
            ),
        )
    return (
        VerificationStatus.FAIL,
        (
            "Lean external library reference backend returned nonzero exit "
            f"code {exit_code} for {spec.formalization_id}; alignment not checked."
        ),
    )


def _log_paths(repo: RepoContext, artifact_id: str, index: int) -> tuple[Path, Path]:
    log_dir = repo.resolve(".cosheaf/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_safe_name(artifact_id)}-lean-library-ref-{index}"
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


def _executed_result(
    *,
    artifact: BaseArtifact,
    repo: RepoContext,
    spec: LeanLibraryRefSpec,
    status: VerificationStatus,
    started_at: datetime,
    ended_at: datetime,
    command: tuple[str, ...],
    cwd: Path,
    exit_code: int | None,
    stdout_path: Path,
    stderr_path: Path,
    message: str,
    backend: LeanLibraryRefBackend,
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
        cwd=str(cwd),
        exit_code=exit_code,
        stdout_path=stdout_relative,
        stderr_path=stderr_relative,
        evidence_paths=(spec.label,),
        timeout_seconds=spec.timeout_seconds,
        input_paths=(spec.label,),
        output_paths=(stderr_relative, stdout_relative),
        tool_name=backend.name,
        tool_version=backend.version(),
        environment=_environment(spec, backend.name),
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
    cwd: str | None,
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
        verifier=LeanLibraryRefAdapter.name,
        artifact_id=artifact.id,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        cwd=cwd,
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


def _environment(spec: LeanLibraryRefSpec, backend_name: str) -> str:
    return (
        f"backend={backend_name}; library={spec.library}; "
        f"library_ref={spec.library_ref}; import_path={spec.import_path}; "
        f"symbol={spec.symbol}; alignment=not_checked"
    )


def _repo_relative(repo: RepoContext, path: Path) -> str:
    return path.relative_to(repo.repo_root).as_posix()


def _now() -> datetime:
    return datetime.now(UTC)
