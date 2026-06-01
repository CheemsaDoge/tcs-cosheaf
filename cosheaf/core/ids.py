"""Artifact ID validation helpers."""

from __future__ import annotations

import re

from cosheaf.core.errors import ArtifactIdError

ARTIFACT_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\.[a-z][a-z0-9]*(?:-[a-z0-9]+)*)+$"
)


def validate_artifact_id(value: str) -> str:
    """Validate and return a globally scoped artifact ID string."""
    if not ARTIFACT_ID_PATTERN.fullmatch(value):
        raise ArtifactIdError(
            "artifact ID must be dot-separated lowercase slugs, "
            "for example 'claim.example.complete-graph-edge-count'"
        )
    return value
