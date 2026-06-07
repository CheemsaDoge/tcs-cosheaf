from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from cosheaf.core.artifact import BaseArtifact
from cosheaf.gates.gatekeeper import run_gatekeeper
from cosheaf.storage.repo import RepoContext
from cosheaf.verification.lean_external import (
    ExternalLeanLibraryRefBackend,
    LeanLibraryRefAdapter,
    LeanLibraryRefBackendResult,
)
from cosheaf.verification.registry import default_verifier_registry
from cosheaf.verification.result import VerificationStatus


@dataclass
class FakeLeanLibraryRefBackend:
    name: str
    available: bool
    result: LeanLibraryRefBackendResult | None = None
    command_value: tuple[str, ...] = ("fake-lean",)
    version_value: str | None = "fake-lean 1.0"
    expected_cwd: Path | None = None
    timeout: bool = False
    startup_error: OSError | None = None

    seen_path: Path | None = None
    seen_source: str | None = None

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
    ) -> LeanLibraryRefBackendResult:
        if self.expected_cwd is not None:
            assert cwd == self.expected_cwd
        self.seen_path = lean_path
        self.seen_source = lean_path.read_text(encoding="utf-8")
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


def _formalization(
    *,
    status: str = "linked",
    import_path: str = "CSLib.Graph.Basic",
    symbol: str = "CSLib.Graph.Basic.fixture_symbol",
) -> dict[str, str]:
    return {
        "id": "cslib.fixture.link",
        "system": "lean4",
        "library": "CSLib",
        "library_ref": "cslib-main",
        "import_path": import_path,
        "symbol": symbol,
        "declaration_kind": "theorem",
        "status": status,
        "check_mode": "external_library_ref",
    }


def _artifact_data(
    *,
    artifact_id: str = "claim.fixture.lean-library-ref",
    formalizations: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": "claim",
        "title": "Lean library reference fixture",
        "domain": ["formalization"],
        "status": "draft",
        "created_at": "2026-06-07T00:00:00Z",
        "updated_at": "2026-06-07T00:00:00Z",
        "authors": ["tester"],
        "depends_on": [],
        "supersedes": [],
        "tags": ["lean"],
        "statement": "Fixture statement with an external Lean reference.",
        "evidence": [],
        "formalizations": formalizations
        if formalizations is not None
        else [_formalization()],
        "verification_policy": {
            "level": "source_reviewed_with_formal_link",
            "require_formal_link": True,
            "require_lean_check": False,
            "require_alignment_review": False,
        },
        "review": {"state": "requested", "notes": "Fixture review."},
        "risk": {"level": "low", "notes": "Fixture risk."},
    }


def _artifact(**kwargs: Any) -> BaseArtifact:
    return BaseArtifact.model_validate(_artifact_data(**kwargs))


