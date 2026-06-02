from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

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
) -> None:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "id": artifact_id,
        "type": "claim",
        "title": f"Claim {artifact_id}",
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


def _load_single_report(repo_root: Path) -> dict[str, Any]:
    json_reports = sorted(
        (repo_root / ".cosheaf" / "reports").glob("*-gate-report.json")
    )
    assert len(json_reports) == 1
    return cast(
        dict[str, Any],
        json.loads(json_reports[0].read_text(encoding="utf-8")),
    )


def test_passing_repo_produces_pass_report(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Gate verdict: pass" in result.output
    report = _load_single_report(tmp_path)
    assert report["verdict"] == "pass"
    assert report["blocking_issues"] == []
    assert {"verdict", "blocking_issues", "nonblocking_issues", "summary"} <= set(
        report
    )
    assert {"started_at", "ended_at"} <= set(report)
    gate_statuses = {gate["id"]: gate["status"] for gate in report["gates"]}
    assert gate_statuses["G6"] == "skipped"
    assert gate_statuses["G7"] == "not_applicable"
    assert gate_statuses["G8"] == "skipped"
    assert "pass" not in {gate_statuses["G6"], gate_statuses["G7"], gate_statuses["G8"]}
    assert not (tmp_path / "reviews" / "gatekeeper").exists()


def test_failing_repo_produces_fail_report_and_nonzero_exit(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
        depends_on=["claim.fixture.missing"],
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "Gate verdict: fail" in result.output
    assert "missing dependency" in result.output
    report = _load_single_report(tmp_path)
    assert report["verdict"] == "fail"
    assert report["blocking_issues"]
    assert report["blocking_issues"][0]["gate_id"] == "G4"


def test_markdown_report_exists(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0
    markdown_reports = sorted(
        (tmp_path / ".cosheaf" / "reports").glob("*-gate-report.md")
    )
    assert len(markdown_reports) == 1
    assert "# Gatekeeper Report" in markdown_reports[0].read_text(encoding="utf-8")


def test_persist_review_writes_reviews_gatekeeper(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "examples/claims/a.yaml",
        artifact_id="claim.fixture.a",
    )

    result = runner.invoke(
        app,
        ["gate", "run", "--repo-root", str(tmp_path), "--persist-review"],
    )

    assert result.exit_code == 0
    review_reports = sorted(
        (tmp_path / "reviews" / "gatekeeper").glob("*-gate-report.json")
    )
    assert len(review_reports) == 1
    review_report = json.loads(review_reports[0].read_text(encoding="utf-8"))
    assert review_report["verdict"] == "pass"

