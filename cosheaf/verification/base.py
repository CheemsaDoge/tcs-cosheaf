"""Verifier adapter protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult


@runtime_checkable
class VerifierAdapter(Protocol):
    """Protocol implemented by verification adapters."""

    name: str

    def can_verify(self, artifact: BaseArtifact, repo: RepoContext) -> bool:
        """Return whether this adapter can verify an artifact."""
        ...

    def verify(self, artifact: BaseArtifact, repo: RepoContext) -> VerificationResult:
        """Run verification and return a normalized result."""
        ...
