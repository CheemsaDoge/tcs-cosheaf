from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_json(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _artifact_request(
    *,
    artifact_id: str = "claim.fixture.controlled-draft",
    status: str = "draft",
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": "claim",
        "title": "Controlled draft claim",
        "domain": ["testing"],
        "status": status,
        "statement": "A draft artifact written through the controlled CLI.",
        "authors": ["tester"],
        "tags": ["controlled-write"],
        "depends_on": [],
        "supersedes": [],
    }


def _source_note_request(
    *,
    target_path: str = "sources/notes/source.fixture.controlled.yaml",
) -> dict[str, Any]:
    return {
        "source_id": "source.fixture.controlled",
        "target_path": target_path,
        "kind": "book",
        "title": "Controlled Source",
        "authors": ["A. Author"],
        "year": 2026,
        "page": "1",
        "notes": "Draft source note for review only.",
    }


def _review_request(
    *,
    review_id: str = "review.fixture.controlled",
    target: str = "claim.fixture.controlled-draft",
    status: str = "draft",
) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "target": target,
        "title": "Controlled review request",
        "status": status,
        "summary": "Request human review later; this record is not human review.",
        "authors": ["tester"],
        "findings": ["No human review has been performed."],
        "decision": "informational",
    }


def _bundle_data() -> dict[str, Any]:
    return {
        "bundle_id": "bundle.issue.fixture.controlled.reasoner.0001",
        "task_id": "task.issue.fixture.controlled.reasoner",
        "worker_role": "reasoner",
        "created_at": "2026-06-09T00:00:00Z",
        "summary": "Controlled bundle submit fixture.",
        "used_artifacts": ["claim.fixture.controlled-draft"],
        "used_sources": ["sources/notes/source.fixture.controlled.yaml"],
        "claims": ["The output remains review-only."],
        "proposed_artifacts": [
            {
                "path": "kb/draft/claims/claim.fixture.controlled-draft.yaml",
                "summary": "Draft proposal.",
            }
        ],
        "verification_requests": ["Run validate and gate before review."],
        "failures_or_counterexamples": ["No proof was checked."],
        "risk_flags": ["needs_human_review"],
        "next_steps": ["Request human review."],
        "confidence": "low",
    }


def _assert_json(output: str) -> dict[str, Any]:
    assert "\x1b[" not in output
    payload = json.loads(output)
    assert isinstance(payload, dict)
    return payload


