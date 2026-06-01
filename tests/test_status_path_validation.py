from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app

runner = CliRunner()


def _write_artifact(
    repo_root: Path,
    relative_path: str,
    *,
    artifact_id: str,
    status: str,
    depends_on: list[str] | None = None,
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": artifact_id,
        "type": "claim",
        "title": "Test claim",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": depends_on or [],
        "supersedes": [],
        "tags": [],
        "statement": "Test statement.",
        "evidence": [],
        "review": {"state": "requested", "notes": "Test review."},
        "risk": {"level": "low", "notes": "Test risk."},
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_status_path_mismatch_fails(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/draft.yaml",
        artifact_id="claim.fixture.status-mismatch",
        status="draft",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "status/path mismatch" in result.output
    assert "kb/accepted/claims/draft.yaml" in result.output


def test_accepted_artifact_depends_on_draft_fails(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "kb/accepted/claims/accepted.yaml",
        artifact_id="claim.fixture.accepted",
        status="accepted",
        depends_on=["claim.fixture.draft"],
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/draft.yaml",
        artifact_id="claim.fixture.draft",
        status="draft",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "accepted artifact depends on draft artifact" in result.output
    assert "claim.fixture.draft" in result.output
