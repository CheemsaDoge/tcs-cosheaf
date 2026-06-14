from __future__ import annotations

import subprocess
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
from cosheaf.verification.sat_adapter import SatAdapter, SatBackendResult


@dataclass(frozen=True)
class FakeSatBackend:
    name: str
    available: bool
    result: SatBackendResult | None = None
    command_value: tuple[str, ...] = ("fake-sat",)
    version_value: str | None = "fake-sat 1.0"
    expected_cwd: Path | None = None
    exception: Exception | None = None

    def command(self, cnf_path: Path) -> tuple[str, ...]:
        return (*self.command_value, cnf_path.as_posix())

    def version(self) -> str | None:
        return self.version_value

    def is_available(self) -> bool:
        return self.available

    def solve(
        self,
        cnf_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> SatBackendResult:
        if self.expected_cwd is not None:
            assert cwd == self.expected_cwd
        if self.exception is not None:
            raise self.exception
        if self.result is None:
            raise AssertionError("fake backend solve called without a result")
        return self.result


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _write_cnf(
    repo_root: Path,
    relative_path: str,
    content: str = "p cnf 1 1\n1 0\n",
) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _artifact_data(
    *,
    artifact_id: str = "construction.fixture.sat",
    evidence_path: str = "examples/sat/tiny.cnf",
    expected_satisfiable: bool = True,
    statement: str | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "construction",
        "title": "SAT fixture",
        "domain": ["satisfiability"],
        "status": "draft",
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["sat"],
        "statement": statement
        or (
            "Fixture SAT statement.\n\n"
            "CHECKER_DATA:\n"
            f"expected:\n  satisfiable: {str(expected_satisfiable).lower()}\n"
        ),
        "evidence": [
            {
                "kind": "sat",
                "path": evidence_path,
                "summary": "Tiny DIMACS CNF SAT evidence.",
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


def test_sat_adapter_skips_when_backend_is_unavailable(tmp_path: Path) -> None:
    artifact = _artifact()
    adapter = SatAdapter(
        backend=FakeSatBackend(name="fake-sat", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.command == ("fake-sat",)
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("examples/sat/tiny.cnf",)
    assert result.input_paths == ("examples/sat/tiny.cnf",)
    assert result.tool_name == "fake-sat"
    assert "not available" in result.message


def test_sat_adapter_passes_satisfiable_toy_cnf_with_fake_backend(
    tmp_path: Path,
) -> None:
    _write_cnf(tmp_path, "examples/sat/tiny.cnf")
    artifact = _artifact()
    adapter = SatAdapter(
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            result=SatBackendResult(
                exit_code=10,
                stdout="s SATISFIABLE\n",
                stderr="",
                result="sat",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.PASS
    assert result.exit_code == 10
    assert result.command == ("fake-sat", "examples/sat/tiny.cnf")
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("examples/sat/tiny.cnf",)
    assert result.input_paths == ("examples/sat/tiny.cnf",)
    assert result.stdout_path
    assert result.stderr_path
    assert result.output_paths == (result.stderr_path, result.stdout_path)
    assert result.tool_name == "fake-sat"
    assert result.tool_version == "fake-sat 1.0"
    assert result.environment is not None
    assert "result=sat" in result.environment
    assert "SAT backend result matched expected satisfiability: sat" == result.message
    assert (tmp_path / result.stdout_path).read_text(encoding="utf-8") == (
        "s SATISFIABLE\n"
    )
    assert (tmp_path / result.stderr_path).read_text(encoding="utf-8") == ""


def test_sat_adapter_passes_unsatisfiable_toy_cnf_with_fake_backend(
    tmp_path: Path,
) -> None:
    _write_cnf(
        tmp_path,
        "examples/sat/tiny-unsat.cnf",
        "p cnf 1 2\n1 0\n-1 0\n",
    )
    artifact = _artifact(
        artifact_id="construction.fixture.unsat",
        evidence_path="examples/sat/tiny-unsat.cnf",
        expected_satisfiable=False,
    )
    adapter = SatAdapter(
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            result=SatBackendResult(
                exit_code=20,
                stdout="s UNSATISFIABLE\n",
                stderr="",
                result="unsat",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.PASS
    assert result.exit_code == 20
    assert result.command == ("fake-sat", "examples/sat/tiny-unsat.cnf")
    assert result.cwd == str(tmp_path)
    assert result.timeout_seconds == 30.0
    assert result.input_paths == ("examples/sat/tiny-unsat.cnf",)
    assert result.stdout_path
    assert result.stderr_path
    assert result.tool_name == "fake-sat"
    assert result.tool_version == "fake-sat 1.0"
    assert result.environment is not None
    assert "result=unsat" in result.environment
    assert "SAT backend result matched expected satisfiability: unsat" == (
        result.message
    )
    assert (tmp_path / result.stdout_path).read_text(encoding="utf-8") == (
        "s UNSATISFIABLE\n"
    )
    assert (tmp_path / result.stderr_path).read_text(encoding="utf-8") == ""


def test_sat_adapter_reports_mismatched_backend_result_as_fail(
    tmp_path: Path,
) -> None:
    _write_cnf(tmp_path, "examples/sat/tiny.cnf")
    artifact = _artifact(expected_satisfiable=True)
    adapter = SatAdapter(
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            result=SatBackendResult(
                exit_code=20,
                stdout="s UNSATISFIABLE\n",
                stderr="",
                result="unsat",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.FAIL
    assert result.exit_code == 20
    assert "expected sat, got unsat" in result.message


def test_sat_adapter_reports_malformed_dimacs_as_error_with_logs(
    tmp_path: Path,
) -> None:
    _write_cnf(
        tmp_path,
        "examples/sat/malformed.cnf",
        "this is not a DIMACS CNF file\n",
    )
    artifact = _artifact(
        artifact_id="construction.fixture.malformed-sat",
        evidence_path="examples/sat/malformed.cnf",
    )
    adapter = SatAdapter(
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            result=SatBackendResult(
                exit_code=1,
                stdout="",
                stderr="parse error: expected DIMACS header\n",
                result="unknown",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code == 1
    assert result.command == ("fake-sat", "examples/sat/malformed.cnf")
    assert result.cwd == str(tmp_path)
    assert result.input_paths == ("examples/sat/malformed.cnf",)
    assert result.output_paths == (result.stderr_path, result.stdout_path)
    assert result.stdout_path
    assert result.stderr_path
    assert "unknown result" in result.message
    assert (tmp_path / result.stdout_path).read_text(encoding="utf-8") == ""
    assert (tmp_path / result.stderr_path).read_text(encoding="utf-8") == (
        "parse error: expected DIMACS header\n"
    )


def test_sat_adapter_reports_timeout_as_error_with_logs(
    tmp_path: Path,
) -> None:
    _write_cnf(tmp_path, "examples/sat/slow.cnf")
    artifact = _artifact(
        artifact_id="construction.fixture.timeout-sat",
        evidence_path="examples/sat/slow.cnf",
    )
    adapter = SatAdapter(
        timeout_seconds=0.25,
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            exception=subprocess.TimeoutExpired(
                cmd=("fake-sat", "examples/sat/slow.cnf"),
                timeout=0.25,
            ),
        ),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert result.command == ("fake-sat", "examples/sat/slow.cnf")
    assert result.cwd == str(tmp_path)
    assert result.timeout_seconds == 0.25
    assert result.input_paths == ("examples/sat/slow.cnf",)
    assert result.output_paths == (result.stderr_path, result.stdout_path)
    assert result.stdout_path
    assert result.stderr_path
    assert "timed out after 0.25 second(s)" in result.message
    assert (tmp_path / result.stdout_path).read_text(encoding="utf-8") == ""
    assert "timed out after 0.25 second(s)" in (
        tmp_path / result.stderr_path
    ).read_text(encoding="utf-8")


def test_sat_adapter_reports_malformed_expected_metadata_as_error(
    tmp_path: Path,
) -> None:
    _write_cnf(tmp_path, "examples/sat/tiny.cnf")
    artifact = _artifact(
        statement="Fixture SAT statement.\n\nCHECKER_DATA:\nexpected: [\n"
    )
    adapter = SatAdapter(
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            result=SatBackendResult(
                exit_code=10,
                stdout="s SATISFIABLE\n",
                stderr="",
                result="sat",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code == 10
    assert "expected-result metadata is invalid" in result.message


def test_sat_adapter_reports_malformed_evidence_path_as_error(
    tmp_path: Path,
) -> None:
    artifact = _artifact(evidence_path="../outside.cnf")
    adapter = SatAdapter(
        backend=FakeSatBackend(name="fake-sat", available=True),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "SAT evidence path must stay inside repository" in result.message


def test_sat_adapter_rejects_external_absolute_evidence_before_backend_skip(
    tmp_path: Path,
) -> None:
    outside_path = tmp_path.parent / "external.cnf"
    artifact = _artifact(evidence_path=str(outside_path))
    adapter = SatAdapter(
        backend=FakeSatBackend(name="fake-sat", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert not result.is_skipped
    assert "SAT evidence path must stay inside repository" in result.message
    assert not (tmp_path / ".cosheaf" / "logs").exists()


def test_sat_adapter_executed_result_satisfies_reproducibility_metadata(
    tmp_path: Path,
) -> None:
    _write_cnf(tmp_path, "examples/sat/tiny.cnf")
    artifact = _artifact()
    result = SatAdapter(
        backend=FakeSatBackend(
            name="fake-sat",
            available=True,
            expected_cwd=tmp_path,
            result=SatBackendResult(
                exit_code=10,
                stdout="s SATISFIABLE\n",
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


def test_gatekeeper_keeps_unavailable_sat_backend_skipped_not_pass(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("PATH", "")
    _write_yaml(
        tmp_path,
        "kb/draft/constructions/sat.yaml",
        _artifact_data(),
    )
    _write_cnf(tmp_path, "examples/sat/tiny.cnf")

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260604T000000000000Z",
    )

    g6 = next(gate for gate in result.report.gates if gate.gate_id == "G6")
    assert g6.status == "skipped"
    assert g6.nonblocking_issues
    assert not g6.blocking_issues
    assert "sat skipped" in g6.nonblocking_issues[0].message
