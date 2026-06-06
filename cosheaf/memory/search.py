"""Deterministic artifact-card text retrieval."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cosheaf.memory.cards import MemoryCardError, build_artifact_cards
from cosheaf.memory.models import (
    ArtifactCard,
    ArtifactCardStatus,
    MemoryRootScope,
    RetrievalAudit,
    RetrievalExclusion,
    RetrievalRequest,
    RetrievalResult,
    RetrievedArtifactCard,
    ScoreBreakdown,
)
from cosheaf.storage.repo import RepoContext

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
DEFAULT_SEARCH_STATUSES = (
    ArtifactCardStatus.ACCEPTED,
    ArtifactCardStatus.HUMAN_REVIEWED,
    ArtifactCardStatus.MACHINE_CHECKED,
    ArtifactCardStatus.LOCALLY_TESTED,
)
DEFAULT_SEARCH_SCOPES = (
    MemoryRootScope.PUBLIC,
    MemoryRootScope.WORKSPACE,
    MemoryRootScope.FRAMEWORK,
)
ISSUE_SCOPED_EXTRA_STATUSES = (ArtifactCardStatus.DRAFT,)
DETERMINISTIC_GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)
ALL_SEARCH_SCOPES = (
    MemoryRootScope.PUBLIC,
    MemoryRootScope.PRIVATE,
    MemoryRootScope.WORKSPACE,
    MemoryRootScope.FRAMEWORK,
)


class MemorySearchError(ValueError):
    """Raised for expected memory-search failures."""


@dataclass(frozen=True)
class _ScoredCard:
    card: ArtifactCard
    lexical_score: float
    fts_score: float
    why_relevant: tuple[str, ...]


def search_artifact_cards(
    context: RepoContext,
    *,
    query: str,
    issue_id: str | None = None,
    status: ArtifactCardStatus | str | None = None,
    max_cards: int = 20,
    allowed_scopes: tuple[MemoryRootScope, ...] | None = None,
) -> RetrievalResult:
    """Return deterministic artifact-card search results.

    The search reads current YAML-derived artifact cards, uses an in-memory
    SQLite FTS5/BM25 table when available, and falls back to deterministic
    lexical scoring when FTS5 is not available. It does not write sidecars,
    rebuild indexes, inspect full artifact statements, or modify repository
    records.
    """
    scopes = tuple(allowed_scopes or DEFAULT_SEARCH_SCOPES)
    statuses = _allowed_statuses(status=status, issue_id=issue_id)
    try:
        request = RetrievalRequest(
            query=query,
            issue_id=issue_id,
            allowed_scopes=list(scopes),
            allowed_statuses=list(statuses),
            max_cards=max_cards,
        )
        issue_cards = tuple(
            build_artifact_cards(
                context,
                issue_id=issue_id,
                allowed_scopes=ALL_SEARCH_SCOPES,
            )
            if issue_id is not None
            else build_artifact_cards(
                context,
                allowed_scopes=ALL_SEARCH_SCOPES,
            )
        )
        cards, audit_exclusions, private_scope_exclusion_count = _filter_cards(
            issue_cards,
            allowed_scopes=scopes,
            allowed_statuses=statuses,
        )
    except (MemoryCardError, ValueError) as exc:
        raise MemorySearchError(str(exc)) from exc

    tokens = _query_tokens(request.query)
    fts_scores, fts_warning = _fts_rank_scores(cards, tokens)
    scored_cards = tuple(
        scored
        for card in cards
        if (
            scored := _score_card(
                card,
                tokens=tokens,
                fts_score=fts_scores.get(card.id, 0.0),
                fts_used=fts_warning is None and bool(fts_scores),
            )
        )
        is not None
    )

    ordered = tuple(
        sorted(
            scored_cards,
            key=lambda scored: (
                -_total_score(scored),
                scored.card.status.value != ArtifactCardStatus.ACCEPTED.value,
                scored.card.id,
                scored.card.path,
            ),
        )[: request.max_cards]
    )

    result_cards = [
        _retrieved_card(scored)
        for scored in ordered
    ]
    warnings = [
        "formal links are metadata only; search results are not proof",
    ]
    if fts_warning is not None:
        warnings.append(fts_warning)
    if private_scope_exclusion_count:
        warnings.append(
            "private scope exclusions are withheld from audit details "
            f"({private_scope_exclusion_count} card(s))"
        )

    return RetrievalResult(
        request_id=_request_id(request, cards),
        generated_at=DETERMINISTIC_GENERATED_AT,
        index_fingerprint=_fingerprint(request, cards),
        cards=result_cards,
        audit=RetrievalAudit(
            filters_applied=[
                "scope:" + ",".join(scope.value for scope in scopes),
                "status:" + ",".join(status.value for status in statuses),
            ]
            + ([f"issue:{request.issue_id}"] if request.issue_id else []),
            excluded=audit_exclusions,
            warnings=warnings,
        ),
    )


def _filter_cards(
    cards: tuple[ArtifactCard, ...],
    *,
    allowed_scopes: tuple[MemoryRootScope, ...],
    allowed_statuses: tuple[ArtifactCardStatus, ...],
) -> tuple[tuple[ArtifactCard, ...], list[RetrievalExclusion], int]:
    included: list[ArtifactCard] = []
    excluded: list[RetrievalExclusion] = []
    private_scope_exclusion_count = 0
    allowed_scope_values = ",".join(scope.value for scope in allowed_scopes)
    allowed_status_values = ",".join(status.value for status in allowed_statuses)

    for card in cards:
        if card.root_scope not in allowed_scopes:
            if card.root_scope is MemoryRootScope.PRIVATE:
                private_scope_exclusion_count += 1
            else:
                excluded.append(
                    RetrievalExclusion(
                        artifact_id=card.id,
                        reason=(
                            f"scope excluded: {card.root_scope.value} "
                            f"not in {allowed_scope_values}"
                        ),
                    )
                )
            continue
        if card.status not in allowed_statuses:
            excluded.append(
                RetrievalExclusion(
                    artifact_id=card.id,
                    reason=(
                        f"status excluded: {card.status.value} "
                        f"not in {allowed_status_values}"
                    ),
                )
            )
            continue
        included.append(card)

    return (
        tuple(sorted(included, key=lambda card: (card.id, card.path))),
        sorted(excluded, key=lambda item: (item.artifact_id, item.reason)),
        private_scope_exclusion_count,
    )


def _allowed_statuses(
    *,
    status: ArtifactCardStatus | str | None,
    issue_id: str | None,
) -> tuple[ArtifactCardStatus, ...]:
    if status is not None:
        return (ArtifactCardStatus(status),)
    statuses = list(DEFAULT_SEARCH_STATUSES)
    if issue_id is not None:
        statuses.extend(ISSUE_SCOPED_EXTRA_STATUSES)
    return tuple(statuses)


def _query_tokens(query: str) -> tuple[str, ...]:
    tokens = tuple(dict.fromkeys(TOKEN_PATTERN.findall(query.lower())))
    if not tokens:
        raise MemorySearchError("query must contain at least one searchable token")
    return tokens


def _score_card(
    card: ArtifactCard,
    *,
    tokens: tuple[str, ...],
    fts_score: float,
    fts_used: bool,
) -> _ScoredCard | None:
    lexical_score, lexical_reasons = _lexical_score(card, tokens)
    retrieval_score = max(lexical_score, fts_score)
    if retrieval_score <= 0:
        return None

    reasons = list(lexical_reasons)
    if fts_used and fts_score > 0:
        reasons.append(f"SQLite FTS/BM25 rank score {fts_score:.3f}")

    updated_card = card.model_copy(
        update={
            "retrieval_score": round(retrieval_score, 6),
            "why_relevant": "; ".join(reasons),
        }
    )
    return _ScoredCard(
        card=updated_card,
        lexical_score=lexical_score,
        fts_score=fts_score,
        why_relevant=tuple(reasons),
    )


def _lexical_score(
    card: ArtifactCard,
    tokens: tuple[str, ...],
) -> tuple[float, tuple[str, ...]]:
    weighted_text = {
        "title": _token_set(card.title),
        "id": _token_set(card.id),
        "domain": _token_set(" ".join(card.domain)),
        "tags": _token_set(" ".join(card.tags)),
        "summary": _token_set(card.summary),
        "dependencies": _token_set(" ".join(card.depends_on)),
        "sources": _token_set(" ".join(card.sources)),
    }
    weights = {
        "title": 4.0,
        "id": 2.0,
        "domain": 2.0,
        "tags": 2.0,
        "summary": 1.0,
        "dependencies": 0.75,
        "sources": 0.5,
    }
    matched_fields: list[str] = []
    raw = 0.0
    for field, field_tokens in weighted_text.items():
        matches = [token for token in tokens if token in field_tokens]
        if not matches:
            continue
        raw += weights[field] * len(matches)
        matched_fields.append(f"{field}:{','.join(matches)}")

    if raw <= 0:
        return 0.0, ()
    max_raw = sum(weights.values()) * len(tokens)
    score = min(raw / max_raw, 1.0)
    return round(score, 6), tuple(f"lexical match {field}" for field in matched_fields)


def _fts_rank_scores(
    cards: tuple[ArtifactCard, ...],
    tokens: tuple[str, ...],
) -> tuple[dict[str, float], str | None]:
    if not cards:
        return {}, None
    try:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute(
                "CREATE VIRTUAL TABLE cards_fts USING fts5(id UNINDEXED, text)"
            )
            connection.executemany(
                "INSERT INTO cards_fts (id, text) VALUES (?, ?)",
                [(card.id, _search_text(card)) for card in cards],
            )
            rows = connection.execute(
                """
                SELECT id, bm25(cards_fts) AS rank
                FROM cards_fts
                WHERE cards_fts MATCH ?
                ORDER BY rank ASC, id ASC
                """,
                (" ".join(tokens),),
            ).fetchall()
    except sqlite3.DatabaseError as exc:
        return {}, f"SQLite FTS/BM25 unavailable; lexical fallback used: {exc}"

    total = len(rows)
    if total == 0:
        return {}, None
    return {
        str(row[0]): round((total - index) / total, 6)
        for index, row in enumerate(rows)
    }, None


def _retrieved_card(scored: _ScoredCard) -> RetrievedArtifactCard:
    retrieval_hybrid = round(max(scored.lexical_score, scored.fts_score), 6)
    quality_prior = round(scored.card.trust_score, 6)
    total = _combined_score(
        retrieval_hybrid=retrieval_hybrid,
        quality_prior=quality_prior,
    )
    return RetrievedArtifactCard(
        card=scored.card.model_copy(update={"retrieval_score": total}),
        score_breakdown=ScoreBreakdown(
            retrieval_hybrid=retrieval_hybrid,
            quality_prior=quality_prior,
            total=total,
        ),
        why_relevant=list(scored.why_relevant),
    )


def _total_score(scored: _ScoredCard) -> float:
    retrieval_hybrid = max(scored.lexical_score, scored.fts_score)
    return _combined_score(
        retrieval_hybrid=retrieval_hybrid,
        quality_prior=scored.card.trust_score,
    )


def _combined_score(*, retrieval_hybrid: float, quality_prior: float) -> float:
    return round((0.50 * retrieval_hybrid) + (0.10 * quality_prior), 6)


def _token_set(text: str) -> frozenset[str]:
    return frozenset(TOKEN_PATTERN.findall(text.lower()))


def _search_text(card: ArtifactCard) -> str:
    return " ".join(
        [
            card.id,
            card.title,
            " ".join(card.domain),
            " ".join(card.tags),
            card.summary,
            " ".join(card.depends_on),
            " ".join(card.sources),
        ]
    )


def _fingerprint(request: RetrievalRequest, cards: tuple[ArtifactCard, ...]) -> str:
    payload: dict[str, Any] = {
        "request": request.to_dict(),
        "cards": [card.to_dict() for card in sorted(cards, key=lambda card: card.id)],
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def _request_id(request: RetrievalRequest, cards: tuple[ArtifactCard, ...]) -> str:
    digest = _fingerprint(request, cards).removeprefix("sha256:")
    return f"retrieval.memory.search.q{digest[:12]}"
