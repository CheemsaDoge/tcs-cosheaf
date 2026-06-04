from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from cosheaf.agent.local_runner import (
    LocalWorkerRunConfig,
    LocalWorkerRunError,
    LocalWorkerRunner,
)
from cosheaf.agent.orchestrator_stub import OrchestratorStub
from cosheaf.agent.task import WorkerType
from cosheaf.storage.repo import RepoContext

NOW = datetime(2026, 6, 4, 8, 0, tzinfo=UTC)
WORKER_ECHO_SCRIPT = (
    "import sys; "
    "print('worker stdout'); "
    "print('worker stderr', file=sys.stderr)"
)


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _issue_data(issue_id: str = "issue.fixture.local-runner") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Run a local worker",
        "status": "open",
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise the local worker runner.",
        "related_artifacts": [],
        "tags": ["local-runner"],
    }


def _artifact_data(
    artifact_id: str = "claim.fixture.local-runner-output",
    *,
    status: str = "draft",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Local runner output claim",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["local-runner"],
        "statement": "A draft output produced by a local command.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Pending review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _create_task(repo_root: Path) -> str:
    _write_yaml(repo_root, "issues/open/local-runner.yaml", _issue_data())
    task = OrchestratorStub(RepoContext(repo_root)).create_task(
        issue_id="issue.fixture.local-runner",
        worker_type=WorkerType.REASONER,
        now=NOW,
    )
    return task.task_id


def test_successful_command_writes_run_directory_stdout_stderr_and_record(
    tmp_path: Path,
) -> None:
    task_id = _create_task(tmp_path)

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[
                sys.executable,
                "-c",
                WORKER_ECHO_SCRIPT,
            ],
            timeout_seconds=10,
            run_id="run.fixture.success",
            started_at=NOW,
        ),
    )

    assert result.status == "completed"
    assert result.returncode == 0
    assert result.run_dir == (
        tmp_path / ".cosheaf" / "tasks" / task_id / "runs" / "run.fixture.success"
    )
    assert result.stdout_path.read_text(encoding="utf-8") == "worker stdout\n"
    assert result.stderr_path.read_text(encoding="utf-8") == "worker stderr\n"

    record = yaml.safe_load(result.record_path.read_text(encoding="utf-8"))
    assert record == {
        "schema_version": 1,
        "task_id": task_id,
        "worker_type": "reasoner",
        "command": [
            sys.executable,
            "-c",
            WORKER_ECHO_SCRIPT,
        ],
        "cwd": ".",
        "started_at": "2026-06-04T08:00:00Z",
        "finished_at": "2026-06-04T08:00:00Z",
        "timeout_seconds": 10,
        "returncode": 0,
        "stdout_path": "stdout.txt",
        "stderr_path": "stderr.txt",
        "bundle_path": None,
        "bundle_valid": None,
        "status": "completed",
    }


def test_failing_command_records_nonzero_return_code(tmp_path: Path) -> None:
    task_id = _create_task(tmp_path)

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "import sys; sys.exit(7)"],
            timeout_seconds=10,
            run_id="run.fixture.failed",
            started_at=NOW,
        ),
    )

    record = yaml.safe_load(result.record_path.read_text(encoding="utf-8"))
    assert result.status == "failed"
    assert result.returncode == 7
    assert record["status"] == "failed"
    assert record["returncode"] == 7


def test_timeout_records_timed_out_status(tmp_path: Path) -> None:
    task_id = _create_task(tmp_path)

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "import time; time.sleep(5)"],
            timeout_seconds=1,
            run_id="run.fixture.timeout",
            started_at=NOW,
        ),
    )

    record = yaml.safe_load(result.record_path.read_text(encoding="utf-8"))
    assert result.status == "timed_out"
    assert result.returncode is None
    assert record["status"] == "timed_out"
    assert record["returncode"] is None


def test_cwd_outside_repo_is_rejected(tmp_path: Path) -> None:
    task_id = _create_task(tmp_path)

    with pytest.raises(LocalWorkerRunError, match="cwd must stay inside repository"):
        LocalWorkerRunner(RepoContext(tmp_path)).run_task(
            task_id,
            LocalWorkerRunConfig(
                command=[sys.executable, "-c", "print('unused')"],
                cwd=tmp_path.parent,
                timeout_seconds=10,
            ),
        )


def test_task_not_found_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(LocalWorkerRunError, match="task not found"):
        LocalWorkerRunner(RepoContext(tmp_path)).run_task(
            "task.issue.fixture.local-runner.reasoner",
            LocalWorkerRunConfig(
                command=[sys.executable, "-c", "print('unused')"],
                timeout_seconds=10,
            ),
        )


def test_command_must_be_explicit_argv_not_shell_string() -> None:
    with pytest.raises(LocalWorkerRunError, match="explicit argv"):
        LocalWorkerRunConfig(command="python -c 'print(1)'")  # type: ignore[arg-type]


def test_valid_optional_bundle_passes_validation(tmp_path: Path) -> None:
    task_id = _create_task(tmp_path)
    _write_yaml(tmp_path, "kb/draft/claims/output.yaml", _artifact_data())
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task_id,
            "worker_type": "reasoner",
            "outputs": [
                {
                    "kind": "artifact",
                    "path": "kb/draft/claims/output.yaml",
                    "summary": "Draft claim emitted by a worker.",
                }
            ],
        },
    )

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "print('ok')"],
            timeout_seconds=10,
            bundle_path=Path("outputs/bundle.yaml"),
            run_id="run.fixture.bundle",
            started_at=NOW,
        ),
    )

    record = yaml.safe_load(result.record_path.read_text(encoding="utf-8"))
    assert result.status == "completed"
    assert result.bundle_valid is True
    assert record["bundle_path"] == "outputs/bundle.yaml"
    assert record["bundle_valid"] is True


