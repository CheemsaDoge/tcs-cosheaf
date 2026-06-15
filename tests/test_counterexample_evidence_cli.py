from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.verification.counterexample_evidence import (
    CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
    SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION,
)

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


def _record_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "evidence_id": (
            "checked-counterexample.claim.fixture.target."
            "candidate.fixture.0001.habc123"
        ),
        "target_artifact_id": "claim.fixture.target",
        "candidate_id": "candidate.fixture.0001",
        "candidate_source": "worker_bundle",
        "check_method": "verifier_result",
        "checked_result": "checked_refutes",
        "verifier_evidence_ids": [
            "verifier-evidence.claim.fixture.target.python.habc123"
        ],
        "review_record_paths": [],
        "evidence_paths": [".cosheaf/evidence/candidate-check.json"],
        "created_at": "2026-06-15T00:00:00Z",
        "checker": "python-checker",
        "limitations": [
            "Checked counterexample evidence is evidence for review only.",
            CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
        ],
    }
    data.update(overrides)
    return data


def test_counterexample_evidence_validate_json(tmp_path: Path) -> None:
    request = _write_json(tmp_path, "requests/evidence.json", _record_data())

    result = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "validate",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["schema_version"] == 1
    assert payload["valid"] is True
    assert payload["accepted_write_performed"] is False
    assert payload["authority_notice"] == CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE
    assert payload["evidence"]["checked_result"] == "checked_refutes"


def test_counterexample_evidence_stage_dry_run_writes_nothing(
    tmp_path: Path,
) -> None:
    request = _write_json(tmp_path, "requests/evidence.json", _record_data())

    result = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "stage",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["kind"] == "checked_counterexample_evidence"
    assert payload["dry_run"] is True
    assert payload["written_paths"] == []
    assert payload["accepted_write_performed"] is False
    assert payload["path"] == (
        "reviews/evidence/checked-counterexamples/"
        "checked-counterexample.claim.fixture.target."
        "candidate.fixture.0001.habc123.yaml"
    )
    assert not (tmp_path / payload["path"]).exists()
    assert not (tmp_path / "kb" / "accepted").exists()


def test_counterexample_evidence_stage_and_show_by_id(tmp_path: Path) -> None:
    request = _write_json(tmp_path, "requests/evidence.json", _record_data())

    stage = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "stage",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert stage.exit_code == 0, stage.output
    stage_payload = _assert_json(stage.output)
    target_path = tmp_path / stage_payload["path"]
    assert target_path.is_file()
    staged = yaml.safe_load(target_path.read_text(encoding="utf-8"))
    assert staged["evidence_id"] == (
        "checked-counterexample.claim.fixture.target."
        "candidate.fixture.0001.habc123"
    )

    show = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "show",
            "--evidence",
            staged["evidence_id"],
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert show.exit_code == 0, show.output
    show_payload = _assert_json(show.output)
    assert show_payload["path"] == stage_payload["path"]
    assert show_payload["evidence"]["evidence_id"] == staged["evidence_id"]
    assert show_payload["authority_notice"] == CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE


def test_counterexample_evidence_stage_rejects_existing_target(
    tmp_path: Path,
) -> None:
    request = _write_json(tmp_path, "requests/evidence.json", _record_data())
    first = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "stage",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )
    assert first.exit_code == 0, first.output

    second = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "stage",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert second.exit_code == 1
    payload = _assert_json(second.output)
    assert payload["code"] == "checked_evidence_path_exists"
    assert not (tmp_path / "kb" / "accepted").exists()


def test_counterexample_evidence_validate_rejects_invalid_input(
    tmp_path: Path,
) -> None:
    request = _write_json(
        tmp_path,
        "requests/evidence.json",
        _record_data(
            checked_result="skipped",
            limitations=[CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE],
            verifier_evidence_ids=[],
            evidence_paths=[],
        ),
    )

    result = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "validate",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "checked_evidence_validation_failed"
    assert "skipped is not pass" in payload["message"]


def test_counterexample_evidence_show_reports_missing_id(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "show",
            "--evidence",
            "checked-counterexample.claim.missing.candidate.missing.h0",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "checked_evidence_not_found"


def test_counterexample_evidence_stage_accepts_skipped_with_limitation(
    tmp_path: Path,
) -> None:
    request = _write_json(
        tmp_path,
        "requests/evidence.json",
        _record_data(
            checked_result="skipped",
            verifier_evidence_ids=[],
            evidence_paths=[],
            limitations=[
                CHECKED_COUNTEREXAMPLE_AUTHORITY_NOTICE,
                SKIPPED_CHECKED_COUNTEREXAMPLE_LIMITATION,
            ],
        ),
    )

    result = runner.invoke(
        app,
        [
            "counterexample",
            "evidence",
            "stage",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["evidence"]["checked_result"] == "skipped"
