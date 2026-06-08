from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from cosheaf.agent.task import WorkerType
from cosheaf.agent.worker_bundle_v2 import (
    WorkerBundleV2,
    WorkerBundleV2Error,
    reduce_worker_bundle_v2,
    validate_worker_bundle_v2,
)
from cosheaf.storage.repo import RepoContext

NOW = datetime(2026, 6, 7, 11, 0, tzinfo=UTC)


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(
    artifact_id: str = "claim.fixture.worker-bundle-v2",
    *,
    status: str = "draft",
    review_state: str = "requested",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Worker bundle v2 fixture",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-07T00:00:00Z",
        "updated_at": "2026-06-07T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["worker-bundle-v2"],
        "statement": "A draft claim proposed by a worker bundle fixture.",
        "evidence": [],
        "review": {"state": review_state, "notes": "Worker output review pending."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _bundle_data(
    *,
    proposed_path: str = "kb/draft/claims/worker-bundle-v2.yaml",
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "bundle_id": "bundle.issue.fixture.worker-bundle-v2.reasoner.0001",
        "task_id": "task.issue.fixture.worker-bundle-v2.reasoner",
        "worker_role": "reasoner",
        "created_at": "2026-06-07T11:00:00Z",
        "summary": "Drafted one reviewable claim and preserved uncertainty.",
        "used_artifacts": ["definition.graph"],
        "used_sources": ["sources/books/diestel-2017.yaml"],
        "claims": ["The fixture claim should remain draft until review."],
        "proposed_artifacts": [
            {
                "path": proposed_path,
                "summary": "Draft claim proposed by the worker.",
            }
        ],
        "verification_requests": [
            "Run cosheaf validate and gate before any review decision."
        ],
        "failures_or_counterexamples": [
            "No machine proof or Lean check was performed."
        ],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Request human review before promotion."],
        "confidence": confidence,
    }


def test_worker_bundle_v2_is_strict_and_deterministic() -> None:
    bundle = WorkerBundleV2.model_validate(_bundle_data())

    assert bundle.bundle_id == "bundle.issue.fixture.worker-bundle-v2.reasoner.0001"
    assert bundle.worker_role is WorkerType.REASONER
    assert bundle.created_at == NOW
    assert bundle.proposed_artifacts[0].path == "kb/draft/claims/worker-bundle-v2.yaml"
    assert bundle.to_json() == bundle.to_json()

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WorkerBundleV2.model_validate({**_bundle_data(), "extra_field": "nope"})


def test_validate_worker_bundle_v2_rejects_paths_outside_repo(tmp_path: Path) -> None:
    external = tmp_path.parent / "outside.yaml"
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        _bundle_data(proposed_path=str(external)),
    )

    with pytest.raises(WorkerBundleV2Error, match="repository-local"):
        validate_worker_bundle_v2(RepoContext(tmp_path), "outputs/bundle.yaml")


def test_validate_worker_bundle_v2_rejects_nested_parent_directory_segments(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        _bundle_data(proposed_path="kb/draft/../claims/worker-bundle-v2.yaml"),
    )

    with pytest.raises(WorkerBundleV2Error, match="repository-local"):
        validate_worker_bundle_v2(RepoContext(tmp_path), "outputs/bundle.yaml")


def test_validate_worker_bundle_v2_rejects_accepted_kb_proposals(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        _bundle_data(proposed_path="kb/accepted/claims/unsafe.yaml"),
    )

    with pytest.raises(WorkerBundleV2Error, match="accepted knowledge"):
        validate_worker_bundle_v2(RepoContext(tmp_path), "outputs/bundle.yaml")


def test_validate_worker_bundle_v2_rejects_human_reviewed_artifact_creation(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/worker-bundle-v2.yaml",
        _artifact_data(review_state="human_reviewed"),
    )
    _write_yaml(tmp_path, "outputs/bundle.yaml", _bundle_data())

    with pytest.raises(WorkerBundleV2Error, match="human_reviewed"):
        validate_worker_bundle_v2(RepoContext(tmp_path), "outputs/bundle.yaml")


def test_reduce_worker_bundle_v2_preserves_failures_and_uncertainty(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/worker-bundle-v2.yaml",
        _artifact_data(),
    )
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        _bundle_data(confidence="low"),
    )

    result = reduce_worker_bundle_v2(
        RepoContext(tmp_path),
        "outputs/bundle.yaml",
        reducer_id="reducer.issue.fixture.worker-bundle-v2.0001",
    )

    assert result.reducer_id == "reducer.issue.fixture.worker-bundle-v2.0001"
    assert result.status == "accepted_for_review"
    assert result.output_paths == ["kb/draft/claims/worker-bundle-v2.yaml"]
    assert any("No machine proof" in warning for warning in result.warnings)
    assert "risk: needs_human_review" in result.warnings
    assert "confidence: low" in result.warnings
