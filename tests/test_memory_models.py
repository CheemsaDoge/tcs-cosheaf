from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from cosheaf.memory import (
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

GENERATED_AT = datetime(2026, 6, 7, 16, 30, tzinfo=timezone(timedelta(hours=8)))


def _artifact_card() -> ArtifactCard:
    return ArtifactCard(
        id="definition.graph.simple",
        path="kb/public/accepted/definitions/definition.graph.simple.yaml",
        root_scope=MemoryRootScope.PUBLIC,
        type=ArtifactCardType.DEFINITION,
        status=ArtifactCardStatus.ACCEPTED,
        title="Simple graph",
        summary="A compact graph definition card derived from accepted metadata.",
        domain=["graph-theory"],
        tags=["graph", "foundation"],
        depends_on=["external:diestel.graph-theory"],
        sources=["source.book.diestel"],
        review_state="human_reviewed",
        verifier_state="none",
        formalization_state="planned",
        trust_score=0.8,
        retrieval_score=0.45,
        why_relevant="Seed artifact for graph examples.",
        risk_flags=[],
        can_pull_full=True,
    )


def test_artifact_card_serializes_deterministically() -> None:
    card = _artifact_card()

    serialized = card.model_dump(mode="json")

    assert list(serialized) == [
        "id",
        "path",
        "root_scope",
        "type",
        "status",
        "title",
        "summary",
        "domain",
        "tags",
        "depends_on",
        "sources",
        "review_state",
        "verifier_state",
        "formalization_state",
        "failure_count",
        "recent_failure_directions",
        "trust_score",
        "retrieval_score",
        "why_relevant",
        "risk_flags",
        "can_pull_full",
    ]
    assert serialized["root_scope"] == "public"
    assert serialized["type"] == "definition"
    assert serialized["status"] == "accepted"
    assert serialized["path"] == (
        "kb/public/accepted/definitions/definition.graph.simple.yaml"
    )
    assert card.to_json() == card.to_json()


def test_retrieval_request_defaults_are_conservative() -> None:
    request = RetrievalRequest(
        query=" graph foundation ",
        issue_id="issue.graph.demo",
        seed_artifacts=["definition.graph.simple"],
        pinned_artifacts=["definition.path.simple"],
        role=RetrievalRole.REASONER,
    )

    serialized = request.model_dump(mode="json")

    assert serialized["schema_version"] == 1
    assert serialized["query"] == "graph foundation"
    assert serialized["allowed_scopes"] == ["public"]
    assert serialized["allowed_statuses"] == [
        "accepted",
        "human_reviewed",
        "machine_checked",
        "locally_tested",
    ]
    assert serialized["include_refuted"] is False
    assert serialized["include_obsolete"] is False
    assert serialized["max_cards"] == 20
    assert serialized["max_full_artifacts"] == 0
    assert serialized["role"] == "reasoner"


def test_retrieval_result_serializes_nested_audit_and_scores() -> None:
    result = RetrievalResult(
        request_id="retrieval.issue.graph.demo.0001",
        generated_at=GENERATED_AT,
        index_fingerprint="sha256:fixture",
        cards=[
            RetrievedArtifactCard(
                card=_artifact_card(),
                score_breakdown=ScoreBreakdown(
                    retrieval_hybrid=0.5,
                    personalized_pagerank=0.1,
                    global_pagerank=0.2,
                    quality_prior=0.4,
                    freshness=0.0,
                    penalty=0.05,
                    total=0.45,
                ),
                why_relevant=["query term match", "seed dependency"],
            )
        ],
        full_artifact_pulls=[
            FullArtifactPull(
                artifact_id="definition.graph.simple",
                path="kb/public/accepted/definitions/definition.graph.simple.yaml",
                reason="explicit request",
            )
        ],
        audit=RetrievalAudit(
            filters_applied=["scope:public"],
            excluded=[
                RetrievalExclusion(
                    artifact_id="claim.private.example",
                    reason="private scope excluded",
                )
            ],
            warnings=["formal links are metadata only"],
        ),
    )

    assert result.generated_at == datetime(2026, 6, 7, 8, 30, tzinfo=UTC)
    serialized = result.model_dump(mode="json")
    assert serialized["schema_version"] == 1
    assert serialized["generated_at"] == "2026-06-07T08:30:00Z"
    assert serialized["cards"][0]["card"]["id"] == "definition.graph.simple"
    assert serialized["cards"][0]["score_breakdown"]["total"] == 0.45
    assert serialized["audit"]["excluded"][0]["reason"] == "private scope excluded"
    assert result.to_json() == result.to_json()


def test_artifact_card_rejects_non_repo_local_path() -> None:
    with pytest.raises(ValidationError, match="path must be repository-local"):
        ArtifactCard(
            id="definition.graph.simple",
            path="../kb/private/definition.graph.simple.yaml",
            root_scope=MemoryRootScope.PRIVATE,
            type=ArtifactCardType.DEFINITION,
            status=ArtifactCardStatus.DRAFT,
            title="Bad path",
            summary="This card should fail path validation.",
        )


def test_artifact_card_rejects_invalid_id() -> None:
    with pytest.raises(ValidationError):
        ArtifactCard(
            id="Definition.Graph",
            path="kb/public/definitions/definition.graph.yaml",
            root_scope=MemoryRootScope.PUBLIC,
            type=ArtifactCardType.DEFINITION,
            status=ArtifactCardStatus.DRAFT,
            title="Bad ID",
            summary="This card should fail ID validation.",
        )


def test_score_breakdown_rejects_negative_component_score() -> None:
    with pytest.raises(ValidationError):
        ScoreBreakdown(retrieval_hybrid=-0.1)


def test_retrieval_request_rejects_invalid_limits() -> None:
    with pytest.raises(ValidationError):
        RetrievalRequest(query="graph", max_cards=0)

    with pytest.raises(ValidationError):
        RetrievalRequest(query="graph", max_full_artifacts=-1)


def test_retrieval_result_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        RetrievalResult(
            request_id="retrieval.issue.graph.demo.0001",
            generated_at=datetime(2026, 6, 7, 8, 30),
            index_fingerprint="sha256:fixture",
        )


def test_extra_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        ArtifactCard.model_validate(
            {
                "id": "definition.graph.simple",
                "path": "kb/public/definitions/definition.graph.simple.yaml",
                "root_scope": "public",
                "type": "definition",
                "status": "draft",
                "title": "Extra field",
                "summary": "This card should reject unknown fields.",
                "unexpected": True,
            }
        )