def test_draft_write_artifact_json_writes_draft_only(tmp_path: Path) -> None:
    request = _write_json(tmp_path, "requests/artifact.json", _artifact_request())

    result = runner.invoke(
        app,
        [
            "draft",
            "write-artifact",
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
    assert payload["kind"] == "draft_artifact"
    assert payload["path"] == "kb/draft/claims/claim.fixture.controlled-draft.yaml"
    assert payload["written_paths"] == [payload["path"]]
    assert payload["accepted_write_performed"] is False
    written = yaml.safe_load((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert written["status"] == "draft"
    assert written["review"]["state"] == "requested"
    assert not (tmp_path / "kb" / "accepted").exists()


def test_draft_write_artifact_dry_run_writes_nothing(tmp_path: Path) -> None:
    request = _write_json(tmp_path, "requests/artifact.json", _artifact_request())

    result = runner.invoke(
        app,
        [
            "draft",
            "write-artifact",
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
    assert payload["dry_run"] is True
    assert payload["written_paths"] == []
    assert payload["path"] == "kb/draft/claims/claim.fixture.controlled-draft.yaml"
    assert not (tmp_path / payload["path"]).exists()


def test_draft_write_artifact_rejects_accepted_status(tmp_path: Path) -> None:
    request = _write_json(
        tmp_path,
        "requests/artifact.json",
        _artifact_request(status="accepted"),
    )

    result = runner.invoke(
        app,
        [
            "draft",
            "write-artifact",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "accepted_write_forbidden"
    assert payload["blocking"] is True
    assert not (tmp_path / "kb" / "accepted").exists()


def test_draft_write_artifact_rejects_readonly_public_root(tmp_path: Path) -> None:
    (tmp_path / "cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "readonly-workspace"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
            ]
        ),
        encoding="utf-8",
    )
    request = _write_json(tmp_path, "requests/artifact.json", _artifact_request())

    result = runner.invoke(
        app,
        [
            "draft",
            "write-artifact",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "no_writable_kb_root"
    assert "readonly" in payload["remediation"].lower() or "writable" in payload[
        "remediation"
    ].lower()


def test_write_source_note_json_writes_staging_note(tmp_path: Path) -> None:
    request = _write_json(tmp_path, "requests/source.json", _source_note_request())

    result = runner.invoke(
        app,
        [
            "draft",
            "write-source-note",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["kind"] == "source_note"
    assert payload["path"] == "sources/notes/source.fixture.controlled.yaml"
    source = yaml.safe_load((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert source["type"] == "source_note"
    assert source["status"] == "draft"
    assert source["source"]["title"] == "Controlled Source"


def test_write_source_note_rejects_accepted_path(tmp_path: Path) -> None:
    request = _write_json(
        tmp_path,
        "requests/source.json",
        _source_note_request(target_path="kb/accepted/sources/unsafe.yaml"),
    )

    result = runner.invoke(
        app,
        [
            "draft",
            "write-source-note",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "accepted_write_forbidden"
    assert not (tmp_path / "kb" / "accepted").exists()


def test_write_source_note_rejects_readonly_public_root(tmp_path: Path) -> None:
    (tmp_path / "cosheaf.toml").write_text(
        "\n".join(
            [
                "[workspace]",
                'name = "readonly-source-note-workspace"',
                "",
                "[[kb]]",
                'name = "public"',
                'path = "kb/public"',
                "readonly = true",
                "priority = 10",
                "",
                "[[kb]]",
                'name = "private"',
                'path = "kb/private"',
                "readonly = false",
                "priority = 100",
                "",
            ]
        ),
        encoding="utf-8",
    )
    request = _write_json(
        tmp_path,
        "requests/source.json",
        _source_note_request(target_path="kb/public/sources/source.fixture.yaml"),
    )

    result = runner.invoke(
        app,
        [
            "draft",
            "write-source-note",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "readonly_kb_root"
    assert not (tmp_path / "kb" / "public" / "sources").exists()


def test_bundle_submit_json_validates_bundle_without_promotion(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.fixture.controlled-draft.yaml",
        {
            "id": "claim.fixture.controlled-draft",
            "type": "claim",
            "title": "Controlled draft claim",
            "domain": ["testing"],
            "status": "draft",
            "created_at": "2026-06-09T00:00:00Z",
            "updated_at": "2026-06-09T00:00:00Z",
            "authors": ["tester"],
            "depends_on": [],
            "supersedes": [],
            "tags": ["controlled-write"],
            "statement": "A draft artifact written through the controlled CLI.",
            "evidence": [],
            "review": {"state": "requested", "notes": "Pending review."},
            "risk": {"level": "low", "notes": "Fixture risk."},
        },
    )
    bundle = _write_yaml(tmp_path, "outputs/bundle.yaml", _bundle_data())
    request = _write_json(
        tmp_path,
        "requests/bundle.json",
        {
            "task_id": "task.issue.fixture.controlled.reasoner",
            "bundle_path": "outputs/bundle.yaml",
            "complete_task": False,
        },
    )

    result = runner.invoke(
        app,
        [
            "bundle",
            "submit",
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
    assert payload["task_id"] == "task.issue.fixture.controlled.reasoner"
    assert payload["bundle_id"] == "bundle.issue.fixture.controlled.reasoner.0001"
    assert payload["accepted_for_review"] is True
    assert payload["output_paths"] == [
        "kb/draft/claims/claim.fixture.controlled-draft.yaml"
    ]
    assert bundle.exists()
    assert not (tmp_path / "kb" / "accepted").exists()


def test_review_request_json_writes_draft_review_only(tmp_path: Path) -> None:
    request = _write_json(tmp_path, "requests/review.json", _review_request())

    result = runner.invoke(
        app,
        [
            "review",
            "request",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = _assert_json(result.output)
    assert payload["kind"] == "review_request"
    assert payload["path"] == "reviews/requests/review.fixture.controlled.yaml"
    review = yaml.safe_load((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert review["type"] == "review"
    assert review["status"] == "draft"
    assert review["decision"] == "informational"
    assert review["status"] != "human_reviewed"


def test_review_request_rejects_human_reviewed_status(tmp_path: Path) -> None:
    request = _write_json(
        tmp_path,
        "requests/review.json",
        _review_request(status="human_reviewed"),
    )

    result = runner.invoke(
        app,
        [
            "review",
            "request",
            "--input-json",
            str(request),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = _assert_json(result.output)
    assert payload["code"] == "human_review_forbidden"
    assert not (tmp_path / "reviews").exists()
