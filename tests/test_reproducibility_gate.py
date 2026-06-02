from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import run_gatekeeper
from cosheaf.gates.reproducibility_gate import validate_reproducibility_metadata
from cosheaf.storage.loader import LoadedRecord
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationResult, VerificationStatus

STARTED_AT = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 1, 10, 1, tzinfo=UTC)


def _artifact(
    *,
    artifact_id: str = "experiment.fixture.repro",
    artifact_type: str = "experiment",
    evidence_kind: str = "python_checker",
    evidence_summary: str = "Deterministic checker evidence.",
    tags: list[str] | None = None,
) -> BaseArtifact:
    return BaseArtifact.model_validate(
        {
            "id": artifact_id,
            "type": artifact_type,
            "title": "Reproducibility fixture",
            "domain": ["testing"],
            "status": "draft",
            "created_at": "2026-06-01T00:00:00Z",
            "updated_at": "2026-06-01T00:00:00Z",
            "authors": ["tester"],
            "depends_on": [],
            "supersedes": [],
            "tags": tags or [],
            "statement": "A fixture artifact.",
            "evidence": [
                {
                    "kind": evidence_kind,
                    "path": "experiments/evaluators/check_fixture.py",
                    "summary": evidence_summary,
                }
            ],
            "review": {"state": "requested", "notes": "Fixture review."},
            "risk": {"level": "low", "notes": "Fixture risk."},
        }
    )


def _record(artifact: BaseArtifact) -> LoadedRecord:
    return LoadedRecord(
        source_path=Path(f"examples/{artifact.type.value}s/{artifact.id}.yaml"),
        record=artifact,
    )


def _verification_result(
    *,
    artifact_id: str = "experiment.fixture.repro",
    command: tuple[str, ...] | None = ("python", "experiments/evaluators/check.py"),
    cwd: str | None = ".",
    stdout_path: str | None = ".cosheaf/logs/stdout.log",
    stderr_path: str | None = ".cosheaf/logs/stderr.log",
    evidence_paths: tuple[str, ...] = ("experiments/evaluators/check_fixture.py",),
    seed: str | None = None,
) -> VerificationResult:
    return VerificationResult(
        verifier="python_checker",
        artifact_id=artifact_id,
        status=VerificationStatus.PASS,
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        command=command,
        cwd=cwd,
        exit_code=0,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        evidence_paths=evidence_paths,
        timeout_seconds=30.0,
        input_paths=("examples/experiments/experiment.fixture.repro.yaml",),
        output_paths=(".cosheaf/logs/stdout.log", ".cosheaf/logs/stderr.log"),
        tool_name="python",
        tool_version="3.11",
        seed=seed,
        environment="local test environment",
        message="checker passed",
    )


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _artifact_data() -> dict[str, Any]:
    return {
        "id": "construction.fixture.repro",
        "type": "construction",
        "title": "Gatekeeper reproducibility fixture",
        "domain": ["testing"],
        "status": "draft",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": [],
        "statement": "A fixture with executable checker evidence.",
        "evidence": [
            {
                "kind": "python_checker",
                "path": "experiments/evaluators/check_fixture.py",
                "summary": "Deterministic checker evidence.",
            }
        ],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def test_passing_reproducibility_metadata() -> None:
    artifact = _artifact()

    result = validate_reproducibility_metadata(
        (_record(artifact),),
        (_verification_result(),),
    )

    assert result.failures == ()
    assert result.applicable_count == 1
    assert result.checks[0].status == "pass"


def test_missing_required_metadata_is_reported() -> None:
    artifact = _artifact()

    result = validate_reproducibility_metadata(
        (_record(artifact),),
        (_verification_result(command=None),),
    )

    assert len(result.failures) == 1
    assert result.failures[0].artifact_id == "experiment.fixture.repro"
    assert "missing reproducibility metadata: command" in result.failures[0].message


def test_randomized_evidence_without_seed_fails() -> None:
    artifact = _artifact(
        evidence_summary="Randomized search evidence.",
        tags=["randomized"],
    )

    result = validate_reproducibility_metadata(
        (_record(artifact),),
        (_verification_result(),),
    )

    assert len(result.failures) == 1
    assert "randomized evidence requires seed metadata" in result.failures[0].message


def test_non_executable_evidence_is_not_applicable() -> None:
    artifact = _artifact(evidence_kind="proof", evidence_summary="Paper proof.")

    result = validate_reproducibility_metadata((_record(artifact),), ())

    assert result.failures == ()
    assert result.applicable_count == 0
    assert result.checks[0].status == "not_applicable"


def test_gatekeeper_report_includes_reproducibility_metadata(tmp_path: Path) -> None:
    _write_yaml(tmp_path, "examples/constructions/repro.yaml", _artifact_data())
    checker_path = tmp_path / "experiments" / "evaluators" / "check_fixture.py"
    checker_path.parent.mkdir(parents=True, exist_ok=True)
    checker_path.write_text("print('repro checker pass')\n", encoding="utf-8")

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260601T000000000000Z",
    )

    assert result.report.verdict == "pass"
    gate_by_id = {gate.gate_id: gate for gate in result.report.gates}
    repro_gate = gate_by_id["G7"]
    assert repro_gate.name == "reproducibility metadata gate"
    assert repro_gate.status == "pass"
    assert repro_gate.details
    assert repro_gate.details[0]["artifact_id"] == "construction.fixture.repro"
    assert repro_gate.details[0]["status"] == "pass"

    report_json = json.loads(result.json_path.read_text(encoding="utf-8"))
    g7 = next(gate for gate in report_json["gates"] if gate["id"] == "G7")
    assert g7["status"] == "pass"
    assert g7["details"][0]["status"] == "pass"
    assert g7["details"][0]["required_metadata"]
