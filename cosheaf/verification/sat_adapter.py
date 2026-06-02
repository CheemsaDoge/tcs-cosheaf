"""SAT verifier skeleton adapter."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

SAT_EVIDENCE_KINDS = frozenset({"sat", "sat_solver", "sat_checker"})


class SatAdapter:
    """Optional SAT solver verifier skeleton."""

    name = "sat"

    def __init__(self, solver_command: str = "kissat") -> None:
        self.solver_command = solver_command

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether the artifact has SAT evidence."""
        return bool(_evidence_paths(artifact))

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Return a skipped skeleton result when SAT verification is unavailable."""
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
                message="No SAT evidence found.",
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
                message=f"SAT solver is not available: {self.solver_command}",
            )

        # TODO: Invoke the configured SAT solver against CNF evidence and parse
        # solver output into pass/fail/error results.
        return _skipped_result(
            artifact=artifact,
            started_at=started_at,
            ended_at=_now(),
            command=command,
            cwd=cwd,
            evidence_paths=evidence_paths,
            message="SAT verifier skeleton is registered but not implemented yet.",
        )


def _evidence_paths(artifact: BaseArtifact) -> tuple[str, ...]:
    paths = [
        evidence.path
        for evidence in artifact.evidence
        if evidence.kind in SAT_EVIDENCE_KINDS
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
        verifier=SatAdapter.name,
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
        message=message,
    )


def _now() -> datetime:
    return datetime.now(UTC)
