"""Artifact type and status vocabulary."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath


class ArtifactType(StrEnum):
    """Supported artifact type names."""

    DEFINITION = "definition"
    CLAIM = "claim"
    THEOREM = "theorem"
    CONJECTURE = "conjecture"
    PROOF = "proof"
    PROOF_ATTEMPT = "proof_attempt"
    CONSTRUCTION = "construction"
    ALGORITHM = "algorithm"
    REDUCTION = "reduction"
    COUNTEREXAMPLE = "counterexample"
    EXPERIMENT = "experiment"
    REVIEW = "review"
    VERIFIER = "verifier"
    ISSUE = "issue"


class ArtifactStatus(StrEnum):
    """Supported artifact lifecycle states."""

    RAW = "raw"
    DRAFT = "draft"
    LOCALLY_TESTED = "locally_tested"
    ADVERSARIALLY_TESTED = "adversarially_tested"
    MACHINE_CHECKED = "machine_checked"
    HUMAN_REVIEWED = "human_reviewed"
    ACCEPTED = "accepted"
    REFUTED = "refuted"
    OBSOLETE = "obsolete"
    SUPERSEDED = "superseded"


TERMINAL_STATUSES = frozenset(
    {
        ArtifactStatus.ACCEPTED,
        ArtifactStatus.REFUTED,
        ArtifactStatus.OBSOLETE,
        ArtifactStatus.SUPERSEDED,
    }
)

PREACCEPTED_STATUSES = frozenset(
    {
        ArtifactStatus.RAW,
        ArtifactStatus.DRAFT,
        ArtifactStatus.LOCALLY_TESTED,
        ArtifactStatus.ADVERSARIALLY_TESTED,
        ArtifactStatus.MACHINE_CHECKED,
        ArtifactStatus.HUMAN_REVIEWED,
    }
)


def is_terminal_status(status: ArtifactStatus) -> bool:
    """Return whether a status is terminal in the current lifecycle."""
    return status in TERMINAL_STATUSES


def is_preaccepted_status(status: ArtifactStatus) -> bool:
    """Return whether a status is pre-accepted and still under development."""
    return status in PREACCEPTED_STATUSES


def is_accepted_status(status: ArtifactStatus) -> bool:
    """Return whether a status is accepted."""
    return status is ArtifactStatus.ACCEPTED


def expected_status_for_path(path: str) -> frozenset[ArtifactStatus]:
    """Return the statuses allowed by a repository-relative artifact path.

    This is a pure path-classification helper. It does not scan the repository
    and does not check whether the path exists.
    """
    normalized = PurePosixPath(PureWindowsPath(path).as_posix())
    parts = normalized.parts

    if len(parts) >= 2 and parts[:2] == ("kb", "accepted"):
        return frozenset({ArtifactStatus.ACCEPTED})
    if len(parts) >= 2 and parts[:2] == ("kb", "draft"):
        return frozenset(
            status for status in ArtifactStatus if status is not ArtifactStatus.ACCEPTED
        )
    if len(parts) >= 2 and parts[:2] == ("kb", "refuted"):
        return frozenset({ArtifactStatus.REFUTED})
    if len(parts) >= 2 and parts[:2] == ("kb", "obsolete"):
        return frozenset({ArtifactStatus.OBSOLETE, ArtifactStatus.SUPERSEDED})

    return frozenset(ArtifactStatus)
