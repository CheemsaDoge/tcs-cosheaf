from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from cosheaf.core.artifact import BaseArtifact, Evidence, ReviewRef, Risk
from cosheaf.core.ids import validate_artifact_id
from cosheaf.core.status import (
    ArtifactStatus,
    ArtifactType,
    expected_status_for_path,
    is_accepted_status,
    is_preaccepted_status,
    is_terminal_status,
)

ROOT = Path(__file__).resolve().parents[1]


def _valid_artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.example.complete-graph-edge-count",
        "type": "claim",
        "title": "Complete graph edge count",
        "domain": ["graph-theory", "combinatorics"],
        "status": "draft",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["example-author"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["complete-graph", "counting"],
        "statement": "For every n >= 1, K_n has n(n - 1) / 2 edges.",
        "evidence": [
            {
                "kind": "proof",
                "path": "examples/proofs/proof.example.yaml",
                "summary": "Counts unordered pairs of distinct vertices.",
            }
        ],
        "review": {
            "state": "requested",
            "notes": "Example artifact for schema scaffolding.",
        },
        "risk": {
            "level": "low",
            "notes": "Standard result, but example remains draft.",
        },
    }


def test_valid_example_artifact_parses() -> None:
    data = yaml.safe_load(
        (ROOT / "examples/claims/claim.example.yaml").read_text(encoding="utf-8")
    )

    artifact = BaseArtifact.model_validate(data)

    assert artifact.id == "claim.example.complete-graph-edge-count"
    assert artifact.type is ArtifactType.CLAIM
    assert artifact.status is ArtifactStatus.DRAFT
    assert artifact.created_at == datetime(2026, 6, 1, tzinfo=UTC)


def test_invalid_status_fails() -> None:
    data = _valid_artifact_data()
    data["status"] = "not-a-status"

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_artifact_type_fails() -> None:
    data = _valid_artifact_data()
    data["type"] = "not-a-type"

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_id_fails() -> None:
    data = _valid_artifact_data()
    data["id"] = "bad id with spaces"

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_validate_artifact_id_returns_valid_id() -> None:
    assert (
        validate_artifact_id("claim.example.complete-graph-edge-count")
        == "claim.example.complete-graph-edge-count"
    )


def test_risk_defaults_work() -> None:
    data = _valid_artifact_data()
    data.pop("risk")

    artifact = BaseArtifact.model_validate(data)

    assert artifact.risk == Risk()
    assert artifact.risk.level == "low"
    assert artifact.risk.notes == ""


def test_evidence_list_parses() -> None:
    artifact = BaseArtifact.model_validate(_valid_artifact_data())

    assert artifact.evidence == [
        Evidence(
            kind="proof",
            path="examples/proofs/proof.example.yaml",
            summary="Counts unordered pairs of distinct vertices.",
        )
    ]
    assert artifact.review == ReviewRef(
        state="requested",
        notes="Example artifact for schema scaffolding.",
    )


def test_status_helpers() -> None:
    assert is_terminal_status(ArtifactStatus.ACCEPTED)
    assert is_terminal_status(ArtifactStatus.REFUTED)
    assert not is_terminal_status(ArtifactStatus.DRAFT)
    assert is_preaccepted_status(ArtifactStatus.MACHINE_CHECKED)
    assert not is_preaccepted_status(ArtifactStatus.ACCEPTED)
    assert is_accepted_status(ArtifactStatus.ACCEPTED)


def test_expected_status_for_path_rules() -> None:
    assert expected_status_for_path("kb/accepted/claims/c.yaml") == frozenset(
        {ArtifactStatus.ACCEPTED}
    )
    assert ArtifactStatus.ACCEPTED not in expected_status_for_path(
        "kb/draft/claims/c.yaml"
    )
    assert expected_status_for_path("kb/refuted/c.yaml") == frozenset(
        {ArtifactStatus.REFUTED}
    )
    assert expected_status_for_path("kb/obsolete/c.yaml") == frozenset(
        {ArtifactStatus.OBSOLETE, ArtifactStatus.SUPERSEDED}
    )
