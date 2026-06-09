from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.services.models import (
    AGENT_ACCESS_SCHEMA_MODELS,
    AGENT_ACCESS_STABLE_ERROR_CODES,
    ContextBuildRequest,
    DraftArtifactWriteRequest,
    ErrorResult,
    GateRunResult,
    MemoryRootScope,
    MemorySearchRequest,
    ModelCallRequest,
    ModelCallResult,
    ProviderRunRecord,
    ValidateResult,
    WorkspaceInfoResult,
)

ROOT = Path(__file__).resolve().parents[1]


def test_agent_access_dtos_are_versioned_and_json_serializable() -> None:
    workspace = WorkspaceInfoResult.model_validate(
        {
            "workspace_name": "research-workspace",
            "repo_root": ".",
            "mode": "configured",
            "kb_roots": [
                {
                    "name": "public",
                    "path": "kb/public",
                    "scope": "public",
                    "readonly": True,
                    "priority": 10,
                },
                {
                    "name": "private",
                    "path": "kb/private",
                    "scope": "private",
                    "readonly": False,
                    "priority": 20,
                },
            ],
            "policy": {
                "private_can_depend_on_public": True,
                "public_can_depend_on_private": False,
                "accepted_requires_source": True,
            },
        }
    )
    payload = workspace.to_dict()

    assert payload["schema_version"] == 1
    assert payload["kb_roots"][0]["scope"] == "public"
    assert payload["kb_roots"][1]["scope"] == "private"
    assert payload["policy"]["public_can_depend_on_private"] is False
    assert workspace.to_json() == workspace.to_json()


def test_error_result_requires_remediation_and_blocking_flag() -> None:
    result = ErrorResult(
        code="private_context_requires_consent",
        message="Private KB context cannot be sent without consent.",
        remediation="Set policy_mode=private_research and grant consent.",
        blocking=True,
        related_path="kb/private/claims/claim.fixture.yaml",
        related_artifact="claim.fixture.agent-access",
    )

    assert result.to_dict() == {
        "schema_version": 1,
        "code": "private_context_requires_consent",
        "message": "Private KB context cannot be sent without consent.",
        "remediation": "Set policy_mode=private_research and grant consent.",
        "blocking": True,
        "related_path": "kb/private/claims/claim.fixture.yaml",
        "related_artifact": "claim.fixture.agent-access",
        "details": {},
    }

    legacy_payload = {
        "code": "legacy_error",
        "message": "Older callers may omit optional correlation fields.",
        "remediation": "Inspect the message and details.",
        "blocking": False,
    }
    assert ErrorResult.model_validate(legacy_payload).to_dict() == {
        "schema_version": 1,
        "code": "legacy_error",
        "message": "Older callers may omit optional correlation fields.",
        "remediation": "Inspect the message and details.",
        "blocking": False,
        "related_path": None,
        "related_artifact": None,
        "details": {},
    }

    with pytest.raises(ValidationError):
        ErrorResult(
            code="missing_remediation",
            message="Missing remediation should fail.",
            remediation="",
            blocking=True,
        )

    with pytest.raises(ValidationError):
        ErrorResult(
            code="bad_path",
            message="Absolute paths must not leak through agent errors.",
            remediation="Use a repository-local path.",
            blocking=True,
            related_path="C:/tmp/private.yaml",
        )

    with pytest.raises(ValidationError):
        ErrorResult(
            code="bad_artifact",
            message="Artifact links must use artifact IDs.",
            remediation="Use a valid artifact ID.",
            blocking=True,
            related_artifact="../claim",
        )


def test_stable_agent_access_error_code_list_exists() -> None:
    assert AGENT_ACCESS_STABLE_ERROR_CODES == tuple(
        sorted(AGENT_ACCESS_STABLE_ERROR_CODES)
    )
    assert len(AGENT_ACCESS_STABLE_ERROR_CODES) == len(
        set(AGENT_ACCESS_STABLE_ERROR_CODES)
    )
    assert {
        "accepted_write_forbidden",
        "artifact_id_exists",
        "private_context_requires_consent",
        "provider_context_scope_violation",
        "repository_load_failed",
    }.issubset(AGENT_ACCESS_STABLE_ERROR_CODES)


def test_request_models_include_scope_and_consent_fields() -> None:
    memory = MemorySearchRequest.model_validate(
        {
            "query": "graph tree",
            "allowed_scopes": [MemoryRootScope.PUBLIC],
            "allowed_statuses": ["accepted"],
            "public_only": True,
        }
    )
    context = ContextBuildRequest.model_validate(
        {
            "issue_id": "issue.fixture.agent-access",
            "policy_mode": "public",
            "public_only": True,
            "allow_private_context": False,
        }
    )
    model_call = ModelCallRequest.model_validate(
        {
            "provider": "fake",
            "model": "fake-deterministic",
            "worker_role": "reasoner",
            "prompt": "Draft review context only.",
            "consent": {
                "consent_required": False,
                "consent_granted": False,
                "allow_private_context": False,
                "policy_scope": "public",
            },
        }
    )

    assert memory.to_dict()["public_only"] is True
    assert memory.to_dict()["allowed_scopes"] == ["public"]
    assert context.to_dict()["policy_mode"] == "public"
    assert context.to_dict()["allow_private_context"] is False
    assert model_call.to_dict()["consent"]["allow_private_context"] is False
    assert model_call.to_dict()["network_policy"] == "disabled"


