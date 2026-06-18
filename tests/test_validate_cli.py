from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

import cosheaf.validation_cli as validation_cli
from cosheaf.cli import app
from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import (
    GatekeeperReport,
    GatekeeperRunResult,
    ValidationReport,
)
from cosheaf.storage.loader import load_artifacts
from cosheaf.storage.repo import RepoContext

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]


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


def test_validate_and_gate_cli_route_through_app_facade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeApp:
        def __init__(self, repo_root: str | Path) -> None:
            self.context = RepoContext(Path(repo_root))

        def validate_repository(self) -> ValidationReport:
            calls.append("validate_repository")
            return ValidationReport(records=(), failures=())

        def run_gate(
            self,
            *,
            persist_review: bool = False,
            pr_checklist_path: str | Path | None = None,
            timestamp: str | None = None,
        ) -> GatekeeperRunResult:
            calls.append(
                f"run_gate:{persist_review}:{pr_checklist_path}:{timestamp}"
            )
            return GatekeeperRunResult(
                report=GatekeeperReport(
                    verdict="pass",
                    blocking_issues=(),
                    nonblocking_issues=(),
                    summary={"records_checked": 0},
                    started_at="2026-06-19T00:00:00Z",
                    ended_at="2026-06-19T00:00:00Z",
                    gates=(),
                ),
                json_path=tmp_path / ".cosheaf" / "reports" / "gate.json",
                markdown_path=tmp_path / ".cosheaf" / "reports" / "gate.md",
            )

    def fake_open_app(repo_root: str | Path = ".") -> FakeApp:
        return FakeApp(repo_root)

    monkeypatch.setattr(validation_cli, "open_app", fake_open_app)

    validate_result = runner.invoke(
        app,
        ["validate", "--repo-root", str(tmp_path), "--json"],
    )
    gate_result = runner.invoke(
        app,
        ["gate", "run", "--repo-root", str(tmp_path), "--json"],
    )

    assert validate_result.exit_code == 0
    assert json.loads(validate_result.output)["checked_count"] == 0
    assert gate_result.exit_code == 0
    assert json.loads(gate_result.output)["verdict"] == "pass"
    assert calls == ["validate_repository", "run_gate:False:None:None"]


def test_repository_examples_and_pilots_are_model_valid() -> None:
    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    records = load_artifacts(RepoContext(ROOT))
    by_id = {record.id: record for record in records}

    for artifact_id in (
        "claim.example.complete-graph-edge-count",
        "claim.example.cslib-formal-link",
        "definition.graph",
        "construction.graph-toy.0001",
        "construction.sat-smt-gadget.0001",
    ):
        assert artifact_id in by_id
        assert isinstance(by_id[artifact_id].record, BaseArtifact)


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
