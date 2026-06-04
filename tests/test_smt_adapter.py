from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import run_gatekeeper
from cosheaf.gates.reproducibility_gate import validate_reproducibility_metadata
from cosheaf.storage.loader import LoadedRecord
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.result import VerificationStatus
from cosheaf.verification.smt_adapter import (
    SmtAdapter,
    SmtBackendResult,
    _parse_solver_result,
)


@dataclass(frozen=True)
class FakeSmtBackend:
    name: str
    available: bool
    result: SmtBackendResult | None = None
    command_value: tuple[str, ...] = ("fake-smt", "-smt2")
    version_value: str | None = "fake-smt 1.0"
    expected_cwd: Path | None = None

    def command(self, smt_path: Path) -> tuple[str, ...]:
        return (*self.command_value, smt_path.as_posix())

    def version(self) -> str | None:
        return self.version_value

    def is_available(self) -> bool:
        return self.available

    def solve(
        self,
        smt_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> SmtBackendResult:
        if self.expected_cwd is not None:
            assert cwd == self.expected_cwd
        if self.result is None:
            raise AssertionError("fake backend solve called without a result")
        return self.result


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _write_smt2(repo_root: Path, relative_path: str) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "(set-logic QF_BOOL)\n(assert true)\n(check-sat)\n",
        encoding="utf-8",
    )
    return path