def test_write_and_provider_results_preserve_governance_boundaries() -> None:
    draft = DraftArtifactWriteRequest.model_validate(
        {
            "artifact_id": "claim.fixture.agent-access",
            "artifact_type": "claim",
            "title": "Agent access draft",
            "domain": ["testing"],
            "status": "draft",
            "statement": "Draft only.",
            "authors": ["tester"],
        }
    )
    provider_record = ProviderRunRecord.model_validate(
        {
            "run_id": "run.fixture.agent-access.0001",
            "provider": "fake",
            "model": "fake-deterministic",
            "policy_scope": "public",
            "consent": {
                "consent_required": False,
                "consent_granted": False,
                "allow_private_context": False,
                "policy_scope": "public",
            },
            "private_context_sent": False,
            "status": "skipped",
        }
    )
    model_result = ModelCallResult.model_validate(
        {
            "request_id": "request.fixture.agent-access.0001",
            "provider": "fake",
            "model": "fake-deterministic",
            "status": "skipped",
            "content": "No hosted call was made.",
            "provider_run": provider_record,
        }
    )

    assert draft.status == "draft"
    assert draft.to_dict()["target_surface"] == "draft"
    assert provider_record.to_dict()["private_context_sent"] is False
    assert model_result.to_dict()["status"] == "skipped"

    with pytest.raises(ValidationError):
        DraftArtifactWriteRequest.model_validate(
            {
                "artifact_id": "claim.fixture.accepted-agent-access",
                "artifact_type": "claim",
                "title": "Unsafe accepted write",
                "domain": ["testing"],
                "status": "accepted",
                "statement": "This must be rejected.",
                "authors": ["tester"],
            }
        )


def test_required_agent_access_schema_files_exist_and_match_model_titles() -> None:
    expected = {
        "context_build_request.schema.json": "ContextBuildRequest",
        "context_build_result.schema.json": "ContextBuildResult",
        "create_task_request.schema.json": "CreateTaskRequest",
        "create_task_result.schema.json": "CreateTaskResult",
        "draft_artifact_write_request.schema.json": "DraftArtifactWriteRequest",
        "draft_artifact_write_result.schema.json": "DraftArtifactWriteResult",
        "error_result.schema.json": "ErrorResult",
        "gate_run_result.schema.json": "GateRunResult",
        "memory_search_request.schema.json": "MemorySearchRequest",
        "memory_search_result.schema.json": "MemorySearchResult",
        "model_call_request.schema.json": "ModelCallRequest",
        "model_call_result.schema.json": "ModelCallResult",
        "provider_run_record.schema.json": "ProviderRunRecord",
        "validate_result.schema.json": "ValidateResult",
        "worker_bundle_submit_request.schema.json": "WorkerBundleSubmitRequest",
        "worker_bundle_submit_result.schema.json": "WorkerBundleSubmitResult",
        "workspace_info_result.schema.json": "WorkspaceInfoResult",
    }

    for filename, title in expected.items():
        path = ROOT / "schemas" / "agent_access" / filename
        assert path.is_file(), f"missing schema: {filename}"
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["title"] == title
        assert schema["type"] == "object"


def test_agent_access_schema_files_match_public_dtos() -> None:
    for name, model in AGENT_ACCESS_SCHEMA_MODELS.items():
        path = ROOT / "schemas" / "agent_access" / f"{name}.schema.json"
        expected = model.model_json_schema(mode="validation")
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        expected["$id"] = (
            f"https://tcs-cosheaf.local/schemas/agent_access/{name}.schema.json"
        )
        actual = json.loads(path.read_text(encoding="utf-8"))

        assert actual == expected


def test_schema_properties_expose_policy_and_consent_contracts() -> None:
    workspace_schema = json.loads(
        (ROOT / "schemas" / "agent_access" / "workspace_info_result.schema.json")
        .read_text(encoding="utf-8")
    )
    model_call_schema = json.loads(
        (ROOT / "schemas" / "agent_access" / "model_call_request.schema.json")
        .read_text(encoding="utf-8")
    )
    error_schema = json.loads(
        (ROOT / "schemas" / "agent_access" / "error_result.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert "policy" in workspace_schema["properties"]
    assert "consent" in model_call_schema["properties"]
    assert set(error_schema["required"]) >= {
        "code",
        "message",
        "remediation",
        "blocking",
    }
    assert "related_path" in error_schema["properties"]
    assert "related_artifact" in error_schema["properties"]


def test_placeholder_result_models_are_importable() -> None:
    assert ValidateResult.__name__ == "ValidateResult"
    assert GateRunResult.__name__ == "GateRunResult"
