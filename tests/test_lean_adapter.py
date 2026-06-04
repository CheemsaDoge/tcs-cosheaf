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
from cosheaf.verification.lean_adapter import LeanAdapter, LeanBackendResult
from cosheaf.verification.result import VerificationStatus


@dataclass(frozen=True)
class FakeLeanBackend:
    name: str
    available: bool
    result: LeanBackendResult | None = None
    command_value: tuple[str, ...] = ("fake-lean",)
    version_value: str | None = "fake-lean 1.0"
    expected_cwd: Path | None = None
    timeout: bool = False
    startup_error: OSError | None = None

    def command(self, lean_path: Path) -> tuple[str, ...]:
        return (*self.command_value, lean_path.as_posix())

    def version(self) -> str | None:
        return self.version_value

    def is_available(self) -> bool:
        return self.available

    def check(
        self,
        lean_path: Path,
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> LeanBackendResult:
        if self.expected_cwd is not None:
            assert cwd == self.expected_cwd
        if self.timeout:
            raise subprocess.TimeoutExpired(cmd=self.command(lean_path), timeout=1)
        if self.startup_error is not None:
            raise self.startup_error
        if self.result is None:
            raise AssertionError("fake backend check called without a result")
        return self.result


def _write_yaml(repo_root: Path, relative_path: str, data: dict[str, Any]) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _write_lean(repo_root: Path, relative_path: str) -> Path:
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("theorem tiny : True := by trivial\n", encoding="utf-8")
    return path


def _artifact_data(
    *,
    artifact_id: str = "claim.fixture.lean",
    evidence_kind: str = "lean",
    evidence_path: str = "examples/lean/tiny.lean",
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Lean fixture",
        "domain": ["formalization"],
        "status": "draft",
        "created_at": "2026-06-04T00:00:00Z",
        "updated_at": "2026-06-04T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["lean"],
        "statement": "Fixture Lean statement.",
        "evidence": evidence
        if evidence is not None
        else [
            {
                "kind": evidence_kind,
                "path": evidence_path,
                "summary": "Tiny Lean evidence.",
            }
        ],
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _artifact(**kwargs: Any) -> BaseArtifact:
    return BaseArtifact.model_validate(_artifact_data(**kwargs))


def _loaded_record(artifact: BaseArtifact) -> LoadedRecord:
    return LoadedRecord(
        source_path=Path(f"kb/draft/claims/{artifact.id}.yaml"),
        record=artifact,
    )


def test_lean_adapter_skips_when_no_lean_evidence(tmp_path: Path) -> None:
    artifact = _artifact(evidence=[])
    adapter = LeanAdapter(
        backend=FakeLeanBackend(name="fake-lean", available=True),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.command is None
    assert result.evidence_paths == ()
    assert "No Lean evidence" in result.message


def test_lean_adapter_skips_when_backend_is_unavailable(tmp_path: Path) -> None:
    _write_lean(tmp_path, "examples/lean/tiny.lean")
    artifact = _artifact()
    adapter = LeanAdapter(
        backend=FakeLeanBackend(name="fake-lean", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.command == ("fake-lean",)
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("examples/lean/tiny.lean",)
    assert result.input_paths == ("examples/lean/tiny.lean",)
    assert result.tool_name == "fake-lean"
    assert "not available" in result.message


def test_lean_adapter_rejects_external_absolute_evidence_before_backend_skip(
    tmp_path: Path,
) -> None:
    outside_path = tmp_path.parent / "external.lean"
    artifact = _artifact(evidence_path=str(outside_path))
    adapter = LeanAdapter(
        backend=FakeLeanBackend(name="fake-lean", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert not result.is_skipped
    assert "Lean evidence path must stay inside repository" in result.message
    assert not (tmp_path / ".cosheaf" / "logs").exists()


def test_lean_adapter_reports_missing_evidence_file_before_backend_skip(
    tmp_path: Path,
) -> None:
    artifact = _artifact(evidence_path="examples/lean/missing.lean")
    adapter = LeanAdapter(
        backend=FakeLeanBackend(name="fake-lean", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert not result.is_skipped
    assert result.exit_code is None
    assert "Lean evidence file not found" in result.message


def test_lean_adapter_passes_tiny_lean_file_with_fake_backend(
    tmp_path: Path,
) -> None:
    _write_lean(tmp_path, "examples/lean/tiny.lean")
    artifact = _artifact()
    adapter = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            result=LeanBackendResult(
                exit_code=0,
                stdout="checked\n",
                stderr="",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.PASS
    assert result.exit_code == 0
    assert result.command == ("fake-lean", "examples/lean/tiny.lean")
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("examples/lean/tiny.lean",)
    assert result.input_paths == ("examples/lean/tiny.lean",)
    assert result.stdout_path
    assert result.stderr_path
    assert result.output_paths == (result.stderr_path, result.stdout_path)
    assert result.tool_name == "fake-lean"
    assert result.tool_version == "fake-lean 1.0"
    assert result.environment is not None
    assert "backend=fake-lean" in result.environment
    assert result.message == "Lean backend completed successfully."
    assert (tmp_path / result.stdout_path).read_text(encoding="utf-8") == "checked\n"
    assert (tmp_path / result.stderr_path).read_text(encoding="utf-8") == ""


def test_lean_adapter_reports_nonzero_exit_as_fail(tmp_path: Path) -> None:
    _write_lean(tmp_path, "examples/lean/tiny.lean")
    artifact = _artifact()
    adapter = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            result=LeanBackendResult(
                exit_code=1,
                stdout="",
                stderr="type mismatch\n",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.FAIL
    assert result.exit_code == 1
    assert "exit code 1" in result.message


def test_lean_adapter_reports_missing_backend_exit_code_as_error(
    tmp_path: Path,
) -> None:
    _write_lean(tmp_path, "examples/lean/tiny.lean")
    artifact = _artifact()
    adapter = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            result=LeanBackendResult(
                exit_code=None,
                stdout="",
                stderr="",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "did not report an exit code" in result.message


def test_lean_adapter_reports_timeout_as_error(tmp_path: Path) -> None:
    _write_lean(tmp_path, "examples/lean/tiny.lean")
    artifact = _artifact()
    adapter = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            timeout=True,
        ),
        timeout_seconds=1,
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "timed out" in result.message
    assert result.stderr_path
    assert "timed out" in (tmp_path / result.stderr_path).read_text(
        encoding="utf-8"
    )


def test_lean_adapter_reports_startup_error_as_error(tmp_path: Path) -> None:
    _write_lean(tmp_path, "examples/lean/tiny.lean")
    artifact = _artifact()
    adapter = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            startup_error=OSError("cannot start"),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert result.exit_code is None
    assert "failed to start" in result.message
    assert result.stderr_path
    assert "cannot start" in (tmp_path / result.stderr_path).read_text(
        encoding="utf-8"
    )


def test_lean_adapter_supports_lean_proof_evidence_kind(tmp_path: Path) -> None:
    _write_lean(tmp_path, "examples/lean/proof.lean")
    artifact = _artifact(
        evidence_kind="lean_proof",
        evidence_path="examples/lean/proof.lean",
    )
    adapter = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            result=LeanBackendResult(exit_code=0, stdout="", stderr=""),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert adapter.can_verify(artifact, RepoContext(tmp_path))
    assert result.status is VerificationStatus.PASS
    assert result.evidence_paths == ("examples/lean/proof.lean",)


def test_lean_adapter_executed_result_satisfies_reproducibility_metadata(
    tmp_path: Path,
) -> None:
    _write_lean(tmp_path, "examples/lean/proof.lean")
    artifact = _artifact(
        evidence_kind="lean_proof",
        evidence_path="examples/lean/proof.lean",
    )
    result = LeanAdapter(
        backend=FakeLeanBackend(
            name="fake-lean",
            available=True,
            expected_cwd=tmp_path,
            result=LeanBackendResult(
                exit_code=0,
                stdout="checked\n",
                stderr="",
            ),
        )
    ).verify(artifact, RepoContext(tmp_path))

    repro = validate_reproducibility_metadata(
        (_loaded_record(artifact),),
        (result,),
    )

    assert repro.failures == ()
    assert repro.checks[0].status == "pass"


def test_gatekeeper_keeps_unavailable_lean_backend_skipped_not_pass(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("PATH", "")
    _write_yaml(
        tmp_path,
        "kb/draft/claims/lean.yaml",
        _artifact_data(),
    )
    _write_lean(tmp_path, "examples/lean/tiny.lean")

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260604T000000000000Z",
    )

    g6 = next(gate for gate in result.report.gates if gate.gate_id == "G6")
    assert g6.status == "skipped"
    assert g6.nonblocking_issues
    assert not g6.blocking_issues
    assert "lean skipped" in g6.nonblocking_issues[0].message
