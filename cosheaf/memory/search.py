"""Deterministic artifact-card text retrieval."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cosheaf.memory.cards import MemoryCardError, build_artifact_cards
from cosheaf.memory.graph import (
    MemoryGraphEdge,
    MemoryGraphNode,
    MemoryGraphSnapshot,
    build_memory_graph,
    compute_global_pagerank,
)
from cosheaf.memory.models import (
    ArtifactCard,
    ArtifactCardStatus,
    MemoryRootScope,
    RetrievalAudit,
    RetrievalExclusion,
    RetrievalRequest,
    RetrievalResult,
    RetrievalRole,
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
    personalized_pagerank: float
    global_pagerank: float
    freshness: float
    penalty: float
    why_relevant: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalScoreWeights:
    """Configurable weights for deterministic memory search scoring."""

    retrieval_hybrid: float = 0.50
    personalized_pagerank: float = 0.20
    global_pagerank: float = 0.15
    quality_prior: float = 0.10
    freshness: float = 0.05

    def __post_init__(self) -> None:
        """Validate non-negative finite formula weights."""
        for field_name, value in self.__dict__.items():
            if not math.isfinite(value):
                raise ValueError(f"{field_name} weight must be finite")
            if value < 0:
                raise ValueError(f"{field_name} weight must be non-negative")


def search_artifact_cards(
    context: RepoContext,
    *,
    query: str,
    issue_id: str | None = None,
    status: ArtifactCardStatus | str | None = None,
    max_cards: int = 20,
    allowed_scopes: tuple[MemoryRootScope, ...] | None = None,
    seed_artifacts: tuple[str, ...] = (),
    pinned_artifacts: tuple[str, ...] = (),
    include_refuted: bool = False,
    include_obsolete: bool = False,
    role: RetrievalRole | str = RetrievalRole.LIBRARIAN,
    max_full_artifacts: int = 0,
    score_weights: RetrievalScoreWeights = RetrievalScoreWeights(),
) -> RetrievalResult:
    """Return deterministic artifact-card search results.

    The search reads current YAML-derived artifact cards, uses an in-memory
    SQLite FTS5/BM25 table when available, falls back to deterministic
    lexical scoring when FTS5 is not available, and blends optional
    issue-conditioned graph signals into the documented ranking formula.
    It does not write sidecars, rebuild indexes, inspect full artifact
    statements, or modify repository records.
    """
    scopes = tuple(allowed_scopes or DEFAULT_SEARCH_SCOPES)
    statuses = _allowed_statuses(
        status=status,
        issue_id=issue_id,
        include_refuted=include_refuted,
        include_obsolete=include_obsolete,
    )
    try:
        request = RetrievalRequest(
            query=query,
            issue_id=issue_id,
            seed_artifacts=list(seed_artifacts),
            pinned_artifacts=list(pinned_artifacts),
            allowed_scopes=list(scopes),
            allowed_statuses=list(statuses),
            include_refuted=include_refuted,
            include_obsolete=include_obsolete,
            max_cards=max_cards,
            max_full_artifacts=max_full_artifacts,
            role=RetrievalRole(role),
        )
        issue_seed_cards = tuple(
            build_artifact_cards(
                context,
                issue_id=issue_id,
                allowed_scopes=ALL_SEARCH_SCOPES,
            )
            if issue_id is not None
            else ()
        )
        all_cards = tuple(
            build_artifact_cards(
                context,
                allowed_scopes=ALL_SEARCH_SCOPES,
            )
        )
        cards, audit_exclusions, private_scope_exclusion_count = _filter_cards(
            all_cards,
            allowed_scopes=scopes,
            allowed_statuses=statuses,
        )
    except (MemoryCardError, ValueError) as exc:
        raise MemorySearchError(str(exc)) from exc

    tokens = _query_tokens(request.query)
    fts_scores, fts_warning = _fts_rank_scores(cards, tokens)
    visible_artifact_ids = tuple(card.id for card in cards)
    graph = _policy_visible_graph(
        build_memory_graph(context, persist=False),
        visible_artifact_ids=visible_artifact_ids,
        issue_id=request.issue_id,
    )
    graph_signals = _graph_ranking_signals(
        graph,
        issue_id=request.issue_id,
        issue_seed_artifacts=tuple(card.id for card in issue_seed_cards),
        seed_artifacts=tuple(request.seed_artifacts),
        pinned_artifacts=tuple(request.pinned_artifacts),
        visible_artifact_ids=visible_artifact_ids,
    )
    scored_cards = tuple(
        scored
        for card in cards
        if (
            scored := _score_card(
                card,
                tokens=tokens,
                fts_score=fts_scores.get(card.id, 0.0),
                fts_used=fts_warning is None and bool(fts_scores),
                personalized_pagerank=graph_signals.personalized_pagerank.get(
                    card.id,
                    0.0,
                ),
                global_pagerank=graph_signals.global_pagerank.get(card.id, 0.0),
                freshness=graph_signals.freshness.get(card.id, 0.0),
                score_weights=score_weights,
            )
        )
        is not None
    )

    ordered = tuple(
        sorted(
            scored_cards,
            key=lambda scored: (
                -_total_score(scored, score_weights=score_weights),
                scored.card.status.value != ArtifactCardStatus.ACCEPTED.value,
                scored.card.id,
                scored.card.path,
            ),
        )[: request.max_cards]
    )

    result_cards = [
        _retrieved_card(scored, score_weights=score_weights)
        for scored in ordered
    ]
    warnings = [
        "formal links are metadata only; search results are not proof",
    ]
    if any(hit.card.failure_count for hit in result_cards):
        warnings.append(
            "failure memory is not proof, verifier success, human review, "
            "checked counterexample evidence, or accepted-status evidence"
        )
    if fts_warning is not None:
        warnings.append(fts_warning)
    warnings.extend(graph_signals.warnings)
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
    include_refuted: bool,
    include_obsolete: bool,
) -> tuple[ArtifactCardStatus, ...]:
    if status is not None:
        return (ArtifactCardStatus(status),)
    statuses = list(DEFAULT_SEARCH_STATUSES)
    if issue_id is not None:
        statuses.extend(ISSUE_SCOPED_EXTRA_STATUSES)
    if include_refuted:
        statuses.append(ArtifactCardStatus.REFUTED)
    if include_obsolete:
        statuses.extend(
            [
                ArtifactCardStatus.OBSOLETE,
                ArtifactCardStatus.SUPERSEDED,
            ]
        )
    return tuple(dict.fromkeys(statuses))


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
    personalized_pagerank: float,
    global_pagerank: float,
    freshness: float,
    score_weights: RetrievalScoreWeights,
) -> _ScoredCard | None:
    lexical_score, lexical_reasons = _lexical_score(card, tokens)
    retrieval_score = max(lexical_score, fts_score)
    if retrieval_score <= 0 and personalized_pagerank <= 0 and freshness <= 0:
        return None

    reasons = list(lexical_reasons)
    if fts_used and fts_score > 0:
        reasons.append(f"SQLite FTS/BM25 rank score {fts_score:.3f}")
    if personalized_pagerank > 0:
        reasons.append(
            "personalized PageRank score "
            f"{personalized_pagerank:.3f} from issue/seed context"
        )
    if global_pagerank > 0:
        reasons.append(f"global PageRank score {global_pagerank:.3f}")
    if freshness > 0:
        reasons.append(f"freshness score {freshness:.3f} from successful run context")

    penalty = _penalty(card)
    total = _combined_score(
        retrieval_hybrid=round(retrieval_score, 6),
        personalized_pagerank=round(personalized_pagerank, 6),
        global_pagerank=round(global_pagerank, 6),
        quality_prior=round(card.trust_score, 6),
        freshness=round(freshness, 6),
        penalty=penalty,
        score_weights=score_weights,
    )
    updated_card = card.model_copy(
        update={
            "retrieval_score": total,
            "why_relevant": "; ".join(reasons),
        }
    )
    return _ScoredCard(
        card=updated_card,
        lexical_score=lexical_score,
        fts_score=fts_score,
        personalized_pagerank=personalized_pagerank,
        global_pagerank=global_pagerank,
        freshness=freshness,
        penalty=penalty,
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
        "failure_memory": _token_set(" ".join(card.recent_failure_directions)),
        "dependencies": _token_set(" ".join(card.depends_on)),
        "sources": _token_set(" ".join(card.sources)),
    }
    weights = {
        "title": 4.0,
        "id": 2.0,
        "domain": 2.0,
        "tags": 2.0,
        "summary": 1.0,
        "failure_memory": 1.0,
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
    reasons = []
    for field in matched_fields:
        if field.startswith("failure_memory:"):
            matched_tokens_label = field.removeprefix("failure_memory:")
            reasons.append(f"failure memory match {matched_tokens_label}")
        else:
            reasons.append(f"lexical match {field}")
    return round(score, 6), tuple(reasons)


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


def _retrieved_card(
    scored: _ScoredCard,
    *,
    score_weights: RetrievalScoreWeights = RetrievalScoreWeights(),
) -> RetrievedArtifactCard:
    retrieval_hybrid = round(max(scored.lexical_score, scored.fts_score), 6)
    personalized_pagerank = round(scored.personalized_pagerank, 6)
    global_pagerank = round(scored.global_pagerank, 6)
    quality_prior = round(scored.card.trust_score, 6)
    freshness = round(scored.freshness, 6)
    penalty = round(scored.penalty, 6)
    total = _combined_score(
        retrieval_hybrid=retrieval_hybrid,
        personalized_pagerank=personalized_pagerank,
        global_pagerank=global_pagerank,
        quality_prior=quality_prior,
        freshness=freshness,
        penalty=penalty,
        score_weights=score_weights,
    )
    return RetrievedArtifactCard(
        card=scored.card.model_copy(update={"retrieval_score": total}),
        score_breakdown=ScoreBreakdown(
            retrieval_hybrid=retrieval_hybrid,
            personalized_pagerank=personalized_pagerank,
            global_pagerank=global_pagerank,
            quality_prior=quality_prior,
            freshness=freshness,
            penalty=penalty,
            total=total,
        ),
        why_relevant=list(scored.why_relevant),
    )


def _total_score(
    scored: _ScoredCard,
    *,
    score_weights: RetrievalScoreWeights,
) -> float:
    retrieval_hybrid = max(scored.lexical_score, scored.fts_score)
    return _combined_score(
        retrieval_hybrid=retrieval_hybrid,
        personalized_pagerank=scored.personalized_pagerank,
        global_pagerank=scored.global_pagerank,
        quality_prior=scored.card.trust_score,
        freshness=scored.freshness,
        penalty=scored.penalty,
        score_weights=score_weights,
    )


def _combined_score(
    *,
    retrieval_hybrid: float,
    personalized_pagerank: float,
    global_pagerank: float,
    quality_prior: float,
    freshness: float,
    penalty: float,
    score_weights: RetrievalScoreWeights,
) -> float:
    weighted = (
        (score_weights.retrieval_hybrid * retrieval_hybrid)
        + (score_weights.personalized_pagerank * personalized_pagerank)
        + (score_weights.global_pagerank * global_pagerank)
        + (score_weights.quality_prior * quality_prior)
        + (score_weights.freshness * freshness)
        - penalty
    )
    return round(max(weighted, 0.0), 6)


def _penalty(card: ArtifactCard) -> float:
    penalty = 0.0
    if card.root_scope is MemoryRootScope.PRIVATE:
        penalty += 0.20
    if card.status is ArtifactCardStatus.DRAFT:
        penalty += 0.12
    if card.status is ArtifactCardStatus.REFUTED:
        penalty += 0.50
    if card.status in {
        ArtifactCardStatus.OBSOLETE,
        ArtifactCardStatus.SUPERSEDED,
    }:
        penalty += 0.35
    if "verifier:fail" in card.risk_flags or "verifier:error" in card.risk_flags:
        penalty += 0.25
    return round(penalty, 6)


@dataclass(frozen=True)
class _GraphSignals:
    personalized_pagerank: dict[str, float]
    global_pagerank: dict[str, float]
    freshness: dict[str, float]
    warnings: list[str]


def _graph_ranking_signals(
    graph: MemoryGraphSnapshot,
    *,
    issue_id: str | None,
    issue_seed_artifacts: tuple[str, ...],
    seed_artifacts: tuple[str, ...],
    pinned_artifacts: tuple[str, ...],
    visible_artifact_ids: tuple[str, ...],
) -> _GraphSignals:
    global_pagerank = _artifact_pagerank_scores(
        compute_global_pagerank(graph).rows,
    )
    seed_weights, seed_warnings = _personalization_seed_weights(
        graph,
        issue_id=issue_id,
        issue_seed_artifacts=issue_seed_artifacts,
        seed_artifacts=seed_artifacts,
        pinned_artifacts=pinned_artifacts,
        visible_artifact_ids=visible_artifact_ids,
    )
    personalized = _personalized_pagerank_scores(graph, seed_weights)
    freshness = _freshness_scores(graph, issue_id=issue_id)
    warnings = [
        "memory graph scores are ranking metadata, not review or proof",
    ]
    warnings.extend(seed_warnings)
    return _GraphSignals(
        personalized_pagerank=personalized,
        global_pagerank=global_pagerank,
        freshness=freshness,
        warnings=warnings,
    )


def _artifact_pagerank_scores(rows: list[Any]) -> dict[str, float]:
    raw = {
        row.record_id: row.score
        for row in rows
        if getattr(row, "kind", None) == "artifact"
    }
    return _normalize_scores(raw)


def _personalization_seed_weights(
    graph: MemoryGraphSnapshot,
    *,
    issue_id: str | None,
    issue_seed_artifacts: tuple[str, ...],
    seed_artifacts: tuple[str, ...],
    pinned_artifacts: tuple[str, ...],
    visible_artifact_ids: tuple[str, ...],
) -> tuple[dict[str, float], list[str]]:
    known_nodes = {node.node_id for node in graph.nodes}
    visible_artifacts = set(visible_artifact_ids)
    seed_weights: dict[str, float] = {}
    warnings: list[str] = []

    def add_seed(
        node_id: str,
        weight: float,
        *,
        label: str,
        warn_missing: bool = True,
    ) -> None:
        if node_id in known_nodes:
            seed_weights[node_id] = seed_weights.get(node_id, 0.0) + weight
        elif warn_missing:
            warnings.append(f"{label} ignored because graph node is missing: {node_id}")

    def add_artifact_seed(
        artifact_id: str,
        weight: float,
        *,
        label: str,
        warn_missing: bool = True,
    ) -> None:
        if artifact_id not in visible_artifacts:
            if warn_missing:
                warnings.append(
                    f"{label} ignored because artifact is outside current "
                    f"scope/status filters: {artifact_id}"
                )
            return
        add_seed(
            _node_id("artifact", artifact_id),
            weight,
            label=label,
            warn_missing=warn_missing,
        )

    if issue_id is not None:
        add_seed(_node_id("issue", issue_id), 1.0, label="issue seed")
    for artifact_id in issue_seed_artifacts:
        add_artifact_seed(
            artifact_id,
            1.0,
            label="issue related artifact seed",
            warn_missing=False,
        )
    for artifact_id in seed_artifacts:
        add_artifact_seed(
            artifact_id,
            2.0,
            label="explicit seed artifact",
        )
    for artifact_id in pinned_artifacts:
        add_artifact_seed(
            artifact_id,
            3.0,
            label="pinned artifact",
        )
    for node in _recent_success_task_run_nodes(graph, issue_id=issue_id):
        add_seed(node.node_id, 0.75, label="successful task run seed")

    return seed_weights, sorted(set(warnings))


def _personalized_pagerank_scores(
    graph: MemoryGraphSnapshot,
    seed_weights: dict[str, float],
    *,
    damping: float = 0.85,
    max_iterations: int = 50,
    tolerance: float = 1e-12,
) -> dict[str, float]:
    if not graph.nodes or not seed_weights:
        return {}
    node_ids = tuple(sorted(node.node_id for node in graph.nodes))
    total_seed_weight = sum(seed_weights.values())
    personalization = {
        node_id: seed_weights.get(node_id, 0.0) / total_seed_weight
        for node_id in node_ids
    }
    scores = dict(personalization)
    incoming: dict[str, list[tuple[str, float]]] = {node_id: [] for node_id in node_ids}
    outgoing_weight = {node_id: 0.0 for node_id in node_ids}
    for edge in sorted(graph.edges, key=_edge_sort_key):
        if edge.source not in outgoing_weight or edge.target not in incoming:
            continue
        outgoing_weight[edge.source] += edge.weight
        incoming[edge.target].append((edge.source, edge.weight))

    for _iteration in range(max_iterations):
        sink_score = sum(
            scores[node_id]
            for node_id in node_ids
            if outgoing_weight[node_id] == 0
        )
        next_scores: dict[str, float] = {}
        delta = 0.0
        for node_id in node_ids:
            rank = (1.0 - damping) * personalization[node_id]
            rank += damping * sink_score * personalization[node_id]
            rank += damping * sum(
                scores[source] * weight / outgoing_weight[source]
                for source, weight in incoming[node_id]
                if outgoing_weight[source] > 0
            )
            next_scores[node_id] = rank
            delta += abs(rank - scores[node_id])
        scores = next_scores
        if delta <= tolerance:
            break

    node_by_id = {node.node_id: node for node in graph.nodes}
    artifact_scores = {
        node.record_id: scores[node_id]
        for node_id, node in node_by_id.items()
        if node.kind == "artifact"
    }
    return _normalize_scores(artifact_scores)


def _freshness_scores(
    graph: MemoryGraphSnapshot,
    *,
    issue_id: str | None,
) -> dict[str, float]:
    if issue_id is None:
        return {}
    successful_task_run_nodes = {
        node.node_id
        for node in _recent_success_task_run_nodes(graph, issue_id=issue_id)
    }
    if not successful_task_run_nodes:
        return {}
    artifact_node_ids = {
        edge.target
        for edge in graph.edges
        if edge.source in successful_task_run_nodes
        and edge.kind == "used_in_success"
        and edge.target.startswith("artifact:")
    }
    return {
        node.record_id: 1.0
        for node in graph.nodes
        if node.node_id in artifact_node_ids and node.kind == "artifact"
    }


def _recent_success_task_run_nodes(
    graph: MemoryGraphSnapshot,
    *,
    issue_id: str | None,
) -> tuple[MemoryGraphNode, ...]:
    if issue_id is None:
        return ()
    return tuple(
        sorted(
            (
                node
                for node in graph.nodes
                if node.kind == "task_run"
                and node.status == "completed"
                and node.metadata.get("issue_id") == issue_id
            ),
            key=lambda node: (node.path, node.record_id, node.node_id),
        )
    )


def _policy_visible_graph(
    graph: MemoryGraphSnapshot,
    *,
    visible_artifact_ids: tuple[str, ...],
    issue_id: str | None,
) -> MemoryGraphSnapshot:
    visible_artifact_nodes = {
        _node_id("artifact", artifact_id)
        for artifact_id in visible_artifact_ids
    }
    visible_nodes = set(visible_artifact_nodes)
    for node in graph.nodes:
        if node.kind == "issue":
            if issue_id is not None and node.record_id == issue_id:
                visible_nodes.add(node.node_id)
            continue
        if node.kind == "task_run":
            if issue_id is not None and node.metadata.get("issue_id") == issue_id:
                visible_nodes.add(node.node_id)
            continue
        if node.kind != "artifact" and _touches_visible_artifact(
            graph.edges,
            node.node_id,
            visible_artifact_nodes=visible_artifact_nodes,
        ):
            visible_nodes.add(node.node_id)
    nodes = [
        node
        for node in graph.nodes
        if node.node_id in visible_nodes
    ]
    edges = [
        edge
        for edge in graph.edges
        if edge.source in visible_nodes and edge.target in visible_nodes
    ]
    return MemoryGraphSnapshot(
        graph_fingerprint=_graph_fingerprint(nodes, edges),
        nodes=nodes,
        edges=edges,
        warnings=list(graph.warnings),
    )


def _touches_visible_artifact(
    edges: list[MemoryGraphEdge],
    node_id: str,
    *,
    visible_artifact_nodes: set[str],
) -> bool:
    return any(
        (
            edge.source == node_id
            and edge.target in visible_artifact_nodes
        )
        or (
            edge.target == node_id
            and edge.source in visible_artifact_nodes
        )
        for edge in edges
    )


def _node_id(kind: str, record_id: str) -> str:
    return f"{kind}:{record_id}"


def _edge_sort_key(edge: MemoryGraphEdge) -> tuple[str, str, str, str]:
    return (edge.kind, edge.source, edge.target, edge.evidence)


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    maximum = max(scores.values())
    if maximum <= 0:
        return {key: 0.0 for key in sorted(scores)}
    return {
        key: round(value / maximum, 6)
        for key, value in sorted(scores.items())
    }


def _graph_fingerprint(
    nodes: list[MemoryGraphNode],
    edges: list[MemoryGraphEdge],
) -> str:
    payload = {
        "nodes": [node.to_dict() for node in sorted(nodes, key=_node_sort_key)],
        "edges": [edge.to_dict() for edge in sorted(edges, key=_edge_sort_key)],
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def _node_sort_key(node: MemoryGraphNode) -> tuple[str, str, str, str]:
    return (node.kind, node.record_id, node.node_id, node.path)


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
            " ".join(card.recent_failure_directions),
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
