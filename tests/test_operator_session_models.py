from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from cosheaf.operator_session import (
    OPERATOR_SESSION_AUTHORITY_NOTICE,
    SKIPPED_OPERATOR_SESSION_LIMITATION,
    OperatorArtifactRef,
    OperatorArtifactRefKind,
    OperatorCheckKind,
    OperatorCheckResult,
    OperatorCheckStatus,
    OperatorPolicyFinding,
    OperatorPolicyFindingSeverity,
    OperatorPolicyMode,
    OperatorSession,
    OperatorSessionStatus,
    OperatorToolCallRecord,
    OperatorToolCallStatus,
)

ROOT = Path(__file__).resolve().parents[1]
STARTED_AT = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
ENDED_AT = datetime(2026, 6, 16, 1, 1, tzinfo=UTC)


def test_operator_session_serializes_deterministically_with_authority_notice() -> None:
    session = (
        OperatorSession.start(
            session_id="session.issue.fixture.s20260616t010000z",
            issue_id="issue.fixture",
            policy_mode=OperatorPolicyMode.PRIVATE_RESEARCH,
            operator_label="external operator",
            now=STARTED_AT,
        )
        .with_artifact_ref(
            OperatorArtifactRef(
                kind=OperatorArtifactRefKind.DRAFT,
                path="kb/private/draft/claims/claim.fixture.yaml",
                artifact_id="claim.fixture",
                summary="draft reference only",
                scope="private",
            )
        )
        .with_check_result(
            OperatorCheckResult(
                kind=OperatorCheckKind.VALIDATE,
                status=OperatorCheckStatus.SKIPPED,
                summary=SKIPPED_OPERATOR_SESSION_LIMITATION,
                report_path=".cosheaf/reports/validate.json",
                recorded_at=STARTED_AT,
            )
        )
        .with_policy_finding(
            OperatorPolicyFinding(
                finding_id="finding.private-reference",
                severity=OperatorPolicyFindingSeverity.WARNING,
                code="private_reference",
                message="private draft reference is allowed in private mode",
                path="kb/private/draft/claims/claim.fixture.yaml",
            )
        )
        .finalize(now=ENDED_AT, status=OperatorSessionStatus.FINALIZED)
    )

    payload = session.to_dict()

    assert list(payload) == [
        "schema_version",
        "session_id",
        "issue_id",
        "policy_mode",
        "operator_label",
        "status",
        "started_at",
        "finalized_at",
        "base_commit",
        "head_commit",
        "artifact_refs",
        "check_results",
        "policy_findings",
        "limitations",
        "operator_notes",
        "authority_notice",
        "accepted_write_performed",
        "human_review_created",
        "promotion_performed",
        "verifier_result_mutated",
    ]
    assert payload["authority_notice"] == OPERATOR_SESSION_AUTHORITY_NOTICE
    assert payload["accepted_write_performed"] is False
    assert payload["human_review_created"] is False
    assert payload["promotion_performed"] is False
    assert payload["verifier_result_mutated"] is False
    assert session.to_json() == session.to_json()

    summary = session.summary()
    assert summary.session_id == session.session_id
    assert summary.artifact_ref_count == 1
    assert summary.check_result_count == 1
    assert summary.skipped_check_count == 1
    assert summary.blocking_finding_count == 0
    assert summary.accepted_write_performed is False


@pytest.mark.parametrize(
    "path",
    [
        "../outside.json",
        "C:/secret/session.json",
        "/tmp/session.json",
        "kb/accepted/claims/unsafe.yaml",
    ],
)
def test_operator_artifact_refs_reject_nonlocal_or_accepted_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        OperatorArtifactRef(kind=OperatorArtifactRefKind.DRAFT, path=path)


def test_operator_check_skipped_must_remain_not_pass() -> None:
    with pytest.raises(ValidationError, match="skipped is not pass"):
        OperatorCheckResult(
            kind=OperatorCheckKind.GATE,
            status=OperatorCheckStatus.SKIPPED,
            summary="optional tool unavailable",
            recorded_at=STARTED_AT,
        )


@pytest.mark.parametrize(
    "metadata",
    [
        {"api_key": "sk-secret-value"},
        {"chain_of_thought": "hidden internal reasoning"},
        {"stdout": "raw command output should not be stored"},
        {"environment": "PATH=C:/tools;TOKEN=ghp_secretValue"},
        {"input_path": "../outside.txt"},
        {"write_path": "kb/accepted/claims/unsafe.yaml"},
    ],
)
def test_operator_tool_call_metadata_rejects_secrets_hidden_reasoning_and_bad_paths(
    metadata: dict[str, str],
) -> None:
    with pytest.raises(ValidationError):
        OperatorToolCallRecord(
            event_id="event.tool.0001",
            tool_name="validate",
            status=OperatorToolCallStatus.COMPLETED,
            recorded_at=STARTED_AT,
            input_metadata=metadata,
        )


def test_operator_session_schema_file_defines_v1_contract() -> None:
    schema = json.loads(
        (ROOT / "schemas" / "operator_session.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "TCS-Cosheaf Operator Session"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == 1
    assert schema["properties"]["authority_notice"]["const"] == (
        OPERATOR_SESSION_AUTHORITY_NOTICE
    )
    assert schema["properties"]["accepted_write_performed"]["const"] is False
    assert schema["properties"]["human_review_created"]["const"] is False
    assert schema["properties"]["promotion_performed"]["const"] is False
    assert schema["properties"]["verifier_result_mutated"]["const"] is False
