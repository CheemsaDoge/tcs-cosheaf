from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from cosheaf.cli import app
from cosheaf.gates.gatekeeper import (
    GateIssue,
    GatekeeperReport,
    GatekeeperRunResult,
    GateResult,
    run_gatekeeper,
)
from cosheaf.storage.repo import RepoContext

runner = CliRunner()


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _artifact_data(
    artifact_id: str,
    *,
    artifact_type: str = "claim",
    status: str = "draft",
    review_state: str = "human_reviewed",
    evidence: list[dict[str, Any]] | None = None,
    statement: str = "A P1 promotion/gate/verifier regression fixture.",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "title": f"Fixture {artifact_id}",
        "domain": ["testing"],
        "status": status,
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["p1-regression"],
        "statement": statement,
        "evidence": evidence or [],
        "review": {"state": review_state, "notes": "Regression fixture review."},
        "risk": {"level": "low", "notes": "Regression fixture risk."},
    }


def _single_report(repo_root: Path) -> dict[str, Any]:
    reports = sorted((repo_root / ".cosheaf" / "reports").glob("*-gate-report.json"))
    assert len(reports) == 1
    data = json.loads(reports[0].read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _verifier_error_run_result(
    repo_root: Path,
    artifact_id: str,
) -> GatekeeperRunResult:
    issue = GateIssue(
        gate_id="G6",
        gate_name="verifier gate",
        source_path="",
        artifact_id=artifact_id,
        message="python_checker error: tool crashed",
        severity="blocking",
    )
    g6 = GateResult(
        gate_id="G6",
        name="verifier gate",
        status="fail",
        summary="1 blocking verifier issue(s).",
        blocking_issues=(issue,),
        details=(
            {
                "artifact_id": artifact_id,
                "verifier": "python_checker",
                "status": "error",
                "message": "tool crashed",
            },
        ),
    )
    report = GatekeeperReport(
        verdict="fail",
        blocking_issues=(issue,),
        nonblocking_issues=(),
        summary={
            "records_checked": 1,
            "gates_total": 1,
            "gates_passed": 0,
            "gates_failed": 1,
            "gates_skipped": 0,
            "gates_not_applicable": 0,
            "blocking_issue_count": 1,
            "nonblocking_issue_count": 0,
        },
        started_at="2026-06-04T00:00:00Z",
        ended_at="2026-06-04T00:00:00Z",
        gates=(g6,),
    )
    return GatekeeperRunResult(
        report=report,
        json_path=repo_root / ".cosheaf" / "reports" / "fake.json",
        markdown_path=repo_root / ".cosheaf" / "reports" / "fake.md",
    )


def test_artifact_promote_refuses_target_verifier_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _write_yaml(
        tmp_path,
        "kb/draft/claims/claim.verifier-error.yaml",
        _artifact_data("claim.verifier-error", status="locally_tested"),
    )

    def fake_run_gatekeeper(*args: object, **kwargs: object) -> GatekeeperRunResult:
        return _verifier_error_run_result(tmp_path, "claim.verifier-error")

    monkeypatch.setattr("cosheaf.cli.run_gatekeeper", fake_run_gatekeeper)

    result = runner.invoke(
        app,
        [
            "artifact",
            "promote",
            "claim.verifier-error",
            "--repo-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "target verifier result blocks promotion" in result.output
    assert "python_checker error: tool crashed" in result.output
    assert source.is_file()
    assert not (
        tmp_path
        / "kb"
        / "accepted"
        / "claims"
        / "claim.verifier-error.yaml"
    ).exists()


def test_missing_evidence_path_fails_unless_explicitly_external(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/external.yaml",
        _artifact_data(
            "claim.external-evidence",
            evidence=[
                {
                    "kind": "external",
                    "path": "external:doi/10.1145/external",
                    "summary": "External evidence is explicitly allowed.",
                }
            ],
        ),
    )
    _write_yaml(
        tmp_path,
        "kb/draft/claims/missing.yaml",
        _artifact_data(
            "claim.missing-evidence",
            evidence=[
                {
                    "kind": "python_checker",
                    "path": "experiments/evaluators/missing.py",
                    "summary": "Missing local evidence must fail.",
                }
            ],
        ),
    )

    result = runner.invoke(app, ["validate", "--repo-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "missing evidence path:" in result.output
    assert "experiments/evaluators/missing.py" in result.output
    assert "claim.missing-evidence" in result.output
    assert "claim.external-evidence" not in result.output
    assert "Traceback" not in result.output


def test_reviewed_draft_with_external_evidence_has_machine_readable_gate_report(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path,
        "kb/draft/claims/valid.yaml",
        _artifact_data(
            "claim.valid-reviewed",
            status="locally_tested",
            evidence=[
                {
                    "kind": "external",
                    "path": "external:reviewed-fixture",
                    "summary": "Reviewed external fixture evidence.",
                }
            ],
        ),
    )

    result = runner.invoke(app, ["gate", "run", "--repo-root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    report = _single_report(tmp_path)
    assert report["verdict"] == "pass"
    assert report["blocking_issues"] == []
    assert {"verdict", "blocking_issues", "summary", "gates"} <= set(report)
    assert isinstance(report["gates"], list)


def test_unavailable_optional_verifier_is_skipped_not_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", "")
    cnf = tmp_path / "examples" / "sat" / "tiny.cnf"
    cnf.parent.mkdir(parents=True, exist_ok=True)
    cnf.write_text("p cnf 1 1\n1 0\n", encoding="utf-8")
    _write_yaml(
        tmp_path,
        "kb/draft/constructions/sat.yaml",
        _artifact_data(
            "construction.optional-sat",
            artifact_type="construction",
            evidence=[
                {
                    "kind": "sat",
                    "path": "examples/sat/tiny.cnf",
                    "summary": "SAT evidence with unavailable optional backend.",
                }
            ],
            statement=(
                "Fixture SAT statement.\n\n"
                "CHECKER_DATA:\n"
                "expected:\n"
                "  satisfiable: true\n"
            ),
        ),
    )

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260604T000000000000Z",
    )

    g6 = next(gate for gate in result.report.gates if gate.gate_id == "G6")
    assert result.report.verdict == "pass"
    assert g6.status == "skipped"
    assert g6.status != "pass"
    assert g6.nonblocking_issues
    assert not g6.blocking_issues
    assert "sat skipped" in g6.nonblocking_issues[0].message
