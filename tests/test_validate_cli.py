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
    status: str = "draft",
    depends_on: list[str] | None = None,
    evidence_path: str | None = None,
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {
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
    if evidence_path is not None:
        data["evidence"] = [
            {
                "kind": "proof",
                "path": evidence_path,
                "summary": "Test evidence.",
            }
        ]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_validate_passes_on_repository_examples() -> None:
    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "Validation passed" in result.output
    assert "scaffold-only" not in result.output


def test_artifact_validate_passes_for_single_example() -> None:
    result = runner.invoke(
        app,
        ["artifact", "validate", "examples/claims/claim.example.yaml"],
    )

    assert result.exit_code == 0
    assert "Artifact validation passed" in result.output


def test_validate_duplicate_id_fails(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.duplicate",
    )
    _write_artifact(
        tmp_path,
        "kb/draft/claims/b.yaml",
        artifact_id="claim.fixture.duplicate",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "duplicate id" in result.output
    assert "claim.fixture.duplicate" in result.output
    assert "Traceback" not in result.output


def test_validate_invalid_yaml_fails_without_traceback(tmp_path: Path) -> None:
    path = tmp_path / "examples" / "claims" / "bad.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("id: [not valid\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "invalid YAML" in result.output
    assert "Traceback" not in result.output


def test_validate_missing_dependency_fails(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.depender",
        depends_on=["claim.fixture.missing"],
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "missing dependency" in result.output
    assert "claim.fixture.missing" in result.output


def test_validate_missing_evidence_path_fails(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.evidence",
        evidence_path="examples/proofs/missing.yaml",
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "missing evidence path" in result.output
    assert "examples/proofs/missing.yaml" in result.output
