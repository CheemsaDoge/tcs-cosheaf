"""Artifact ID validation helpers."""

from __future__ import annotations

import re

from cosheaf.core.errors import ArtifactIdError

SLUG_SEGMENT = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
NUMBER_SEGMENT = r"[0-9]+"
ARTIFACT_ID_PATTERN = re.compile(
    rf"^{SLUG_SEGMENT}(?:\.(?:{SLUG_SEGMENT}|{NUMBER_SEGMENT}))+$"
)


def validate_artifact_id(value: str) -> str:
    """Validate and return a globally scoped artifact ID string."""
    if not ARTIFACT_ID_PATTERN.fullmatch(value):
        raise ArtifactIdError(
            "artifact ID must be dot-separated lowercase slugs, "
            "with optional numeric version segments, for example "
            "'claim.example.complete-graph-edge-count' or 'issue.topic.0001'"
        )
    return value
