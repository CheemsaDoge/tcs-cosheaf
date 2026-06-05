from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from cosheaf.core.artifact import (
    AlignmentReview,
    BaseArtifact,
    Evidence,
    FormalizationRef,
    ReviewRef,
    Risk,
    SourceMetadata,
    VerificationPolicy,
)
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


def test_validate_artifact_id_allows_numeric_version_segment() -> None:
    assert (
        validate_artifact_id("issue.graph-toy-search.0001")
        == "issue.graph-toy-search.0001"
    )


def test_risk_defaults_work() -> None:
    data = _valid_artifact_data()
    data.pop("risk")

    artifact = BaseArtifact.model_validate(data)

    assert artifact.risk == Risk()
    assert artifact.risk.level == "low"
    assert artifact.risk.notes == ""


def test_sources_default_to_empty_list() -> None:
    artifact = BaseArtifact.model_validate(_valid_artifact_data())

    assert artifact.sources == []


def test_formal_link_defaults_are_backward_compatible() -> None:
    artifact = BaseArtifact.model_validate(_valid_artifact_data())

    assert artifact.formalizations == []
    assert artifact.alignment == AlignmentReview()
    assert artifact.alignment.status == "none"
    assert artifact.verification_policy == VerificationPolicy()
    assert artifact.verification_policy.level == "source_reviewed"


def test_artifact_with_formalization_link_parses() -> None:
    data = _valid_artifact_data()
    data["formalizations"] = [
        {
            "id": "cslib.complete-graph-edge-count",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "CSLib.Graph.Basic",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.completeGraph_edgeCount",
            "declaration_kind": "theorem",
            "status": "linked",
            "check_mode": "external_library_ref",
            "expected_type": "Fake Lean type for documentation-only example.",
            "notes": "External CSLib declaration reference; no proof copied.",
        }
    ]
    data["alignment"] = {
        "status": "requested",
        "reviewer": "",
        "reviewed_at": None,
        "convention_notes": [
            "Confirm K_n convention matches the informal complete graph statement."
        ],
        "limitations": "Lean link alone does not prove informal alignment.",
    }
    data["verification_policy"] = {
        "level": "source_reviewed_with_formal_link",
        "require_formal_link": True,
        "require_lean_check": False,
        "require_alignment_review": False,
    }

    artifact = BaseArtifact.model_validate(data)

    assert artifact.formalizations == [
        FormalizationRef(
            id="cslib.complete-graph-edge-count",
            system="lean4",
            library="CSLib",
            library_ref="CSLib.Graph.Basic",
            import_path="CSLib.Graph.Basic",
            symbol="CSLib.Graph.completeGraph_edgeCount",
            declaration_kind="theorem",
            status="linked",
            check_mode="external_library_ref",
            expected_type="Fake Lean type for documentation-only example.",
            notes="External CSLib declaration reference; no proof copied.",
        )
    ]
    assert artifact.alignment.status == "requested"
    assert artifact.verification_policy.level == "source_reviewed_with_formal_link"
    assert artifact.verification_policy.require_formal_link is True
    assert artifact.verification_policy.require_lean_check is False


@pytest.mark.parametrize("missing_field", ["library_ref", "import_path", "symbol"])
def test_missing_required_formalization_subfield_fails(missing_field: str) -> None:
    data = _valid_artifact_data()
    formalization = {
        "id": "cslib.complete-graph-edge-count",
        "system": "lean4",
        "library": "CSLib",
        "library_ref": "CSLib.Graph.Basic",
        "import_path": "CSLib.Graph.Basic",
        "symbol": "CSLib.Graph.completeGraph_edgeCount",
        "declaration_kind": "theorem",
        "status": "linked",
        "check_mode": "external_library_ref",
        "expected_type": "Fake Lean type.",
        "notes": "",
    }
    formalization.pop(missing_field)
    data["formalizations"] = [formalization]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


@pytest.mark.parametrize("empty_field", ["library_ref", "import_path", "symbol"])
def test_empty_required_formalization_subfield_fails(empty_field: str) -> None:
    data = _valid_artifact_data()
    formalization = {
        "id": "cslib.complete-graph-edge-count",
        "system": "lean4",
        "library": "CSLib",
        "library_ref": "CSLib.Graph.Basic",
        "import_path": "CSLib.Graph.Basic",
        "symbol": "CSLib.Graph.completeGraph_edgeCount",
        "declaration_kind": "theorem",
        "status": "linked",
        "check_mode": "external_library_ref",
        "expected_type": "Fake Lean type.",
        "notes": "",
    }
    formalization[empty_field] = " "
    data["formalizations"] = [formalization]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_formalization_status_fails() -> None:
    data = _valid_artifact_data()
    data["formalizations"] = [
        {
            "id": "cslib.complete-graph-edge-count",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "CSLib.Graph.Basic",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.completeGraph_edgeCount",
            "declaration_kind": "theorem",
            "status": "proved",
            "check_mode": "external_library_ref",
            "expected_type": "Fake Lean type.",
            "notes": "",
        }
    ]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_formalization_expected_type_and_notes_default_to_empty_strings() -> None:
    data = _valid_artifact_data()
    data["formalizations"] = [
        {
            "id": "cslib.complete-graph-edge-count",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "CSLib.Graph.Basic",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.completeGraph_edgeCount",
            "declaration_kind": "theorem",
            "status": "planned",
            "check_mode": "external_library_ref",
        }
    ]

    artifact = BaseArtifact.model_validate(data)

    assert artifact.formalizations[0].expected_type == ""
    assert artifact.formalizations[0].notes == ""


