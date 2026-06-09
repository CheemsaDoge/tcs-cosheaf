from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from cosheaf.agent.task import WorkerType
from cosheaf.core.status import ArtifactStatus, ArtifactType
from cosheaf.memory import ArtifactCardStatus
from cosheaf.services import (
    BundleValidationService,
    ContextPackService,
    DraftWriteService,
    DraftWriteServiceError,
    GateService,
    MemorySearchService,
    TaskService,
    ValidationService,
    WorkspaceService,
)
from cosheaf.storage.repo import RepoContext


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(artifact_id: str = "claim.fixture.service") -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Service fixture claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-09T00:00:00Z",
        "updated_at": "2026-06-09T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["service"],
        "statement": "A service-layer fixture claim.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Service fixture review."},
        "risk": {"level": "low", "notes": "Service fixture risk."},
    }


def _issue_data(issue_id: str = "issue.fixture.service") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Service fixture issue",
        "status": "open",
        "created_at": "2026-06-09T00:00:00Z",
        "updated_at": "2026-06-09T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise service-layer entry points.",
        "related_artifacts": ["claim.fixture.service"],
        "tags": ["service"],
    }


def _bundle_v2_data() -> dict[str, Any]:
    return {
        "bundle_id": "bundle.issue.fixture.service.reasoner.0001",
        "task_id": "task.issue.fixture.service.reasoner",
        "worker_role": "reasoner",
        "created_at": "2026-06-09T00:00:00Z",
        "summary": "Service bundle fixture.",
        "used_artifacts": ["claim.fixture.service"],
        "used_sources": [],
        "claims": ["The service layer should preserve draft-only authority."],
        "proposed_artifacts": [
            {
                "path": "kb/draft/claims/service.yaml",
                "summary": "Draft service fixture.",
            }
        ],
        "verification_requests": ["Run validation and gate before review."],
        "failures_or_counterexamples": ["No machine proof was performed."],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Request human review."],
        "confidence": "medium",
    }


def _fixture_repo(repo_root: Path) -> RepoContext:
    _write_yaml(repo_root, "kb/draft/claims/service.yaml", _artifact_data())
    _write_yaml(repo_root, "issues/open/service.yaml", _issue_data())
    return RepoContext(repo_root)


def test_workspace_validation_gate_context_and_memory_services_return_typed_results(
    tmp_path: Path,
) -> None:
    context = _fixture_repo(tmp_path)

    workspace = WorkspaceService(context).info()
    assert workspace.name == tmp_path.name
    assert workspace.mode == "legacy"
    assert workspace.kb_roots[0].name == "default"

    validation = ValidationService(context).validate_repository()
    assert validation.ok is True
    assert validation.checked_count == 2

    gate = GateService(context).run(timestamp="20260609T000000000000Z")
    assert gate.report.verdict == "pass"
    assert gate.json_path.name == "20260609T000000000000Z-gate-report.json"

    cards = MemorySearchService(context).cards()
    assert [card.id for card in cards] == ["claim.fixture.service"]

    search = MemorySearchService(context).search(
        "service",
        status=ArtifactCardStatus.DRAFT,
    )
    assert search.cards[0].card.id == "claim.fixture.service"

    context_pack = ContextPackService(context).build("issue.fixture.service")
    assert context_pack.issue_id == "issue.fixture.service"
    assert context_pack.task_dir.name == "issue.fixture.service"
    assert ContextPackService(context).show("issue.fixture.service").startswith(
        "# Context Pack"
    )


def test_task_and_bundle_services_preserve_review_only_outputs(tmp_path: Path) -> None:
    context = _fixture_repo(tmp_path)

    task_service = TaskService(context)
    task = task_service.create_task(
        issue_id="issue.fixture.service",
        worker_type=WorkerType.REASONER,
    )
    assert task.task_id == "task.issue.fixture.service.reasoner"
    assert task_service.list_tasks()[0].task_id == task.task_id

    _write_yaml(tmp_path, "outputs/bundle.yaml", _bundle_v2_data())
    bundle = BundleValidationService(context).validate("outputs/bundle.yaml")
    assert bundle.task_id == "task.issue.fixture.service.reasoner"

    run = task_service.run_task(
        task.task_id,
        command=[sys.executable, "-c", "print('service runner')"],
        timeout_seconds=10,
    )
    assert run.status == "completed"
    assert run.returncode == 0

    reducer = BundleValidationService(context).reduce(
        "outputs/bundle.yaml",
        reducer_id="reducer.issue.fixture.service.0001",
    )
    assert reducer.status == "accepted_for_review"
    assert reducer.output_paths == ["kb/draft/claims/service.yaml"]


def test_draft_write_service_creates_draft_and_refuses_accepted(
    tmp_path: Path,
) -> None:
    context = RepoContext(tmp_path)
    service = DraftWriteService(context)

    result = service.create_artifact(
        artifact_id="claim.fixture.draft-service",
        artifact_type=ArtifactType.CLAIM,
        title="Draft service claim",
        domain=["testing"],
        status=ArtifactStatus.DRAFT,
        statement="Draft created through the service layer.",
        authors=["tester"],
        tags=[],
        depends_on=[],
        supersedes=[],
        created_at="2026-06-09T00:00:00Z",
    )
    assert result.relative_path.as_posix() == (
        "kb/draft/claims/claim.fixture.draft-service.yaml"
    )
    assert result.artifact.status is ArtifactStatus.DRAFT
    assert not (tmp_path / "kb" / "accepted").exists()

    with pytest.raises(DraftWriteServiceError, match="accepted artifacts"):
        service.create_artifact(
            artifact_id="claim.fixture.accepted-service",
            artifact_type=ArtifactType.CLAIM,
            title="Accepted service claim",
            domain=["testing"],
            status=ArtifactStatus.ACCEPTED,
            statement="Accepted writes are forbidden through DraftWriteService.",
            authors=["tester"],
            tags=[],
            depends_on=[],
            supersedes=[],
            created_at="2026-06-09T00:00:00Z",
        )


def test_draft_write_service_errors_expose_stable_error_codes(
    tmp_path: Path,
) -> None:
    service = DraftWriteService(RepoContext(tmp_path))

    with pytest.raises(DraftWriteServiceError) as accepted_error:
        service.create_artifact(
            artifact_id="claim.fixture.accepted-service",
            artifact_type=ArtifactType.CLAIM,
            title="Accepted service claim",
            domain=["testing"],
            status=ArtifactStatus.ACCEPTED,
            statement="Accepted writes are forbidden through DraftWriteService.",
            authors=["tester"],
            tags=[],
            depends_on=[],
            supersedes=[],
            created_at="2026-06-09T00:00:00Z",
        )

    assert accepted_error.value.code == "accepted_write_forbidden"
    accepted_result = accepted_error.value.to_error_result()
    assert accepted_result.code == "accepted_write_forbidden"
    assert accepted_result.blocking is True
    assert "promotion" in accepted_result.remediation

    with pytest.raises(DraftWriteServiceError) as domain_error:
        service.create_artifact(
            artifact_id="claim.fixture.missing-domain",
            artifact_type=ArtifactType.CLAIM,
            title="Missing domain claim",
            domain=[],
            status=ArtifactStatus.DRAFT,
            statement="Domain is required.",
            authors=["tester"],
            tags=[],
            depends_on=[],
            supersedes=[],
            created_at="2026-06-09T00:00:00Z",
        )

    assert domain_error.value.code == "missing_required_domain"