def _artifact_data(
    *,
    artifact_id: str = "construction.fixture.smt",
    evidence_path: str = "examples/smt/tiny.smt2",
    expected_satisfiable: bool = True,
    statement: str | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "construction",
        "title": "SMT fixture",
        "domain": ["satisfiability"],
        "status": "draft",
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["smt"],
        "statement": statement
        or (
            "Fixture SMT statement.\n\n"
            "CHECKER_DATA:\n"
            f"expected:\n  satisfiable: {str(expected_satisfiable).lower()}\n"
        ),
        "evidence": evidence
        if evidence is not None
        else [
            {
                "kind": "smt",
                "path": evidence_path,
                "summary": "Tiny SMT-LIB evidence.",
            }
        ],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _artifact(**kwargs: Any) -> BaseArtifact:
    return BaseArtifact.model_validate(_artifact_data(**kwargs))


def _loaded_record(artifact: BaseArtifact) -> LoadedRecord:
    return LoadedRecord(
        source_path=Path(f"kb/draft/constructions/{artifact.id}.yaml"),
        record=artifact,
    )


def test_smt_adapter_skips_when_no_smt_evidence(tmp_path: Path) -> None:
    artifact = _artifact(evidence=[])
    adapter = SmtAdapter(
        backend=FakeSmtBackend(name="fake-smt", available=True),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.command is None
    assert result.evidence_paths == ()
    assert "No SMT evidence" in result.message


def test_smt_adapter_skips_when_backend_is_unavailable(tmp_path: Path) -> None:
    _write_smt2(tmp_path, "examples/smt/tiny.smt2")
    artifact = _artifact()
    adapter = SmtAdapter(
        backend=FakeSmtBackend(name="fake-smt", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.command == ("fake-smt",)
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("examples/smt/tiny.smt2",)
    assert result.input_paths == ("examples/smt/tiny.smt2",)
    assert result.tool_name == "fake-smt"
    assert "not available" in result.message


def test_smt_adapter_rejects_external_absolute_evidence_before_backend_skip(
    tmp_path: Path,
) -> None:
    outside_path = tmp_path.parent / "external.smt2"
    artifact = _artifact(evidence_path=str(outside_path))
    adapter = SmtAdapter(
        backend=FakeSmtBackend(name="fake-smt", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert not result.is_skipped
    assert "SMT evidence path must stay inside repository" in result.message
    assert not (tmp_path / ".cosheaf" / "logs").exists()


def test_smt_adapter_reports_missing_evidence_file_as_error(tmp_path: Path) -> None:
    artifact = _artifact(evidence_path="examples/smt/missing.smt2")
    adapter = SmtAdapter(
        backend=FakeSmtBackend(name="fake-smt", available=True),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "SMT evidence file not found" in result.message


def test_smt_adapter_passes_satisfiable_toy_smt_with_fake_backend(
    tmp_path: Path,
) -> None:
    _write_smt2(tmp_path, "examples/smt/tiny.smt2")
    artifact = _artifact()
    adapter = SmtAdapter(
        backend=FakeSmtBackend(
            name="fake-smt",
            available=True,
            expected_cwd=tmp_path,
            result=SmtBackendResult(
                exit_code=0,
                stdout="sat\n",
                stderr="",
                result="sat",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.PASS
    assert result.exit_code == 0
    assert result.command == ("fake-smt", "-smt2", "examples/smt/tiny.smt2")
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("examples/smt/tiny.smt2",)
    assert result.input_paths == ("examples/smt/tiny.smt2",)
    assert result.stdout_path
    assert result.stderr_path
    assert result.output_paths == (result.stderr_path, result.stdout_path)
    assert result.tool_name == "fake-smt"
    assert result.tool_version == "fake-smt 1.0"
    assert result.environment is not None
    assert "result=sat" in result.environment
    assert result.message == "SMT backend result matched expected satisfiability: sat"
    assert (tmp_path / result.stdout_path).read_text(encoding="utf-8") == "sat\n"
    assert (tmp_path / result.stderr_path).read_text(encoding="utf-8") == ""


def test_smt_adapter_reports_mismatched_backend_result_as_fail(
    tmp_path: Path,
) -> None:
    _write_smt2(tmp_path, "examples/smt/tiny.smt2")
    artifact = _artifact(expected_satisfiable=True)
    adapter = SmtAdapter(
        backend=FakeSmtBackend(
            name="fake-smt",
            available=True,
            expected_cwd=tmp_path,
            result=SmtBackendResult(
                exit_code=0,
                stdout="unsat\n",
                stderr="",
                result="unsat",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.FAIL
    assert result.exit_code == 0
    assert "expected sat, got unsat" in result.message


def test_smt_adapter_reports_unknown_backend_result_as_error(tmp_path: Path) -> None:
    _write_smt2(tmp_path, "examples/smt/tiny.smt2")
    artifact = _artifact()
    adapter = SmtAdapter(
        backend=FakeSmtBackend(
            name="fake-smt",
            available=True,
            expected_cwd=tmp_path,
            result=SmtBackendResult(
                exit_code=0,
                stdout="unknown\n",
                stderr="",
                result="unknown",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code == 0
    assert "returned unknown" in result.message


def test_smt_adapter_executed_result_satisfies_reproducibility_metadata(
    tmp_path: Path,
) -> None:
    _write_smt2(tmp_path, "examples/smt/tiny.smt2")
    artifact = _artifact()
    result = SmtAdapter(
        backend=FakeSmtBackend(
            name="fake-smt",
            available=True,
            expected_cwd=tmp_path,
            result=SmtBackendResult(
                exit_code=0,
                stdout="sat\n",
                stderr="",
                result="sat",
            ),
        )
    ).verify(artifact, RepoContext(tmp_path))

    repro = validate_reproducibility_metadata(
        (_loaded_record(artifact),),
        (result,),
    )

    assert repro.failures == ()
    assert repro.checks[0].status == "pass"


def test_smt_solver_result_parser_uses_exact_status_lines() -> None:
    assert _parse_solver_result(stdout="unsat\n", stderr="") == "unsat"
    assert _parse_solver_result(stdout="sat\n", stderr="") == "sat"
    assert _parse_solver_result(stdout="unknown\n", stderr="") == "unknown"
    assert _parse_solver_result(stdout="s unsat\n", stderr="") == "unknown"
    assert _parse_solver_result(stdout="not-sat\n", stderr="") == "unknown"


def test_gatekeeper_keeps_unavailable_smt_backend_skipped_not_pass(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("PATH", "")
    _write_yaml(
        tmp_path,
        "kb/draft/constructions/smt.yaml",
        _artifact_data(),
    )
    _write_smt2(tmp_path, "examples/smt/tiny.smt2")

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260604T000000000000Z",
    )

    g6 = next(gate for gate in result.report.gates if gate.gate_id == "G6")
    assert g6.status == "skipped"
    assert g6.nonblocking_issues
    assert not g6.blocking_issues
    assert "smt skipped" in g6.nonblocking_issues[0].message