def test_valid_optional_bundle_directory_uses_contained_bundle_yaml(
    tmp_path: Path,
) -> None:
    task_id = _create_task(tmp_path)
    _write_yaml(tmp_path, "kb/draft/claims/output.yaml", _artifact_data())
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task_id,
            "worker_type": "reasoner",
            "outputs": [
                {
                    "kind": "artifact",
                    "path": "kb/draft/claims/output.yaml",
                    "summary": "Draft claim emitted by a worker.",
                }
            ],
        },
    )

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "print('ok')"],
            timeout_seconds=10,
            bundle_path=Path("outputs"),
            run_id="run.fixture.bundle-dir",
            started_at=NOW,
        ),
    )

    record = yaml.safe_load(result.record_path.read_text(encoding="utf-8"))
    assert result.status == "completed"
    assert result.bundle_valid is True
    assert record["bundle_path"] == "outputs/bundle.yaml"
    assert record["bundle_valid"] is True


def test_external_absolute_bundle_path_is_rejected_before_run_creation(
    tmp_path: Path,
) -> None:
    task_id = _create_task(tmp_path)
    external_bundle_path = tmp_path.parent / "external-local-runner-bundle.yaml"
    external_bundle_path.write_text("task_id: external\n", encoding="utf-8")

    with pytest.raises(
        LocalWorkerRunError,
        match="bundle_path must stay inside repository",
    ):
        LocalWorkerRunner(RepoContext(tmp_path)).run_task(
            task_id,
            LocalWorkerRunConfig(
                command=[
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('command-ran').write_text('bad')",
                ],
                timeout_seconds=10,
                bundle_path=external_bundle_path,
                run_id="run.fixture.external-bundle",
                started_at=NOW,
            ),
        )

    assert not (tmp_path / "command-ran").exists()
    assert not (tmp_path / ".cosheaf" / "tasks" / task_id / "runs").exists()


def test_invalid_bundle_is_reported_without_accepting_run(tmp_path: Path) -> None:
    task_id = _create_task(tmp_path)
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task_id,
            "worker_type": "reasoner",
            "outputs": [
                {
                    "kind": "report",
                    "path": "outputs/missing.md",
                    "summary": "Missing report.",
                }
            ],
        },
    )

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "print('ok')"],
            timeout_seconds=10,
            bundle_path=Path("outputs/bundle.yaml"),
            run_id="run.fixture.invalid-bundle",
            started_at=NOW,
        ),
    )

    assert result.status == "bundle_invalid"
    assert result.bundle_valid is False
    stderr = result.stderr_path.read_text(encoding="utf-8")
    assert "output path does not exist" in stderr


def test_bundle_targeting_accepted_knowledge_is_rejected(tmp_path: Path) -> None:
    task_id = _create_task(tmp_path)
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/output.yaml",
        _artifact_data("claim.fixture.accepted-output", status="accepted"),
    )
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task_id,
            "worker_type": "reasoner",
            "outputs": [
                {
                    "kind": "artifact",
                    "path": "kb/accepted/claims/output.yaml",
                    "summary": "This would bypass promotion.",
                }
            ],
        },
    )

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "print('ok')"],
            timeout_seconds=10,
            bundle_path=Path("outputs/bundle.yaml"),
            run_id="run.fixture.accepted-rejected",
            started_at=NOW,
        ),
    )

    assert result.status == "bundle_invalid"
    assert result.bundle_valid is False
    assert "accepted knowledge" in result.stderr_path.read_text(encoding="utf-8")


def test_valid_bundle_does_not_promote_or_modify_accepted_knowledge(
    tmp_path: Path,
) -> None:
    task_id = _create_task(tmp_path)
    _write_yaml(tmp_path, "kb/draft/claims/output.yaml", _artifact_data())
    _write_yaml(
        tmp_path,
        "kb/accepted/claims/existing.yaml",
        _artifact_data("claim.fixture.accepted-existing", status="accepted"),
    )
    accepted_path = tmp_path / "kb" / "accepted" / "claims" / "existing.yaml"
    accepted_before = accepted_path.read_text(encoding="utf-8")
    _write_yaml(
        tmp_path,
        "outputs/bundle.yaml",
        {
            "task_id": task_id,
            "worker_type": "reasoner",
            "outputs": [
                {
                    "kind": "artifact",
                    "path": "kb/draft/claims/output.yaml",
                    "summary": "Draft claim emitted by a worker.",
                }
            ],
        },
    )

    result = LocalWorkerRunner(RepoContext(tmp_path)).run_task(
        task_id,
        LocalWorkerRunConfig(
            command=[sys.executable, "-c", "print('ok')"],
            timeout_seconds=10,
            bundle_path=Path("outputs/bundle.yaml"),
            run_id="run.fixture.no-promotion",
            started_at=NOW,
        ),
    )

    assert result.status == "completed"
    assert accepted_path.read_text(encoding="utf-8") == accepted_before
    assert not (
        tmp_path
        / "kb"
        / "accepted"
        / "claims"
        / "claim.fixture.local-runner-output.yaml"
    ).exists()
