from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.verification.evidence import (
    LEAN_REF_LIMITATION,
    SKIPPED_LIMITATION,
    VerifierEvidenceKind,
    VerifierEvidenceRecord,
)
from cosheaf.verification.result import VerificationResult, VerificationStatus

STARTED_AT = datetime(2026, 6, 14, 10, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 14, 10, 1, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[1]


def _verification_result(
    *,
    verifier: str = "python_checker",
    status: VerificationStatus = VerificationStatus.PASS,
    command: tuple[str, ...] | None = ("python", "checks/check.py"),
    cwd: str | None = ".",
    tool_name: str | None = "python",
    stdout_path: str | None = ".cosheaf/logs/check.stdout.log",
    stderr_path: str | None = ".cosheaf/logs/check.stderr.log",
    message: str = "checker passed",
) -> VerificationResult:
    return VerificationResult(
        verifier=verifier,
        artifact_id="claim.fixture.verifier-evidence",
        status=status,
        started_at=STARTED_AT,
        ended_at=ENDED_AT,
        command=command,
        cwd=cwd,
        exit_code=0 if status is VerificationStatus.PASS else None,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        evidence_paths=("checks/check.py",),
        timeout_seconds=30.0,
        input_paths=("checks/check.py", "kb/draft/claims/claim.fixture.yaml"),
        output_paths=tuple(
            path for path in (stderr_path, stdout_path) if path is not None
        ),
        tool_name=tool_name,
        tool_version="3.13.5" if tool_name == "python" else None,
        environment=None,
        message=message,
    )


def test_verifier_evidence_record_serializes_deterministically() -> None:
    record = VerifierEvidenceRecord(
        evidence_id="verifier-evidence.claim.fixture.verifier-evidence.python.habc123",
        artifact_id="claim.fixture.verifier-evidence",
        claim_id=None,
        verifier_kind=VerifierEvidenceKind.PYTHON,
        tool_name="python",
        tool_version="3.13.5",
        command_argv=("python", "checks/check.py"),
        cwd=".",
        result=VerificationStatus.PASS,
        reason_code="verifier_passed",
        stdout_path=".cosheaf/logs/check.stdout.log",
        stderr_path=".cosheaf/logs/check.stderr.log",
        log_path=None,
        created_at=ENDED_AT,
        checker_input_hash="sha256:" + "0" * 64,
        checker_output_hash=None,
        limitations=(
            "Verifier evidence is not human review.",
            "Verifier evidence does not auto-promote accepted knowledge.",
        ),
    )

    serialized = record.to_dict()

    assert list(serialized) == [
        "evidence_id",
        "artifact_id",
        "claim_id",
        "verifier_kind",
        "tool_name",
        "tool_version",
        "command_argv",
        "cwd",
        "result",
        "reason_code",
        "stdout_path",
        "stderr_path",
        "log_path",
        "created_at",
        "checker_input_hash",
        "checker_output_hash",
        "limitations",
    ]
    assert serialized["result"] == "pass"
    assert serialized["command_argv"] == ["python", "checks/check.py"]
    assert record.to_json() == record.to_json()


def test_verification_result_converts_to_evidence_record() -> None:
    result = _verification_result()

    first = result.to_evidence_record()
    second = result.to_evidence_record()

    assert first == second
    assert first.evidence_id.startswith(
        "verifier-evidence.claim.fixture.verifier-evidence.python.h"
    )
    assert first.verifier_kind is VerifierEvidenceKind.PYTHON
    assert first.result is VerificationStatus.PASS
    assert first.reason_code == "verifier_passed"
    assert first.tool_name == "python"
    assert first.command_argv == ("python", "checks/check.py")
    assert first.cwd == "."
    assert first.is_pass


def test_invalid_result_state_fails() -> None:
    with pytest.raises(ValidationError):
        VerifierEvidenceRecord.model_validate(
            {
                "evidence_id": (
                    "verifier-evidence.claim.fixture.verifier-evidence.python.hbad"
                ),
                "verifier_kind": "python",
                "tool_name": "python",
                "result": "unknown",
                "reason_code": "solver_unknown",
                "created_at": ENDED_AT.isoformat(),
                "limitations": ["Verifier evidence is not human review."],
            }
        )


def test_skipped_record_is_not_pass_and_records_limitation() -> None:
    result = _verification_result(
        verifier="lean",
        status=VerificationStatus.SKIPPED,
        command=("lean",),
        cwd=".",
        tool_name="lean",
        stdout_path=None,
        stderr_path=None,
        message="Lean backend is not available: lean",
    )

    record = result.to_evidence_record()

    assert record.result is VerificationStatus.SKIPPED
    assert record.reason_code == "verifier_skipped"
    assert record.is_skipped
    assert not record.is_pass
    assert SKIPPED_LIMITATION in record.limitations


def test_skipped_record_without_skipped_limitation_fails() -> None:
    with pytest.raises(ValidationError, match="skipped is not pass"):
        VerifierEvidenceRecord(
            evidence_id="verifier-evidence.claim.fixture.verifier-evidence.lean.hbad",
            artifact_id="claim.fixture.verifier-evidence",
            verifier_kind=VerifierEvidenceKind.LEAN,
            tool_name="lean",
            result=VerificationStatus.SKIPPED,
            reason_code="verifier_skipped",
            created_at=ENDED_AT,
            limitations=("Verifier evidence is not human review.",),
        )


def test_external_lean_reference_records_alignment_limitation() -> None:
    result = _verification_result(
        verifier="lean_library_ref",
        tool_name="lean",
        message="Lean external library reference checked; alignment not checked.",
    )

    record = result.to_evidence_record()

    assert record.verifier_kind is VerifierEvidenceKind.EXTERNAL_REFERENCE
    assert ".external-reference." in record.evidence_id
    assert LEAN_REF_LIMITATION in record.limitations
    assert "semantic alignment is not checked" in record.to_json()


def test_schema_file_defines_v1_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "verifier_evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "TCS-Cosheaf Verifier Evidence Record"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "evidence_id",
        "verifier_kind",
        "tool_name",
        "result",
        "reason_code",
        "created_at",
        "limitations",
    }
    assert schema["properties"]["result"]["enum"] == [
        "pass",
        "fail",
        "error",
        "skipped",
    ]
    assert schema["properties"]["verifier_kind"]["enum"] == [
        "python",
        "sat",
        "smt",
        "lean",
        "external_reference",
        "manual_note",
    ]
