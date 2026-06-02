from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from cosheaf.verification.base import VerifierAdapter
from cosheaf.verification.registry import VerifierRegistry, VerifierRegistryError
from cosheaf.verification.result import VerificationResult, VerificationStatus

STARTED_AT = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 1, 10, 1, tzinfo=UTC)


class DummyAdapter:
    def __init__(self, name: str) -> None:
        self.name = name

    def can_verify(self, artifact: Any, repo: Any) -> bool:
        return True

    def verify(self, artifact: Any, repo: Any) -> VerificationResult:
        return VerificationResult(
            verifier=self.name,
            artifact_id=artifact.id,
            status=VerificationStatus.PASS,
            started_at=STARTED_AT,
            ended_at=ENDED_AT,
            command=("dummy", "verify"),
            cwd=str(repo.repo_root),
            exit_code=0,
            stdout_path=None,
            stderr_path=None,
            evidence_paths=(),
            message="dummy pass",
        )


def test_pass_result_serializes_deterministically() -> None:
    result = VerificationResult(
        verifier="python-checker",
        artifact_id="claim.fixture.a",
        status=VerificationStatus.PASS,
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        command=("python", "-m", "pytest"),
        cwd=".",
        exit_code=0,
        stdout_path=".cosheaf/logs/stdout.txt",
        stderr_path=".cosheaf/logs/stderr.txt",
        evidence_paths=("evidence/z.txt", "evidence/a.txt"),
        message="checker passed",
    )

    serialized = result.to_dict()

    assert list(serialized) == [
        "verifier",
        "artifact_id",
        "status",
        "started_at",
        "ended_at",
        "command",
        "cwd",
        "exit_code",
        "stdout_path",
        "stderr_path",
        "evidence_paths",
        "timeout_seconds",
        "input_paths",
        "output_paths",
        "tool_name",
        "tool_version",
        "seed",
        "environment",
        "message",
    ]
    assert serialized["status"] == "pass"
    assert serialized["command"] == ["python", "-m", "pytest"]
    assert serialized["evidence_paths"] == ["evidence/a.txt", "evidence/z.txt"]
    assert result.is_pass
    assert not result.is_fail
    assert result.to_json() == result.to_json()


def test_fail_result_serializes_as_verification_failure() -> None:
    result = VerificationResult(
        verifier="python-checker",
        artifact_id="claim.fixture.a",
        status=VerificationStatus.FAIL,
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        command=("python", "check.py"),
        cwd=".",
        exit_code=1,
        stdout_path=None,
        stderr_path=".cosheaf/logs/stderr.txt",
        evidence_paths=(),
        message="counterexample found",
    )

    serialized = result.to_dict()

    assert serialized["status"] == "fail"
    assert result.is_fail
    assert not result.is_error
    assert serialized["exit_code"] == 1


def test_skipped_result_serializes_and_is_not_pass() -> None:
    result = VerificationResult(
        verifier="lean",
        artifact_id="claim.fixture.a",
        status=VerificationStatus.SKIPPED,
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        command=None,
        cwd=None,
        exit_code=None,
        stdout_path=None,
        stderr_path=None,
        evidence_paths=(),
        message="Lean is not installed",
    )

    serialized = result.to_dict()

    assert serialized["status"] == "skipped"
    assert not result.is_pass
    assert result.is_skipped


def test_error_result_is_distinct_from_fail() -> None:
    result = VerificationResult(
        verifier="smt",
        artifact_id="claim.fixture.a",
        status=VerificationStatus.ERROR,
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        command=("smt-check", "artifact.yaml"),
        cwd=".",
        exit_code=None,
        stdout_path=None,
        stderr_path=".cosheaf/logs/stderr.txt",
        evidence_paths=(),
        message="tool crashed before checking the artifact",
    )

    assert result.to_dict()["status"] == "error"
    assert result.is_error
    assert not result.is_fail


def test_external_command_requires_cwd() -> None:
    with pytest.raises(ValueError, match="cwd is required when command is recorded"):
        VerificationResult(
            verifier="python-checker",
            artifact_id="claim.fixture.a",
            status=VerificationStatus.PASS,
            started_at=STARTED_AT,
            ended_at=ENDED_AT,
            command=("python", "check.py"),
            cwd=None,
            exit_code=0,
            stdout_path=None,
            stderr_path=None,
            evidence_paths=(),
            message="missing cwd",
        )


def test_registry_can_register_adapters() -> None:
    adapter: VerifierAdapter = DummyAdapter("dummy")
    registry = VerifierRegistry()

    registry.register(adapter)

    assert registry.get("dummy") is adapter
    assert registry.names == ("dummy",)
    assert registry.adapters == (adapter,)


def test_duplicate_adapter_name_fails() -> None:
    registry = VerifierRegistry()
    registry.register(DummyAdapter("dummy"))

    with pytest.raises(VerifierRegistryError, match="duplicate verifier adapter"):
        registry.register(DummyAdapter("dummy"))
