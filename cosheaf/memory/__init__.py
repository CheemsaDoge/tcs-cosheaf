"""Public memory/retrieval model surface.

The Phase 3 memory package currently contains typed request/result/card models
only. It does not implement retrieval, ranking execution, sidecar writers, or
agent runtime behavior.
"""

from __future__ import annotations

from cosheaf.memory.cards import (
    DEFAULT_CARD_SCOPES,
    MemoryCardError,
    artifact_card_from_loaded_record,
    build_artifact_cards,
)
from cosheaf.memory.models import (
    ArtifactCard,
    ArtifactCardStatus,
    ArtifactCardType,
    FullArtifactPull,
    MemoryRootScope,
    RetrievalAudit,
    RetrievalExclusion,
    RetrievalRequest,
    RetrievalResult,
    RetrievalRole,
    RetrievedArtifactCard,
    ScoreBreakdown,
)

__all__ = [
    "DEFAULT_CARD_SCOPES",
    "ArtifactCard",
    "ArtifactCardStatus",
    "ArtifactCardType",
    "FullArtifactPull",
    "MemoryRootScope",
    "RetrievalAudit",
    "RetrievalExclusion",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalRole",
    "RetrievedArtifactCard",
    "ScoreBreakdown",
    "MemoryCardError",
    "artifact_card_from_loaded_record",
    "build_artifact_cards",
]
