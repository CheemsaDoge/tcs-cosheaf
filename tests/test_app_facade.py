from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.app import CosheafApp, open_app
from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.memory import ArtifactCardStatus
from cosheaf.services import (
    BundleValidationService,
    ContextPackService,
    DraftWriteService,
    GateService,
    MemorySearchService,
    ValidationService,
    WorkspaceService,
)
from cosheaf.services.models import (
    DraftArtifactWriteRequest,
    WorkerBundleSubmitRequest,
)
from cosheaf.storage.repo import RepoContext


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(
    artifact_id: str = "claim.fixture.app",
    *,
    status: str = "draft",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "App facade fixture claim",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["app"],
        "statement": "An app facade fixture claim.",
        "evidence": [],
        "review": {"state": "requested", "notes": "App facade fixture review."},
        "risk": {"level": "low", "notes": "App facade fixture risk."},
    }


def _issue_data(issue_id: str = "issue.fixture.app") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "App facade fixture issue",
        "status": "open",
        "created_at": "2026-06-19T00:00:00Z",
        "updated_at": "2026-06-19T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise app facade entry points.",
        "related_artifacts": ["claim.fixture.app"],
        "tags": ["app"],
    }


def _bundle_v2_data() -> dict[str, Any]:
    return {
        "bundle_id": "bundle.issue.fixture.app.reasoner.0001",
        "task_id": "task.issue.fixture.app.reasoner",
        "worker_role": "reasoner",
        "created_at": "2026-06-19T00:00:00Z",
        "summary": "App facade bundle fixture.",
        "used_artifacts": ["claim.fixture.app"],
        "used_sources": [],
        "claims": ["The app facade preserves draft-only authority."],
        "proposed_artifacts": [
            {
                "path": "kb/draft/claims/app.yaml",
                "summary": "Draft app facade fixture.",
            }
        ],
        "assumptions": ["App facade assumptions remain review context."],
        "uncertainty": ["No human review has been performed."],
        "verification_requests": ["Run validation and gate before review."],
        "failed_attempts": ["No external verifier was invoked."],
        "counterexamples": ["Candidate counterexample evidence is unreviewed."],
        "failures_or_counterexamples": ["No machine proof was performed."],
        "dependency_questions": ["Should this cite a public accepted definition?"],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Request human review."],
        "confidence": "medium",
    }


def _fixture_repo(repo_root: Path) -> RepoContext:
    _write_yaml(repo_root, "kb/draft/claims/app.yaml", _artifact_data())
    _write_yaml(repo_root, "issues/open/app.yaml", _issue_data())
    return RepoContext(repo_root)


def test_app_facade_delegates_read_and_check_use_cases(tmp_path: Path) -> None:
    context = _fixture_repo(tmp_path)
    app = CosheafApp(context)

    assert app.workspace_info() == WorkspaceService(context).info()
    assert open_app(tmp_path).workspace_info().repo_root == tmp_path

    assert (
        app.validate_repository().checked_count
        == ValidationService(context).validate_repository().checked_count
    )
    assert (
        app.validate_artifact_file("kb/draft/claims/app.yaml").ok
        == ValidationService(context)
        .validate_artifact_file("kb/draft/claims/app.yaml")
        .ok
    )

    gate = app.run_gate(timestamp="20260619T000000000000Z")
    service_gate = GateService(context).run(timestamp="20260619T000001000000Z")
    assert gate.report.verdict == service_gate.report.verdict == "pass"

    assert app.build_context("issue.fixture.app").issue_id == (
        ContextPackService(context).build("issue.fixture.app").issue_id
    )
    assert app.show_context("issue.fixture.app").startswith("# Context Pack")

    assert [card.id for card in app.memory_cards()] == [
        card.id for card in MemorySearchService(context).cards()
    ]
    assert app.memory_search(
        "app",
        status=ArtifactCardStatus.DRAFT,
    ).cards[0].card.id == "claim.fixture.app"


def test_app_facade_delegates_controlled_writes_and_bundle_review(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)
    app = CosheafApp(context)

    draft_request = DraftArtifactWriteRequest(
        artifact_id="claim.fixture.app-draft",
        artifact_type=ArtifactType.CLAIM,
        title="App facade draft",
        domain=["testing"],
        status=ArtifactStatus.DRAFT,
        statement="Draft preview through the app facade.",
        authors=["tester"],
    )
    draft = app.write_draft_artifact(draft_request, dry_run=True)
    service_draft = DraftWriteService(context).write_artifact_request(
        draft_request,
        dry_run=True,
    )
    assert draft == service_draft
    assert not (tmp_path / draft.relative_path).exists()

    review = app.write_review_request(
        {
            "review_id": "review.request.fixture.app",
            "title": "App facade review request",
            "status": "draft",
            "authors": ["tester"],
            "target": "claim.fixture.app",
            "summary": "Request human review later.",
            "findings": ["not human-reviewed"],
            "decision": "informational",
        },
        dry_run=True,
    )
    assert review.kind == "review_request"
    assert review.accepted_write_performed is False

    _write_yaml(tmp_path, "outputs/bundle.yaml", _bundle_v2_data())
    request = WorkerBundleSubmitRequest(
        task_id="task.issue.fixture.app.reasoner",
        bundle_path="outputs/bundle.yaml",
    )
    submitted = app.submit_bundle(request, dry_run=True)
    service_submitted = BundleValidationService(context).submit(
        request,
        dry_run=True,
    )
    assert submitted == service_submitted

    reducer = app.reduce_bundle(
        "outputs/bundle.yaml",
        reducer_id="reducer.issue.fixture.app.0001",
    )
    assert reducer.status == "accepted_for_review"
    assert "kb/draft/claims/app.yaml" in reducer.output_paths

    bundle_review = app.write_review_request_from_bundle(
        "outputs/bundle.yaml",
        dry_run=True,
    )
    assert bundle_review.write_result.kind == "review_request"
    assert bundle_review.write_result.accepted_write_performed is False


def test_app_facade_promotion_readiness_is_readonly(tmp_path: Path) -> None:
    context = _fixture_repo(tmp_path)
    report = CosheafApp(context).promotion_readiness(artifact_id="claim.fixture.app")

    assert report.target_mode == "artifact"
    assert report.artifact_id == "claim.fixture.app"
    assert report.accepted_write_performed is False
    assert not (tmp_path / "kb" / "accepted").exists()
