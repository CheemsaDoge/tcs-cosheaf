from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.research.run import RESEARCH_RUN_AUTHORITY_NOTICE

runner = CliRunner()


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _assert_json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_research_run_cli_lifecycle_and_review_export(tmp_path: Path) -> None:
    run_id = "run.issue.fixture.research.0001"
    start = runner.invoke(
        app,
        [
            "run",
            "start",
            "--issue",
            "issue.fixture.research",
            "--operator",
            "external",
            "--operator-label",
            "Codex CLI",
            "--run-id",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert start.exit_code == 0, start.output
    start_payload = _assert_json(start.output)
    assert start_payload["kind"] == "research_run"
    assert start_payload["run_id"] == run_id
    assert start_payload["status"] == "in_progress"
    assert start_payload["path"] == f".cosheaf/runs/{run_id}/run.json"
    assert start_payload["accepted_write_performed"] is False
    assert start_payload["authority_notice"] == RESEARCH_RUN_AUTHORITY_NOTICE

    command_input = _write_json(
        tmp_path,
        "requests/command.json",
        {
            "argv": ["python", "-m", "pytest", "--api-key", "sk-secret-value"],
            "cwd": ".",
            "started_at": "2026-06-15T01:00:00Z",
            "ended_at": "2026-06-15T01:01:00Z",
            "exit_code": 0,
            "status": "completed",
            "stdout_path": ".cosheaf/runs/run.issue.fixture.research.0001/stdout.txt",
            "stderr_path": ".cosheaf/runs/run.issue.fixture.research.0001/stderr.txt",
        },
    )
    append_command = runner.invoke(
        app,
        [
            "run",
            "append-command",
            "--run",
            run_id,
            "--input-json",
            str(command_input),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_command.exit_code == 0, append_command.output
    command_payload = _assert_json(append_command.output)
    assert command_payload["command_count"] == 1
    assert "sk-secret-value" not in append_command.output
    assert command_payload["run"]["commands"][0]["argv"][-1] == "<redacted>"

    append_artifact = runner.invoke(
        app,
        [
            "run",
            "append-artifact",
            "--run",
            run_id,
            "--artifact",
            "claim.fixture.target",
            "--mode",
            "read",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_artifact.exit_code == 0, append_artifact.output
    assert _assert_json(append_artifact.output)["run"]["artifacts_read"] == [
        "claim.fixture.target"
    ]

    output_input = _write_json(
        tmp_path,
        "requests/output.json",
        {
            "kind": "checked_counterexample_evidence",
            "path": "reviews/evidence/checked-counterexamples/"
            "checked-counterexample.claim.fixture.candidate.fixture.habc123.yaml",
            "identifier": (
                "checked-counterexample.claim.fixture.candidate.fixture.habc123"
            ),
            "status": "completed",
            "summary": "checked evidence staged for review",
        },
    )
    append_output = runner.invoke(
        app,
        [
            "run",
            "append-output",
            "--run",
            run_id,
            "--input-json",
            str(output_input),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert append_output.exit_code == 0, append_output.output
    assert _assert_json(append_output.output)["run"][
        "checked_counterexample_evidence_paths"
    ][0]["identifier"] == (
        "checked-counterexample.claim.fixture.candidate.fixture.habc123"
    )

    report = runner.invoke(
        app,
        [
            "run",
            "evidence-report",
            "--run",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert report.exit_code == 0, report.output
    report_payload = _assert_json(report.output)
    assert report_payload["command_count"] == 1
    assert report_payload["checked_counterexample_evidence_count"] == 1
    assert report_payload["accepted_write_performed"] is False

    replay = runner.invoke(
        app,
        [
            "run",
            "replay-plan",
            "--run",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert replay.exit_code == 0, replay.output
    replay_payload = _assert_json(replay.output)
    assert replay_payload["read_only"] is True
    assert replay_payload["commands"][0]["argv"][:3] == ["python", "-m", "pytest"]

    finalize = runner.invoke(
        app,
        [
            "run",
            "finalize",
            "--run",
            run_id,
            "--status",
            "completed",
            "--stop-reason",
            "full verification ladder passed",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert finalize.exit_code == 0, finalize.output
    assert _assert_json(finalize.output)["run"]["status"] == "completed"

    dry_run_export = runner.invoke(
        app,
        [
            "run",
            "export-review",
            "--run",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
            "--dry-run",
        ],
    )
    assert dry_run_export.exit_code == 0, dry_run_export.output
    dry_payload = _assert_json(dry_run_export.output)
    assert dry_payload["dry_run"] is True
    assert dry_payload["written_paths"] == []
    assert not (tmp_path / "reviews" / "runs" / f"{run_id}.yaml").exists()

    export = runner.invoke(
        app,
        [
            "run",
            "export-review",
            "--run",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert export.exit_code == 0, export.output
    export_payload = _assert_json(export.output)
    assert export_payload["written_paths"] == [f"reviews/runs/{run_id}.yaml"]
    exported = yaml.safe_load(
        (tmp_path / "reviews" / "runs" / f"{run_id}.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert exported["run_id"] == run_id
    assert exported["authority_notice"] == RESEARCH_RUN_AUTHORITY_NOTICE

    show = runner.invoke(
        app,
        [
            "run",
            "show",
            run_id,
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert show.exit_code == 0, show.output
    assert _assert_json(show.output)["run"]["status"] == "completed"
    assert not (tmp_path / "kb" / "accepted").exists()
