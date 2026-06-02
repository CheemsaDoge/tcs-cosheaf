from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import run_gatekeeper
from cosheaf.storage.loader import load_yaml_file
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.python_checker import PythonCheckerAdapter
from cosheaf.verification.result import VerificationStatus


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _artifact_data(
    artifact_id: str = "construction.fixture.graph",
    *,
    checker_path: str = "experiments/evaluators/check_graph.py",
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "construction",
        "title": "Fixture graph",
        "domain": ["graph-theory"],
        "status": "draft",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["fixture"],
        "statement": "A fixture graph with three vertices and three edges.",
        "evidence": [
            {
                "kind": "python_checker",
                "path": checker_path,
                "summary": "Run the graph checker.",
            }
        ],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _write_artifact(
    repo_root: Path,
    *,
    checker_path: str = "experiments/evaluators/check_graph.py",
) -> BaseArtifact:
    path = _write_yaml(
        repo_root,
        "examples/constructions/graph.yaml",
        _artifact_data(checker_path=checker_path),
    )
    loaded = load_yaml_file(RepoContext(repo_root), path)
    assert isinstance(loaded.record, BaseArtifact)
    return loaded.record


def _write_checker(repo_root: Path, body: str) -> None:
    path = repo_root / "experiments" / "evaluators" / "check_graph.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_checker_pass_writes_logs(tmp_path: Path) -> None:
    artifact = _write_artifact(tmp_path)
    _write_checker(
        tmp_path,
        "import sys\nprint('checker stdout')\nprint(sys.argv[1])\n",
    )

    result = PythonCheckerAdapter(python_executable=sys.executable).verify(
        artifact,
        RepoContext(tmp_path),
    )

    assert result.status is VerificationStatus.PASS
    assert result.exit_code == 0
    assert result.command == (
        sys.executable,
        "experiments/evaluators/check_graph.py",
        "examples/constructions/graph.yaml",
    )
    assert result.cwd == str(tmp_path.resolve())
    assert result.stdout_path is not None
    assert result.stderr_path is not None
    stdout_path = tmp_path / result.stdout_path
    stderr_path = tmp_path / result.stderr_path
    assert stdout_path.read_text(encoding="utf-8").startswith("checker stdout")
    assert stderr_path.read_text(encoding="utf-8") == ""


def test_checker_fail_records_nonzero_exit(tmp_path: Path) -> None:
    artifact = _write_artifact(tmp_path)
    _write_checker(
        tmp_path,
        "import sys\nprint('bad graph', file=sys.stderr)\nsys.exit(7)\n",
    )

    result = PythonCheckerAdapter(python_executable=sys.executable).verify(
        artifact,
        RepoContext(tmp_path),
    )

    assert result.status is VerificationStatus.FAIL
    assert result.exit_code == 7
    assert result.stderr_path is not None
    assert "bad graph" in (tmp_path / result.stderr_path).read_text(encoding="utf-8")


def test_checker_missing_script_is_error(tmp_path: Path) -> None:
    artifact = _write_artifact(
        tmp_path,
        checker_path="experiments/evaluators/missing.py",
    )

    result = PythonCheckerAdapter(python_executable=sys.executable).verify(
        artifact,
        RepoContext(tmp_path),
    )

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "missing checker script" in result.message
    assert result.stderr_path is not None
    assert "missing checker script" in (
        tmp_path / result.stderr_path
    ).read_text(encoding="utf-8")


def test_checker_timeout_is_error(tmp_path: Path) -> None:
    artifact = _write_artifact(tmp_path)
    _write_checker(
        tmp_path,
        "import time\nprint('before sleep')\ntime.sleep(2)\n",
    )

    result = PythonCheckerAdapter(
        python_executable=sys.executable,
        timeout_seconds=0.1,
    ).verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "timed out" in result.message
    assert result.stdout_path is not None
    assert result.stderr_path is not None


def test_gatekeeper_sees_verifier_result(tmp_path: Path) -> None:
    _write_artifact(tmp_path)
    _write_checker(tmp_path, "print('gate checker pass')\n")

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260601T000000000000Z",
    )

    assert result.report.verdict == "pass"
    gate_by_id = {gate.gate_id: gate for gate in result.report.gates}
    verifier_gate = gate_by_id["G6"]
    assert verifier_gate.status == "pass"
    assert verifier_gate.details
    verifier_detail = verifier_gate.details[0]
    assert verifier_detail["status"] == "pass"
    assert verifier_detail["artifact_id"] == "construction.fixture.graph"

    report_json = json.loads(result.json_path.read_text(encoding="utf-8"))
    g6 = next(gate for gate in report_json["gates"] if gate["id"] == "G6")
    assert g6["details"][0]["status"] == "pass"