def test_lean_library_ref_adapter_skips_planned_links_by_default(
    tmp_path: Path,
) -> None:
    artifact = _artifact(formalizations=[_formalization(status="planned")])
    adapter = LeanLibraryRefAdapter(
        backend=FakeLeanLibraryRefBackend(name="fake-lean", available=True),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert not adapter.can_verify(artifact, RepoContext(tmp_path))
    assert result.status is VerificationStatus.SKIPPED
    assert result.command is None
    assert "No linked or checked external Lean formalization" in result.message


def test_lean_library_ref_adapter_passes_with_fake_backend(
    tmp_path: Path,
) -> None:
    artifact = _artifact()
    fake_backend = FakeLeanLibraryRefBackend(
        name="fake-lean",
        available=True,
        expected_cwd=tmp_path,
        result=LeanLibraryRefBackendResult(
            exit_code=0,
            stdout="CSLib.Graph.Basic.fixture_symbol : Prop\n",
            stderr="",
        ),
    )
    adapter = LeanLibraryRefAdapter(backend=fake_backend)

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.PASS
    assert result.verifier == "lean_library_ref"
    assert result.exit_code == 0
    assert result.command is not None
    assert result.command[0] == "fake-lean"
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("formalization:cslib.fixture.link",)
    assert result.input_paths == ("formalization:cslib.fixture.link",)
    assert result.stdout_path
    assert result.stderr_path
    assert result.output_paths == (result.stderr_path, result.stdout_path)
    assert result.tool_name == "fake-lean"
    assert result.tool_version == "fake-lean 1.0"
    assert result.environment is not None
    assert "library_ref=cslib-main" in result.environment
    assert "alignment not checked" in result.message
    assert fake_backend.seen_source == (
        "import CSLib.Graph.Basic\n"
        "#check CSLib.Graph.Basic.fixture_symbol\n"
    )
    assert fake_backend.seen_path is not None
    assert not fake_backend.seen_path.exists()
    assert not fake_backend.seen_path.resolve().is_relative_to(tmp_path.resolve())
    assert "fixture_symbol" in (tmp_path / result.stdout_path).read_text(
        encoding="utf-8"
    )


def test_lean_library_ref_adapter_reports_nonzero_exit_as_fail(
    tmp_path: Path,
) -> None:
    artifact = _artifact()
    adapter = LeanLibraryRefAdapter(
        backend=FakeLeanLibraryRefBackend(
            name="fake-lean",
            available=True,
            result=LeanLibraryRefBackendResult(
                exit_code=1,
                stdout="",
                stderr="unknown identifier\n",
            ),
        )
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.FAIL
    assert result.exit_code == 1
    assert "returned nonzero exit code 1" in result.message


def test_lean_library_ref_adapter_skips_when_backend_is_unavailable(
    tmp_path: Path,
) -> None:
    artifact = _artifact()
    adapter = LeanLibraryRefAdapter(
        backend=FakeLeanLibraryRefBackend(name="fake-lean", available=False),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.SKIPPED
    assert not result.is_pass
    assert result.command == ("fake-lean",)
    assert result.cwd == str(tmp_path)
    assert result.evidence_paths == ("formalization:cslib.fixture.link",)
    assert result.tool_name == "fake-lean"
    assert "not available" in result.message
    assert not (tmp_path / ".cosheaf" / "logs").exists()


def test_lean_library_ref_adapter_reports_timeout_as_error(
    tmp_path: Path,
) -> None:
    artifact = _artifact()
    adapter = LeanLibraryRefAdapter(
        backend=FakeLeanLibraryRefBackend(
            name="fake-lean",
            available=True,
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


def test_lean_library_ref_adapter_rejects_multiline_import_or_symbol(
    tmp_path: Path,
) -> None:
    artifact = _artifact(
        formalizations=[
            _formalization(import_path="CSLib.Graph.Basic\n#eval boom")
        ]
    )
    adapter = LeanLibraryRefAdapter(
        backend=FakeLeanLibraryRefBackend(name="fake-lean", available=True),
    )

    result = adapter.verify(artifact, RepoContext(tmp_path))

    assert result.status is VerificationStatus.ERROR
    assert "must fit on one Lean command line" in result.message
    assert not (tmp_path / ".cosheaf" / "logs").exists()


def test_external_lean_library_ref_backend_supports_lake_env_command() -> None:
    backend = ExternalLeanLibraryRefBackend(
        lean_command="lean",
        lake_command="lake",
        use_lake=True,
    )

    command = backend.command(Path("check.lean"))

    assert command == ("lake", "env", "lean", "check.lean")


def test_default_registry_includes_lean_library_ref_adapter() -> None:
    registry = default_verifier_registry()

    assert "lean_library_ref" in registry.names


def test_gatekeeper_keeps_unavailable_lean_library_ref_skipped_not_pass(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("PATH", "")
    _write_yaml(
        tmp_path,
        "kb/draft/claims/lean-library-ref.yaml",
        _artifact_data(),
    )

    result = run_gatekeeper(
        RepoContext(tmp_path),
        timestamp="20260607T000000000000Z",
    )

    g6 = next(gate for gate in result.report.gates if gate.gate_id == "G6")
    assert g6.status == "skipped"
    assert g6.nonblocking_issues
    assert not g6.blocking_issues
    assert "lean_library_ref skipped" in g6.nonblocking_issues[0].message
