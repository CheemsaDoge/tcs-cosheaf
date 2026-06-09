from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.services import ContextSendPolicyService
from cosheaf.services.models import ContextBuildRequest, ErrorResult, MemoryRootScope
from cosheaf.storage.repo import RepoContext


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
            tags=["public"],
            statement="Public fixture context.",
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
            statement="Private fixture context with API-like value sk-test-secret.",
            depends_on=["claim.fixture.public-preview"],
        ),
    )
    _write_yaml(
        repo_root,
        "issues/open/context-send.yaml",
        _issue_data(
            "issue.fixture.context-send",
            related_artifacts=[
                "claim.fixture.public-preview",
                "claim.fixture.private-preview",
            ],
        ),
    )
    return RepoContext(repo_root)


def test_public_provider_preview_excludes_private_even_when_private_scores_high(
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