def test_artifact_with_alignment_review_parses() -> None:
    data = _valid_artifact_data()
    data["alignment"] = {
        "status": "human_reviewed",
        "reviewer": " reviewer@example.org ",
        "reviewed_at": "2026-06-04T00:00:00Z",
        "convention_notes": [" finite simple graphs ", ""],
        "limitations": " None known. ",
    }

    artifact = BaseArtifact.model_validate(data)

    assert artifact.alignment.status == "human_reviewed"
    assert artifact.alignment.reviewer == "reviewer@example.org"
    assert artifact.alignment.reviewed_at == datetime(2026, 6, 4, tzinfo=UTC)
    assert artifact.alignment.convention_notes == ["finite simple graphs"]
    assert artifact.alignment.limitations == "None known."


def test_artifact_with_verification_policy_parses() -> None:
    data = _valid_artifact_data()
    data["verification_policy"] = {
        "level": "source_reviewed_with_formal_link",
        "require_formal_link": True,
        "require_lean_check": False,
        "require_alignment_review": True,
    }

    artifact = BaseArtifact.model_validate(data)

    assert artifact.verification_policy.level == "source_reviewed_with_formal_link"
    assert artifact.verification_policy.require_formal_link is True
    assert artifact.verification_policy.require_lean_check is False
    assert artifact.verification_policy.require_alignment_review is True


def test_invalid_formalization_id_fails() -> None:
    data = _valid_artifact_data()
    data["formalizations"] = [
        {
            "id": "CSLib.bad_id",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "CSLib.Graph.Basic",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.completeGraph_edgeCount",
            "declaration_kind": "theorem",
            "status": "planned",
            "check_mode": "external_library_ref",
        }
    ]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_formalization_declaration_kind_fails() -> None:
    data = _valid_artifact_data()
    data["formalizations"] = [
        {
            "id": "cslib.complete-graph-edge-count",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "CSLib.Graph.Basic",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.completeGraph_edgeCount",
            "declaration_kind": "axiom",
            "status": "planned",
            "check_mode": "external_library_ref",
        }
    ]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_formalization_check_mode_fails() -> None:
    data = _valid_artifact_data()
    data["formalizations"] = [
        {
            "id": "cslib.complete-graph-edge-count",
            "system": "lean4",
            "library": "CSLib",
            "library_ref": "CSLib.Graph.Basic",
            "import_path": "CSLib.Graph.Basic",
            "symbol": "CSLib.Graph.completeGraph_edgeCount",
            "declaration_kind": "theorem",
            "status": "planned",
            "check_mode": "lake_project",
        }
    ]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_verification_policy_level_fails() -> None:
    data = _valid_artifact_data()
    data["verification_policy"] = {
        "level": "fully_autoformalized",
        "require_formal_link": False,
        "require_lean_check": False,
        "require_alignment_review": False,
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_source_reviewed_with_formal_link_requires_formal_link() -> None:
    data = _valid_artifact_data()
    data["verification_policy"] = {
        "level": "source_reviewed_with_formal_link",
        "require_formal_link": False,
        "require_lean_check": False,
        "require_alignment_review": False,
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_lean_required_policy_requires_formal_link_and_lean_check() -> None:
    data = _valid_artifact_data()
    data["verification_policy"] = {
        "level": "lean_required",
        "require_formal_link": True,
        "require_lean_check": False,
        "require_alignment_review": False,
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_lean_required_policy_requires_formal_link() -> None:
    data = _valid_artifact_data()
    data["verification_policy"] = {
        "level": "lean_required",
        "require_formal_link": False,
        "require_lean_check": True,
        "require_alignment_review": False,
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_alignment_human_reviewed_requires_reviewer() -> None:
    data = _valid_artifact_data()
    data["alignment"] = {
        "status": "human_reviewed",
        "reviewer": " ",
        "reviewed_at": "2026-06-04T00:00:00Z",
        "convention_notes": [],
        "limitations": "",
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_alignment_rejected_requires_reviewer() -> None:
    data = _valid_artifact_data()
    data["alignment"] = {
        "status": "rejected",
        "reviewer": "",
        "reviewed_at": "2026-06-04T00:00:00Z",
        "convention_notes": [],
        "limitations": "Convention mismatch.",
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_alignment_naive_reviewed_at_fails() -> None:
    data = _valid_artifact_data()
    data["alignment"] = {
        "status": "requested",
        "reviewer": "",
        "reviewed_at": "2026-06-04T00:00:00",
        "convention_notes": [],
        "limitations": "",
    }

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_source_metadata_parses_and_normalizes_strings() -> None:
    data = _valid_artifact_data()
    data["sources"] = [
        {
            "kind": "paper",
            "title": " Complete Graphs ",
            "authors": [" Example Author ", ""],
            "year": 2024,
            "doi": " 10.1145/example ",
            "arxiv": " 2401.00001 ",
            "url": " https://example.org/paper ",
            "theorem_number": " Theorem 2 ",
            "page": " 7 ",
            "notes": " Standard reference. ",
        }
    ]

    artifact = BaseArtifact.model_validate(data)

    assert artifact.sources == [
        SourceMetadata(
            kind="paper",
            title="Complete Graphs",
            authors=["Example Author"],
            year=2024,
            doi="10.1145/example",
            arxiv="2401.00001",
            url="https://example.org/paper",
            theorem_number="Theorem 2",
            page="7",
            notes="Standard reference.",
        )
    ]


def test_invalid_source_kind_fails() -> None:
    data = _valid_artifact_data()
    data["sources"] = [{"kind": "tweet"}]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


def test_invalid_source_year_fails() -> None:
    data = _valid_artifact_data()
    data["sources"] = [{"kind": "paper", "year": 0}]

    with pytest.raises(ValidationError):
        BaseArtifact.model_validate(data)


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
