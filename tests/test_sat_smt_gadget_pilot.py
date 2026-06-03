from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationStatus
from cosheaf.verification.sat_adapter import SatAdapter

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "experiments" / "evaluators" / "check_sat_smt_gadget.py"
ARTIFACT = (
    ROOT
    / "kb"
    / "draft"
    / "constructions"
    / "construction.sat-smt-gadget.0001.yaml"
)
ASSIGNMENT = ROOT / "examples" / "sat" / "tiny-sat.assignment.json"


def test_sat_smt_gadget_checker_passes_on_pilot_artifact() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(ARTIFACT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "tiny SAT gadget verified: 3 variables, 3 clauses" in result.stdout


def test_sat_smt_gadget_checker_rejects_tampered_assignment(
    tmp_path: Path,
) -> None:
    tampered_assignment = tmp_path / "assignment.yaml"
    data = yaml.safe_load(ASSIGNMENT.read_text(encoding="utf-8"))
    data["assignment"]["2"] = True
    tampered_assignment.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )

    tampered_artifact = tmp_path / "construction.sat-smt-gadget.0001.yaml"
    text = ARTIFACT.read_text(encoding="utf-8")
    text = text.replace(
        "examples/sat/tiny-sat.assignment.json",
        tampered_assignment.as_posix(),
    )
    tampered_artifact.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CHECKER), str(tampered_artifact)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "clause 3 is not satisfied" in result.stderr


def test_sat_smt_gadget_sat_adapter_skips_without_solver() -> None:
    artifact = BaseArtifact.model_validate(
        yaml.safe_load(ARTIFACT.read_text(encoding="utf-8"))
    )

    result = SatAdapter(
        solver_command="__missing_sat_solver_for_cosheaf__"
    ).verify(artifact, RepoContext(ROOT))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.evidence_paths == ("examples/sat/tiny-sat.cnf",)
    assert "not available" in result.message
