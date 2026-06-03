from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _artifact_data(
    artifact_id: str,
    *,
    status: str = "draft",
    review_state: str = "requested",
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Lifecycle claim",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-03T00:00:00Z",
        "updated_at": "2026-06-03T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["lifecycle"],
        "statement": "A lifecycle CLI fixture.",
        "evidence": evidence or [],
        "review": {"state": review_state, "notes": "Fixture review state."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    artifact_id: str,
    *,
    status: str = "draft",
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            _artifact_data(artifact_id, status=status),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_artifact_create_writes_valid_draft_artifact(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "artifact",
            "create",
            "--id",
            "claim.fixture.lifecycle",
            "--type",
            "claim",
            "--title",
            "Lifecycle claim",
            "--domain",
            "testing",
            "--status",
            "draft",
            "--statement",
            "A lifecycle CLI fixture.",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        "Artifact created: kb/draft/claims/claim.fixture.lifecycle.yaml"
        in result.output
    )
    path = tmp_path / "kb" / "draft" / "claims" / "claim.fixture.lifecycle.yaml"
    artifact = _read_yaml(path)
    assert list(artifact) == [
        "id",
        "type",
        "title",
        "domain",
        "status",
        "created_at",
        "updated_at",
        "authors",
        "depends_on",
        "supersedes",
        "tags",
        "statement",
        "evidence",
        "review",
        "risk",
    ]
    assert artifact["id"] == "claim.fixture.lifecycle"
    assert artifact["type"] == "claim"
    assert artifact["domain"] == ["testing"]
    assert artifact["status"] == "draft"

    validate_result = runner.invoke(
        app,
        [
            "artifact",
            "validate",
            "kb/draft/claims/claim.fixture.lifecycle.yaml",
            "--repo-root",
            str(tmp_path),
        ],
    )
    assert validate_result.exit_code == 0, validate_result.output


def test_artifact_create_rejects_duplicate_id(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/draft/claims/existing.yaml",
        "claim.fixture.duplicate",
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "create",
            "--id",
            "claim.fixture.duplicate",
            "--type",
            "claim",
            "--title",
            "Duplicate claim",
            "--domain",
            "testing",
            "--status",
            "draft",
            "--statement",
            "Duplicate fixture.",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "artifact already exists: claim.fixture.duplicate" in result.output
    assert "Traceback" not in result.output


def test_artifact_create_rejects_invalid_id_before_path_write(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "artifact",
            "create",
            "--id",
            "bad/id",
            "--type",
            "claim",
            "--title",
            "Bad ID claim",
            "--domain",
            "testing",
            "--status",
            "draft",
            "--statement",
            "Invalid ID fixture.",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "artifact ID must be dot-separated lowercase slugs" in result.output
    assert "Traceback" not in result.output
    assert not (tmp_path / "kb").exists()


def test_artifact_move_status_updates_preaccepted_status(tmp_path: Path) -> None:
    path = _write_artifact(
        tmp_path,
        "kb/draft/claims/claim.fixture.move.yaml",
        "claim.fixture.move",
        status="draft",
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "move-status",
            "claim.fixture.move",
            "locally_tested",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        "Artifact moved: claim.fixture.move | draft -> locally_tested"
        in result.output
    )
    assert _read_yaml(path)["status"] == "locally_tested"


def test_artifact_move_status_moves_refuted_artifact_to_refuted_area(
    tmp_path: Path,
) -> None:
    source = _write_artifact(
        tmp_path,
        "kb/draft/claims/claim.fixture.refuted.yaml",
        "claim.fixture.refuted",
        status="draft",
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "move-status",
            "claim.fixture.refuted",
            "refuted",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    target = tmp_path / "kb" / "refuted" / "claim.fixture.refuted.yaml"
    assert not source.exists()
    assert target.is_file()
    assert _read_yaml(target)["status"] == "refuted"
    assert "kb/refuted/claim.fixture.refuted.yaml" in result.output


def test_artifact_move_status_rejects_accepted_promotion(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/draft/claims/claim.fixture.accepted.yaml",
        "claim.fixture.accepted",
        status="draft",
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "move-status",
            "claim.fixture.accepted",
            "accepted",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert (
        "accepted promotion requires a dedicated gate/review workflow"
        in result.output
    )
    assert "Traceback" not in result.output
    assert not (tmp_path / "kb" / "accepted" / "claims").exists()


def test_artifact_move_status_rejects_current_status_path_mismatch(
    tmp_path: Path,
) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/bad.yaml",
        "claim.fixture.mismatch",
        status="draft",
    )

    result = runner.invoke(
        app,
        [
            "artifact",
            "move-status",
            "claim.fixture.mismatch",
            "locally_tested",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "status/path mismatch" in result.output
    assert "kb/accepted/claims/bad.yaml" in result.output
    assert "Traceback" not in result.output
