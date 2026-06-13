from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.services import ContextSendPolicyService
from cosheaf.services.models import (
    ContextBuildRequest,
    ContextPolicyMode,
    ErrorResult,
    MemoryRootScope,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()
FULL_TEXT_MARKERS = (
    "FULL_PUBLIC_TEXT_SHOULD_NOT_APPEAR",
    "FULL_PRIVATE_TEXT_SHOULD_NOT_APPEAR",
    "FULL_WORKSPACE_TEXT_SHOULD_NOT_APPEAR",
    "FULL_FRAMEWORK_TEXT_SHOULD_NOT_APPEAR",
)


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_workspace_config(repo_root: Path) -> None:
    repo_root.joinpath("cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "context-send-fixture"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "framework"',
                'path = "kb/framework"',
                "readonly = true",
                "priority = 15",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 20",
                "",
                "[policy]",
                "private_can_depend_on_public = true",
                "public_can_depend_on_private = false",
                "accepted_requires_source = true",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _artifact_data(
    artifact_id: str,
    *,
    title: str,
    status: str,
    tags: list[str],
    statement: str,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": title,
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-09T00:00:00Z",
        "updated_at": "2026-06-09T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": tags,
        "statement": statement,
        "evidence": [],
        "review": {"state": "requested", "notes": "Context-send fixture review."},
        "risk": {"level": "low", "notes": "Context-send fixture risk."},
    }


def _issue_data(issue_id: str, *, related_artifacts: list[str]) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Private leakage score test",
        "status": "open",
        "created_at": "2026-06-09T00:00:00Z",
        "updated_at": "2026-06-09T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": (
            "The private artifact has the strongest lexical score for "
            "supersecret-token but must not appear in public provider preview."
        ),
        "related_artifacts": related_artifacts,
        "tags": ["supersecret-token"],
    }


def _fixture_repo(repo_root: Path) -> RepoContext:
    _write_workspace_config(repo_root)
    _write_yaml(
        repo_root,
        "kb/public/accepted/claims/public.yaml",
        _artifact_data(
            "claim.fixture.public-preview",
            title="Public preview-safe claim",
            status="accepted",
            tags=["public", "matrix-token"],
            statement="Public fixture context. FULL_PUBLIC_TEXT_SHOULD_NOT_APPEAR.",
        ),
    )
    _write_yaml(
        repo_root,
        "kb/framework/accepted/claims/framework.yaml",
        _artifact_data(
            "claim.fixture.framework-preview",
            title="Framework local claim",
            status="accepted",
            tags=["framework-marker", "matrix-token"],
            statement=(
                "Framework fixture context. FULL_FRAMEWORK_TEXT_SHOULD_NOT_APPEAR."
            ),
        ),
    )
    _write_yaml(
        repo_root,
        "kb/private/draft/claims/private.yaml",
        _artifact_data(
            "claim.fixture.private-preview",
            title="supersecret-token private draft",
            status="draft",
            tags=["supersecret-token"],
            statement=(
                "Private fixture context with API-like value sk-test-secret. "
                "FULL_PRIVATE_TEXT_SHOULD_NOT_APPEAR."
            ),
            depends_on=["claim.fixture.public-preview"],
        ),
    )
    _write_yaml(
        repo_root,
        "examples/claims/workspace.yaml",
        _artifact_data(
            "claim.fixture.workspace-preview",
            title="Workspace local claim",
            status="accepted",
            tags=["workspace-marker", "matrix-token"],
            statement=(
                "Workspace fixture context. FULL_WORKSPACE_TEXT_SHOULD_NOT_APPEAR."
            ),
        ),
    )
    _write_yaml(
        repo_root,
        "issues/open/context-send.yaml",
        _issue_data(
            "issue.fixture.context-send",
            related_artifacts=[
                "claim.fixture.public-preview",
                "claim.fixture.framework-preview",
                "claim.fixture.private-preview",
                "claim.fixture.workspace-preview",
            ],
        ),
    )
    return RepoContext(repo_root)


@pytest.mark.parametrize(
    (
        "preview_request",
        "expected_artifacts",
        "expected_scopes",
        "private_requested",
    ),
    [
        (
            ContextBuildRequest(issue_id="issue.fixture.context-send"),
            ["claim.fixture.public-preview"],
            [MemoryRootScope.PUBLIC],
            False,
        ),
        (
            ContextBuildRequest(
                issue_id="issue.fixture.context-send",
                policy_mode=ContextPolicyMode.PRIVATE_RESEARCH,
                public_only=True,
                allow_private_context=False,
            ),
            ["claim.fixture.public-preview"],
            [MemoryRootScope.PUBLIC],
            False,
        ),
        (
            ContextBuildRequest(
                issue_id="issue.fixture.context-send",
                policy_mode=ContextPolicyMode.PRIVATE_RESEARCH,
                public_only=False,
                allow_private_context=True,
            ),
            ["claim.fixture.private-preview", "claim.fixture.public-preview"],
            [MemoryRootScope.PRIVATE, MemoryRootScope.PUBLIC],
            True,
        ),
    ],
)
def test_provider_preview_policy_matrix_allows_only_explicit_scopes(
    tmp_path: Path,
    preview_request: ContextBuildRequest,
    expected_artifacts: list[str],
    expected_scopes: list[MemoryRootScope],
    private_requested: bool,
) -> None:
    context = _fixture_repo(tmp_path)

    preview = ContextSendPolicyService(context).provider_preview(preview_request)

    assert not isinstance(preview, ErrorResult)
    assert set(preview.artifact_ids) == set(expected_artifacts)
    assert set(preview.root_scopes) == set(expected_scopes)
    assert preview.private_context_requested is private_requested
    assert preview.private_context_included is (
        MemoryRootScope.PRIVATE in expected_scopes
    )
    assert preview.card_count == len(expected_artifacts)
    assert preview.full_artifact_count == 0
    assert preview.content_mode == "cards_only"
    assert preview.estimated_tokens >= len(expected_artifacts)
    assert all(item.estimated_tokens > 0 for item in preview.items)
    assert all(item.artifact_id in preview.artifact_ids for item in preview.items)
    assert "claim.fixture.workspace-preview" not in preview.artifact_ids
    assert "claim.fixture.framework-preview" not in preview.artifact_ids
    payload = preview.to_json()
    for marker in FULL_TEXT_MARKERS:
        assert marker not in payload
    if MemoryRootScope.PRIVATE in expected_scopes:
        assert "private_context" in preview.risk_flags
        assert "draft" in preview.risk_flags
    else:
        assert "private_context" not in preview.risk_flags


@pytest.mark.parametrize(
    ("policy_mode", "public_only", "allow_private_context", "expected_code"),
    [
        (
            ContextPolicyMode.PUBLIC,
            False,
            False,
            "private_context_requires_policy",
        ),
        (
            ContextPolicyMode.PUBLIC,
            False,
            True,
            "private_context_requires_policy",
        ),
        (
            ContextPolicyMode.PRIVATE_RESEARCH,
            False,
            False,
            "private_context_requires_consent",
        ),
    ],
)
def test_provider_preview_policy_matrix_denials_have_stable_error_codes(
    tmp_path: Path,
    policy_mode: ContextPolicyMode,
    public_only: bool,
    allow_private_context: bool,
    expected_code: str,
) -> None:
    context = _fixture_repo(tmp_path)

    denied = ContextSendPolicyService(context).provider_preview(
        ContextBuildRequest(
            issue_id="issue.fixture.context-send",
            policy_mode=policy_mode,
            public_only=public_only,
            allow_private_context=allow_private_context,
        )
    )

    assert isinstance(denied, ErrorResult)
    assert denied.code == expected_code
    assert denied.blocking is True
    assert denied.details["policy_mode"] == policy_mode.value
    assert denied.details["public_only"] == str(public_only).lower()
    assert denied.details["allow_private_context"] == str(
        allow_private_context
    ).lower()


def test_public_provider_preview_excludes_private_before_ranking_scores(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)

    preview = ContextSendPolicyService(context).provider_preview(
        ContextBuildRequest(issue_id="issue.fixture.context-send")
    )

    assert not isinstance(preview, ErrorResult)
    assert preview.issue_id == "issue.fixture.context-send"
    assert preview.artifact_ids == ["claim.fixture.public-preview"]
    assert preview.root_scopes == [MemoryRootScope.PUBLIC]
    assert "claim.fixture.private-preview" not in preview.to_json()
    assert "supersecret-token" not in preview.to_json()
    assert "sk-test-secret" not in preview.to_json()


def test_private_provider_preview_requires_private_research_policy(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)

    denied = ContextSendPolicyService(context).provider_preview(
        ContextBuildRequest(
            issue_id="issue.fixture.context-send",
            public_only=False,
            allow_private_context=True,
        )
    )

    assert isinstance(denied, ErrorResult)
    assert denied.code == "private_context_requires_policy"
    assert denied.blocking is True
    assert "private_research" in denied.remediation


def test_private_provider_preview_includes_private_only_with_policy_and_consent(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)

    preview = ContextSendPolicyService(context).provider_preview(
        ContextBuildRequest.model_validate(
            {
                "issue_id": "issue.fixture.context-send",
                "policy_mode": "private_research",
                "public_only": False,
                "allow_private_context": True,
            }
        )
    )

    assert not isinstance(preview, ErrorResult)
    assert set(preview.artifact_ids) == {
        "claim.fixture.private-preview",
        "claim.fixture.public-preview",
    }
    assert set(preview.root_scopes) == {MemoryRootScope.PRIVATE, MemoryRootScope.PUBLIC}
    assert "private_context" in preview.risk_flags
    assert "draft" in preview.risk_flags


@pytest.mark.parametrize("provider", ["fake", "openai"])
def test_provider_preview_cli_matrix_for_fake_and_openai_provider_metadata(
    tmp_path: Path,
    provider: str,
) -> None:
    _fixture_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "provider",
            "preview-send",
            "--issue",
            "issue.fixture.context-send",
            "--provider",
            provider,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["provider"] == provider
    assert payload["real_run_performed"] is False
    assert payload["preview"]["artifact_ids"] == ["claim.fixture.public-preview"]
    assert payload["payload_shape"]["root_scopes"] == ["public"]
    assert payload["payload_shape"]["estimated_tokens"] > 0
    assert payload["payload_shape"]["private_context_included"] is False
    assert payload["payload_shape"]["card_count"] == 1
    assert payload["payload_shape"]["full_artifact_count"] == 0
    assert payload["payload_shape"]["content_mode"] == "cards_only"
    for marker in FULL_TEXT_MARKERS:
        assert marker not in result.output
