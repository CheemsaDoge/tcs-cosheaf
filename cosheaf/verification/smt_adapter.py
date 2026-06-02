"""SMT verifier skeleton adapter."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

SMT_EVIDENCE_KINDS = frozenset({"smt", "smt_solver", "smt_checker"})


class SmtAdapter:
    """Optional SMT solver verifier skeleton."""

    name = "smt"

    def __init__(self, solver_command: str = "z3") -> None:
        self.solver_command = solver_command

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether the artifact has SMT evidence."""
        return bool(_evidence_paths(artifact))

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Return a skipped skeleton result when SMT verification is unavailable."""
        started_at = _now()
        evidence_paths = _evidence_paths(artifact)
        if not evidence_paths:
            return _skipped_result(
                artifact=artifact,
                started_at=started_at,
                ended_at=_now(),
                command=None,
                cwd=None,
                evidence_paths=(),
                message="No SMT evidence found.",
            )

        command = (self.solver_command,)
        cwd = str(repo.repo_root)
        if shutil.which(self.solver_command) is None:
            return _skipped_result(
                artifact=artifact,
                started_at=started_at,
                ended_at=_now(),
                command=command,
                cwd=cwd,
                evidence_paths=evidence_paths,
                message=f"SMT solver is not available: {self.solver_command}",
            )

        # TODO: Invoke the configured SMT solver against SMT-LIB evidence and
        # parse solver output into pass/fail/error results.
        return _skipped_result(
            artifact=artifact,
            started_at=started_at,
            ended_at=_now(),
            command=command,
            cwd=cwd,
            evidence_paths=evidence_paths,
            message="SMT verifier skeleton is registered but not implemented yet.",
        )


def _evidence_paths(artifact: BaseArtifact) -> tuple[str, ...]:
    paths = [
        evidence.path
        for evidence in artifact.evidence
        if evidence.kind in SMT_EVIDENCE_KINDS
    ]
    return tuple(sorted(paths))


def _skipped_result(
    *,
    artifact: BaseArtifact,
    started_at: datetime,
    ended_at: datetime,
    command: tuple[str, ...] | None,
    cwd: str | None,
    evidence_paths: tuple[str, ...],
    message: str,
) -> VerificationResult:
    return VerificationResult(
        verifier=SmtAdapter.name,
        artifact_id=artifact.id,
        status=VerificationStatus.SKIPPED,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        cwd=cwd,
        exit_code=None,
        stdout_path=None,
        stderr_path=None,
        evidence_paths=evidence_paths,
        input_paths=evidence_paths,
        tool_name=SmtAdapter.name,
        tool_version=None,
        message=message,
    )


def _now() -> datetime:
    return datetime.now(UTC)
