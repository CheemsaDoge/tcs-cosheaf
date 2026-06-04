from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cosheaf.core.artifact import BaseArtifact
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.lean_adapter import LeanAdapter
from cosheaf.verification.registry import default_verifier_registry
from cosheaf.verification.result import VerificationStatus
from cosheaf.verification.sat_adapter import SatAdapter
from cosheaf.verification.smt_adapter import SmtAdapter


def _artifact_with_evidence(kind: str, path: str) -> BaseArtifact:
    kind_slug = kind.replace("_", "-")
    return BaseArtifact.model_validate(
        {
            "id": f"claim.fixture.{kind_slug}",
            "type": "claim",
            "title": f"{kind} fixture",
            "domain": ["testing"],
            "status": "draft",
            "created_at": datetime(2026, 6, 1, tzinfo=UTC),
            "updated_at": datetime(2026, 6, 1, tzinfo=UTC),
            "authors": ["tester"],
            "depends_on": [],
            "supersedes": [],
            "tags": [],
            "statement": "Fixture statement.",
            "evidence": [
                {
                    "kind": kind,
                    "path": path,
                    "summary": f"{kind} skeleton evidence.",
                }
            ],
            "review": {"state": "requested", "notes": "Fixture review."},
            "risk": {"level": "low", "notes": "Fixture risk."},
        }
    )


def _assert_skipped_missing_tool(
    result_data: dict[str, Any],
    *,
    adapter_name: str,
    artifact_id: str,
    tool_name: str,
) -> None:
    assert result_data["verifier"] == adapter_name
    assert result_data["artifact_id"] == artifact_id
    assert result_data["status"] == "skipped"
    assert result_data["command"] == [tool_name]
    assert result_data["exit_code"] is None
    assert result_data["stdout_path"] is None
    assert result_data["stderr_path"] is None
    assert "not available" in result_data["message"]


def test_sat_adapter_skips_when_solver_is_unavailable(tmp_path: Path) -> None:
    artifact = _artifact_with_evidence("sat", "examples/formulas/a.cnf")
    adapter = SatAdapter(solver_command="__missing_sat_solver_for_cosheaf__")

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert adapter.can_verify(artifact, RepoContext(tmp_path))
    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    _assert_skipped_missing_tool(
        result.to_dict(),
        adapter_name="sat",
        artifact_id="claim.fixture.sat",
        tool_name="__missing_sat_solver_for_cosheaf__",
    )


def test_smt_adapter_skips_when_solver_is_unavailable(tmp_path: Path) -> None:
    smt_path = tmp_path / "examples" / "formulas" / "a.smt2"
    smt_path.parent.mkdir(parents=True, exist_ok=True)
    smt_path.write_text("(check-sat)\n", encoding="utf-8")
    artifact = _artifact_with_evidence("smt", "examples/formulas/a.smt2")
    adapter = SmtAdapter(solver_command="__missing_smt_solver_for_cosheaf__")

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert adapter.can_verify(artifact, RepoContext(tmp_path))
    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    _assert_skipped_missing_tool(
        result.to_dict(),
        adapter_name="smt",
        artifact_id="claim.fixture.smt",
        tool_name="__missing_smt_solver_for_cosheaf__",
    )


def test_lean_adapter_skips_when_lean_is_unavailable(tmp_path: Path) -> None:
    lean_path = tmp_path / "examples" / "lean" / "a.lean"
    lean_path.parent.mkdir(parents=True, exist_ok=True)
    lean_path.write_text("theorem a : True := by trivial\n", encoding="utf-8")
    artifact = _artifact_with_evidence("lean", "examples/lean/a.lean")
    adapter = LeanAdapter(lean_command="__missing_lean_for_cosheaf__")

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert adapter.can_verify(artifact, RepoContext(tmp_path))
    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    _assert_skipped_missing_tool(
        result.to_dict(),
        adapter_name="lean",
        artifact_id="claim.fixture.lean",
        tool_name="__missing_lean_for_cosheaf__",
    )


def test_optional_adapters_skip_artifacts_without_matching_evidence(
    tmp_path: Path,
) -> None:
    artifact = _artifact_with_evidence("python_checker", "checker.py")

    sat_result = SatAdapter("__missing_sat_solver_for_cosheaf__").verify(
        artifact,
        RepoContext(tmp_path),
    )
    smt_result = SmtAdapter("__missing_smt_solver_for_cosheaf__").verify(
        artifact,
        RepoContext(tmp_path),
    )
    lean_result = LeanAdapter("__missing_lean_for_cosheaf__").verify(
        artifact,
        RepoContext(tmp_path),
    )

    assert sat_result.status is VerificationStatus.SKIPPED
    assert smt_result.status is VerificationStatus.SKIPPED
    assert lean_result.status is VerificationStatus.SKIPPED
    assert "No SAT evidence" in sat_result.message
    assert "No SMT evidence" in smt_result.message
    assert "No Lean evidence" in lean_result.message


def test_default_registry_includes_optional_skeletons() -> None:
    registry = default_verifier_registry()

    assert registry.names == ("lean", "python_checker", "sat", "smt")
