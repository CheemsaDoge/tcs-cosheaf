"""Public memory/retrieval model and deterministic search surface.

The Phase 3 memory package contains typed request/result/card models, a
YAML-metadata card builder, and bounded deterministic text search over cards.
It does not implement embeddings, graph ranking execution, sidecar writers, or
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
from cosheaf.memory.search import MemorySearchError, search_artifact_cards

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
    "MemorySearchError",
    "artifact_card_from_loaded_record",
    "build_artifact_cards",
    "search_artifact_cards",
]
