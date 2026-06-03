from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from cosheaf.agent.task import AgentTask, TaskStatus, WorkerType, create_task_id
from cosheaf.agent.worker_contract import OutputBundleError, validate_output_bundle
from cosheaf.storage.repo import RepoContext

NOW = datetime(2026, 6, 2, 8, 30, tzinfo=UTC)


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _artifact_data(
    artifact_id: str,
    *,
    status: str = "draft",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Task output claim",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-02T00:00:00Z",
        "updated_at": "2026-06-02T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["task-output"],
        "statement": "A draft output that still goes through artifact gates.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Task output review pending."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def test_task_model_generates_deterministic_id() -> None:
    task = AgentTask.create(
        issue_id="issue.fixture.task",
        worker_type=WorkerType.REASONER,
        now=NOW,
    )

    assert task.task_id == "task.issue.fixture.task.reasoner"
    assert task.issue_id == "issue.fixture.task"
    assert task.worker_type is WorkerType.REASONER
    assert task.status is TaskStatus.OPEN
    assert task.input_context == []
    assert task.budget == {}
    assert "gate_ready_yaml" in task.expected_outputs
    assert task.created_at == NOW
    assert task.updated_at == NOW


def test_task_id_slugifies_worker_type() -> None:
    assert (
        create_task_id("issue.fixture.task", WorkerType.CONSTRUCTION_SEARCHER)
        == "task.issue.fixture.task.construction-searcher"
    )


def test_task_model_preserves_explicit_empty_expected_outputs() -> None:
    task = AgentTask.create(
        issue_id="issue.fixture.task",
        worker_type=WorkerType.REASONER,
        now=NOW,
        expected_outputs=[],
    )

    assert task.expected_outputs == []


def test_invalid_worker_type_fails_model_validation() -> None:
    with pytest.raises(ValidationError):
        AgentTask.model_validate(
            {
                "task_id": "task.issue.fixture.task.unknown",
                "issue_id": "issue.fixture.task",
                "worker_type": "unknown",
                "status": "open",
                "input_context": [],
                "budget": {},
                "expected_outputs": ["gate_ready_yaml"],
                "created_at": "2026-06-02T00:00:00Z",
                "updated_at": "2026-06-02T00:00:00Z",
            }
        )


def test_task_status_accepts_protocol_lifecycle_values() -> None:
    status_values = {status.value for status in TaskStatus}

    assert status_values == {
        "open",
        "in_progress",
        "blocked",
        "completed",
        "failed",
        "cancelled",
    }


def test_validate_output_bundle_accepts_gate_ready_draft_artifact(
    tmp_path: Path,
) -> None:
    task = AgentTask.create(
        issue_id="issue.fixture.task",
        worker_type=WorkerType.VERIFIER,
        now=NOW,
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/output.yaml",
        _artifact_data("claim.fixture.task-output"),
    )
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task.task_id,
            "worker_type": "verifier",
            "outputs": [
                {
                    "kind": "artifact",
                    "path": "kb/draft/claims/output.yaml",
                    "summary": "Draft claim emitted by a worker.",
                }
            ],
            "notes": "No accepted knowledge merge.",
        },
    )

    bundle = validate_output_bundle(
        RepoContext(tmp_path),
        tmp_path / "outputs" / "bundle.yaml",
        task=task,
    )

    assert bundle.task_id == task.task_id
    assert bundle.outputs[0].path == "kb/draft/claims/output.yaml"


def test_validate_output_bundle_rejects_accepted_knowledge_output(
    tmp_path: Path,
) -> None:
    task = AgentTask.create(
        issue_id="issue.fixture.task",
        worker_type=WorkerType.REASONER,
        now=NOW,
    )
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/output.yaml",
        _artifact_data("claim.fixture.accepted-output", status="accepted"),
    )
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task.task_id,
            "worker_type": "reasoner",
            "outputs": [
                {
                    "kind": "artifact",
                    "path": "kb/accepted/claims/output.yaml",
                    "summary": "This would bypass accepted knowledge gates.",
                }
            ],
        },
    )

    with pytest.raises(OutputBundleError, match="accepted knowledge"):
        validate_output_bundle(
            RepoContext(tmp_path),
            tmp_path / "outputs" / "bundle.yaml",
            task=task,
        )
