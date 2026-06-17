"""Deterministic librarian: policy-scored retrieval engine.

Provides deterministic artifact ranking, bounded context selection,
and memory temperature partitioning for the orchestrator and research loop.
Never creates claims, accepted knowledge, or truth judgments.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

LIBRARIAN_AUTHORITY_NOTICE = (
    "Librarian results are retrieval context only; they are not proof, "
    "verifier pass, gate pass, human review, accepted status, or promotion "
    "authority. Ranking scores are advisory, not truth judgments."
)

MemoryTemperature = Literal["hot", "warm", "cold"]


class LibrarianCandidate(BaseModel):
    artifact_id: str
    status: str
    type: str
    title: str = ""
    statement: str = ""
    score: float = 0.0
    text_retrieval_score: float = 0.0
    issue_graph_score: float = 0.0
    artifact_graph_prior: float = 0.0
    quality_prior: float = 0.0
    freshness: float = 0.0
    penalty: float = 0.0
    temperature: MemoryTemperature = "cold"
    explanation: str = ""


class LibrarianResult(BaseModel):
    query_id: str
    query_text: str = ""
    issue_id: str = ""
    candidates: list[LibrarianCandidate] = Field(default_factory=list)
    total_candidates: int = 0
    authority_notice: str = LIBRARIAN_AUTHORITY_NOTICE
    created_at: str = ""


class LibrarianTrace(BaseModel):
    query_id: str
    score_components: list[dict[str, Any]] = Field(default_factory=list)
    policy_findings: list[str] = Field(default_factory=list)
    filtered_out: list[str] = Field(default_factory=list)
    authority_notice: str = LIBRARIAN_AUTHORITY_NOTICE


def _compute_text_score(artifact: dict, query: str) -> float:
    """Simple BM25-like text matching score."""
    if not query:
        return 0.0
    query_lower = query.lower()
    fields = " ".join(
        artifact.get(k, "")
        for k in ("title", "statement", "description")
        if isinstance(artifact.get(k), str)
    ).lower()
    if not fields:
        return 0.0
    terms = query_lower.split()
    matches = sum(1 for t in terms if t in fields)
    return min(1.0, matches / max(len(terms), 1))


def _compute_freshness(artifact: dict) -> float:
    """Score based on recency of updates."""
    updated_value = artifact.get("updated_at", "")
    if not isinstance(updated_value, str) or not updated_value:
        return 0.0
    try:
        dt = datetime.fromisoformat(updated_value.replace("Z", "+00:00"))
        delta_days = (datetime.now(UTC) - dt).days
        return math.pow(0.5, max(delta_days, 0) / 30.0)
    except (ValueError, TypeError):
        return 0.0


def _quality_prior_for_status(status: str) -> float:
    mapping: dict[str, float] = {
        "accepted": 1.0,
        "preaccepted": 0.6,
        "draft": 0.3,
        "refuted": -0.5,
        "obsolete": -0.3,
        "superseded": -0.2,
    }
    return mapping.get(status, 0.0)


def rank(
    artifacts: Sequence[dict[str, Any]],
    query: str = "",
    issue_id: str = "",
    *,
    mode: str = "private_research",
    max_hot: int = 10,
) -> LibrarianResult:
    """Deterministic ranking of artifacts by retrieval policy."""
    query_id = f"lib-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    candidates: list[LibrarianCandidate] = []

    for art in artifacts:
        art_id = art.get("id", "")
        status = art.get("status", "draft")
        if mode == "public_only" and status not in ("accepted", "preaccepted"):
            continue

        text_score = _compute_text_score(art, query)
        freshness = _compute_freshness(art)
        quality_prior = _quality_prior_for_status(status)
        penalty = 0.0

        # Penalize refuted/obsolete unless query asks for them
        if status in ("refuted", "obsolete") and "counterexample" not in query.lower():
            penalty += 0.3

        score = (
            0.50 * text_score
            + 0.15 * quality_prior
            + 0.10 * 0.0  # issue_graph_score placeholder
            + 0.20 * 0.0  # artifact_graph_prior placeholder
            + 0.05 * freshness
            - penalty
        )
        score = max(0.0, min(1.0, score))

        temperature: MemoryTemperature = "cold"
        if status == "accepted" and score >= 0.45:
            temperature = "hot"
        elif status == "refuted" or status == "obsolete":
            temperature = "cold"
        elif score >= 0.30:
            temperature = "warm"

        candidates.append(
            LibrarianCandidate(
                artifact_id=art_id,
                status=status,
                type=art.get("type", ""),
                title=art.get("title", ""),
                statement=art.get("statement", "")[:200],
                score=round(score, 4),
                text_retrieval_score=round(text_score, 4),
                issue_graph_score=0.0,
                artifact_graph_prior=0.0,
                quality_prior=round(quality_prior, 4),
                freshness=round(freshness, 4),
                penalty=round(penalty, 4),
                temperature=temperature,
                explanation=(
                    f"text={text_score:.3f} qual={quality_prior:.3f} "
                    f"fresh={freshness:.3f} penalty={penalty:.3f}"
                ),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    hot = [c for c in candidates if c.temperature == "hot"][:max_hot]

    return LibrarianResult(
        query_id=query_id,
        query_text=query,
        issue_id=issue_id,
        candidates=hot,
        total_candidates=len(candidates),
        created_at=datetime.now(UTC).isoformat(),
    )


def compute_trace(result: LibrarianResult) -> LibrarianTrace:
    components = []
    for c in result.candidates:
        components.append(
            {
                "artifact_id": c.artifact_id,
                "score": c.score,
                "text": c.text_retrieval_score,
                "quality": c.quality_prior,
                "freshness": c.freshness,
                "penalty": c.penalty,
                "temperature": c.temperature,
            }
        )
    return LibrarianTrace(query_id=result.query_id, score_components=components)
