from pathlib import Path

import pytest

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.loader import (
    IssueRecord,
    LoadError,
    ReviewRecord,
    UnsupportedArtifactTypeError,
    load_artifacts,
)
from cosheaf.storage.repo import RepoContext
from cosheaf.storage.writer import dump_yaml_deterministic

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def test_loads_example_artifacts() -> None:
    records = load_artifacts(RepoContext(ROOT))
    by_id = {record.id: record for record in records}

    claim = by_id["claim.example.complete-graph-edge-count"]
    issue = by_id["issue.example.missing-proof-boundary"]
    review = by_id["review.example.complete-graph-edge-count"]

    assert isinstance(claim.record, BaseArtifact)
    assert isinstance(issue.record, IssueRecord)
    assert isinstance(review.record, ReviewRecord)
    assert claim.source_path.as_posix() == "examples/claims/claim.example.yaml"


def test_deterministic_ordering_by_path_then_id() -> None:
    records = load_artifacts(RepoContext(FIXTURES / "ordered_repo"))

    assert [(record.source_path.as_posix(), record.id) for record in records] == [
        ("examples/claims/a-claim.yaml", "claim.fixture.a"),
        ("examples/claims/b-claim.yaml", "claim.fixture.b"),
        ("issues/open/issue.yaml", "issue.fixture.open"),
    ]


def test_invalid_yaml_produces_useful_error() -> None:
    with pytest.raises(LoadError, match="invalid YAML") as exc_info:
        load_artifacts(RepoContext(FIXTURES / "invalid_yaml_repo"))

    assert "examples/claims/bad.yaml" in str(exc_info.value)


def test_missing_fields_produce_useful_error() -> None:
    with pytest.raises(LoadError, match="missing required fields") as exc_info:
        load_artifacts(RepoContext(FIXTURES / "missing_fields_repo"))

    message = str(exc_info.value)
    assert "examples/claims/missing.yaml" in message
    assert "created_at" in message


def test_unsupported_artifact_type_produces_useful_error() -> None:
    with pytest.raises(UnsupportedArtifactTypeError, match="unsupported artifact type"):
        load_artifacts(RepoContext(FIXTURES / "unsupported_type_repo"))


def test_writer_preserves_mapping_order() -> None:
    output = dump_yaml_deterministic(
        {
            "id": "claim.fixture.a",
            "type": "claim",
            "title": "A claim",
            "status": "draft",
        }
    )

    assert output.splitlines() == [
        "id: claim.fixture.a",
        "type: claim",
        "title: A claim",
        "status: draft",
    ]
