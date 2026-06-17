from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_checker_list_and_describe_json() -> None:
    listed = runner.invoke(app, ["checker", "list", "--json"])
    described = runner.invoke(
        app,
        ["checker", "describe", "schema_check", "--json"],
    )

    assert listed.exit_code == 0, listed.output
    assert described.exit_code == 0, described.output
    list_payload = _json(listed.output)
    describe_payload = _json(described.output)
    assert list_payload["schema_version"] == 1
    assert list_payload["checkers"][0]["checker_id"] == (
        "artifact_path_policy_check"
    )
    assert describe_payload["checker"]["checker_id"] == "schema_check"
    assert "accepted status" in describe_payload["checker"]["authority_notice"][
        "message"
    ]


def test_checker_run_json_writes_runtime_record(tmp_path: Path) -> None:
    input_path = _write_json(
        tmp_path / "checker-input.json",
        {
            "schema_version": 1,
            "paths": ["kb/draft/claims/claim.fixture.yaml"],
        },
    )

    result = runner.invoke(
        app,
        [
            "checker",
            "run",
            "artifact_path_policy_check",
            "--repo-root",
            str(tmp_path),
            "--input-json",
            str(input_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.output)
    assert payload["schema_version"] == 1
    assert payload["result"]["status"] == "pass"
    assert payload["result_path"].startswith(".cosheaf/checker-runs/")
    assert (tmp_path / payload["result_path"]).is_file()
    assert (tmp_path / payload["stdout_path"]).is_file()
    assert (tmp_path / payload["stderr_path"]).is_file()


def test_checker_run_blocks_authority_overclaim(tmp_path: Path) -> None:
    input_path = _write_json(
        tmp_path / "checker-input.json",
        {
            "schema_version": 1,
            "text": "human reviewed and promoted to accepted",
        },
    )

    result = runner.invoke(
        app,
        [
            "checker",
            "run",
            "authority_overclaim_check",
            "--repo-root",
            str(tmp_path),
            "--input-json",
            str(input_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _json(result.output)
    assert payload["result"]["status"] == "blocked_by_policy"
    assert payload["result"]["authority_notice"][
        "checker_pass_is_not_human_review"
    ] is True


def test_checker_run_suite_json(tmp_path: Path) -> None:
    input_path = _write_json(
        tmp_path / "checker-input.json",
        {
            "schema_version": 1,
            "payload": {"tool_command": "cosheaf-definitely-missing-tool"},
        },
    )

    result = runner.invoke(
        app,
        [
            "checker",
            "run-suite",
            "--repo-root",
            str(tmp_path),
            "--input-json",
            str(input_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _json(result.output)
    assert payload["kind"] == "checker_suite_result"
    assert payload["run_count"] == 10
    assert payload["status_counts"]["skipped"] >= 1
    assert payload["has_blocking_result"] is False

