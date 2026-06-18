from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from cosheaf.app.models import (
    AgentAccessStatus,
    ContextBuildRequest,
    ContextBuildResult,
    DraftWriteRequest,
    DraftWriteResult,
    ErrorResult,
    GateRunRequest,
    GateRunResult,
    ReviewRequestWriteRequest,
    ReviewRequestWriteResult,
    SourceNoteWriteRequest,
    ValidateRequest,
    ValidateResult,
    WorkspaceInfoRequest,
    WorkspaceInfoResult,
)
from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.services.models import DraftArtifactWriteRequest


def test_app_request_result_dtos_serialize_deterministically() -> None:
    models = [
        WorkspaceInfoRequest(),
        WorkspaceInfoResult.model_validate(
            {
                "workspace_name": "workspace",
                "repo_root": ".",
                "mode": "legacy",
                "kb_roots": [],
                "policy": {
                    "private_can_depend_on_public": True,
                    "public_can_depend_on_private": False,
                    "accepted_requires_source": True,
                },
            }
        ),
        ValidateRequest(artifact_path="kb/draft/claims/claim.fixture.yaml"),
        ValidateResult(ok=True, checked_count=1),
        GateRunRequest(
            pr_checklist_path=".github/pull_request_template.md",
            timestamp="20260619T000000000000Z",
        ),
        GateRunResult(
            verdict="pass",
            report_json_path=".cosheaf/reports/gate.json",
            report_markdown_path=".cosheaf/reports/gate.md",
        ),
        ContextBuildRequest(issue_id="issue.fixture.app-dtos"),
        ContextBuildResult(
            issue_id="issue.fixture.app-dtos",
            task_dir="context/TASKS/issue.fixture.app-dtos",
            files=["context/TASKS/issue.fixture.app-dtos/CONTEXT.md"],
            public_only=True,
        ),
        ErrorResult(
            code="validation_failed",
            message="Validation failed.",
            remediation="Fix the YAML record.",
            blocking=True,
        ),
    ]

    for model in models:
        payload = model.to_dict()
        assert payload["schema_version"] == 1
        assert json.loads(model.to_json()) == payload
        assert model.to_json() == model.to_json()


def test_draft_write_request_covers_artifact_and_source_note() -> None:
    artifact = DraftArtifactWriteRequest(
        artifact_id="claim.fixture.app-dtos",
        artifact_type=ArtifactType.CLAIM,
        title="App DTO draft",
        domain=["testing"],
        statement="Draft only.",
        authors=["tester"],
    )
    artifact_request = DraftWriteRequest(
        kind="artifact",
        artifact=artifact,
        dry_run=True,
    )
    source_request = DraftWriteRequest(
        kind="source_note",
        source_note=SourceNoteWriteRequest(
            source_id="source.fixture.app-dtos",
            kind="paper",
            authors=["tester"],
            target_path="sources/notes/source.fixture.app-dtos.yaml",
        ),
        dry_run=True,
    )

    assert artifact_request.to_dict()["artifact"]["status"] == "draft"
    assert source_request.to_dict()["source_note"]["kind"] == "paper"

    with pytest.raises(ValidationError):
        DraftWriteRequest(kind="artifact", source_note=source_request.source_note)

    with pytest.raises(ValidationError):
        DraftArtifactWriteRequest(
            artifact_id="claim.fixture.accepted-app-dtos",
            artifact_type=ArtifactType.CLAIM,
            title="Unsafe accepted write",
            domain=["testing"],
            status=ArtifactStatus.ACCEPTED,
            statement="This must be rejected.",
            authors=["tester"],
        )


def test_draft_and_review_results_cannot_claim_accepted_authority() -> None:
    draft = DraftWriteResult(
        kind="draft_artifact",
        path="kb/draft/claims/claim.fixture.app-dtos.yaml",
        written_paths=[],
        dry_run=True,
        record_id="claim.fixture.app-dtos",
    )
    review = ReviewRequestWriteResult(
        review_id="review.request.fixture.app-dtos",
        path="reviews/requests/review.request.fixture.app-dtos.yaml",
        written_paths=[],
        dry_run=True,
    )

    assert draft.accepted_write_performed is False
    assert review.accepted_write_performed is False

    with pytest.raises(ValidationError):
        DraftWriteResult.model_validate(
            {
                "kind": "draft_artifact",
                "path": "kb/accepted/claims/claim.fixture.app-dtos.yaml",
                "written_paths": [],
                "dry_run": True,
                "accepted_write_performed": True,
                "record_id": "claim.fixture.app-dtos",
            }
        )


def test_review_request_write_request_is_informational_only() -> None:
    request = ReviewRequestWriteRequest(
        review_id="review.request.fixture.app-dtos",
        title="Review request",
        authors=["tester"],
        target="claim.fixture.app-dtos",
        summary="Ask for human review later.",
        findings=["not human reviewed"],
        dry_run=True,
    )

    assert request.to_dict()["decision"] == "informational"
    assert request.to_dict()["status"] == "draft"

    with pytest.raises(ValidationError):
        ReviewRequestWriteRequest(
            review_id="review.request.fixture.bad",
            title="Bad review request",
            status="human_reviewed",  # type: ignore[arg-type]
            target="claim.fixture.app-dtos",
            summary="This must not validate.",
        )

    with pytest.raises(ValidationError):
        ReviewRequestWriteRequest(
            review_id="review.request.fixture.bad-decision",
            title="Bad review request",
            target="claim.fixture.app-dtos",
            summary="This must not validate.",
            decision="accepted",  # type: ignore[arg-type]
        )


def test_skipped_status_remains_distinct_from_pass() -> None:
    assert AgentAccessStatus.SKIPPED != AgentAccessStatus.PASS
    assert AgentAccessStatus.SKIPPED.value == "skipped"
    assert AgentAccessStatus.PASS.value == "pass"
