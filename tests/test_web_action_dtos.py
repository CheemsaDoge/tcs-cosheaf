from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.app import models as app_models
from cosheaf.web_actions import (
    WebActionAuditEntry,
    WebActionConfirmRequest,
    WebActionDtoBundle,
    WebActionError,
    WebActionKind,
    WebActionMode,
    WebActionPreviewRequest,
    WebActionResult,
)

ROOT = Path(__file__).resolve().parents[1]


def test_web_action_requests_and_result_serialize_deterministically() -> None:
    preview = WebActionPreviewRequest(
        action=WebActionKind.ISSUE_CREATE,
        mode=WebActionMode.LOCAL,
        actor="local.researcher",
        parameters={"issue_id": "issue.fixture.web-action"},
    )
    confirm = WebActionConfirmRequest(
        action=WebActionKind.ISSUE_CREATE,
        mode=WebActionMode.LOCAL,
        actor="local.researcher",
        preview_plan_hash="sha256:abc123",
    )
    result = WebActionResult(
        action=WebActionKind.ISSUE_CREATE,
        mode=WebActionMode.LOCAL,
        preview_only=True,
        confirm_required=True,
        confirmed=False,
        performed=False,
        planned_files=["issues/open/issue.fixture.web-action.yaml"],
        validation_summary="not_run",
        gate_summary="not_run",
        authority_warnings=["Preview only; no repository write was performed."],
    )

    for model in (preview, confirm, result):
        payload = model.to_dict()
        assert payload["schema_version"] == 1
        assert json.loads(model.to_json()) == payload
        assert model.to_json() == model.to_json()

    assert result.to_dict()["repo_writes_performed"] is False
    assert result.to_dict()["written_files"] == []
    assert app_models.WebActionResult is WebActionResult


def test_invalid_action_and_unsafe_preview_result_are_rejected() -> None:
    with pytest.raises(ValidationError):
        WebActionPreviewRequest.model_validate(
            {"action": "unknown.action", "mode": "local"}
        )

    with pytest.raises(ValidationError):
        WebActionResult(
            action=WebActionKind.ISSUE_CREATE,
            mode=WebActionMode.LOCAL,
            preview_only=True,
            confirm_required=True,
            confirmed=False,
            performed=True,
            repo_writes_performed=True,
        )

    with pytest.raises(ValidationError):
        WebActionResult(
            action=WebActionKind.ISSUE_CREATE,
            mode=WebActionMode.LOCAL,
            preview_only=False,
            confirm_required=True,
            confirmed=False,
            performed=True,
        )


def test_web_action_errors_and_audit_entries_are_strict() -> None:
    error = WebActionError(
        code="confirm_required",
        message="Explicit confirmation is required.",
        remediation="Preview the action, then confirm it.",
        blocking=True,
        related_path="issues/open/issue.fixture.web-action.yaml",
    )
    audit = WebActionAuditEntry(
        timestamp=datetime(2026, 6, 19, tzinfo=UTC),
        actor="local.researcher",
        action=WebActionKind.ISSUE_CREATE,
        mode=WebActionMode.LOCAL,
        repo_root="H:/ai4tcs/tcs-cosheaf",
        preview_only=False,
        confirmed=True,
        performed=True,
        planned_files=["issues/open/issue.fixture.web-action.yaml"],
        written_files=["issues/open/issue.fixture.web-action.yaml"],
        authority_warnings=["Repository files remain the source of truth."],
        operator_notes="Reviewed by hand.",
        errors=[error],
    )

    assert audit.to_dict()["timestamp"] == "2026-06-19T00:00:00Z"
    assert audit.to_dict()["operator_notes"] == "Reviewed by hand."
    assert audit.to_dict()["errors"][0]["code"] == "confirm_required"

    with pytest.raises(ValidationError):
        WebActionError(
            code="bad_path",
            message="Bad path.",
            remediation="Use a repository-local path.",
            blocking=True,
            related_path="C:/tmp/token.txt",
        )

    with pytest.raises(ValidationError):
        WebActionError(
            code="bad_posix_path",
            message="Bad path.",
            remediation="Use a repository-local path.",
            blocking=True,
            related_path="/tmp/token.txt",
        )

    with pytest.raises(ValidationError):
        WebActionAuditEntry(
            timestamp=datetime(2026, 6, 19, tzinfo=UTC),
            actor="",
            action=WebActionKind.ISSUE_CREATE,
            mode=WebActionMode.LOCAL,
            repo_root="H:/ai4tcs/tcs-cosheaf",
            preview_only=False,
            confirmed=True,
            performed=True,
        )


def test_web_action_schema_file_covers_public_dtos() -> None:
    schema_path = ROOT / "schemas" / "web_action.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    generated = WebActionDtoBundle.model_json_schema(mode="validation")
    expected_defs = {
        "GitHubWritePlan",
        "GitWritePlan",
        "PromotionPlan",
        "RepoWritePlan",
        "ReviewDecisionPlan",
        "WebActionAuditEntry",
        "WebActionConfirmRequest",
        "WebActionError",
        "WebActionPreviewRequest",
        "WebActionResult",
    }

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "WebActionDtoBundle"
    assert set(schema["$defs"]) >= expected_defs
    assert set(generated["$defs"]) >= expected_defs
    generated["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    generated["$id"] = "https://tcs-cosheaf.local/schemas/web_action.schema.json"
    assert schema == generated
