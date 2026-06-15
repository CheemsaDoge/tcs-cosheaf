from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n")
    return path


def _assert_json(output: str) -> dict[str, Any]:
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def _start_run(repo_root: Path) -> str:
    run_id = "run.issue.security.research.0001"
    result = runner.invoke(
        app,
        [
            "run",
            "start",
            "--issue",
            "issue.security.research",
            "--operator",
            "external",
            "--operator-label",
            "Codex CLI",
            "--run-id",
            run_id,
            "--repo-root",
            str(repo_root),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    return run_id


def test_research_run_append_output_rejects_authority_claims(
    tmp_path: Path,
) -> None:
    run_id = _start_run(tmp_path)
    for field, value in {
        "human_reviewed": True,
        "review_state": "human_reviewed",
        "accepted": True,
        "accepted_write_performed": True,
        "artifact_status": "accepted",
        "promote": True,
    }.items():
        request = _write_json(
            tmp_path,
            f"requests/output-{field}.json",
            {"kind": "controlled_write", "path": ".cosheaf/out.json", field: value},
        )
        result = runner.invoke(
            app,
            [
                "run",
                "append-output",
                "--run",
                run_id,
                "--input-json",
                str(request),
                "--repo-root",
                str(tmp_path),
                "--json",
            ],
        )

        assert result.exit_code == 1
        payload = _assert_json(result.output)
        assert payload["code"] == "authority_claim_forbidden"
        assert field in payload["details"]["forbidden_fields"].split(",")
        assert not (tmp_path / "kb" / "accepted").exists()


def test_research_run_rejects_unsafe_paths_and_secret_summaries(
    tmp_path: Path,
) -> None:
    run_id = _start_run(tmp_path)

    unsafe_path = _write_json(
        tmp_path,
        "requests/unsafe-path.json",
        {"kind": "controlled_write", "path": "kb/accepted/claims/unsafe.yaml"},
    )
    path_result = runner.invoke(
        app,
        [
            "run",
            "append-output",
            "--run",
            run_id,
            "--input-json",
            str(unsafe_path),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert path_result.exit_code == 1
    path_payload = _assert_json(path_result.output)
    assert path_payload["code"] == "research_run_validation_failed"
    assert "accepted KB paths" in path_payload["message"]

    secret_summary = _write_json(
        tmp_path,
        "requests/secret-summary.json",
        {
            "kind": "controlled_write",
            "path": ".cosheaf/out.json",
            "summary": "leaked sk-secret-value",
        },
    )
    secret_result = runner.invoke(
        app,
        [
            "run",
            "append-output",
            "--run",
            run_id,
            "--input-json",
            str(secret_summary),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert secret_result.exit_code == 1
    secret_payload = _assert_json(secret_result.output)
    assert secret_payload["code"] == "research_run_validation_failed"
    assert "secret-looking" in secret_payload["message"]
    assert "sk-secret-value" not in secret_result.output
    assert not (tmp_path / "kb" / "accepted").exists()
