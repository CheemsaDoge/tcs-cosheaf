from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.agent.orchestrator_runner import (
    OrchestratorLocalRunConfig,
    OrchestratorLocalRunError,
    OrchestratorLocalRunner,
)
from cosheaf.cli import app
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _issue_data(issue_id: str = "issue.fixture.orchestrator-run") -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": "issue",
        "title": "Run a local-only orchestrator plan",
        "status": "open",
        "created_at": "2026-06-07T00:00:00Z",
        "updated_at": "2026-06-07T00:00:00Z",
        "authors": ["tester"],
        "severity": "medium",
        "description": "Exercise deterministic local orchestrator execution.",
        "related_artifacts": ["claim.fixture.orchestrator-run"],
        "tags": ["orchestrator", "local-runner"],
    }


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "claim.fixture.orchestrator-run",
        "type": "claim",
        "title": "Orchestrator runner fixture claim",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-07T00:00:00Z",
        "updated_at": "2026-06-07T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["orchestrator"],
        "statement": "A fixture claim used by the local orchestrator runner.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Fixture review pending."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _write_repo(repo_root: Path) -> None:
    _write_yaml(repo_root, "issues/open/orchestrator-run.yaml", _issue_data())
    _write_yaml(repo_root, "kb/draft/claims/orchestrator-run.yaml", _artifact_data())


def test_orchestrator_run_dry_run_local_only_executes_plan_and_records_logs(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    result = runner.invoke(
        app,
        [
            "orchestrator",
            "run",
            "--issue",
            "issue.fixture.orchestrator-run",
            "--dry-run",
            "--local-only",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Orchestrator run: run.issue.fixture.orchestrator-run" in result.output
    assert "state: completed" in result.output
    assert "local_only: true" in result.output
    assert "hosted_llm: not used" in result.output
    assert "accepted_writes: not performed" in result.output

    run_root = (
        tmp_path
        / ".cosheaf"
        / "orchestrator"
        / "issue.fixture.orchestrator-run"
        / "runs"
        / "run.issue.fixture.orchestrator-run"
    )
    record_path = run_root / "run.yaml"
    assert record_path.is_file()
    record = yaml.safe_load(record_path.read_text(encoding="utf-8"))
    assert record["state"] == "completed"
    assert record["plan"]["plan_id"] == "plan.issue.fixture.orchestrator-run"
    assert len(record["worker_calls"]) == 4
    assert len(record["reducer_results"]) == 4
    assert not (tmp_path / "kb" / "accepted").exists()

    for call in record["worker_calls"]:
        assert call["status"] == "completed"
        assert call["command"][0] == sys.executable
        assert call["cwd"] == "."
        assert call["stdout_path"].endswith("/stdout.txt")
        assert call["stderr_path"].endswith("/stderr.txt")
        assert (tmp_path / call["stdout_path"]).is_file()
        assert (tmp_path / call["stderr_path"]).is_file()
        assert call["bundle_path"].startswith(
            ".cosheaf/orchestrator/issue.fixture.orchestrator-run/"
        )


def test_orchestrator_run_timeout_exits_nonzero_and_records_failed_run(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    result = OrchestratorLocalRunner(RepoContext(tmp_path)).run_issue(
        OrchestratorLocalRunConfig(
            issue_id="issue.fixture.orchestrator-run",
            timeout_seconds=1,
            worker_command=[
                sys.executable,
                "-c",
                "import time; time.sleep(5)",
            ],
        )
    )

    assert result.run.state.value == "failed"
    assert result.run.worker_calls[0].status == "timed_out"
    assert result.run.worker_calls[0].exit_code is None
    record = yaml.safe_load(
        (
            tmp_path
            / ".cosheaf"
            / "orchestrator"
            / "issue.fixture.orchestrator-run"
            / "runs"
            / "run.issue.fixture.orchestrator-run"
            / "run.yaml"
        ).read_text(encoding="utf-8")
    )
    assert record["state"] == "failed"
    assert record["worker_calls"][0]["status"] == "timed_out"
    assert record["worker_calls"][0]["exit_code"] is None


def test_orchestrator_run_can_repeat_issue_with_distinct_run_ids(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    first = OrchestratorLocalRunner(RepoContext(tmp_path)).run_issue(
        OrchestratorLocalRunConfig(
            issue_id="issue.fixture.orchestrator-run",
            run_id="run.issue.fixture.orchestrator-run.0001",
        )
    )
    second = OrchestratorLocalRunner(RepoContext(tmp_path)).run_issue(
        OrchestratorLocalRunConfig(
            issue_id="issue.fixture.orchestrator-run",
            run_id="run.issue.fixture.orchestrator-run.0002",
        )
    )

    assert first.run.state.value == "completed"
    assert second.run.state.value == "completed"
    first_call = first.run.worker_calls[0]
    second_call = second.run.worker_calls[0]
    assert first_call.stdout_path is not None
    assert second_call.stdout_path is not None
    assert first_call.stdout_path != second_call.stdout_path
    assert "run.issue.fixture.orchestrator-run.0001" in first_call.stdout_path
    assert "run.issue.fixture.orchestrator-run.0002" in second_call.stdout_path


def test_orchestrator_run_does_not_replace_invalid_existing_task(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)
    task_path = (
        tmp_path
        / ".cosheaf"
        / "tasks"
        / "task.node.issue.fixture.orchestrator-run.librarian-retrieval.yaml"
    )
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text("task_id: invalid\n", encoding="utf-8")

    with pytest.raises(OrchestratorLocalRunError, match="invalid task record"):
        OrchestratorLocalRunner(RepoContext(tmp_path)).run_issue(
            OrchestratorLocalRunConfig(
                issue_id="issue.fixture.orchestrator-run",
            )
        )


def test_orchestrator_run_rejects_unsafe_worker_bundle_without_accepted_writes(
    tmp_path: Path,
) -> None:
    _write_repo(tmp_path)

    result = OrchestratorLocalRunner(RepoContext(tmp_path)).run_issue(
        OrchestratorLocalRunConfig(
            issue_id="issue.fixture.orchestrator-run",
            proposal_path="kb/accepted/claims/unsafe.yaml",
        )
    )

    assert result.run.state.value == "failed"
    assert any(
        "accepted knowledge" in stop.description
        for stop in result.run.stop_conditions
    )
    assert not (tmp_path / "kb" / "accepted" / "claims" / "unsafe.yaml").exists()
