from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _issue_data(issue_id: str = "issue.fixture.task") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Create an agent task",
        "status": "open",
        "created_at": "2026-06-02T00:00:00Z",
        "updated_at": "2026-06-02T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise the task CLI.",
        "related_artifacts": [],
        "tags": ["task-cli"],
    }


def _artifact_data(artifact_id: str = "claim.fixture.task-output") -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Task output claim",
        "domain": ["testing"],
        "status": "draft",
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


def _create_reasoner_task(repo_root: Path) -> str:
    _write_yaml(repo_root, "issues/open/task.yaml", _issue_data())
    result = runner.invoke(
        app,
        [
            "task",
            "create",
            "--issue",
            "issue.fixture.task",
            "--worker",
            "reasoner",
            "--repo-root",
            str(repo_root),
        ],
    )
    assert result.exit_code == 0, result.output
    return "task.issue.fixture.task.reasoner"


def test_task_create_writes_runtime_task_file(tmp_path: Path) -> None:
    task_id = _create_reasoner_task(tmp_path)

    task_path = tmp_path / ".cosheaf" / "tasks" / f"{task_id}.yaml"
    assert task_path.is_file()
    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    assert task["task_id"] == task_id
    assert task["issue_id"] == "issue.fixture.task"
    assert task["worker_type"] == "reasoner"
    assert task["status"] == "open"


def test_task_list_shows_tasks_in_deterministic_order(tmp_path: Path) -> None:
    task_id = _create_reasoner_task(tmp_path)

    result = runner.invoke(
        app,
        ["task", "list", "--repo-root", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert task_id in result.output
    assert "reasoner" in result.output
    assert "open" in result.output


def test_task_complete_accepts_valid_bundle_without_merging_accepted_knowledge(
    tmp_path: Path,
) -> None:
    task_id = _create_reasoner_task(tmp_path)
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

    result = runner.invoke(
        app,
        [
            "task",
            "complete",
            task_id,
            "--bundle",
            str(tmp_path / "outputs" / "bundle.yaml"),
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    task = yaml.safe_load(
        (tmp_path / ".cosheaf" / "tasks" / f"{task_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert task["status"] == "completed"
    assert not (tmp_path / "kb" / "accepted").exists()


def test_task_run_executes_command_and_prints_run_directory(tmp_path: Path) -> None:
    task_id = _create_reasoner_task(tmp_path)

    result = runner.invoke(
        app,
        [
            "task",
            "run",
            task_id,
            "--timeout-seconds",
            "10",
            "--repo-root",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "print('cli worker')",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "status: completed" in result.output
    assert "returncode: 0" in result.output
    assert ".cosheaf" in result.output
    run_records = list((tmp_path / ".cosheaf" / "tasks" / task_id / "runs").glob("*"))
    assert len(run_records) == 1
    assert (run_records[0] / "stdout.txt").read_text(encoding="utf-8") == (
        "cli worker\n"
    )


def test_task_run_failing_command_exits_nonzero(tmp_path: Path) -> None:
    task_id = _create_reasoner_task(tmp_path)

    result = runner.invoke(
        app,
        [
            "task",
            "run",
            task_id,
            "--timeout-seconds",
            "10",
            "--repo-root",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "import sys; sys.exit(5)",
        ],
    )

    assert result.exit_code != 0
    assert "status: failed" in result.output
    assert "returncode: 5" in result.output


def test_task_run_timeout_exits_nonzero(tmp_path: Path) -> None:
    task_id = _create_reasoner_task(tmp_path)

    result = runner.invoke(
        app,
        [
            "task",
            "run",
            task_id,
            "--timeout-seconds",
            "1",
            "--repo-root",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "import time; time.sleep(5)",
        ],
    )

    assert result.exit_code != 0
    assert "status: timed_out" in result.output


def test_task_run_with_bundle_validates_but_does_not_complete_task(
    tmp_path: Path,
) -> None:
    task_id = _create_reasoner_task(tmp_path)
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

    result = runner.invoke(
        app,
        [
            "task",
            "run",
            task_id,
            "--bundle",
            str(tmp_path / "outputs" / "bundle.yaml"),
            "--timeout-seconds",
            "10",
            "--repo-root",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "print('ok')",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "bundle_valid: true" in result.output
    task = yaml.safe_load(
        (tmp_path / ".cosheaf" / "tasks" / f"{task_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert task["status"] == "open"


def test_task_run_complete_with_bundle_delegates_task_completion(
    tmp_path: Path,
) -> None:
    task_id = _create_reasoner_task(tmp_path)
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

    result = runner.invoke(
        app,
        [
            "task",
            "run",
            task_id,
            "--complete-with-bundle",
            str(tmp_path / "outputs" / "bundle.yaml"),
            "--timeout-seconds",
            "10",
            "--repo-root",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "print('ok')",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "task_completed: true" in result.output
    task = yaml.safe_load(
        (tmp_path / ".cosheaf" / "tasks" / f"{task_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert task["status"] == "completed"


def test_task_run_invalid_bundle_exits_nonzero(tmp_path: Path) -> None:
    task_id = _create_reasoner_task(tmp_path)
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

    result = runner.invoke(
        app,
        [
            "task",
            "run",
            task_id,
            "--bundle",
            str(tmp_path / "outputs" / "bundle.yaml"),
            "--timeout-seconds",
            "10",
            "--repo-root",
            str(tmp_path),
            "--",
            sys.executable,
            "-c",
            "print('ok')",
        ],
    )

    assert result.exit_code != 0
    assert "status: bundle_invalid" in result.output
    assert "bundle_valid: false" in result.output


def test_invalid_worker_type_fails_cli(tmp_path: Path) -> None:
    _write_yaml(tmp_path, "issues/open/task.yaml", _issue_data())

    result = runner.invoke(
        app,
        [
            "task",
            "create",
            "--issue",
            "issue.fixture.task",
            "--worker",
            "not-a-worker",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "not-a-worker" in result.output


def test_missing_issue_fails_cli(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "task",
            "create",
            "--issue",
            "issue.fixture.missing",
            "--worker",
            "reasoner",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "issue not found: issue.fixture.missing" in result.output
    assert "Traceback" not in result.output
